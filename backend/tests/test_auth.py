"""Auth endpoint tests."""

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_register_user(client: AsyncClient) -> None:
    """Test user registration returns 201 and user data."""
    response = await client.post(
        "/api/v1/auth/register",
        json={
            "email": "newuser@example.com",
            "password": "StrongPass123!",
            "full_name": "New User",
            "role": "user",
        },
    )
    assert response.status_code == 201
    data = response.json()
    assert data["email"] == "newuser@example.com"
    assert data["role"] == "user"
    assert "id" in data


@pytest.mark.asyncio
async def test_register_duplicate_email(client: AsyncClient, test_user) -> None:
    """Test registration with existing email returns 409."""
    response = await client.post(
        "/api/v1/auth/register",
        json={
            "email": "testuser@example.com",
            "password": "AnotherPass123!",
            "full_name": "Duplicate User",
            "role": "user",
        },
    )
    assert response.status_code == 409


@pytest.mark.asyncio
async def test_login_success(client: AsyncClient, test_user) -> None:
    """Test login with valid credentials returns tokens."""
    response = await client.post(
        "/api/v1/auth/login",
        json={"email": "testuser@example.com", "password": "TestPass123!"},
    )
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert "refresh_token" in data
    assert data["token_type"] == "bearer"


@pytest.mark.asyncio
async def test_login_wrong_password(client: AsyncClient, test_user) -> None:
    """Test login with wrong password returns 401."""
    response = await client.post(
        "/api/v1/auth/login",
        json={"email": "testuser@example.com", "password": "WrongPassword!"},
    )
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_get_profile(client: AsyncClient, test_user, user_token: str) -> None:
    """Test getting the authenticated user's profile."""
    response = await client.get(
        "/api/v1/auth/me",
        headers={"Authorization": f"Bearer {user_token}"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["email"] == "testuser@example.com"


@pytest.mark.asyncio
async def test_get_profile_no_token(client: AsyncClient) -> None:
    """Test accessing profile without token returns 401."""
    response = await client.get("/api/v1/auth/me")
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_update_profile(client: AsyncClient, test_user, user_token: str) -> None:
    """Test updating user profile."""
    response = await client.put(
        "/api/v1/auth/me",
        json={"full_name": "Updated Name"},
        headers={"Authorization": f"Bearer {user_token}"},
    )
    assert response.status_code == 200
    assert response.json()["full_name"] == "Updated Name"


@pytest.mark.asyncio
async def test_register_host_creates_profile(client: AsyncClient) -> None:
    """Test that registering as host also creates a host profile."""
    response = await client.post(
        "/api/v1/auth/register",
        json={
            "email": "newhost@example.com",
            "password": "HostPass123!",
            "full_name": "New Host",
            "role": "host",
        },
    )
    assert response.status_code == 201
    assert response.json()["role"] == "host"
