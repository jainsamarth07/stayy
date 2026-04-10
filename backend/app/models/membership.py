"""Membership model for host subscriptions."""

import uuid
from datetime import UTC, datetime
from decimal import Decimal
from enum import StrEnum

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, Numeric, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class MembershipPlan(StrEnum):
    """Available membership tier levels."""

    BASIC = "basic"
    PRO = "pro"
    PREMIUM = "premium"


class MembershipStatus(StrEnum):
    """Possible lifecycle states of a membership subscription."""

    ACTIVE = "active"
    CANCELLED = "cancelled"
    EXPIRED = "expired"
    PAST_DUE = "past_due"


# Plan configuration — can move to DB later for admin control
PLAN_CONFIG = {
    MembershipPlan.BASIC: {
        "price": Decimal("2499.00"), "max_listings": 5, "label": "Basic",
    },
    MembershipPlan.PRO: {
        "price": Decimal("6499.00"), "max_listings": 25, "label": "Pro",
    },
    MembershipPlan.PREMIUM: {
        "price": Decimal("16499.00"), "max_listings": 999999, "label": "Premium",
    },
}


class Membership(Base):
    """Host membership subscription."""

    __tablename__ = "memberships"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    host_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("host_profiles.id", ondelete="CASCADE"),
        unique=True,
        nullable=False,
    )
    plan_type: Mapped[str] = mapped_column(String(20), nullable=False, default=MembershipPlan.BASIC)
    start_date: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    end_date: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    status: Mapped[str] = mapped_column(
        String(20), nullable=False, default=MembershipStatus.ACTIVE, index=True
    )
    auto_renew: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    payment_ref: Mapped[str | None] = mapped_column(String(255), nullable=True)
    amount: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    max_listings: Mapped[int] = mapped_column(Integer, nullable=False, default=5)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(UTC), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(UTC),
        onupdate=lambda: datetime.now(UTC),
        nullable=False,
    )

    # Relationships
    host: Mapped["HostProfile"] = relationship(  # type: ignore[name-defined]
        "HostProfile", back_populates="membership"
    )
