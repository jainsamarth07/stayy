"""Membership endpoints — plans, subscribe, cancel, webhook."""

from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.dependencies import require_host
from app.models.user import User
from app.schemas.membership import (
    MembershipOut,
    MembershipPlanOut,
    MembershipSubscribeRequest,
    MembershipWebhookPayload,
)
from app.services import membership_service

router = APIRouter()


@router.get("/plans", response_model=list[MembershipPlanOut])
async def list_plans() -> list[MembershipPlanOut]:
    """List all available membership plans (public)."""
    return membership_service.get_available_plans()


@router.post("/subscribe", response_model=MembershipOut, status_code=201)
async def subscribe(
    data: MembershipSubscribeRequest,
    host: User = Depends(require_host),
    db: AsyncSession = Depends(get_db),
) -> MembershipOut:
    """Subscribe to a membership plan (host only)."""
    membership = await membership_service.subscribe(db, data, host)
    return MembershipOut.model_validate(membership)


@router.get("/current", response_model=MembershipOut)
async def get_current_membership(
    host: User = Depends(require_host),
    db: AsyncSession = Depends(get_db),
) -> MembershipOut:
    """Get the host's current membership."""
    membership = await membership_service.get_current_membership(db, host)
    return MembershipOut.model_validate(membership)


@router.put("/cancel", response_model=MembershipOut)
async def cancel_membership(
    host: User = Depends(require_host),
    db: AsyncSession = Depends(get_db),
) -> MembershipOut:
    """Cancel the current membership (host only)."""
    membership = await membership_service.cancel_membership(db, host)
    return MembershipOut.model_validate(membership)


@router.post("/webhook", status_code=200)
async def payment_webhook(
    payload: MembershipWebhookPayload,
    request: Request,
    db: AsyncSession = Depends(get_db),
) -> dict[str, str]:
    """Process payment gateway webhook with secret verification."""
    from app.config import settings

    webhook_secret = request.headers.get("x-webhook-secret", "")
    if webhook_secret != settings.WEBHOOK_SECRET:
        raise HTTPException(status_code=403, detail="Invalid webhook secret")

    await membership_service.process_webhook(
        db, payload.event_type, payload.payment_ref, payload.status
    )
    return {"status": "processed"}
