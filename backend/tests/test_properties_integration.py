"""Integration tests for property endpoints — happy paths and edge cases."""

import uuid

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_create_property_success(client: AsyncClient, host_with_membership: str) -> None:
    """Host with active membership can create a property."""
    response = await client.post(
        "/api/v1/properties",
        json={
            "title": "Ocean View Villa",
            "description": "Beautiful beachfront villa with stunning ocean views",
            "city": "Miami",
            "address": "100 Ocean Drive, Miami",
            "price_per_night": 250.0,
            "max_guests": 6,
            "latitude": 25.7617,
            "longitude": -80.1918,
            "amenities": ["wifi", "pool", "parking"],
        },
        headers={"Authorization": f"Bearer {host_with_membership}"},
    )
    assert response.status_code == 201
    data = response.json()
    assert data["title"] == "Ocean View Villa"
    assert data["city"] == "Miami"
    assert data["price_per_night"] == 250.0
    assert data["max_guests"] == 6
    assert data["is_active"] is True
    assert data["hourly_enabled"] is False
    assert data["images"] == []
    assert data["hourly_config"] is None
    assert "id" in data
    assert "host_id" in data


@pytest.mark.asyncio
async def test_get_property_by_id(client: AsyncClient, created_property: dict) -> None:
    """Get a single property by ID returns full data."""
    prop_id = created_property["id"]
    response = await client.get(f"/api/v1/properties/{prop_id}")
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == prop_id
    assert data["title"] == "Fixture Property"


@pytest.mark.asyncio
async def test_update_property_success(
    client: AsyncClient, host_with_membership: str, created_property: dict
) -> None:
    """Host can update their own property."""
    prop_id = created_property["id"]
    response = await client.put(
        f"/api/v1/properties/{prop_id}",
        json={
            "title": "Updated Property Title",
            "price_per_night": 150.0,
        },
        headers={"Authorization": f"Bearer {host_with_membership}"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["title"] == "Updated Property Title"
    assert data["price_per_night"] == 150.0


@pytest.mark.asyncio
async def test_update_property_not_owner(
    client: AsyncClient, created_property: dict, second_host_token: str
) -> None:
    """Different host cannot update someone else's property."""
    prop_id = created_property["id"]
    response = await client.put(
        f"/api/v1/properties/{prop_id}",
        json={"title": "Hacked Title"},
        headers={"Authorization": f"Bearer {second_host_token}"},
    )
    assert response.status_code == 403


@pytest.mark.asyncio
async def test_delete_property_success(
    client: AsyncClient, host_with_membership: str, created_property: dict
) -> None:
    """Host can delete (deactivate) their own property."""
    prop_id = created_property["id"]
    response = await client.delete(
        f"/api/v1/properties/{prop_id}",
        headers={"Authorization": f"Bearer {host_with_membership}"},
    )
    assert response.status_code == 204

    # Verify it's no longer returned as active in search
    search_resp = await client.get("/api/v1/properties")
    items = search_resp.json()["items"]
    active_ids = [i["id"] for i in items if i["is_active"]]
    assert prop_id not in active_ids


@pytest.mark.asyncio
async def test_delete_property_not_owner(
    client: AsyncClient, created_property: dict, second_host_token: str
) -> None:
    """Different host cannot delete someone else's property."""
    prop_id = created_property["id"]
    response = await client.delete(
        f"/api/v1/properties/{prop_id}",
        headers={"Authorization": f"Bearer {second_host_token}"},
    )
    assert response.status_code == 403


@pytest.mark.asyncio
async def test_search_properties_with_results(
    client: AsyncClient, created_property: dict
) -> None:
    """Search returns properties when they exist."""
    response = await client.get("/api/v1/properties")
    assert response.status_code == 200
    data = response.json()
    assert data["total"] >= 1
    assert len(data["items"]) >= 1


@pytest.mark.asyncio
async def test_search_properties_by_city(
    client: AsyncClient, created_property: dict
) -> None:
    """Search by city filter."""
    response = await client.get("/api/v1/properties", params={"city": "Portland"})
    assert response.status_code == 200
    data = response.json()
    assert data["total"] >= 1
    for item in data["items"]:
        assert "portland" in item["city"].lower()


@pytest.mark.asyncio
async def test_search_properties_city_no_match(client: AsyncClient, created_property: dict) -> None:
    """Search by city with no match returns empty."""
    response = await client.get("/api/v1/properties", params={"city": "Nonexistentville"})
    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 0
    assert data["items"] == []


@pytest.mark.asyncio
async def test_search_properties_by_price_range(
    client: AsyncClient, created_property: dict
) -> None:
    """Search by min/max price filters."""
    response = await client.get(
        "/api/v1/properties",
        params={"min_price": 100, "max_price": 200},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["total"] >= 1


@pytest.mark.asyncio
async def test_search_properties_by_max_guests(
    client: AsyncClient, created_property: dict
) -> None:
    """Search by max_guests filter."""
    response = await client.get("/api/v1/properties", params={"max_guests": 4})
    assert response.status_code == 200
    data = response.json()
    assert data["total"] >= 1


@pytest.mark.asyncio
async def test_search_properties_by_host_id(
    client: AsyncClient, created_property: dict
) -> None:
    """Search by host_id filter."""
    host_id = created_property["host_id"]
    response = await client.get("/api/v1/properties", params={"host_id": host_id})
    assert response.status_code == 200
    data = response.json()
    assert data["total"] >= 1
    for item in data["items"]:
        assert item["host_id"] == host_id


@pytest.mark.asyncio
async def test_search_properties_hourly_filter(
    client: AsyncClient, created_property: dict
) -> None:
    """Search by hourly_available filter — none configured yet so empty."""
    response = await client.get(
        "/api/v1/properties", params={"hourly_available": True}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 0


@pytest.mark.asyncio
async def test_search_properties_pagination(
    client: AsyncClient, host_with_membership: str
) -> None:
    """Test pagination params."""
    # Create 3 properties
    for i in range(3):
        await client.post(
            "/api/v1/properties",
            json={
                "title": f"Paginated Property {i}",
                "description": "A property for pagination testing",
                "city": "Portland",
                "address": f"{i} Pagination St, Portland",
                "price_per_night": 100.0,
                "max_guests": 2,
            },
            headers={"Authorization": f"Bearer {host_with_membership}"},
        )

    # Page 1 with page_size=2
    response = await client.get("/api/v1/properties", params={"page": 1, "page_size": 2})
    data = response.json()
    assert len(data["items"]) == 2
    assert data["total"] >= 3

    # Page 2
    response = await client.get("/api/v1/properties", params={"page": 2, "page_size": 2})
    data = response.json()
    assert len(data["items"]) >= 1


@pytest.mark.asyncio
async def test_configure_hourly_booking(
    client: AsyncClient, host_with_membership: str, created_property: dict
) -> None:
    """Host can configure hourly booking for a property."""
    prop_id = created_property["id"]
    response = await client.put(
        f"/api/v1/properties/{prop_id}/hourly",
        json={
            "hourly_price": 25.0,
            "min_hours": 2,
            "max_hours": 8,
            "available_from": "09:00:00",
            "available_to": "21:00:00",
        },
        headers={"Authorization": f"Bearer {host_with_membership}"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["hourly_enabled"] is True

    # Verify via a fresh GET
    get_resp = await client.get(f"/api/v1/properties/{prop_id}")
    assert get_resp.status_code == 200
    assert get_resp.json()["hourly_enabled"] is True


@pytest.mark.asyncio
async def test_configure_hourly_booking_update(
    client: AsyncClient, host_with_membership: str, created_property: dict
) -> None:
    """Updating hourly config on a property that already has one works."""
    prop_id = created_property["id"]
    # First configure
    await client.put(
        f"/api/v1/properties/{prop_id}/hourly",
        json={"hourly_price": 20.0, "min_hours": 1, "max_hours": 6},
        headers={"Authorization": f"Bearer {host_with_membership}"},
    )
    # Update
    response = await client.put(
        f"/api/v1/properties/{prop_id}/hourly",
        json={"hourly_price": 30.0, "min_hours": 2, "max_hours": 10},
        headers={"Authorization": f"Bearer {host_with_membership}"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["hourly_enabled"] is True


@pytest.mark.asyncio
async def test_configure_hourly_not_owner(
    client: AsyncClient, created_property: dict, second_host_token: str
) -> None:
    """Non-owner cannot configure hourly booking."""
    prop_id = created_property["id"]
    response = await client.put(
        f"/api/v1/properties/{prop_id}/hourly",
        json={"hourly_price": 25.0},
        headers={"Authorization": f"Bearer {second_host_token}"},
    )
    assert response.status_code == 403


@pytest.mark.asyncio
async def test_listing_cap_enforcement(
    client: AsyncClient, host_with_membership: str
) -> None:
    """Host cannot exceed plan listing limit (basic = 5)."""
    for i in range(5):
        resp = await client.post(
            "/api/v1/properties",
            json={
                "title": f"Cap Test Property {i}",
                "description": "Testing listing cap enforcement",
                "city": "Portland",
                "address": f"{i} Cap St, Portland",
                "price_per_night": 50.0,
                "max_guests": 2,
            },
            headers={"Authorization": f"Bearer {host_with_membership}"},
        )
        assert resp.status_code == 201

    # 6th should fail
    response = await client.post(
        "/api/v1/properties",
        json={
            "title": "Over the Cap",
            "description": "This should be rejected by the cap",
            "city": "Portland",
            "address": "6 Cap St, Portland",
            "price_per_night": 50.0,
            "max_guests": 2,
        },
        headers={"Authorization": f"Bearer {host_with_membership}"},
    )
    assert response.status_code == 403


@pytest.mark.asyncio
async def test_update_nonexistent_property(
    client: AsyncClient, host_with_membership: str
) -> None:
    """Updating a nonexistent property returns 404."""
    response = await client.put(
        f"/api/v1/properties/{uuid.uuid4()}",
        json={"title": "Does not exist"},
        headers={"Authorization": f"Bearer {host_with_membership}"},
    )
    assert response.status_code == 404
