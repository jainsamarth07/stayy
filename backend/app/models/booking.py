"""Booking model."""

import uuid
from datetime import UTC, datetime
from decimal import Decimal
from enum import StrEnum

from sqlalchemy import DateTime, ForeignKey, Integer, Numeric, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class BookingStatus(StrEnum):
    """Enumeration of possible booking statuses."""

    PENDING = "pending"
    CONFIRMED = "confirmed"
    CANCELLED = "cancelled"
    COMPLETED = "completed"
    REJECTED = "rejected"


class BookingType(StrEnum):
    """Enumeration of booking duration types."""

    NIGHTLY = "nightly"
    HOURLY = "hourly"


class Booking(Base):
    """A reservation for a property."""

    __tablename__ = "bookings"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    property_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("properties.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    guest_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    host_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    check_in: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    check_out: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    total_price: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    booking_type: Mapped[str] = mapped_column(
        String(20), nullable=False, default=BookingType.NIGHTLY
    )
    hours: Mapped[int | None] = mapped_column(Integer, nullable=True)
    status: Mapped[str] = mapped_column(
        String(20), nullable=False, default=BookingStatus.PENDING, index=True
    )
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
    property: Mapped["Property"] = relationship(  # type: ignore[name-defined]
        "Property", back_populates="bookings"
    )
    guest: Mapped["User"] = relationship(  # type: ignore[name-defined]
        "User", back_populates="bookings_as_guest", foreign_keys=[guest_id]
    )
    host: Mapped["User"] = relationship("User", foreign_keys=[host_id])  # type: ignore[name-defined]
    review: Mapped["Review | None"] = relationship(  # type: ignore[name-defined]
        "Review", back_populates="booking", uselist=False
    )
