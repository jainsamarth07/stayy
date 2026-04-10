"""Admin endpoints — platform management."""

import uuid

from fastapi import APIRouter, Depends, Query
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.database import get_db
from app.dependencies import require_admin
from app.models.booking import Booking, BookingStatus
from app.models.membership import Membership, MembershipStatus
from app.models.property import Property
from app.models.user import HostProfile, User
from app.schemas.user import UserOut

router = APIRouter()


@router.get("/users", response_model=dict)
async def list_users(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    _admin: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
) -> dict:
    """List all users (admin only)."""
    count_result = await db.execute(select(func.count()).select_from(User))
    total = count_result.scalar() or 0

    stmt = (
        select(User)
        .order_by(User.created_at.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
    )
    result = await db.execute(stmt)
    users = result.scalars().all()
    return {
        "items": [UserOut.model_validate(u) for u in users],
        "total": total,
        "page": page,
        "page_size": page_size,
    }


@router.get("/properties", response_model=dict)
async def list_all_properties(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    _admin: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
) -> dict:
    """List all properties (admin only)."""
    count_result = await db.execute(select(func.count()).select_from(Property))
    total = count_result.scalar() or 0

    stmt = (
        select(Property)
        .options(selectinload(Property.host))
        .order_by(Property.created_at.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
    )
    result = await db.execute(stmt)
    return {
        "items": [
            {
                "id": str(p.id),
                "title": p.title,
                "city": p.city,
                "country": p.country,
                "is_active": p.is_active,
                "price_per_night": float(p.price_per_night),
                "host_name": p.host.full_name if p.host else "Unknown",
            }
            for p in result.scalars().all()
        ],
        "total": total,
        "page": page,
        "page_size": page_size,
    }


@router.get("/memberships", response_model=dict)
async def list_all_memberships(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    _admin: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
) -> dict:
    """List all memberships (admin only)."""
    count_result = await db.execute(select(func.count()).select_from(Membership))
    total = count_result.scalar() or 0

    stmt = (
        select(Membership)
        .options(
            selectinload(Membership.host).selectinload(HostProfile.user)
        )
        .order_by(Membership.created_at.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
    )
    result = await db.execute(stmt)
    return {
        "items": [
            {
                "id": str(m.id),
                "user_name": m.host.user.full_name if m.host and m.host.user else "Unknown",
                "email": m.host.user.email if m.host and m.host.user else "",
                "plan": m.plan_type,
                "status": m.status,
                "amount": float(m.amount),
                "started_at": m.start_date.isoformat(),
                "expires_at": m.end_date.isoformat(),
            }
            for m in result.scalars().all()
        ],
        "total": total,
        "page": page,
        "page_size": page_size,
    }


@router.get("/bookings", response_model=dict)
async def list_all_bookings(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    _admin: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
) -> dict:
    """List all bookings (admin only)."""
    count_result = await db.execute(select(func.count()).select_from(Booking))
    total = count_result.scalar() or 0

    stmt = (
        select(Booking)
        .options(
            selectinload(Booking.property),
            selectinload(Booking.guest),
        )
        .order_by(Booking.created_at.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
    )
    result = await db.execute(stmt)
    bookings = result.scalars().all()
    return {
        "items": [
            {
                "id": str(b.id),
                "property_id": str(b.property_id),
                "property_title": b.property.title if b.property else "Deleted",
                "guest_id": str(b.guest_id),
                "guest_name": b.guest.full_name if b.guest else "Unknown",
                "host_id": str(b.host_id),
                "check_in": b.check_in.isoformat(),
                "check_out": b.check_out.isoformat(),
                "total_price": b.total_price,
                "status": b.status,
                "booking_type": b.booking_type,
                "created_at": b.created_at.isoformat(),
            }
            for b in bookings
        ],
        "total": total,
        "page": page,
        "page_size": page_size,
    }


@router.get("/dashboard")
async def dashboard(
    _admin: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Platform dashboard metrics (admin only)."""
    total_users = (await db.execute(select(func.count()).select_from(User))).scalar() or 0
    total_properties = (await db.execute(select(func.count()).select_from(Property))).scalar() or 0
    active_memberships = (
        await db.execute(
            select(func.count()).select_from(Membership).where(
                Membership.status == MembershipStatus.ACTIVE
            )
        )
    ).scalar() or 0
    total_bookings = (await db.execute(select(func.count()).select_from(Booking))).scalar() or 0
    completed_bookings = (
        await db.execute(
            select(func.count()).select_from(Booking).where(
                Booking.status == BookingStatus.COMPLETED
            )
        )
    ).scalar() or 0
    monthly_revenue = (
        await db.execute(
            select(func.sum(Membership.amount)).where(
                Membership.status == MembershipStatus.ACTIVE
            )
        )
    ).scalar() or 0.0

    return {
        "total_users": total_users,
        "total_properties": total_properties,
        "active_members": active_memberships,
        "total_bookings": total_bookings,
        "completed_bookings": completed_bookings,
        "monthly_revenue": float(monthly_revenue),
        "platform_growth": 0,
    }


@router.put("/users/{user_id}/status")
async def toggle_user_status(
    user_id: uuid.UUID,
    _admin: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Enable or disable a user account (admin only)."""
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if user is None:
        from app.core.exceptions import NotFoundError  # noqa: E402
        raise NotFoundError("User not found")

    user.is_active = not user.is_active
    await db.flush()
    return {"id": str(user.id), "is_active": user.is_active}
