"""Integration tests for booking endpoints — full lifecycle."""

from datetime import UTC, datetime, timedelta

import pytest
from httpx import AsyncClient


def _future_checkin(days: int = 10) -> str:
    return (datetime.now(UTC) + timedelta(days=days)).isoformat()


def _future_checkout(days: int = 15) -> str:
    return (datetime.now(UTC) + timedelta(days=days)).isoformat()


@pytest.mark.asyncio
async def test_create_booking_nightly_success(
    client: AsyncClient, user_token: str, created_property: dict
) -> None:
    """Guest can create a nightly booking on an active property."""
    response = await client.post(
        "/api/v1/bookings",
        json={
            "property_id": created_property["id"],
            "check_in": _future_checkin(10),
            "check_out": _future_checkout(15),
        },
        headers={"Authorization": f"Bearer {user_token}"},
    )
    assert response.status_code == 201
    data = response.json()
    assert data["property_id"] == created_property["id"]
    assert data["status"] == "pending"
    assert data["booking_type"] == "nightly"
    assert data["total_price"] > 0
    assert "id" in data


@pytest.mark.asyncio
async def test_create_booking_host_cannot_book_own(
    client: AsyncClient, host_with_membership: str, created_property: dict
) -> None:
    """Host cannot book their own property."""
    response = await client.post(
        "/api/v1/bookings",
        json={
            "property_id": created_property["id"],
            "check_in": _future_checkin(20),
            "check_out": _future_checkout(25),
        },
        headers={"Authorization": f"Bearer {host_with_membership}"},
    )
    assert response.status_code == 400


@pytest.mark.asyncio
async def test_create_booking_checkout_before_checkin(
    client: AsyncClient, user_token: str, created_property: dict
) -> None:
    """Check-out before check-in returns 400."""
    response = await client.post(
        "/api/v1/bookings",
        json={
            "property_id": created_property["id"],
            "check_in": _future_checkout(15),
            "check_out": _future_checkin(10),
        },
        headers={"Authorization": f"Bearer {user_token}"},
    )
    assert response.status_code == 400


@pytest.mark.asyncio
async def test_create_booking_overlapping_dates(
    client: AsyncClient, user_token: str, guest_token: str, created_property: dict
) -> None:
    """Overlapping bookings are rejected."""
    checkin = _future_checkin(30)
    checkout = _future_checkout(35)

    # First booking
    r1 = await client.post(
        "/api/v1/bookings",
        json={
            "property_id": created_property["id"],
            "check_in": checkin,
            "check_out": checkout,
        },
        headers={"Authorization": f"Bearer {user_token}"},
    )
    assert r1.status_code == 201

    # Overlapping booking by different guest
    r2 = await client.post(
        "/api/v1/bookings",
        json={
            "property_id": created_property["id"],
            "check_in": checkin,
            "check_out": checkout,
        },
        headers={"Authorization": f"Bearer {guest_token}"},
    )
    assert r2.status_code == 400


@pytest.mark.asyncio
async def test_get_booking_as_guest(
    client: AsyncClient, user_token: str, created_property: dict
) -> None:
    """Guest can retrieve their own booking."""
    create_resp = await client.post(
        "/api/v1/bookings",
        json={
            "property_id": created_property["id"],
            "check_in": _future_checkin(40),
            "check_out": _future_checkout(45),
        },
        headers={"Authorization": f"Bearer {user_token}"},
    )
    booking_id = create_resp.json()["id"]

    response = await client.get(
        f"/api/v1/bookings/{booking_id}",
        headers={"Authorization": f"Bearer {user_token}"},
    )
    assert response.status_code == 200
    assert response.json()["id"] == booking_id


@pytest.mark.asyncio
async def test_get_booking_as_host(
    client: AsyncClient, user_token: str, host_with_membership: str, created_property: dict
) -> None:
    """Host can retrieve a booking on their property."""
    create_resp = await client.post(
        "/api/v1/bookings",
        json={
            "property_id": created_property["id"],
            "check_in": _future_checkin(50),
            "check_out": _future_checkout(55),
        },
        headers={"Authorization": f"Bearer {user_token}"},
    )
    booking_id = create_resp.json()["id"]

    response = await client.get(
        f"/api/v1/bookings/{booking_id}",
        headers={"Authorization": f"Bearer {host_with_membership}"},
    )
    assert response.status_code == 200
    assert response.json()["id"] == booking_id


@pytest.mark.asyncio
async def test_get_booking_access_denied(
    client: AsyncClient, user_token: str, guest_token: str, created_property: dict
) -> None:
    """Unrelated user cannot access another's booking."""
    create_resp = await client.post(
        "/api/v1/bookings",
        json={
            "property_id": created_property["id"],
            "check_in": _future_checkin(60),
            "check_out": _future_checkout(65),
        },
        headers={"Authorization": f"Bearer {user_token}"},
    )
    booking_id = create_resp.json()["id"]

    response = await client.get(
        f"/api/v1/bookings/{booking_id}",
        headers={"Authorization": f"Bearer {guest_token}"},
    )
    assert response.status_code == 403


@pytest.mark.asyncio
async def test_confirm_booking_by_host(
    client: AsyncClient, user_token: str, host_with_membership: str, created_property: dict
) -> None:
    """Host confirms a pending booking."""
    create_resp = await client.post(
        "/api/v1/bookings",
        json={
            "property_id": created_property["id"],
            "check_in": _future_checkin(70),
            "check_out": _future_checkout(75),
        },
        headers={"Authorization": f"Bearer {user_token}"},
    )
    booking_id = create_resp.json()["id"]

    response = await client.put(
        f"/api/v1/bookings/{booking_id}/status",
        json={"status": "confirmed"},
        headers={"Authorization": f"Bearer {host_with_membership}"},
    )
    assert response.status_code == 200
    assert response.json()["status"] == "confirmed"


@pytest.mark.asyncio
async def test_reject_booking_by_host(
    client: AsyncClient, user_token: str, host_with_membership: str, created_property: dict
) -> None:
    """Host rejects a pending booking."""
    create_resp = await client.post(
        "/api/v1/bookings",
        json={
            "property_id": created_property["id"],
            "check_in": _future_checkin(80),
            "check_out": _future_checkout(85),
        },
        headers={"Authorization": f"Bearer {user_token}"},
    )
    booking_id = create_resp.json()["id"]

    response = await client.put(
        f"/api/v1/bookings/{booking_id}/status",
        json={"status": "rejected"},
        headers={"Authorization": f"Bearer {host_with_membership}"},
    )
    assert response.status_code == 200
    assert response.json()["status"] == "rejected"


@pytest.mark.asyncio
async def test_cancel_booking_by_guest(
    client: AsyncClient, user_token: str, created_property: dict
) -> None:
    """Guest cancels their own pending booking."""
    create_resp = await client.post(
        "/api/v1/bookings",
        json={
            "property_id": created_property["id"],
            "check_in": _future_checkin(90),
            "check_out": _future_checkout(95),
        },
        headers={"Authorization": f"Bearer {user_token}"},
    )
    booking_id = create_resp.json()["id"]

    response = await client.post(
        f"/api/v1/bookings/{booking_id}/cancel",
        headers={"Authorization": f"Bearer {user_token}"},
    )
    assert response.status_code == 200
    assert response.json()["status"] == "cancelled"


@pytest.mark.asyncio
async def test_complete_booking_by_host(
    client: AsyncClient, user_token: str, host_with_membership: str, created_property: dict
) -> None:
    """Host completes a confirmed booking."""
    # Create
    create_resp = await client.post(
        "/api/v1/bookings",
        json={
            "property_id": created_property["id"],
            "check_in": _future_checkin(100),
            "check_out": _future_checkout(105),
        },
        headers={"Authorization": f"Bearer {user_token}"},
    )
    booking_id = create_resp.json()["id"]

    # Confirm
    await client.put(
        f"/api/v1/bookings/{booking_id}/status",
        json={"status": "confirmed"},
        headers={"Authorization": f"Bearer {host_with_membership}"},
    )

    # Complete
    response = await client.put(
        f"/api/v1/bookings/{booking_id}/status",
        json={"status": "completed"},
        headers={"Authorization": f"Bearer {host_with_membership}"},
    )
    assert response.status_code == 200
    assert response.json()["status"] == "completed"


@pytest.mark.asyncio
async def test_invalid_status_transition(
    client: AsyncClient, user_token: str, host_with_membership: str, created_property: dict
) -> None:
    """Cannot transition from rejected to confirmed."""
    create_resp = await client.post(
        "/api/v1/bookings",
        json={
            "property_id": created_property["id"],
            "check_in": _future_checkin(110),
            "check_out": _future_checkout(115),
        },
        headers={"Authorization": f"Bearer {user_token}"},
    )
    booking_id = create_resp.json()["id"]

    # Reject
    await client.put(
        f"/api/v1/bookings/{booking_id}/status",
        json={"status": "rejected"},
        headers={"Authorization": f"Bearer {host_with_membership}"},
    )

    # Try to confirm after rejection
    response = await client.put(
        f"/api/v1/bookings/{booking_id}/status",
        json={"status": "confirmed"},
        headers={"Authorization": f"Bearer {host_with_membership}"},
    )
    assert response.status_code == 400


@pytest.mark.asyncio
async def test_guest_cannot_confirm_booking(
    client: AsyncClient, user_token: str, created_property: dict
) -> None:
    """Guest cannot confirm a booking (only host can)."""
    create_resp = await client.post(
        "/api/v1/bookings",
        json={
            "property_id": created_property["id"],
            "check_in": _future_checkin(120),
            "check_out": _future_checkout(125),
        },
        headers={"Authorization": f"Bearer {user_token}"},
    )
    booking_id = create_resp.json()["id"]

    response = await client.put(
        f"/api/v1/bookings/{booking_id}/status",
        json={"status": "confirmed"},
        headers={"Authorization": f"Bearer {user_token}"},
    )
    assert response.status_code == 403


@pytest.mark.asyncio
async def test_list_bookings_as_guest(
    client: AsyncClient, user_token: str, created_property: dict
) -> None:
    """Guest sees their own bookings in the list."""
    await client.post(
        "/api/v1/bookings",
        json={
            "property_id": created_property["id"],
            "check_in": _future_checkin(130),
            "check_out": _future_checkout(135),
        },
        headers={"Authorization": f"Bearer {user_token}"},
    )

    response = await client.get(
        "/api/v1/bookings",
        headers={"Authorization": f"Bearer {user_token}"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["total"] >= 1
    assert len(data["items"]) >= 1


@pytest.mark.asyncio
async def test_list_bookings_as_host(
    client: AsyncClient, user_token: str, host_with_membership: str, created_property: dict
) -> None:
    """Host sees bookings on their properties."""
    await client.post(
        "/api/v1/bookings",
        json={
            "property_id": created_property["id"],
            "check_in": _future_checkin(140),
            "check_out": _future_checkout(145),
        },
        headers={"Authorization": f"Bearer {user_token}"},
    )

    response = await client.get(
        "/api/v1/bookings",
        headers={"Authorization": f"Bearer {host_with_membership}"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["total"] >= 1


@pytest.mark.asyncio
async def test_list_bookings_as_admin(
    client: AsyncClient, user_token: str, admin_token: str, created_property: dict
) -> None:
    """Admin sees all bookings."""
    await client.post(
        "/api/v1/bookings",
        json={
            "property_id": created_property["id"],
            "check_in": _future_checkin(150),
            "check_out": _future_checkout(155),
        },
        headers={"Authorization": f"Bearer {user_token}"},
    )

    response = await client.get(
        "/api/v1/bookings",
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["total"] >= 1


@pytest.mark.asyncio
async def test_cancel_confirmed_booking(
    client: AsyncClient, user_token: str, host_with_membership: str, created_property: dict
) -> None:
    """Confirmed booking can be cancelled."""
    create_resp = await client.post(
        "/api/v1/bookings",
        json={
            "property_id": created_property["id"],
            "check_in": _future_checkin(160),
            "check_out": _future_checkout(165),
        },
        headers={"Authorization": f"Bearer {user_token}"},
    )
    booking_id = create_resp.json()["id"]

    # Confirm
    await client.put(
        f"/api/v1/bookings/{booking_id}/status",
        json={"status": "confirmed"},
        headers={"Authorization": f"Bearer {host_with_membership}"},
    )

    # Cancel
    response = await client.post(
        f"/api/v1/bookings/{booking_id}/cancel",
        headers={"Authorization": f"Bearer {user_token}"},
    )
    assert response.status_code == 200
    assert response.json()["status"] == "cancelled"


@pytest.mark.asyncio
async def test_create_hourly_booking(
    client: AsyncClient, user_token: str, host_with_membership: str, created_property: dict
) -> None:
    """Guest can create an hourly booking on a property with hourly config."""
    prop_id = created_property["id"]

    # Configure hourly
    await client.put(
        f"/api/v1/properties/{prop_id}/hourly",
        json={"hourly_price": 25.0, "min_hours": 2, "max_hours": 8},
        headers={"Authorization": f"Bearer {host_with_membership}"},
    )

    response = await client.post(
        "/api/v1/bookings",
        json={
            "property_id": prop_id,
            "check_in": _future_checkin(170),
            "check_out": _future_checkout(170),  # same day
            "booking_type": "hourly",
            "hours": 4,
        },
        headers={"Authorization": f"Bearer {user_token}"},
    )
    assert response.status_code == 201
    data = response.json()
    assert data["booking_type"] == "hourly"
    assert data["hours"] == 4
    assert data["total_price"] == 100.0  # 25 * 4


@pytest.mark.asyncio
async def test_hourly_booking_not_enabled(
    client: AsyncClient, user_token: str, host_with_membership: str
) -> None:
    """Hourly booking fails when not enabled on the property."""
    # Create a property without hourly config
    prop_resp = await client.post(
        "/api/v1/properties",
        json={
            "title": "No Hourly",
            "description": "A property without hourly booking",
            "city": "Portland",
            "address": "789 No Hourly St",
            "price_per_night": 100.0,
            "max_guests": 2,
        },
        headers={"Authorization": f"Bearer {host_with_membership}"},
    )
    prop_id = prop_resp.json()["id"]

    response = await client.post(
        "/api/v1/bookings",
        json={
            "property_id": prop_id,
            "check_in": _future_checkin(180),
            "check_out": _future_checkout(180),
            "booking_type": "hourly",
            "hours": 3,
        },
        headers={"Authorization": f"Bearer {user_token}"},
    )
    assert response.status_code == 400


@pytest.mark.asyncio
async def test_hourly_booking_invalid_hours(
    client: AsyncClient, user_token: str, host_with_membership: str, created_property: dict
) -> None:
    """Hourly booking with hours outside allowed range fails."""
    prop_id = created_property["id"]

    # Configure hourly: min=2, max=8
    await client.put(
        f"/api/v1/properties/{prop_id}/hourly",
        json={"hourly_price": 25.0, "min_hours": 2, "max_hours": 8},
        headers={"Authorization": f"Bearer {host_with_membership}"},
    )

    # Try with hours=1 (below min)
    response = await client.post(
        "/api/v1/bookings",
        json={
            "property_id": prop_id,
            "check_in": _future_checkin(190),
            "check_out": _future_checkout(190),
            "booking_type": "hourly",
            "hours": 1,
        },
        headers={"Authorization": f"Bearer {user_token}"},
    )
    assert response.status_code == 400
