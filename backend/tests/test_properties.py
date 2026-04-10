"""Property endpoint tests."""

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_search_properties_empty(client: AsyncClient) -> None:
    """Test searching properties when none exist returns empty list."""
    response = await client.get("/api/v1/properties")
    assert response.status_code == 200
    data = response.json()
    assert data["items"] == []
    assert data["total"] == 0


@pytest.mark.asyncio
async def test_create_property_requires_host(client: AsyncClient, user_token: str) -> None:
    """Test that regular users cannot create properties."""
    response = await client.post(
        "/api/v1/properties",
        json={
            "title": "Test Property",
            "description": "A nice place to stay",
            "city": "Portland",
            "address": "123 Main St",
            "price_per_night": 100.0,
            "max_guests": 4,
        },
        headers={"Authorization": f"Bearer {user_token}"},
    )
    assert response.status_code == 403


@pytest.mark.asyncio
async def test_create_property_requires_membership(
    client: AsyncClient, host_token: str
) -> None:
    """Test that hosts need active membership to create properties."""
    response = await client.post(
        "/api/v1/properties",
        json={
            "title": "Test Property",
            "description": "A nice place to stay in the city center",
            "city": "Portland",
            "address": "123 Main Street, Portland",
            "price_per_night": 100.0,
            "max_guests": 4,
        },
        headers={"Authorization": f"Bearer {host_token}"},
    )
    # Should fail because host has no active membership
    assert response.status_code == 402


@pytest.mark.asyncio
async def test_search_with_filters(client: AsyncClient) -> None:
    """Test property search with price filters."""
    response = await client.get(
        "/api/v1/properties",
        params={"city": "Portland", "min_price": 50, "max_price": 200},
    )
    assert response.status_code == 200
    data = response.json()
    assert "items" in data
    assert "total" in data


@pytest.mark.asyncio
async def test_get_nonexistent_property(client: AsyncClient) -> None:
    """Test getting a property that doesn't exist returns 404."""
    import uuid
    response = await client.get(f"/api/v1/properties/{uuid.uuid4()}")
    assert response.status_code == 404
