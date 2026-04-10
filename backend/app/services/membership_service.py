"""Membership service — subscribe, cancel, webhook processing."""

from datetime import UTC, datetime, timedelta

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import BadRequestError, NotFoundError
from app.models.membership import (
    PLAN_CONFIG,
    Membership,
    MembershipPlan,
    MembershipStatus,
)
from app.models.user import HostProfile, User
from app.schemas.membership import MembershipPlanOut, MembershipSubscribeRequest


def get_available_plans() -> list[MembershipPlanOut]:
    """Return all available membership plans."""
    return [
        MembershipPlanOut(
            plan_type=plan.value,
            label=config["label"],
            price=config["price"],
            max_listings=config["max_listings"],
        )
        for plan, config in PLAN_CONFIG.items()
    ]


async def subscribe(
    db: AsyncSession, data: MembershipSubscribeRequest, host: User
) -> Membership:
    """Create or reactivate a membership subscription for a host.

    If an existing membership row exists (cancelled/expired), it is updated
    in-place to avoid violating the unique constraint on host_id.
    If the membership is already active, the plan is switched directly.
    """
    # Find host profile
    profile_result = await db.execute(
        select(HostProfile).where(HostProfile.user_id == host.id)
    )
    profile = profile_result.scalar_one_or_none()
    if profile is None:
        raise NotFoundError("Host profile not found. Register as a host first.")

    plan = MembershipPlan(data.plan_type)
    config = PLAN_CONFIG[plan]
    now = datetime.now(UTC)

    # Check for any existing membership row (unique constraint on host_id)
    existing_result = await db.execute(
        select(Membership).where(Membership.host_id == profile.id)
    )
    existing = existing_result.scalar_one_or_none()

    if existing is not None:
        # Reactivate / switch plan on the existing row
        existing.plan_type = plan.value
        existing.start_date = now
        existing.end_date = now + timedelta(days=30)
        existing.status = MembershipStatus.ACTIVE
        existing.auto_renew = True
        existing.amount = config["price"]
        existing.max_listings = config["max_listings"]
        existing.payment_ref = f"sim_{data.payment_token}"
        await db.flush()
        return existing

    # TODO: Process payment with data.payment_token via payment gateway
    # For now, we simulate successful payment
    membership = Membership(
        host_id=profile.id,
        plan_type=plan.value,
        start_date=now,
        end_date=now + timedelta(days=30),
        status=MembershipStatus.ACTIVE,
        amount=config["price"],
        max_listings=config["max_listings"],
        payment_ref=f"sim_{data.payment_token}",
    )
    db.add(membership)
    await db.flush()
    return membership


async def get_current_membership(db: AsyncSession, host: User) -> Membership:
    """Get the host's current membership."""
    profile_result = await db.execute(
        select(HostProfile).where(HostProfile.user_id == host.id)
    )
    profile = profile_result.scalar_one_or_none()
    if profile is None:
        raise NotFoundError("Host profile not found")

    mem_result = await db.execute(
        select(Membership).where(Membership.host_id == profile.id).order_by(
            Membership.created_at.desc()
        )
    )
    membership = mem_result.scalar_one_or_none()
    if membership is None:
        raise NotFoundError("No membership found")
    return membership


async def cancel_membership(db: AsyncSession, host: User) -> Membership:
    """Cancel the host's active membership."""
    membership = await get_current_membership(db, host)
    if membership.status != MembershipStatus.ACTIVE:
        raise BadRequestError("Membership is not active")
    membership.status = MembershipStatus.CANCELLED
    membership.auto_renew = False
    await db.flush()
    return membership


async def process_webhook(db: AsyncSession, event_type: str, payment_ref: str, status: str) -> None:
    """Process a payment gateway webhook to update membership status.

    In production, verify the webhook signature before processing.
    """
    result = await db.execute(
        select(Membership).where(Membership.payment_ref == payment_ref)
    )
    membership = result.scalar_one_or_none()
    if membership is None:
        return  # Unknown payment ref — ignore silently

    if event_type == "payment.succeeded":
        membership.status = MembershipStatus.ACTIVE
    elif event_type == "payment.failed":
        membership.status = MembershipStatus.PAST_DUE
    elif event_type == "subscription.cancelled":
        membership.status = MembershipStatus.CANCELLED

    await db.flush()
