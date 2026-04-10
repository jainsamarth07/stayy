"""Authentication service — registration, login, token management."""

import logging
import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import ConflictError, UnauthorizedError
from app.core.security import (
    create_access_token,
    create_refresh_token,
    decode_token,
    hash_password,
    verify_password,
)
from app.models.user import HostProfile, User
from app.schemas.user import TokenResponse, UserRegister

logger = logging.getLogger(__name__)


async def register_user(db: AsyncSession, data: UserRegister) -> User:
    """Register a new user. Creates a HostProfile if role is 'host'."""
    existing = await db.execute(select(User).where(User.email == data.email))
    if existing.scalar_one_or_none() is not None:
        raise ConflictError("A user with this email already exists")

    user = User(
        email=data.email,
        hashed_password=hash_password(data.password),
        full_name=data.full_name,
        phone=data.phone,
        role=data.role,
    )
    db.add(user)
    await db.flush()

    if data.role == "host":
        host_profile = HostProfile(user_id=user.id)
        db.add(host_profile)
        await db.flush()

    # Trigger welcome email asynchronously
    try:
        from app.tasks.email_tasks import send_welcome_email
        send_welcome_email.delay(user.email, user.full_name)
    except Exception:
        logger.warning("Failed to queue welcome email", exc_info=True)

    return user


async def authenticate_user(db: AsyncSession, email: str, password: str) -> TokenResponse:
    """Authenticate user and return JWT tokens."""
    result = await db.execute(select(User).where(User.email == email))
    user = result.scalar_one_or_none()

    if user is None or not verify_password(password, user.hashed_password):
        raise UnauthorizedError("Incorrect email or password")

    if not user.is_active:
        raise UnauthorizedError("Account is deactivated")

    access_token = create_access_token({"sub": str(user.id), "role": user.role})
    refresh_token = create_refresh_token({"sub": str(user.id), "role": user.role})

    return TokenResponse(access_token=access_token, refresh_token=refresh_token)


async def refresh_access_token(db: AsyncSession, refresh_token_str: str) -> TokenResponse:
    """Issue a new access token using a valid refresh token."""
    payload = decode_token(refresh_token_str)
    if payload is None or payload.get("type") != "refresh":
        raise UnauthorizedError("Invalid refresh token")

    user_id = payload.get("sub")
    result = await db.execute(select(User).where(User.id == uuid.UUID(user_id)))
    user = result.scalar_one_or_none()

    if user is None or not user.is_active:
        raise UnauthorizedError("User not found or inactive")

    # Check if refresh token was issued before last password change
    if user.password_changed_at is not None:
        token_iat = payload.get("iat")
        if token_iat is not None and token_iat < user.password_changed_at.timestamp():
            raise UnauthorizedError("Token invalidated by password change")

    access_token = create_access_token({"sub": str(user.id), "role": user.role})
    new_refresh = create_refresh_token({"sub": str(user.id), "role": user.role})

    return TokenResponse(access_token=access_token, refresh_token=new_refresh)
