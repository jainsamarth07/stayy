"""Review endpoint tests."""

import uuid

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_create_review_requires_auth(client: AsyncClient) -> None:
    """Test creating a review requires authentication."""
    response = await client.post(
        "/api/v1/reviews",
        json={
            "booking_id": str(uuid.uuid4()),
            "rating": 4.5,
            "comment": "Great place!",
        },
    )
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_create_review_invalid_booking(client: AsyncClient, user_token: str) -> None:
    """Test creating a review for nonexistent booking returns 404."""
    response = await client.post(
        "/api/v1/reviews",
        json={
            "booking_id": str(uuid.uuid4()),
            "rating": 4.5,
            "comment": "Great stay!",
        },
        headers={"Authorization": f"Bearer {user_token}"},
    )
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_list_property_reviews_empty(client: AsyncClient) -> None:
    """Test listing reviews for a property when none exist."""
    response = await client.get(f"/api/v1/reviews/property/{uuid.uuid4()}")
    assert response.status_code == 200
    data = response.json()
    assert data["items"] == []
    assert data["total"] == 0
