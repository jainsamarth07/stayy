"""Property-related Pydantic schemas."""

import uuid
from datetime import datetime, time
from decimal import Decimal

from pydantic import BaseModel, Field

from app.schemas import DecimalFloat


# ---------- Property ----------
class PropertyCreate(BaseModel):
    """Schema for creating a new property listing."""

    title: str = Field(..., min_length=3, max_length=255)
    description: str = Field(..., min_length=10)
    city: str = Field(..., min_length=1, max_length=100)
    address: str = Field(..., min_length=5, max_length=500)
    latitude: float | None = None
    longitude: float | None = None
    price_per_night: Decimal = Field(..., gt=0, decimal_places=2)
    max_guests: int = Field(default=1, ge=1, le=50)
    amenities: list[str] | None = None


class PropertyUpdate(BaseModel):
    """Schema for partially updating a property listing."""

    title: str | None = Field(None, min_length=3, max_length=255)
    description: str | None = Field(None, min_length=10)
    city: str | None = Field(None, min_length=1, max_length=100)
    address: str | None = Field(None, min_length=5, max_length=500)
    latitude: float | None = None
    longitude: float | None = None
    price_per_night: Decimal | None = Field(None, gt=0, decimal_places=2)
    max_guests: int | None = Field(None, ge=1, le=50)
    amenities: list[str] | None = None
    is_active: bool | None = None


class PropertyImageOut(BaseModel):
    """Public representation of a property image."""

    id: uuid.UUID
    image_url: str
    is_primary: bool
    sort_order: int

    model_config = {"from_attributes": True}


class HourlyBookingConfigOut(BaseModel):
    """Public representation of hourly booking configuration."""

    id: uuid.UUID
    hourly_price: DecimalFloat
    min_hours: int
    max_hours: int
    available_from: time
    available_to: time

    model_config = {"from_attributes": True}


class HourlyBookingConfigUpdate(BaseModel):
    """Schema for creating or updating hourly booking settings."""

    hourly_price: Decimal = Field(..., gt=0, decimal_places=2)
    min_hours: int = Field(default=1, ge=1)
    max_hours: int = Field(default=12, ge=1, le=24)
    available_from: time = Field(default=time(8, 0))
    available_to: time = Field(default=time(22, 0))


class PropertyOut(BaseModel):
    """Full property listing returned by API, including images and hourly config."""

    id: uuid.UUID
    host_id: uuid.UUID
    title: str
    description: str
    city: str
    address: str
    latitude: float | None = None
    longitude: float | None = None
    price_per_night: DecimalFloat
    max_guests: int
    amenities: list[str] | None = None
    is_active: bool
    hourly_enabled: bool
    images: list[PropertyImageOut] = []
    hourly_config: HourlyBookingConfigOut | None = None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class PropertySearchParams(BaseModel):
    """Query parameters for property search."""

    city: str | None = None
    min_price: Decimal | None = Field(None, ge=0)
    max_price: Decimal | None = Field(None, ge=0)
    max_guests: int | None = Field(None, ge=1)
    amenities: list[str] | None = None
    hourly_available: bool | None = None
    host_id: uuid.UUID | None = None
    page: int = Field(default=1, ge=1)
    page_size: int = Field(default=20, ge=1, le=100)
