"""Booking-related Pydantic schemas."""

import uuid
from datetime import datetime

from pydantic import BaseModel, Field

from app.schemas import DecimalFloat


class BookingCreate(BaseModel):
    """Schema for creating a new booking (nightly or hourly)."""

    property_id: uuid.UUID
    check_in: datetime
    check_out: datetime
    booking_type: str = Field(default="nightly", pattern="^(nightly|hourly)$")
    hours: int | None = Field(None, ge=1, le=24)


class BookingStatusUpdate(BaseModel):
    """Schema for transitioning a booking to a new status."""

    status: str = Field(..., pattern="^(confirmed|cancelled|completed|rejected)$")


class BookingOut(BaseModel):
    """Public booking representation returned by API responses."""

    id: uuid.UUID
    property_id: uuid.UUID
    guest_id: uuid.UUID
    host_id: uuid.UUID
    check_in: datetime
    check_out: datetime
    total_price: DecimalFloat
    booking_type: str
    hours: int | None = None
    status: str
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class PaginatedBookings(BaseModel):
    """Paginated list of bookings with total count."""

    items: list[BookingOut]
    total: int
    page: int
    page_size: int
