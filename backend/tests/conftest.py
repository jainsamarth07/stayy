"""Shared test fixtures and async test database setup."""

import uuid
from collections.abc import AsyncGenerator

import pytest_asyncio
from fastapi import Depends, HTTPException
from fastapi.security import HTTPAuthorizationCredentials
from httpx import ASGITransport, AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.core.security import create_access_token, decode_token, hash_password
from app.database import Base, get_db
from app.dependencies import bearer_scheme, get_current_user
from app.main import app
from app.models.user import HostProfile, User

# Use an in-memory SQLite for tests — swap to test Postgres in CI
TEST_DATABASE_URL = "sqlite+aiosqlite:///./test.db"

engine = create_async_engine(TEST_DATABASE_URL, echo=False)
TestSessionLocal = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


@pytest_asyncio.fixture(autouse=True)
async def setup_database():
    """Create tables before each test and drop after."""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)
    yield
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


@pytest_asyncio.fixture
async def db_session() -> AsyncGenerator[AsyncSession, None]:
    """Provide a clean database session for each test."""
    async with TestSessionLocal() as session:
        yield session


@pytest_asyncio.fixture
async def client(db_session: AsyncSession) -> AsyncGenerator[AsyncClient, None]:
    """Provide an async HTTP client wired to the test database."""

    async def override_get_db():
        try:
            yield db_session
            await db_session.commit()
        except Exception:
            await db_session.rollback()
            raise

    app.dependency_overrides[get_db] = override_get_db

    async def override_get_current_user(
        credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
    ):
        """Decode JWT tokens for test auth instead of BetterAuth sessions."""
        if credentials is None:
            raise HTTPException(
                status_code=401,
                detail="Not authenticated",
                headers={"WWW-Authenticate": "Bearer"},
            )
        token = credentials.credentials
        payload = decode_token(token)
        if payload is None:
            raise HTTPException(status_code=401, detail="Invalid token")
        user_id = payload.get("sub")
        if user_id is None:
            raise HTTPException(status_code=401, detail="Invalid token payload")
        result = await db_session.execute(
            select(User).where(User.id == uuid.UUID(user_id))
        )
        user = result.scalar_one_or_none()
        if user is None:
            raise HTTPException(status_code=401, detail="User not found")
        if not user.is_active:
            raise HTTPException(status_code=401, detail="Account is inactive")
        return user

    app.dependency_overrides[get_current_user] = override_get_current_user

    transport = ASGITransport(app=app)
    async with AsyncClient(
        transport=transport,
        base_url="http://test",
        headers={"Origin": "http://localhost:3000"},  # Satisfy CSRF middleware
    ) as ac:
        yield ac
    app.dependency_overrides.clear()


@pytest_asyncio.fixture
async def test_user(db_session: AsyncSession) -> User:
    """Create a regular test user."""
    user = User(
        id=uuid.uuid4(),
        email="testuser@example.com",
        hashed_password=hash_password("TestPass123!"),
        full_name="Test User",
        role="user",
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    return user


@pytest_asyncio.fixture
async def test_host(db_session: AsyncSession) -> User:
    """Create a test host with profile."""
    user = User(
        id=uuid.uuid4(),
        email="testhost@example.com",
        hashed_password=hash_password("TestPass123!"),
        full_name="Test Host",
        role="host",
    )
    db_session.add(user)
    await db_session.flush()

    profile = HostProfile(user_id=user.id)
    db_session.add(profile)
    await db_session.commit()
    await db_session.refresh(user)
    return user


@pytest_asyncio.fixture
async def test_admin(db_session: AsyncSession) -> User:
    """Create a test admin user."""
    user = User(
        id=uuid.uuid4(),
        email="admin@example.com",
        hashed_password=hash_password("AdminPass123!"),
        full_name="Admin User",
        role="admin",
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    return user


@pytest_asyncio.fixture
def user_token(test_user: User) -> str:
    """JWT token for the test user."""
    return create_access_token({"sub": str(test_user.id), "role": test_user.role})


@pytest_asyncio.fixture
def host_token(test_host: User) -> str:
    """JWT token for the test host."""
    return create_access_token({"sub": str(test_host.id), "role": test_host.role})


@pytest_asyncio.fixture
def admin_token(test_admin: User) -> str:
    """JWT token for the test admin."""
    return create_access_token({"sub": str(test_admin.id), "role": test_admin.role})


@pytest_asyncio.fixture
async def test_guest(db_session: AsyncSession) -> User:
    """Create a second guest user for multi-party tests."""
    user = User(
        id=uuid.uuid4(),
        email="guest2@example.com",
        hashed_password=hash_password("GuestPass123!"),
        full_name="Second Guest",
        role="user",
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    return user


@pytest_asyncio.fixture
def guest_token(test_guest: User) -> str:
    """JWT token for the second guest."""
    return create_access_token({"sub": str(test_guest.id), "role": test_guest.role})


@pytest_asyncio.fixture
async def second_host(db_session: AsyncSession) -> User:
    """Create a second host user with profile."""
    user = User(
        id=uuid.uuid4(),
        email="host2@example.com",
        hashed_password=hash_password("HostPass123!"),
        full_name="Second Host",
        role="host",
    )
    db_session.add(user)
    await db_session.flush()
    profile = HostProfile(user_id=user.id)
    db_session.add(profile)
    await db_session.commit()
    await db_session.refresh(user)
    return user


@pytest_asyncio.fixture
def second_host_token(second_host: User) -> str:
    """JWT token for the second host."""
    return create_access_token({"sub": str(second_host.id), "role": second_host.role})


@pytest_asyncio.fixture
async def host_with_membership(client: AsyncClient, host_token: str) -> str:
    """Subscribe the test host to a basic plan and return the host_token."""
    await client.post(
        "/api/v1/memberships/subscribe",
        json={"plan_type": "basic", "payment_token": "tok_fixture"},
        headers={"Authorization": f"Bearer {host_token}"},
    )
    return host_token


@pytest_asyncio.fixture
async def created_property(client: AsyncClient, host_with_membership: str) -> dict:
    """Create a property and return its JSON response data."""
    response = await client.post(
        "/api/v1/properties",
        json={
            "title": "Fixture Property",
            "description": "A lovely fixture property for testing purposes",
            "city": "Portland",
            "address": "456 Test Avenue, Portland",
            "price_per_night": 120.0,
            "max_guests": 4,
            "amenities": ["wifi", "parking"],
        },
        headers={"Authorization": f"Bearer {host_with_membership}"},
    )
    assert response.status_code == 201
    return response.json()
