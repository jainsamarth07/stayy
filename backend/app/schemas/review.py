"""Review Pydantic schemas."""

import uuid
from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, Field

from app.schemas import DecimalFloat


class ReviewCreate(BaseModel):
    """Request schema for submitting a property review."""
    booking_id: uuid.UUID
    rating: Decimal = Field(..., ge=1.0, le=5.0)
    comment: str | None = Field(None, max_length=2000)


class ReviewOut(BaseModel):
    """Response schema for a property review."""
    id: uuid.UUID
    booking_id: uuid.UUID
    property_id: uuid.UUID
    reviewer_id: uuid.UUID
    rating: DecimalFloat
    comment: str | None = None
    created_at: datetime

    model_config = {"from_attributes": True}


class PaginatedReviews(BaseModel):
    """Paginated wrapper for review lists."""
    items: list[ReviewOut]
    total: int
    page: int
    page_size: int
