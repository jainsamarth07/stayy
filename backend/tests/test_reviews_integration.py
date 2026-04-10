"""Integration tests for review endpoints — full lifecycle."""

from datetime import UTC, datetime, timedelta

import pytest
from httpx import AsyncClient


def _future(days: int) -> str:
    return (datetime.now(UTC) + timedelta(days=days)).isoformat()


@pytest.mark.asyncio
async def test_create_review_success(
    client: AsyncClient,
    user_token: str,
    host_with_membership: str,
    created_property: dict,
) -> None:
    """Guest can review a completed booking."""
    # Create booking
    booking_resp = await client.post(
        "/api/v1/bookings",
        json={
            "property_id": created_property["id"],
            "check_in": _future(10),
            "check_out": _future(15),
        },
        headers={"Authorization": f"Bearer {user_token}"},
    )
    booking_id = booking_resp.json()["id"]

    # Confirm
    await client.put(
        f"/api/v1/bookings/{booking_id}/status",
        json={"status": "confirmed"},
        headers={"Authorization": f"Bearer {host_with_membership}"},
    )
    # Complete
    await client.put(
        f"/api/v1/bookings/{booking_id}/status",
        json={"status": "completed"},
        headers={"Authorization": f"Bearer {host_with_membership}"},
    )

    # Review
    response = await client.post(
        "/api/v1/reviews",
        json={
            "booking_id": booking_id,
            "rating": 4.5,
            "comment": "Wonderful stay, highly recommended!",
        },
        headers={"Authorization": f"Bearer {user_token}"},
    )
    assert response.status_code == 201
    data = response.json()
    assert data["rating"] == 4.5
    assert data["comment"] == "Wonderful stay, highly recommended!"
    assert data["booking_id"] == booking_id
    assert data["property_id"] == created_property["id"]


@pytest.mark.asyncio
async def test_create_review_without_comment(
    client: AsyncClient,
    user_token: str,
    host_with_membership: str,
    created_property: dict,
) -> None:
    """Review without comment succeeds."""
    booking_resp = await client.post(
        "/api/v1/bookings",
        json={
            "property_id": created_property["id"],
            "check_in": _future(20),
            "check_out": _future(25),
        },
        headers={"Authorization": f"Bearer {user_token}"},
    )
    booking_id = booking_resp.json()["id"]

    await client.put(
        f"/api/v1/bookings/{booking_id}/status",
        json={"status": "confirmed"},
        headers={"Authorization": f"Bearer {host_with_membership}"},
    )
    await client.put(
        f"/api/v1/bookings/{booking_id}/status",
        json={"status": "completed"},
        headers={"Authorization": f"Bearer {host_with_membership}"},
    )

    response = await client.post(
        "/api/v1/reviews",
        json={"booking_id": booking_id, "rating": 3.0},
        headers={"Authorization": f"Bearer {user_token}"},
    )
    assert response.status_code == 201
    assert response.json()["comment"] is None


@pytest.mark.asyncio
async def test_create_review_not_completed_booking(
    client: AsyncClient, user_token: str, created_property: dict
) -> None:
    """Cannot review a booking that isn't completed."""
    booking_resp = await client.post(
        "/api/v1/bookings",
        json={
            "property_id": created_property["id"],
            "check_in": _future(30),
            "check_out": _future(35),
        },
        headers={"Authorization": f"Bearer {user_token}"},
    )
    booking_id = booking_resp.json()["id"]

    response = await client.post(
        "/api/v1/reviews",
        json={"booking_id": booking_id, "rating": 4.0},
        headers={"Authorization": f"Bearer {user_token}"},
    )
    assert response.status_code == 400


@pytest.mark.asyncio
async def test_create_review_not_guest(
    client: AsyncClient,
    user_token: str,
    host_with_membership: str,
    created_property: dict,
    guest_token: str,
) -> None:
    """Only the booking guest can review."""
    booking_resp = await client.post(
        "/api/v1/bookings",
        json={
            "property_id": created_property["id"],
            "check_in": _future(40),
            "check_out": _future(45),
        },
        headers={"Authorization": f"Bearer {user_token}"},
    )
    booking_id = booking_resp.json()["id"]

    await client.put(
        f"/api/v1/bookings/{booking_id}/status",
        json={"status": "confirmed"},
        headers={"Authorization": f"Bearer {host_with_membership}"},
    )
    await client.put(
        f"/api/v1/bookings/{booking_id}/status",
        json={"status": "completed"},
        headers={"Authorization": f"Bearer {host_with_membership}"},
    )

    response = await client.post(
        "/api/v1/reviews",
        json={"booking_id": booking_id, "rating": 5.0},
        headers={"Authorization": f"Bearer {guest_token}"},
    )
    assert response.status_code == 403


@pytest.mark.asyncio
async def test_create_duplicate_review(
    client: AsyncClient,
    user_token: str,
    host_with_membership: str,
    created_property: dict,
) -> None:
    """Cannot review the same booking twice."""
    booking_resp = await client.post(
        "/api/v1/bookings",
        json={
            "property_id": created_property["id"],
            "check_in": _future(50),
            "check_out": _future(55),
        },
        headers={"Authorization": f"Bearer {user_token}"},
    )
    booking_id = booking_resp.json()["id"]

    await client.put(
        f"/api/v1/bookings/{booking_id}/status",
        json={"status": "confirmed"},
        headers={"Authorization": f"Bearer {host_with_membership}"},
    )
    await client.put(
        f"/api/v1/bookings/{booking_id}/status",
        json={"status": "completed"},
        headers={"Authorization": f"Bearer {host_with_membership}"},
    )

    # First review
    await client.post(
        "/api/v1/reviews",
        json={"booking_id": booking_id, "rating": 4.0},
        headers={"Authorization": f"Bearer {user_token}"},
    )

    # Duplicate
    response = await client.post(
        "/api/v1/reviews",
        json={"booking_id": booking_id, "rating": 3.0},
        headers={"Authorization": f"Bearer {user_token}"},
    )
    assert response.status_code == 400


@pytest.mark.asyncio
async def test_list_property_reviews_with_data(
    client: AsyncClient,
    user_token: str,
    host_with_membership: str,
    created_property: dict,
) -> None:
    """List reviews for a property that has reviews."""
    booking_resp = await client.post(
        "/api/v1/bookings",
        json={
            "property_id": created_property["id"],
            "check_in": _future(60),
            "check_out": _future(65),
        },
        headers={"Authorization": f"Bearer {user_token}"},
    )
    booking_id = booking_resp.json()["id"]

    await client.put(
        f"/api/v1/bookings/{booking_id}/status",
        json={"status": "confirmed"},
        headers={"Authorization": f"Bearer {host_with_membership}"},
    )
    await client.put(
        f"/api/v1/bookings/{booking_id}/status",
        json={"status": "completed"},
        headers={"Authorization": f"Bearer {host_with_membership}"},
    )

    await client.post(
        "/api/v1/reviews",
        json={
            "booking_id": booking_id,
            "rating": 5.0,
            "comment": "Perfect!",
        },
        headers={"Authorization": f"Bearer {user_token}"},
    )

    response = await client.get(
        f"/api/v1/reviews/property/{created_property['id']}"
    )
    assert response.status_code == 200
    data = response.json()
    assert data["total"] >= 1
    assert data["items"][0]["rating"] == 5.0


@pytest.mark.asyncio
async def test_list_host_reviews(
    client: AsyncClient,
    user_token: str,
    host_with_membership: str,
    created_property: dict,
) -> None:
    """Host can list all reviews on their properties."""
    booking_resp = await client.post(
        "/api/v1/bookings",
        json={
            "property_id": created_property["id"],
            "check_in": _future(70),
            "check_out": _future(75),
        },
        headers={"Authorization": f"Bearer {user_token}"},
    )
    booking_id = booking_resp.json()["id"]

    await client.put(
        f"/api/v1/bookings/{booking_id}/status",
        json={"status": "confirmed"},
        headers={"Authorization": f"Bearer {host_with_membership}"},
    )
    await client.put(
        f"/api/v1/bookings/{booking_id}/status",
        json={"status": "completed"},
        headers={"Authorization": f"Bearer {host_with_membership}"},
    )

    await client.post(
        "/api/v1/reviews",
        json={"booking_id": booking_id, "rating": 4.0, "comment": "Great host!"},
        headers={"Authorization": f"Bearer {user_token}"},
    )

    response = await client.get(
        "/api/v1/reviews/host",
        headers={"Authorization": f"Bearer {host_with_membership}"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["total"] >= 1
