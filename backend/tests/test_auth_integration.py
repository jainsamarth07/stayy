"""Integration tests for auth endpoints — extended scenarios."""

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_refresh_token_flow(client: AsyncClient, test_user) -> None:
    """Login and use refresh token to get new access token."""
    login_resp = await client.post(
        "/api/v1/auth/login",
        json={"email": "testuser@example.com", "password": "TestPass123!"},
    )
    assert login_resp.status_code == 200
    refresh_token = login_resp.json()["refresh_token"]

    response = await client.post(
        "/api/v1/auth/refresh",
        json={"refresh_token": refresh_token},
    )
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert "refresh_token" in data
    assert data["token_type"] == "bearer"


@pytest.mark.asyncio
async def test_refresh_token_invalid(client: AsyncClient) -> None:
    """Invalid refresh token returns 401."""
    response = await client.post(
        "/api/v1/auth/refresh",
        json={"refresh_token": "invalid.token.here"},
    )
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_change_password_success(
    client: AsyncClient, test_user, user_token: str
) -> None:
    """User can change their password."""
    response = await client.put(
        "/api/v1/auth/me/password",
        json={
            "current_password": "TestPass123!",
            "new_password": "NewSecurePass456!",
        },
        headers={"Authorization": f"Bearer {user_token}"},
    )
    assert response.status_code == 200
    assert response.json()["message"] == "Password changed successfully"

    # Can login with new password
    login_resp = await client.post(
        "/api/v1/auth/login",
        json={"email": "testuser@example.com", "password": "NewSecurePass456!"},
    )
    assert login_resp.status_code == 200


@pytest.mark.asyncio
async def test_change_password_wrong_current(
    client: AsyncClient, test_user, user_token: str
) -> None:
    """Changing password with wrong current password returns 401."""
    response = await client.put(
        "/api/v1/auth/me/password",
        json={
            "current_password": "WrongPassword!",
            "new_password": "NewPass456!",
        },
        headers={"Authorization": f"Bearer {user_token}"},
    )
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_forgot_password(client: AsyncClient) -> None:
    """Forgot password always returns success (no email enumeration)."""
    response = await client.post(
        "/api/v1/auth/forgot-password",
        json={"email": "anyone@example.com"},
    )
    assert response.status_code == 200
    assert "reset link" in response.json()["message"].lower()


@pytest.mark.asyncio
async def test_reset_password_invalid_token(client: AsyncClient) -> None:
    """Reset password with invalid token returns 401."""
    response = await client.post(
        "/api/v1/auth/reset-password",
        json={"token": "invalid.token.here", "new_password": "NewPass123!"},
    )
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_login_inactive_user(client: AsyncClient, db_session) -> None:
    """Inactive user cannot login."""
    import uuid

    from app.core.security import hash_password
    from app.models.user import User
    user = User(
        id=uuid.uuid4(),
        email="inactive@example.com",
        hashed_password=hash_password("InactivePass123!"),
        full_name="Inactive User",
        role="user",
        is_active=False,
    )
    db_session.add(user)
    await db_session.commit()

    response = await client.post(
        "/api/v1/auth/login",
        json={"email": "inactive@example.com", "password": "InactivePass123!"},
    )
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_register_with_phone(client: AsyncClient) -> None:
    """Register with optional phone field."""
    response = await client.post(
        "/api/v1/auth/register",
        json={
            "email": "phoneuser@example.com",
            "password": "PhonePass123!",
            "full_name": "Phone User",
            "phone": "+1234567890",
            "role": "user",
        },
    )
    assert response.status_code == 201
    data = response.json()
    assert data["phone"] == "+1234567890"


@pytest.mark.asyncio
async def test_update_profile_phone(
    client: AsyncClient, test_user, user_token: str
) -> None:
    """Update profile with phone field."""
    response = await client.put(
        "/api/v1/auth/me",
        json={"phone": "+9876543210"},
        headers={"Authorization": f"Bearer {user_token}"},
    )
    assert response.status_code == 200
    assert response.json()["phone"] == "+9876543210"
