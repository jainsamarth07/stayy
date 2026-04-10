"""Property, PropertyImage, and HourlyBookingConfig models."""

import uuid
from datetime import UTC, datetime, time
from decimal import Decimal

from sqlalchemy import (
    Boolean,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    Numeric,
    String,
    Text,
    Time,
)
from sqlalchemy.dialects.postgresql import JSON, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class Property(Base):
    """A rental property listing."""

    __tablename__ = "properties"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    host_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    city: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    address: Mapped[str] = mapped_column(String(500), nullable=False)
    latitude: Mapped[float | None] = mapped_column(Float, nullable=True)
    longitude: Mapped[float | None] = mapped_column(Float, nullable=True)
    price_per_night: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    max_guests: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    amenities: Mapped[list | None] = mapped_column(JSON, nullable=True, default=list)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    hourly_enabled: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
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
    host: Mapped["User"] = relationship(  # type: ignore[name-defined]
        "User", back_populates="properties"
    )
    images: Mapped[list["PropertyImage"]] = relationship(
        "PropertyImage", back_populates="property", cascade="all, delete-orphan"
    )
    hourly_config: Mapped["HourlyBookingConfig | None"] = relationship(
        "HourlyBookingConfig",
        back_populates="property",
        uselist=False,
        cascade="all, delete-orphan",
    )
    bookings: Mapped[list["Booking"]] = relationship(  # type: ignore[name-defined]
        "Booking", back_populates="property"
    )
    reviews: Mapped[list["Review"]] = relationship(  # type: ignore[name-defined]
        "Review", back_populates="property"
    )


class PropertyImage(Base):
    """Image attached to a property listing."""

    __tablename__ = "property_images"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    property_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("properties.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    image_url: Mapped[str] = mapped_column(String(1000), nullable=False)
    is_primary: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    sort_order: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    # Relationships
    property: Mapped["Property"] = relationship("Property", back_populates="images")


class HourlyBookingConfig(Base):
    """Hourly booking settings for a property (host-controlled)."""

    __tablename__ = "hourly_booking_configs"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    property_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("properties.id", ondelete="CASCADE"),
        unique=True,
        nullable=False,
    )
    hourly_price: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    min_hours: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    max_hours: Mapped[int] = mapped_column(Integer, default=12, nullable=False)
    available_from: Mapped[time] = mapped_column(Time, nullable=False, default=time(8, 0))
    available_to: Mapped[time] = mapped_column(Time, nullable=False, default=time(22, 0))

    # Relationships
    property: Mapped["Property"] = relationship("Property", back_populates="hourly_config")
