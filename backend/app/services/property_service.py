"""Property service — listing CRUD, search, image management, hourly config."""

import uuid
from datetime import UTC

from sqlalchemy import and_, func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.exceptions import ForbiddenError, MembershipRequiredError, NotFoundError
from app.models.membership import Membership, MembershipStatus
from app.models.property import HourlyBookingConfig, Property, PropertyImage
from app.models.user import HostProfile, User
from app.schemas.property import (
    HourlyBookingConfigUpdate,
    PropertyCreate,
    PropertySearchParams,
    PropertyUpdate,
)


async def _verify_active_membership(db: AsyncSession, user: User) -> Membership:
    """Ensure the host has an active, non-expired membership. Returns the membership."""
    from datetime import datetime

    result = await db.execute(
        select(HostProfile).where(HostProfile.user_id == user.id)
    )
    profile = result.scalar_one_or_none()
    if profile is None:
        raise ForbiddenError("Host profile not found")

    mem_result = await db.execute(
        select(Membership).where(
            and_(Membership.host_id == profile.id, Membership.status == MembershipStatus.ACTIVE)
        )
    )
    membership = mem_result.scalar_one_or_none()
    if membership is None:
        raise MembershipRequiredError()

    # Also check end_date hasn't passed
    if membership.end_date:
        end_date = membership.end_date
        if end_date.tzinfo is None:
            end_date = end_date.replace(tzinfo=UTC)
        if end_date < datetime.now(UTC):
            membership.status = "expired"
            await db.flush()
            raise MembershipRequiredError()

    return membership


async def _count_host_listings(db: AsyncSession, host_id: uuid.UUID) -> int:
    """Count active listings for a host."""
    result = await db.execute(
        select(func.count()).select_from(Property).where(
            and_(Property.host_id == host_id, Property.is_active.is_(True))
        )
    )
    return result.scalar() or 0


async def create_property(db: AsyncSession, data: PropertyCreate, host: User) -> Property:
    """Create a new property listing (requires active membership + listing cap)."""
    membership = await _verify_active_membership(db, host)

    # Enforce plan-based listing limit
    current_count = await _count_host_listings(db, host.id)
    if current_count >= membership.max_listings:
        raise ForbiddenError(
            f"Your {membership.plan_type} plan allows up to {membership.max_listings} listings. "
            f"Upgrade your plan to add more."
        )

    prop = Property(
        host_id=host.id,
        title=data.title,
        description=data.description,
        city=data.city,
        address=data.address,
        latitude=data.latitude,
        longitude=data.longitude,
        price_per_night=data.price_per_night,
        max_guests=data.max_guests,
        amenities=data.amenities,
    )
    db.add(prop)
    await db.flush()

    # Re-fetch with eager-loaded relationships so serialisation works in async
    result = await db.execute(
        select(Property)
        .where(Property.id == prop.id)
        .options(selectinload(Property.images), selectinload(Property.hourly_config))
    )
    return result.scalar_one()


async def update_property(
    db: AsyncSession, property_id: uuid.UUID, data: PropertyUpdate, host: User
) -> Property:
    """Update an existing property listing."""
    prop = await _get_property_for_host(db, property_id, host.id)
    update_data = data.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(prop, key, value)
    await db.flush()
    return prop


async def delete_property(db: AsyncSession, property_id: uuid.UUID, host: User) -> None:
    """Soft-delete (deactivate) a property."""
    prop = await _get_property_for_host(db, property_id, host.id)
    prop.is_active = False
    await db.flush()


async def get_property(db: AsyncSession, property_id: uuid.UUID) -> Property:
    """Get a single property with all relations loaded."""
    result = await db.execute(
        select(Property)
        .where(Property.id == property_id)
        .options(selectinload(Property.images), selectinload(Property.hourly_config))
    )
    prop = result.scalar_one_or_none()
    if prop is None:
        raise NotFoundError("Property not found")
    return prop


async def search_properties(
    db: AsyncSession, params: PropertySearchParams
) -> tuple[list[Property], int]:
    """Search properties with filters, pagination."""
    query = (
        select(Property)
        .where(Property.is_active.is_(True))
        .options(selectinload(Property.images), selectinload(Property.hourly_config))
    )
    count_query = select(func.count()).select_from(Property).where(Property.is_active.is_(True))

    if params.city:
        # Escape LIKE wildcards in user input to prevent unintended matches
        safe_city = params.city.replace("%", r"\%").replace("_", r"\_")
        city_filter = Property.city.ilike(f"%{safe_city}%", escape="\\")
        query = query.where(city_filter)
        count_query = count_query.where(city_filter)
    if params.min_price is not None:
        query = query.where(Property.price_per_night >= params.min_price)
        count_query = count_query.where(Property.price_per_night >= params.min_price)
    if params.max_price is not None:
        query = query.where(Property.price_per_night <= params.max_price)
        count_query = count_query.where(Property.price_per_night <= params.max_price)
    if params.max_guests is not None:
        query = query.where(Property.max_guests >= params.max_guests)
        count_query = count_query.where(Property.max_guests >= params.max_guests)
    if params.hourly_available is True:
        query = query.where(Property.hourly_enabled.is_(True))
        count_query = count_query.where(Property.hourly_enabled.is_(True))
    if params.host_id is not None:
        query = query.where(Property.host_id == params.host_id)
        count_query = count_query.where(Property.host_id == params.host_id)

    total = (await db.execute(count_query)).scalar() or 0
    offset = (params.page - 1) * params.page_size
    query = query.order_by(Property.created_at.desc()).offset(offset).limit(params.page_size)

    result = await db.execute(query)
    return list(result.scalars().all()), total


async def configure_hourly_booking(
    db: AsyncSession, property_id: uuid.UUID, data: HourlyBookingConfigUpdate, host: User
) -> Property:
    """Enable or update hourly booking configuration for a property."""
    prop = await _get_property_for_host(db, property_id, host.id)

    result = await db.execute(
        select(HourlyBookingConfig).where(HourlyBookingConfig.property_id == property_id)
    )
    config = result.scalar_one_or_none()

    if config is None:
        config = HourlyBookingConfig(
            property_id=property_id,
            hourly_price=data.hourly_price,
            min_hours=data.min_hours,
            max_hours=data.max_hours,
            available_from=data.available_from,
            available_to=data.available_to,
        )
        db.add(config)
    else:
        for key, value in data.model_dump().items():
            setattr(config, key, value)

    prop.hourly_enabled = True
    await db.flush()

    # Re-fetch with eager-loaded relationships so the response includes the new config
    result = await db.execute(
        select(Property)
        .where(Property.id == property_id)
        .options(selectinload(Property.images), selectinload(Property.hourly_config))
    )
    return result.scalar_one()


async def add_property_image(
    db: AsyncSession,
    property_id: uuid.UUID,
    image_url: str,
    is_primary: bool,
    host: User,
) -> PropertyImage:
    """Add an image to a property listing."""
    await _get_property_for_host(db, property_id, host.id)

    if is_primary:
        # Un-mark existing primary
        existing_primary = await db.execute(
            select(PropertyImage).where(
                and_(PropertyImage.property_id == property_id, PropertyImage.is_primary.is_(True))
            )
        )
        for img in existing_primary.scalars().all():
            img.is_primary = False

    image = PropertyImage(
        property_id=property_id,
        image_url=image_url,
        is_primary=is_primary,
    )
    db.add(image)
    await db.flush()
    return image


async def _get_property_for_host(
    db: AsyncSession, property_id: uuid.UUID, host_id: uuid.UUID
) -> Property:
    """Fetch property and verify the caller is its host."""
    result = await db.execute(
        select(Property)
        .where(Property.id == property_id)
        .options(selectinload(Property.images), selectinload(Property.hourly_config))
    )
    prop = result.scalar_one_or_none()
    if prop is None:
        raise NotFoundError("Property not found")
    if prop.host_id != host_id:
        raise ForbiddenError("You do not own this property")
    return prop
