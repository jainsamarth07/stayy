"""User and HostProfile models."""

import uuid
from datetime import UTC, datetime

from sqlalchemy import Boolean, DateTime, Float, ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class User(Base):
    """Platform user — can be guest, host, or admin."""

    __tablename__ = "users"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True, nullable=False)
    hashed_password: Mapped[str] = mapped_column(String(255), nullable=False)
    full_name: Mapped[str] = mapped_column(String(255), nullable=False)
    phone: Mapped[str | None] = mapped_column(String(20), nullable=True)
    role: Mapped[str] = mapped_column(String(20), nullable=False, default="user")
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(UTC), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(UTC),
        onupdate=lambda: datetime.now(UTC),
        nullable=False,
    )
    # Timestamp of last password change — used to invalidate JWTs issued before this
    password_changed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True, default=None
    )

    # Relationships
    host_profile: Mapped["HostProfile | None"] = relationship(
        "HostProfile", back_populates="user", uselist=False
    )
    properties: Mapped[list["Property"]] = relationship(  # type: ignore[name-defined]
        "Property", back_populates="host", foreign_keys="Property.host_id"
    )
    bookings_as_guest: Mapped[list["Booking"]] = relationship(  # type: ignore[name-defined]
        "Booking", back_populates="guest", foreign_keys="Booking.guest_id"
    )
    reviews: Mapped[list["Review"]] = relationship(  # type: ignore[name-defined]
        "Review", back_populates="reviewer"
    )


class HostProfile(Base):
    """Extended profile for hosts with business details."""

    __tablename__ = "host_profiles"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), unique=True, nullable=False
    )
    business_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    bio: Mapped[str | None] = mapped_column(Text, nullable=True)
    phone_visible: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    is_verified: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    avg_rating: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    total_reviews: Mapped[int] = mapped_column(default=0, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(UTC), nullable=False
    )

    # Relationships
    user: Mapped["User"] = relationship("User", back_populates="host_profile")
    membership: Mapped["Membership | None"] = relationship(  # type: ignore[name-defined]
        "Membership", back_populates="host", uselist=False
    )
