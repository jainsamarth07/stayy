"""Booking endpoints."""

import uuid

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.dependencies import get_current_user
from app.models.user import User
from app.schemas.booking import BookingCreate, BookingOut, BookingStatusUpdate, PaginatedBookings
from app.services import booking_service

router = APIRouter()


@router.post("", response_model=BookingOut, status_code=201)
async def create_booking(
    data: BookingCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> BookingOut:
    """Create a new booking (nightly or hourly)."""
    booking = await booking_service.create_booking(db, data, current_user)
    return BookingOut.model_validate(booking)


@router.get("", response_model=PaginatedBookings)
async def list_bookings(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> PaginatedBookings:
    """List bookings for the current user."""
    items, total = await booking_service.list_bookings(db, current_user, page, page_size)
    return PaginatedBookings(
        items=[BookingOut.model_validate(b) for b in items],
        total=total,
        page=page,
        page_size=page_size,
    )


@router.get("/{booking_id}", response_model=BookingOut)
async def get_booking(
    booking_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> BookingOut:
    """Get booking details (participants only)."""
    booking = await booking_service.get_booking(db, booking_id, current_user)
    return BookingOut.model_validate(booking)


@router.put("/{booking_id}/status", response_model=BookingOut)
async def update_booking_status(
    booking_id: uuid.UUID,
    data: BookingStatusUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> BookingOut:
    """Update booking status (confirm, reject, cancel, complete)."""
    booking = await booking_service.update_booking_status(db, booking_id, data.status, current_user)
    return BookingOut.model_validate(booking)


@router.post("/{booking_id}/cancel", response_model=BookingOut)
async def cancel_booking(
    booking_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> BookingOut:
    """Cancel a booking."""
    booking = await booking_service.update_booking_status(
        db, booking_id, "cancelled", current_user
    )
    return BookingOut.model_validate(booking)
