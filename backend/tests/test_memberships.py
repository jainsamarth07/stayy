"""Membership endpoint tests."""

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_list_plans_public(client: AsyncClient) -> None:
    """Test listing membership plans is public and returns all plans."""
    response = await client.get("/api/v1/memberships/plans")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 3
    plan_types = {p["plan_type"] for p in data}
    assert plan_types == {"basic", "pro", "premium"}


@pytest.mark.asyncio
async def test_subscribe_requires_host(client: AsyncClient, user_token: str) -> None:
    """Test that subscribing requires host role."""
    response = await client.post(
        "/api/v1/memberships/subscribe",
        json={"plan_type": "basic", "payment_token": "tok_test"},
        headers={"Authorization": f"Bearer {user_token}"},
    )
    assert response.status_code == 403


@pytest.mark.asyncio
async def test_subscribe_as_host(client: AsyncClient, host_token: str) -> None:
    """Test host can subscribe to a plan."""
    response = await client.post(
        "/api/v1/memberships/subscribe",
        json={"plan_type": "basic", "payment_token": "tok_test_123"},
        headers={"Authorization": f"Bearer {host_token}"},
    )
    assert response.status_code == 201
    data = response.json()
    assert data["plan_type"] == "basic"
    assert data["status"] == "active"
    assert data["amount"] == 29.0


@pytest.mark.asyncio
async def test_get_current_membership(client: AsyncClient, host_token: str) -> None:
    """Test getting current membership after subscribing."""
    # First subscribe
    await client.post(
        "/api/v1/memberships/subscribe",
        json={"plan_type": "pro", "payment_token": "tok_test_456"},
        headers={"Authorization": f"Bearer {host_token}"},
    )
    # Then get current
    response = await client.get(
        "/api/v1/memberships/current",
        headers={"Authorization": f"Bearer {host_token}"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["plan_type"] == "pro"


@pytest.mark.asyncio
async def test_cancel_membership(client: AsyncClient, host_token: str) -> None:
    """Test cancelling an active membership."""
    # Subscribe first
    await client.post(
        "/api/v1/memberships/subscribe",
        json={"plan_type": "basic", "payment_token": "tok_cancel_test"},
        headers={"Authorization": f"Bearer {host_token}"},
    )
    # Cancel
    response = await client.put(
        "/api/v1/memberships/cancel",
        headers={"Authorization": f"Bearer {host_token}"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "cancelled"
    assert data["auto_renew"] is False


@pytest.mark.asyncio
async def test_webhook_processing(client: AsyncClient) -> None:
    """Test the payment webhook endpoint accepts valid payload."""
    response = await client.post(
        "/api/v1/memberships/webhook",
        json={
            "event_type": "payment.succeeded",
            "payment_ref": "sim_tok_nonexistent",
            "status": "succeeded",
        },
        headers={"x-webhook-secret": "CHANGE-ME-webhook-secret"},
    )
    assert response.status_code == 200
    assert response.json()["status"] == "processed"
