"""Admin endpoint tests."""

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_admin_list_users(client: AsyncClient, admin_token: str, test_user) -> None:
    """Admin can list all users."""
    response = await client.get(
        "/api/v1/admin/users",
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert response.status_code == 200
    data = response.json()
    assert "items" in data
    assert "total" in data
    assert data["total"] >= 1


@pytest.mark.asyncio
async def test_admin_list_users_unauthorized(client: AsyncClient, user_token: str) -> None:
    """Non-admin user cannot access admin endpoints."""
    response = await client.get(
        "/api/v1/admin/users",
        headers={"Authorization": f"Bearer {user_token}"},
    )
    assert response.status_code == 403


@pytest.mark.asyncio
async def test_admin_list_users_no_auth(client: AsyncClient) -> None:
    """Unauthenticated request is rejected."""
    response = await client.get("/api/v1/admin/users")
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_admin_dashboard(client: AsyncClient, admin_token: str) -> None:
    """Admin dashboard returns platform statistics."""
    response = await client.get(
        "/api/v1/admin/dashboard",
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert response.status_code == 200
    data = response.json()
    assert "total_users" in data
    assert "total_properties" in data
    assert "total_bookings" in data


@pytest.mark.asyncio
async def test_admin_list_properties(client: AsyncClient, admin_token: str) -> None:
    """Admin can list all properties."""
    response = await client.get(
        "/api/v1/admin/properties",
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert response.status_code == 200
    data = response.json()
    assert "items" in data
    assert "total" in data


@pytest.mark.asyncio
async def test_admin_list_memberships(client: AsyncClient, admin_token: str) -> None:
    """Admin can list all memberships."""
    response = await client.get(
        "/api/v1/admin/memberships",
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert response.status_code == 200
    data = response.json()
    assert "items" in data
    assert data["page"] == 1
