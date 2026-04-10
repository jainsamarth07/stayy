"""Integration tests for admin endpoints — extended scenarios."""

import uuid

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_admin_list_bookings(client: AsyncClient, admin_token: str) -> None:
    """Admin can list all bookings."""
    response = await client.get(
        "/api/v1/admin/bookings",
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert response.status_code == 200
    data = response.json()
    assert "items" in data
    assert "total" in data


@pytest.mark.asyncio
async def test_admin_toggle_user_status(
    client: AsyncClient, admin_token: str, test_user
) -> None:
    """Admin can toggle a user's active status."""
    response = await client.put(
        f"/api/v1/admin/users/{test_user.id}/status",
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["is_active"] is False

    # Toggle back
    response2 = await client.put(
        f"/api/v1/admin/users/{test_user.id}/status",
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert response2.status_code == 200
    assert response2.json()["is_active"] is True


@pytest.mark.asyncio
async def test_admin_toggle_nonexistent_user(
    client: AsyncClient, admin_token: str
) -> None:
    """Toggling a nonexistent user returns 404."""
    response = await client.put(
        f"/api/v1/admin/users/{uuid.uuid4()}/status",
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_admin_dashboard_with_data(
    client: AsyncClient,
    admin_token: str,
    host_with_membership: str,
    user_token: str,
    created_property: dict,
) -> None:
    """Dashboard shows correct statistics when data exists."""
    response = await client.get(
        "/api/v1/admin/dashboard",
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["total_users"] >= 2
    assert data["total_properties"] >= 1
    assert data["active_members"] >= 1
    assert "monthly_revenue" in data


@pytest.mark.asyncio
async def test_admin_list_properties_with_data(
    client: AsyncClient, admin_token: str, created_property: dict
) -> None:
    """Admin properties list returns data."""
    response = await client.get(
        "/api/v1/admin/properties",
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["total"] >= 1
    assert len(data["items"]) >= 1
    # Check item structure
    item = data["items"][0]
    assert "id" in item
    assert "title" in item
    assert "city" in item
    assert "is_active" in item


@pytest.mark.asyncio
async def test_admin_list_memberships_with_data(
    client: AsyncClient, admin_token: str, host_with_membership: str
) -> None:
    """Admin memberships list returns data."""
    response = await client.get(
        "/api/v1/admin/memberships",
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["total"] >= 1
    item = data["items"][0]
    assert "id" in item
    assert "plan_type" in item
    assert "status" in item
    assert "amount" in item


@pytest.mark.asyncio
async def test_admin_list_bookings_with_data(
    client: AsyncClient,
    admin_token: str,
    user_token: str,
    created_property: dict,
) -> None:
    """Admin bookings list returns data when bookings exist."""
    from datetime import UTC, datetime, timedelta

    ci = (datetime.now(UTC) + timedelta(days=300)).isoformat()
    co = (datetime.now(UTC) + timedelta(days=305)).isoformat()
    await client.post(
        "/api/v1/bookings",
        json={"property_id": created_property["id"], "check_in": ci, "check_out": co},
        headers={"Authorization": f"Bearer {user_token}"},
    )

    response = await client.get(
        "/api/v1/admin/bookings",
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["total"] >= 1
    item = data["items"][0]
    assert "id" in item
    assert "status" in item
    assert "total_price" in item


@pytest.mark.asyncio
async def test_admin_list_users_pagination(
    client: AsyncClient, admin_token: str, test_user, test_host
) -> None:
    """Admin user list supports pagination."""
    response = await client.get(
        "/api/v1/admin/users",
        params={"page": 1, "page_size": 1},
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert response.status_code == 200
    data = response.json()
    assert len(data["items"]) == 1
    assert data["total"] >= 2


@pytest.mark.asyncio
async def test_admin_endpoints_forbidden_for_host(
    client: AsyncClient, host_token: str
) -> None:
    """Host cannot access admin endpoints."""
    for endpoint in ["/api/v1/admin/users", "/api/v1/admin/properties",
                     "/api/v1/admin/memberships", "/api/v1/admin/bookings",
                     "/api/v1/admin/dashboard"]:
        response = await client.get(
            endpoint,
            headers={"Authorization": f"Bearer {host_token}"},
        )
        assert response.status_code == 403, f"Expected 403 for {endpoint}"
