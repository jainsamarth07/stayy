"""Booking endpoint tests."""

import uuid

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_create_booking_requires_auth(client: AsyncClient) -> None:
    """Test that creating a booking requires authentication."""
    response = await client.post(
        "/api/v1/bookings",
        json={
            "property_id": str(uuid.uuid4()),
            "check_in": "2026-04-01T14:00:00Z",
            "check_out": "2026-04-05T11:00:00Z",
        },
    )
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_list_bookings_empty(client: AsyncClient, user_token: str) -> None:
    """Test listing bookings when none exist."""
    response = await client.get(
        "/api/v1/bookings",
        headers={"Authorization": f"Bearer {user_token}"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["items"] == []
    assert data["total"] == 0


@pytest.mark.asyncio
async def test_create_booking_invalid_property(client: AsyncClient, user_token: str) -> None:
    """Test booking a nonexistent property returns 404."""
    response = await client.post(
        "/api/v1/bookings",
        json={
            "property_id": str(uuid.uuid4()),
            "check_in": "2026-04-01T14:00:00Z",
            "check_out": "2026-04-05T11:00:00Z",
        },
        headers={"Authorization": f"Bearer {user_token}"},
    )
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_get_nonexistent_booking(client: AsyncClient, user_token: str) -> None:
    """Test getting a booking that doesn't exist returns 404."""
    response = await client.get(
        f"/api/v1/bookings/{uuid.uuid4()}",
        headers={"Authorization": f"Bearer {user_token}"},
    )
    assert response.status_code == 404
