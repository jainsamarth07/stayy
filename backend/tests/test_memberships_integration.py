"""Integration tests for membership endpoints — extended scenarios."""

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_subscribe_upgrade_plan(client: AsyncClient, host_token: str) -> None:
    """Host can upgrade from basic to pro plan."""
    # Subscribe to basic
    await client.post(
        "/api/v1/memberships/subscribe",
        json={"plan_type": "basic", "payment_token": "tok_basic"},
        headers={"Authorization": f"Bearer {host_token}"},
    )

    # Upgrade to pro (reactivation/switch on existing row)
    response = await client.post(
        "/api/v1/memberships/subscribe",
        json={"plan_type": "pro", "payment_token": "tok_pro"},
        headers={"Authorization": f"Bearer {host_token}"},
    )
    assert response.status_code == 201
    data = response.json()
    assert data["plan_type"] == "pro"
    assert data["status"] == "active"
    assert data["amount"] == 6499.0
    assert data["max_listings"] == 25


@pytest.mark.asyncio
async def test_subscribe_premium_plan(client: AsyncClient, host_token: str) -> None:
    """Host can subscribe to premium plan."""
    response = await client.post(
        "/api/v1/memberships/subscribe",
        json={"plan_type": "premium", "payment_token": "tok_premium"},
        headers={"Authorization": f"Bearer {host_token}"},
    )
    assert response.status_code == 201
    data = response.json()
    assert data["plan_type"] == "premium"
    assert data["amount"] == 16499.0


@pytest.mark.asyncio
async def test_reactivate_after_cancel(client: AsyncClient, host_token: str) -> None:
    """Host can reactivate after cancellation."""
    # Subscribe
    await client.post(
        "/api/v1/memberships/subscribe",
        json={"plan_type": "basic", "payment_token": "tok_react"},
        headers={"Authorization": f"Bearer {host_token}"},
    )
    # Cancel
    await client.put(
        "/api/v1/memberships/cancel",
        headers={"Authorization": f"Bearer {host_token}"},
    )
    # Resubscribe
    response = await client.post(
        "/api/v1/memberships/subscribe",
        json={"plan_type": "pro", "payment_token": "tok_react2"},
        headers={"Authorization": f"Bearer {host_token}"},
    )
    assert response.status_code == 201
    assert response.json()["status"] == "active"
    assert response.json()["plan_type"] == "pro"


@pytest.mark.asyncio
async def test_cancel_already_cancelled(client: AsyncClient, host_token: str) -> None:
    """Cancelling an already-cancelled membership returns 400."""
    await client.post(
        "/api/v1/memberships/subscribe",
        json={"plan_type": "basic", "payment_token": "tok_cancel2"},
        headers={"Authorization": f"Bearer {host_token}"},
    )
    await client.put(
        "/api/v1/memberships/cancel",
        headers={"Authorization": f"Bearer {host_token}"},
    )
    response = await client.put(
        "/api/v1/memberships/cancel",
        headers={"Authorization": f"Bearer {host_token}"},
    )
    assert response.status_code == 400


@pytest.mark.asyncio
async def test_get_membership_no_subscription(client: AsyncClient, host_token: str) -> None:
    """Getting membership when none exists returns 404."""
    response = await client.get(
        "/api/v1/memberships/current",
        headers={"Authorization": f"Bearer {host_token}"},
    )
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_webhook_payment_succeeded(client: AsyncClient, host_token: str) -> None:
    """Webhook for payment.succeeded updates membership to active."""
    await client.post(
        "/api/v1/memberships/subscribe",
        json={"plan_type": "basic", "payment_token": "tok_wh_success"},
        headers={"Authorization": f"Bearer {host_token}"},
    )
    payment_ref = "sim_tok_wh_success"

    response = await client.post(
        "/api/v1/memberships/webhook",
        json={
            "event_type": "payment.succeeded",
            "payment_ref": payment_ref,
            "status": "succeeded",
        },
        headers={"x-webhook-secret": "CHANGE-ME-webhook-secret"},
    )
    assert response.status_code == 200
    assert response.json()["status"] == "processed"


@pytest.mark.asyncio
async def test_webhook_payment_failed(client: AsyncClient, host_token: str) -> None:
    """Webhook for payment.failed updates membership to past_due."""
    await client.post(
        "/api/v1/memberships/subscribe",
        json={"plan_type": "basic", "payment_token": "tok_wh_fail"},
        headers={"Authorization": f"Bearer {host_token}"},
    )

    response = await client.post(
        "/api/v1/memberships/webhook",
        json={
            "event_type": "payment.failed",
            "payment_ref": "sim_tok_wh_fail",
            "status": "failed",
        },
        headers={"x-webhook-secret": "CHANGE-ME-webhook-secret"},
    )
    assert response.status_code == 200

    # Verify membership status
    mem_resp = await client.get(
        "/api/v1/memberships/current",
        headers={"Authorization": f"Bearer {host_token}"},
    )
    assert mem_resp.json()["status"] == "past_due"


@pytest.mark.asyncio
async def test_webhook_subscription_cancelled(client: AsyncClient, host_token: str) -> None:
    """Webhook for subscription.cancelled updates membership status."""
    await client.post(
        "/api/v1/memberships/subscribe",
        json={"plan_type": "basic", "payment_token": "tok_wh_cancel"},
        headers={"Authorization": f"Bearer {host_token}"},
    )

    response = await client.post(
        "/api/v1/memberships/webhook",
        json={
            "event_type": "subscription.cancelled",
            "payment_ref": "sim_tok_wh_cancel",
            "status": "cancelled",
        },
        headers={"x-webhook-secret": "CHANGE-ME-webhook-secret"},
    )
    assert response.status_code == 200

    mem_resp = await client.get(
        "/api/v1/memberships/current",
        headers={"Authorization": f"Bearer {host_token}"},
    )
    assert mem_resp.json()["status"] == "cancelled"


@pytest.mark.asyncio
async def test_membership_fields_complete(client: AsyncClient, host_token: str) -> None:
    """Membership response includes all expected fields."""
    await client.post(
        "/api/v1/memberships/subscribe",
        json={"plan_type": "basic", "payment_token": "tok_fields"},
        headers={"Authorization": f"Bearer {host_token}"},
    )
    response = await client.get(
        "/api/v1/memberships/current",
        headers={"Authorization": f"Bearer {host_token}"},
    )
    data = response.json()
    assert "id" in data
    assert "host_id" in data
    assert "plan_type" in data
    assert "start_date" in data
    assert "end_date" in data
    assert "status" in data
    assert "auto_renew" in data
    assert "amount" in data
    assert "max_listings" in data
    assert data["auto_renew"] is True
