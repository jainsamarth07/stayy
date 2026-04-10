"""Booking service — create bookings (nightly & hourly), manage status."""

import logging
import uuid
from datetime import UTC, datetime
from decimal import Decimal

from sqlalchemy import and_, func, or_, select
from sqlalchemy import true as sa_true
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import BadRequestError, ForbiddenError, NotFoundError
from app.models.booking import Booking, BookingStatus, BookingType
from app.models.property import HourlyBookingConfig, Property
from app.models.user import User
from app.schemas.booking import BookingCreate

logger = logging.getLogger(__name__)

# Valid booking status transitions (state machine)
VALID_TRANSITIONS: dict[str, set[str]] = {
    BookingStatus.PENDING: {
        BookingStatus.CONFIRMED,
        BookingStatus.REJECTED,
        BookingStatus.CANCELLED,
    },
    BookingStatus.CONFIRMED: {BookingStatus.CANCELLED, BookingStatus.COMPLETED},
    BookingStatus.COMPLETED: set(),      # terminal
    BookingStatus.CANCELLED: set(),      # terminal
    BookingStatus.REJECTED: set(),       # terminal
}


async def create_booking(db: AsyncSession, data: BookingCreate, guest: User) -> Booking:
    """Create a new booking — supports both nightly and hourly types."""
    # Validate property
    prop_result = await db.execute(select(Property).where(Property.id == data.property_id))
    prop = prop_result.scalar_one_or_none()
    if prop is None or not prop.is_active:
        raise NotFoundError("Property not found or inactive")

    if prop.host_id == guest.id:
        raise BadRequestError("Cannot book your own property")

    # Validate dates
    if data.check_in >= data.check_out:
        raise BadRequestError("Check-out must be after check-in")
    if data.check_in < datetime.now(UTC):
        raise BadRequestError("Check-in must be in the future")

    # Check for overlapping bookings — use FOR UPDATE to prevent race conditions.
    # SQLite does not support FOR UPDATE, so we degrade gracefully.
    overlap_stmt = select(Booking).where(
        and_(
            Booking.property_id == data.property_id,
            Booking.status.in_([BookingStatus.PENDING, BookingStatus.CONFIRMED]),
            Booking.check_in < data.check_out,
            Booking.check_out > data.check_in,
        )
    )
    if "sqlite" not in str(db.bind.url):
        overlap_stmt = overlap_stmt.with_for_update()
    overlap = await db.execute(overlap_stmt)
    if overlap.scalars().first() is not None:
        raise BadRequestError("Property is not available for these dates")

    # Calculate price
    total_price: Decimal
    if data.booking_type == BookingType.HOURLY:
        if not prop.hourly_enabled:
            raise BadRequestError("Hourly booking not available for this property")
        config_result = await db.execute(
            select(HourlyBookingConfig).where(HourlyBookingConfig.property_id == prop.id)
        )
        config = config_result.scalar_one_or_none()
        if config is None:
            raise BadRequestError("Hourly configuration missing")
        if data.hours is None or data.hours < config.min_hours or data.hours > config.max_hours:
            raise BadRequestError(
                f"Hours must be between {config.min_hours} and {config.max_hours}"
            )
        total_price = config.hourly_price * data.hours
    else:
        nights = (data.check_out - data.check_in).days
        if nights < 1:
            raise BadRequestError("Booking must be at least 1 night")
        total_price = prop.price_per_night * nights

    booking = Booking(
        property_id=data.property_id,
        guest_id=guest.id,
        host_id=prop.host_id,
        check_in=data.check_in,
        check_out=data.check_out,
        total_price=total_price,
        booking_type=data.booking_type,
        hours=data.hours,
    )
    db.add(booking)
    await db.flush()

    # Trigger booking confirmation email asynchronously
    try:
        from app.tasks.email_tasks import send_booking_confirmation
        send_booking_confirmation.delay(guest.email, str(booking.id))
    except Exception:
        logger.warning("Failed to queue booking confirmation email", exc_info=True)

    return booking


async def update_booking_status(
    db: AsyncSession, booking_id: uuid.UUID, new_status: str, user: User
) -> Booking:
    """Update booking status — host can confirm/reject, both can cancel."""
    result = await db.execute(select(Booking).where(Booking.id == booking_id))
    booking = result.scalar_one_or_none()
    if booking is None:
        raise NotFoundError("Booking not found")

    # State machine validation
    allowed = VALID_TRANSITIONS.get(booking.status, set())
    if new_status not in allowed:
        raise BadRequestError(
            f"Cannot transition from '{booking.status}' to '{new_status}'"
        )

    # Permission checks
    if new_status in (BookingStatus.CONFIRMED, BookingStatus.REJECTED):
        if booking.host_id != user.id and user.role != "admin":
            raise ForbiddenError("Only the host can confirm or reject bookings")
    elif new_status == BookingStatus.CANCELLED:
        if booking.guest_id != user.id and booking.host_id != user.id and user.role != "admin":
            raise ForbiddenError("Only participants can cancel a booking")
    elif new_status == BookingStatus.COMPLETED:
        if booking.host_id != user.id and user.role != "admin":
            raise ForbiddenError("Only the host can mark a booking as completed")

    booking.status = new_status
    await db.flush()
    return booking


async def get_booking(db: AsyncSession, booking_id: uuid.UUID, user: User) -> Booking:
    """Get a single booking — only visible to participants and admins."""
    result = await db.execute(select(Booking).where(Booking.id == booking_id))
    booking = result.scalar_one_or_none()
    if booking is None:
        raise NotFoundError("Booking not found")
    if booking.guest_id != user.id and booking.host_id != user.id and user.role != "admin":
        raise ForbiddenError("Access denied")
    return booking


async def list_bookings(
    db: AsyncSession, user: User, page: int = 1, page_size: int = 20
) -> tuple[list[Booking], int]:
    """List bookings for the current user (guest or host — hosts see both)."""
    if user.role == "admin":
        base_filter = sa_true()
    elif user.role == "host":
        # Hosts see bookings they received AND any they made as guests
        base_filter = or_(Booking.host_id == user.id, Booking.guest_id == user.id)
    else:
        base_filter = Booking.guest_id == user.id

    count_result = await db.execute(
        select(func.count()).select_from(Booking).where(base_filter)
    )
    total = count_result.scalar() or 0

    result = await db.execute(
        select(Booking)
        .where(base_filter)
        .order_by(Booking.created_at.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
    )
    return list(result.scalars().all()), total
