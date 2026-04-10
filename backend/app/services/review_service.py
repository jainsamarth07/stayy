"""Review service — create reviews, list property reviews."""

import uuid

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import BadRequestError, ForbiddenError, NotFoundError
from app.models.booking import Booking, BookingStatus
from app.models.review import Review
from app.models.user import HostProfile, User
from app.schemas.review import ReviewCreate


async def create_review(db: AsyncSession, data: ReviewCreate, reviewer: User) -> Review:
    """Create a review for a completed booking (guests only)."""
    # Validate the booking
    booking_result = await db.execute(select(Booking).where(Booking.id == data.booking_id))
    booking = booking_result.scalar_one_or_none()
    if booking is None:
        raise NotFoundError("Booking not found")
    if booking.guest_id != reviewer.id:
        raise ForbiddenError("Only the guest can review a booking")
    if booking.status != BookingStatus.COMPLETED:
        raise BadRequestError("Can only review completed bookings")

    # Check for existing review
    existing = await db.execute(
        select(Review).where(Review.booking_id == data.booking_id)
    )
    if existing.scalar_one_or_none() is not None:
        raise BadRequestError("A review already exists for this booking")

    review = Review(
        booking_id=data.booking_id,
        property_id=booking.property_id,
        reviewer_id=reviewer.id,
        rating=data.rating,
        comment=data.comment,
    )
    db.add(review)
    await db.flush()

    # Update host avg rating
    await _update_host_rating(db, booking.host_id)

    return review


async def list_property_reviews(
    db: AsyncSession, property_id: uuid.UUID, page: int = 1, page_size: int = 20
) -> tuple[list[Review], int]:
    """List all reviews for a property."""
    count_result = await db.execute(
        select(func.count()).select_from(Review).where(Review.property_id == property_id)
    )
    total = count_result.scalar() or 0

    result = await db.execute(
        select(Review)
        .where(Review.property_id == property_id)
        .order_by(Review.created_at.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
    )
    return list(result.scalars().all()), total


async def list_host_reviews(
    db: AsyncSession, host_id: uuid.UUID, page: int = 1, page_size: int = 20
) -> tuple[list[Review], int]:
    """List all reviews for properties owned by a host."""
    from app.models.property import Property

    host_property_ids = select(Property.id).where(Property.host_id == host_id)

    count_result = await db.execute(
        select(func.count()).select_from(Review).where(Review.property_id.in_(host_property_ids))
    )
    total = count_result.scalar() or 0

    result = await db.execute(
        select(Review)
        .where(Review.property_id.in_(host_property_ids))
        .order_by(Review.created_at.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
    )
    return list(result.scalars().all()), total


async def _update_host_rating(db: AsyncSession, host_user_id: uuid.UUID) -> None:
    """Recalculate and update the host's average rating."""
    # Get all reviews for properties owned by this host
    avg_result = await db.execute(
        select(func.avg(Review.rating), func.count(Review.id)).where(
            Review.property_id.in_(
                select(Booking.property_id).where(Booking.host_id == host_user_id)
            )
        )
    )
    row = avg_result.one_or_none()
    if row is None:
        return

    avg_rating, total_reviews = row
    profile_result = await db.execute(
        select(HostProfile).where(HostProfile.user_id == host_user_id)
    )
    profile = profile_result.scalar_one_or_none()
    if profile:
        profile.avg_rating = float(avg_rating or 0.0)
        profile.total_reviews = int(total_reviews or 0)
        await db.flush()
