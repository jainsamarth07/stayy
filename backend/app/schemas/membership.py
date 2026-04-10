"""Membership Pydantic schemas."""

import uuid
from datetime import datetime

from pydantic import BaseModel, Field

from app.schemas import DecimalFloat


class MembershipPlanOut(BaseModel):
    """Response schema for a membership plan description."""
    plan_type: str
    label: str
    price: DecimalFloat
    max_listings: int


class MembershipSubscribeRequest(BaseModel):
    """Request schema for subscribing to a membership plan."""
    plan_type: str = Field(..., pattern="^(basic|pro|premium)$")
    payment_token: str = Field(..., min_length=1, description="Payment gateway token")


class MembershipOut(BaseModel):
    """Response schema for a host's membership subscription."""
    id: uuid.UUID
    host_id: uuid.UUID
    plan_type: str
    start_date: datetime
    end_date: datetime
    status: str
    auto_renew: bool
    amount: DecimalFloat
    max_listings: int
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class MembershipWebhookPayload(BaseModel):
    """Generic payment webhook payload — adapt to your gateway."""

    event_type: str
    payment_ref: str
    status: str
    metadata: dict | None = None
