"""Direct unit tests for all service-layer functions.

These tests call service functions directly (bypassing HTTP/ASGI) so that
pytest-cov can reliably track every executed branch.  They complement the
integration tests in test_*_integration.py which exercise the full stack.
"""
# ruff: noqa: S106  # hardcoded passwords/tokens are unavoidable in test fixtures

from __future__ import annotations

import uuid
from datetime import UTC, datetime, timedelta
from decimal import Decimal

import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import (
    BadRequestError,
    ConflictError,
    ForbiddenError,
    MembershipRequiredError,
    NotFoundError,
    UnauthorizedError,
)
from app.core.security import create_refresh_token, hash_password
from app.models.booking import Booking, BookingStatus, BookingType
from app.models.membership import Membership, MembershipStatus
from app.models.property import HourlyBookingConfig, Property
from app.models.user import HostProfile, User
from app.schemas.booking import BookingCreate
from app.schemas.membership import MembershipSubscribeRequest
from app.schemas.message import ConversationCreate, MessageCreate
from app.schemas.property import (
    HourlyBookingConfigUpdate,
    PropertyCreate,
    PropertySearchParams,
    PropertyUpdate,
)
from app.schemas.review import ReviewCreate
from app.schemas.user import UserRegister
from app.services import (
    auth_service,
    booking_service,
    membership_service,
    message_service,
    property_service,
    review_service,
)

# ---------------------------------------------------------------------------
# Shared helpers
# ---------------------------------------------------------------------------

def _make_user(
    role: str = "user",
    email: str | None = None,
    is_active: bool = True,
) -> User:
    """Build an in-memory User (not yet persisted)."""
    return User(
        id=uuid.uuid4(),
        email=email or f"u_{uuid.uuid4().hex[:8]}@test.com",
        hashed_password=hash_password("Password1!"),
        full_name="Unit Tester",
        role=role,
        is_active=is_active,
    )


async def _persist_host_with_membership(
    db: AsyncSession,
    plan: str = "basic",
) -> tuple[User, HostProfile, Membership]:
    """Create a host user + profile + active membership and flush to DB."""
    user = _make_user(role="host")
    db.add(user)
    await db.flush()

    profile = HostProfile(user_id=user.id)
    db.add(profile)
    await db.flush()

    mem = Membership(
        host_id=profile.id,
        plan_type=plan,
        start_date=datetime.now(UTC),
        end_date=datetime.now(UTC) + timedelta(days=30),
        status=MembershipStatus.ACTIVE,
        amount=Decimal("2499"),
        max_listings=5 if plan == "basic" else 25,
    )
    db.add(mem)
    await db.flush()

    return user, profile, mem


async def _create_property(db: AsyncSession, host: User) -> Property:
    """Create and persist a minimal active property."""
    prop = Property(
        host_id=host.id,
        title="Test Property",
        description="A nice place for unit testing",
        city="Testville",
        address="1 Test Street",
        price_per_night=Decimal("100.00"),
        max_guests=2,
    )
    db.add(prop)
    await db.flush()
    return prop


async def _create_completed_booking(
    db: AsyncSession, prop: Property, guest: User
) -> Booking:
    """Create a completed booking so reviews can be written."""
    booking = Booking(
        property_id=prop.id,
        guest_id=guest.id,
        host_id=prop.host_id,
        check_in=datetime.now(UTC) - timedelta(days=10),
        check_out=datetime.now(UTC) - timedelta(days=7),
        total_price=Decimal("300.00"),
        status=BookingStatus.COMPLETED,
    )
    db.add(booking)
    await db.flush()
    return booking


# ===========================================================================
# auth_service
# ===========================================================================

class TestAuthService:

    async def test_register_user_success(self, db_session: AsyncSession):
        data = UserRegister(
            email="newuser@example.com",
            password="Secure1!",
            full_name="New User",
            role="user",
        )
        user = await auth_service.register_user(db_session, data)
        assert user.email == "newuser@example.com"
        assert user.role == "user"

    async def test_register_host_creates_profile(self, db_session: AsyncSession):
        data = UserRegister(
            email="newhost@example.com",
            password="Secure1!",
            full_name="New Host",
            role="host",
        )
        user = await auth_service.register_user(db_session, data)
        assert user.role == "host"
        # HostProfile row should exist
        from sqlalchemy import select
        result = await db_session.execute(
            select(HostProfile).where(HostProfile.user_id == user.id)
        )
        assert result.scalar_one_or_none() is not None

    async def test_register_duplicate_email_raises(self, db_session: AsyncSession):
        data = UserRegister(
            email="dup@example.com",
            password="Secure1!",
            full_name="First",
            role="user",
        )
        await auth_service.register_user(db_session, data)
        with pytest.raises(ConflictError):
            await auth_service.register_user(db_session, data)

    async def test_authenticate_user_success(self, db_session: AsyncSession):
        data = UserRegister(
            email="auth_ok@example.com",
            password="Secure1!",
            full_name="Auth User",
            role="user",
        )
        await auth_service.register_user(db_session, data)
        tokens = await auth_service.authenticate_user(
            db_session, "auth_ok@example.com", "Secure1!"
        )
        assert tokens.access_token

    async def test_authenticate_wrong_password(self, db_session: AsyncSession):
        data = UserRegister(
            email="auth_bad@example.com",
            password="Secure1!",
            full_name="Bad Auth",
            role="user",
        )
        await auth_service.register_user(db_session, data)
        with pytest.raises(UnauthorizedError):
            await auth_service.authenticate_user(
                db_session, "auth_bad@example.com", "WrongPass!"
            )

    async def test_authenticate_wrong_email(self, db_session: AsyncSession):
        with pytest.raises(UnauthorizedError):
            await auth_service.authenticate_user(
                db_session, "nobody@example.com", "pass"
            )

    async def test_authenticate_inactive_user(self, db_session: AsyncSession):
        user = _make_user(email="inactive@example.com", is_active=False)
        db_session.add(user)
        await db_session.flush()
        with pytest.raises(UnauthorizedError):
            await auth_service.authenticate_user(
                db_session, "inactive@example.com", "Password1!"
            )

    async def test_refresh_token_success(self, db_session: AsyncSession):
        data = UserRegister(
            email="refresh_ok@example.com",
            password="Secure1!",
            full_name="Refresh User",
            role="user",
        )
        user = await auth_service.register_user(db_session, data)
        refresh = create_refresh_token({"sub": str(user.id), "role": user.role})
        tokens = await auth_service.refresh_access_token(db_session, refresh)
        assert tokens.access_token

    async def test_refresh_token_invalid(self, db_session: AsyncSession):
        with pytest.raises(UnauthorizedError):
            await auth_service.refresh_access_token(db_session, "not-a-token")

    async def test_refresh_token_wrong_type(self, db_session: AsyncSession):
        from app.core.security import create_access_token
        user = _make_user()
        db_session.add(user)
        await db_session.flush()
        # Access token used where refresh is expected
        access = create_access_token({"sub": str(user.id), "role": user.role})
        with pytest.raises(UnauthorizedError):
            await auth_service.refresh_access_token(db_session, access)

    async def test_refresh_token_nonexistent_user(self, db_session: AsyncSession):
        fake_id = str(uuid.uuid4())
        refresh = create_refresh_token({"sub": fake_id, "role": "user"})
        with pytest.raises(UnauthorizedError):
            await auth_service.refresh_access_token(db_session, refresh)


# ===========================================================================
# booking_service
# ===========================================================================

class TestBookingService:

    @pytest_asyncio.fixture
    async def host(self, db_session: AsyncSession) -> User:
        user, _profile, _mem = await _persist_host_with_membership(db_session)
        return user

    @pytest_asyncio.fixture
    async def prop(self, db_session: AsyncSession, host: User) -> Property:
        return await _create_property(db_session, host)

    @pytest_asyncio.fixture
    async def guest(self, db_session: AsyncSession) -> User:
        user = _make_user(role="user")
        db_session.add(user)
        await db_session.flush()
        return user

    # --- create_booking ---

    async def test_create_booking_nightly(
        self, db_session: AsyncSession, prop: Property, guest: User
    ):
        data = BookingCreate(
            property_id=prop.id,
            check_in=datetime.now(UTC) + timedelta(days=5),
            check_out=datetime.now(UTC) + timedelta(days=8),
        )
        booking = await booking_service.create_booking(db_session, data, guest)
        assert booking.total_price == Decimal("300.00")
        assert booking.booking_type == BookingType.NIGHTLY

    async def test_create_booking_invalid_property(
        self, db_session: AsyncSession, guest: User
    ):
        data = BookingCreate(
            property_id=uuid.uuid4(),
            check_in=datetime.now(UTC) + timedelta(days=1),
            check_out=datetime.now(UTC) + timedelta(days=2),
        )
        with pytest.raises(NotFoundError):
            await booking_service.create_booking(db_session, data, guest)

    async def test_create_booking_host_books_own(
        self, db_session: AsyncSession, host: User, prop: Property
    ):
        data = BookingCreate(
            property_id=prop.id,
            check_in=datetime.now(UTC) + timedelta(days=1),
            check_out=datetime.now(UTC) + timedelta(days=2),
        )
        with pytest.raises(BadRequestError):
            await booking_service.create_booking(db_session, data, host)

    async def test_create_booking_checkout_before_checkin(
        self, db_session: AsyncSession, prop: Property, guest: User
    ):
        data = BookingCreate(
            property_id=prop.id,
            check_in=datetime.now(UTC) + timedelta(days=5),
            check_out=datetime.now(UTC) + timedelta(days=3),
        )
        with pytest.raises(BadRequestError):
            await booking_service.create_booking(db_session, data, guest)

    async def test_create_booking_checkin_in_past(
        self, db_session: AsyncSession, prop: Property, guest: User
    ):
        data = BookingCreate(
            property_id=prop.id,
            check_in=datetime.now(UTC) - timedelta(days=2),
            check_out=datetime.now(UTC) + timedelta(days=1),
        )
        with pytest.raises(BadRequestError):
            await booking_service.create_booking(db_session, data, guest)

    async def test_create_booking_overlap(
        self, db_session: AsyncSession, prop: Property, guest: User
    ):
        data1 = BookingCreate(
            property_id=prop.id,
            check_in=datetime.now(UTC) + timedelta(days=5),
            check_out=datetime.now(UTC) + timedelta(days=10),
        )
        await booking_service.create_booking(db_session, data1, guest)
        # Overlapping range
        data2 = BookingCreate(
            property_id=prop.id,
            check_in=datetime.now(UTC) + timedelta(days=7),
            check_out=datetime.now(UTC) + timedelta(days=12),
        )
        with pytest.raises(BadRequestError):
            await booking_service.create_booking(db_session, data2, guest)

    async def test_create_hourly_booking_not_enabled(
        self, db_session: AsyncSession, prop: Property, guest: User
    ):
        data = BookingCreate(
            property_id=prop.id,
            check_in=datetime.now(UTC) + timedelta(days=1),
            check_out=datetime.now(UTC) + timedelta(days=2),
            booking_type=BookingType.HOURLY,
            hours=3,
        )
        with pytest.raises(BadRequestError):
            await booking_service.create_booking(db_session, data, guest)

    async def test_create_hourly_booking_success(
        self, db_session: AsyncSession, prop: Property, guest: User
    ):
        prop.hourly_enabled = True
        config = HourlyBookingConfig(
            property_id=prop.id,
            hourly_price=Decimal("50.00"),
            min_hours=1,
            max_hours=8,
        )
        db_session.add(config)
        await db_session.flush()

        data = BookingCreate(
            property_id=prop.id,
            check_in=datetime.now(UTC) + timedelta(days=1),
            check_out=datetime.now(UTC) + timedelta(days=1, hours=3),
            booking_type=BookingType.HOURLY,
            hours=3,
        )
        booking = await booking_service.create_booking(db_session, data, guest)
        assert booking.booking_type == BookingType.HOURLY
        assert booking.total_price == Decimal("150.00")

    async def test_create_hourly_booking_invalid_hours(
        self, db_session: AsyncSession, prop: Property, guest: User
    ):
        prop.hourly_enabled = True
        config = HourlyBookingConfig(
            property_id=prop.id,
            hourly_price=Decimal("50.00"),
            min_hours=2,
            max_hours=6,
        )
        db_session.add(config)
        await db_session.flush()

        data = BookingCreate(
            property_id=prop.id,
            check_in=datetime.now(UTC) + timedelta(days=1),
            check_out=datetime.now(UTC) + timedelta(days=1, hours=1),
            booking_type=BookingType.HOURLY,
            hours=1,  # below min_hours
        )
        with pytest.raises(BadRequestError):
            await booking_service.create_booking(db_session, data, guest)

    # --- update_booking_status ---

    async def test_update_status_confirm(
        self, db_session: AsyncSession, prop: Property, guest: User, host: User
    ):
        booking = await booking_service.create_booking(
            db_session,
            BookingCreate(
                property_id=prop.id,
                check_in=datetime.now(UTC) + timedelta(days=5),
                check_out=datetime.now(UTC) + timedelta(days=8),
            ),
            guest,
        )
        updated = await booking_service.update_booking_status(
            db_session, booking.id, BookingStatus.CONFIRMED, host
        )
        assert updated.status == BookingStatus.CONFIRMED

    async def test_update_status_invalid_transition(
        self, db_session: AsyncSession, prop: Property, guest: User, host: User
    ):
        booking = await booking_service.create_booking(
            db_session,
            BookingCreate(
                property_id=prop.id,
                check_in=datetime.now(UTC) + timedelta(days=5),
                check_out=datetime.now(UTC) + timedelta(days=8),
            ),
            guest,
        )
        with pytest.raises(BadRequestError):
            await booking_service.update_booking_status(
                db_session, booking.id, BookingStatus.COMPLETED, host
            )

    async def test_update_status_not_found(
        self, db_session: AsyncSession, host: User
    ):
        with pytest.raises(NotFoundError):
            await booking_service.update_booking_status(
                db_session, uuid.uuid4(), BookingStatus.CONFIRMED, host
            )

    async def test_update_status_guest_cannot_confirm(
        self, db_session: AsyncSession, prop: Property, guest: User
    ):
        booking = await booking_service.create_booking(
            db_session,
            BookingCreate(
                property_id=prop.id,
                check_in=datetime.now(UTC) + timedelta(days=5),
                check_out=datetime.now(UTC) + timedelta(days=8),
            ),
            guest,
        )
        with pytest.raises(ForbiddenError):
            await booking_service.update_booking_status(
                db_session, booking.id, BookingStatus.CONFIRMED, guest
            )

    async def test_update_status_guest_cancels(
        self, db_session: AsyncSession, prop: Property, guest: User
    ):
        booking = await booking_service.create_booking(
            db_session,
            BookingCreate(
                property_id=prop.id,
                check_in=datetime.now(UTC) + timedelta(days=5),
                check_out=datetime.now(UTC) + timedelta(days=8),
            ),
            guest,
        )
        updated = await booking_service.update_booking_status(
            db_session, booking.id, BookingStatus.CANCELLED, guest
        )
        assert updated.status == BookingStatus.CANCELLED

    async def test_update_status_complete_by_host(
        self, db_session: AsyncSession, prop: Property, guest: User, host: User
    ):
        booking = await booking_service.create_booking(
            db_session,
            BookingCreate(
                property_id=prop.id,
                check_in=datetime.now(UTC) + timedelta(days=5),
                check_out=datetime.now(UTC) + timedelta(days=8),
            ),
            guest,
        )
        await booking_service.update_booking_status(
            db_session, booking.id, BookingStatus.CONFIRMED, host
        )
        updated = await booking_service.update_booking_status(
            db_session, booking.id, BookingStatus.COMPLETED, host
        )
        assert updated.status == BookingStatus.COMPLETED

    # --- get_booking ---

    async def test_get_booking_success(
        self, db_session: AsyncSession, prop: Property, guest: User
    ):
        booking = await booking_service.create_booking(
            db_session,
            BookingCreate(
                property_id=prop.id,
                check_in=datetime.now(UTC) + timedelta(days=5),
                check_out=datetime.now(UTC) + timedelta(days=8),
            ),
            guest,
        )
        fetched = await booking_service.get_booking(db_session, booking.id, guest)
        assert fetched.id == booking.id

    async def test_get_booking_not_found(
        self, db_session: AsyncSession, guest: User
    ):
        with pytest.raises(NotFoundError):
            await booking_service.get_booking(db_session, uuid.uuid4(), guest)

    async def test_get_booking_access_denied(
        self, db_session: AsyncSession, prop: Property, guest: User
    ):
        booking = await booking_service.create_booking(
            db_session,
            BookingCreate(
                property_id=prop.id,
                check_in=datetime.now(UTC) + timedelta(days=5),
                check_out=datetime.now(UTC) + timedelta(days=8),
            ),
            guest,
        )
        stranger = _make_user()
        db_session.add(stranger)
        await db_session.flush()
        with pytest.raises(ForbiddenError):
            await booking_service.get_booking(db_session, booking.id, stranger)

    # --- list_bookings ---

    async def test_list_bookings_as_guest(
        self, db_session: AsyncSession, prop: Property, guest: User
    ):
        await booking_service.create_booking(
            db_session,
            BookingCreate(
                property_id=prop.id,
                check_in=datetime.now(UTC) + timedelta(days=5),
                check_out=datetime.now(UTC) + timedelta(days=8),
            ),
            guest,
        )
        items, total = await booking_service.list_bookings(db_session, guest)
        assert total == 1
        assert len(items) == 1

    async def test_list_bookings_as_host(
        self, db_session: AsyncSession, prop: Property, guest: User, host: User
    ):
        await booking_service.create_booking(
            db_session,
            BookingCreate(
                property_id=prop.id,
                check_in=datetime.now(UTC) + timedelta(days=5),
                check_out=datetime.now(UTC) + timedelta(days=8),
            ),
            guest,
        )
        items, total = await booking_service.list_bookings(db_session, host)
        assert total >= 1

    async def test_list_bookings_as_admin(self, db_session: AsyncSession):
        admin = _make_user(role="admin")
        db_session.add(admin)
        await db_session.flush()
        items, total = await booking_service.list_bookings(db_session, admin)
        assert isinstance(total, int)


# ===========================================================================
# membership_service
# ===========================================================================

class TestMembershipService:

    @pytest_asyncio.fixture
    async def host_with_profile(self, db_session: AsyncSession) -> tuple[User, HostProfile]:
        user = _make_user(role="host")
        db_session.add(user)
        await db_session.flush()
        profile = HostProfile(user_id=user.id)
        db_session.add(profile)
        await db_session.flush()
        return user, profile

    async def test_subscribe_basic(
        self, db_session: AsyncSession, host_with_profile: tuple[User, HostProfile]
    ):
        host, _ = host_with_profile
        req = MembershipSubscribeRequest(plan_type="basic", payment_token="tok_test")
        mem = await membership_service.subscribe(db_session, req, host)
        assert mem.plan_type == "basic"
        assert mem.status == MembershipStatus.ACTIVE

    async def test_subscribe_pro(
        self, db_session: AsyncSession, host_with_profile: tuple[User, HostProfile]
    ):
        host, _ = host_with_profile
        req = MembershipSubscribeRequest(plan_type="pro", payment_token="tok_test")
        mem = await membership_service.subscribe(db_session, req, host)
        assert mem.plan_type == "pro"
        assert mem.max_listings == 25

    async def test_subscribe_upgrade_plan(
        self, db_session: AsyncSession, host_with_profile: tuple[User, HostProfile]
    ):
        host, _ = host_with_profile
        await membership_service.subscribe(
            db_session,
            MembershipSubscribeRequest(plan_type="basic", payment_token="tok1"),
            host,
        )
        # upgrade
        updated = await membership_service.subscribe(
            db_session,
            MembershipSubscribeRequest(plan_type="pro", payment_token="tok2"),
            host,
        )
        assert updated.plan_type == "pro"

    async def test_subscribe_no_host_profile(self, db_session: AsyncSession):
        user = _make_user(role="host")
        db_session.add(user)
        await db_session.flush()
        req = MembershipSubscribeRequest(plan_type="basic", payment_token="tok")
        with pytest.raises(NotFoundError):
            await membership_service.subscribe(db_session, req, user)

    async def test_get_current_membership(
        self, db_session: AsyncSession, host_with_profile: tuple[User, HostProfile]
    ):
        host, _ = host_with_profile
        await membership_service.subscribe(
            db_session,
            MembershipSubscribeRequest(plan_type="basic", payment_token="tok"),
            host,
        )
        mem = await membership_service.get_current_membership(db_session, host)
        assert mem.status == MembershipStatus.ACTIVE

    async def test_get_current_membership_not_found(
        self, db_session: AsyncSession, host_with_profile: tuple[User, HostProfile]
    ):
        host, _ = host_with_profile
        with pytest.raises(NotFoundError):
            await membership_service.get_current_membership(db_session, host)

    async def test_get_current_membership_no_profile(self, db_session: AsyncSession):
        user = _make_user(role="host")
        db_session.add(user)
        await db_session.flush()
        with pytest.raises(NotFoundError):
            await membership_service.get_current_membership(db_session, user)

    async def test_cancel_membership(
        self, db_session: AsyncSession, host_with_profile: tuple[User, HostProfile]
    ):
        host, _ = host_with_profile
        await membership_service.subscribe(
            db_session,
            MembershipSubscribeRequest(plan_type="basic", payment_token="tok"),
            host,
        )
        cancelled = await membership_service.cancel_membership(db_session, host)
        assert cancelled.status == MembershipStatus.CANCELLED

    async def test_cancel_already_cancelled(
        self, db_session: AsyncSession, host_with_profile: tuple[User, HostProfile]
    ):
        host, _ = host_with_profile
        await membership_service.subscribe(
            db_session,
            MembershipSubscribeRequest(plan_type="basic", payment_token="tok"),
            host,
        )
        await membership_service.cancel_membership(db_session, host)
        with pytest.raises(BadRequestError):
            await membership_service.cancel_membership(db_session, host)

    async def test_get_available_plans(self):
        plans = membership_service.get_available_plans()
        assert len(plans) >= 3
        plan_types = {p.plan_type for p in plans}
        assert "basic" in plan_types
        assert "pro" in plan_types
        assert "premium" in plan_types


# ===========================================================================
# property_service
# ===========================================================================

class TestPropertyService:

    @pytest_asyncio.fixture
    async def host_ready(self, db_session: AsyncSession) -> User:
        """Host user with profile + active membership."""
        user, _profile, _mem = await _persist_host_with_membership(db_session)
        return user

    async def test_create_property_success(
        self, db_session: AsyncSession, host_ready: User
    ):
        data = PropertyCreate(
            title="My Flat",
            description="Nice flat in the city centre with modern amenities",
            city="London",
            address="10 Downing St",
            price_per_night=Decimal("200.00"),
            max_guests=4,
            amenities=["wifi"],
        )
        prop = await property_service.create_property(db_session, data, host_ready)
        assert prop.title == "My Flat"
        assert prop.host_id == host_ready.id

    async def test_create_property_no_membership(self, db_session: AsyncSession):
        user = _make_user(role="host")
        db_session.add(user)
        await db_session.flush()
        profile = HostProfile(user_id=user.id)
        db_session.add(profile)
        await db_session.flush()
        data = PropertyCreate(
            title="Flat",
            description="Flat description for no membership test",
            city="Paris",
            address="Eiffel Tower",
            price_per_night=Decimal("150.00"),
            max_guests=2,
            amenities=[],
        )
        with pytest.raises(MembershipRequiredError):
            await property_service.create_property(db_session, data, user)

    async def test_create_property_no_profile(self, db_session: AsyncSession):
        user = _make_user(role="host")
        db_session.add(user)
        await db_session.flush()
        data = PropertyCreate(
            title="Flat",
            description="Flat description for missing profile test case here",
            city="Berlin",
            address="Brandenburg Gate",
            price_per_night=Decimal("100.00"),
            max_guests=2,
            amenities=[],
        )
        with pytest.raises(ForbiddenError):
            await property_service.create_property(db_session, data, user)

    async def test_create_property_listing_cap(
        self, db_session: AsyncSession, host_ready: User
    ):
        """Basic plan allows 5 listings — 6th should raise ForbiddenError."""
        for i in range(5):
            await property_service.create_property(
                db_session,
                PropertyCreate(
                    title=f"Prop {i}",
                    description="Description long enough to pass validation here",
                    city="Madrid",
                    address=f"Calle {i}",
                    price_per_night=Decimal("80.00"),
                    max_guests=2,
                    amenities=[],
                ),
                host_ready,
            )
        with pytest.raises(ForbiddenError):
            await property_service.create_property(
                db_session,
                PropertyCreate(
                    title="Prop 6",
                    description="Description long enough to pass validation too",
                    city="Madrid",
                    address="Calle 6",
                    price_per_night=Decimal("80.00"),
                    max_guests=2,
                    amenities=[],
                ),
                host_ready,
            )

    async def test_get_property_success(
        self, db_session: AsyncSession, host_ready: User
    ):
        prop = await _create_property(db_session, host_ready)
        fetched = await property_service.get_property(db_session, prop.id)
        assert fetched.id == prop.id

    async def test_get_property_not_found(self, db_session: AsyncSession):
        with pytest.raises(NotFoundError):
            await property_service.get_property(db_session, uuid.uuid4())

    async def test_update_property(
        self, db_session: AsyncSession, host_ready: User
    ):
        prop = await _create_property(db_session, host_ready)
        updated = await property_service.update_property(
            db_session, prop.id, PropertyUpdate(title="New Title"), host_ready
        )
        assert updated.title == "New Title"

    async def test_update_property_wrong_host(
        self, db_session: AsyncSession, host_ready: User
    ):
        prop = await _create_property(db_session, host_ready)
        intruder = _make_user(role="host")
        db_session.add(intruder)
        await db_session.flush()
        with pytest.raises(ForbiddenError):
            await property_service.update_property(
                db_session, prop.id, PropertyUpdate(title="New Title"), intruder
            )

    async def test_update_property_not_found(
        self, db_session: AsyncSession, host_ready: User
    ):
        with pytest.raises(NotFoundError):
            await property_service.update_property(
                db_session, uuid.uuid4(), PropertyUpdate(title="No Such Property"), host_ready
            )

    async def test_delete_property(
        self, db_session: AsyncSession, host_ready: User
    ):
        prop = await _create_property(db_session, host_ready)
        await property_service.delete_property(db_session, prop.id, host_ready)
        assert not prop.is_active

    async def test_search_properties_no_filter(
        self, db_session: AsyncSession, host_ready: User
    ):
        await _create_property(db_session, host_ready)
        items, total = await property_service.search_properties(
            db_session, PropertySearchParams()
        )
        assert total == 1

    async def test_search_by_city(
        self, db_session: AsyncSession, host_ready: User
    ):
        await _create_property(db_session, host_ready)
        items, total = await property_service.search_properties(
            db_session, PropertySearchParams(city="Testville")
        )
        assert total == 1
        items2, total2 = await property_service.search_properties(
            db_session, PropertySearchParams(city="Nowhere")
        )
        assert total2 == 0

    async def test_search_by_price_range(
        self, db_session: AsyncSession, host_ready: User
    ):
        await _create_property(db_session, host_ready)
        items, total = await property_service.search_properties(
            db_session, PropertySearchParams(min_price=50, max_price=200)
        )
        assert total == 1
        items2, total2 = await property_service.search_properties(
            db_session, PropertySearchParams(min_price=200, max_price=500)
        )
        assert total2 == 0

    async def test_search_by_max_guests(
        self, db_session: AsyncSession, host_ready: User
    ):
        await _create_property(db_session, host_ready)
        items, total = await property_service.search_properties(
            db_session, PropertySearchParams(max_guests=2)
        )
        assert total == 1

    async def test_search_by_host_id(
        self, db_session: AsyncSession, host_ready: User
    ):
        await _create_property(db_session, host_ready)
        items, total = await property_service.search_properties(
            db_session, PropertySearchParams(host_id=host_ready.id)
        )
        assert total == 1

    async def test_search_hourly_filter(
        self, db_session: AsyncSession, host_ready: User
    ):
        prop = await _create_property(db_session, host_ready)
        prop.hourly_enabled = True
        await db_session.flush()
        items, total = await property_service.search_properties(
            db_session, PropertySearchParams(hourly_available=True)
        )
        assert total == 1

    async def test_configure_hourly_booking(
        self, db_session: AsyncSession, host_ready: User
    ):
        prop = await _create_property(db_session, host_ready)
        updated = await property_service.configure_hourly_booking(
            db_session,
            prop.id,
            HourlyBookingConfigUpdate(
                hourly_price=Decimal("40.00"),
                min_hours=1,
                max_hours=8,
            ),
            host_ready,
        )
        assert updated.hourly_enabled is True

    async def test_configure_hourly_booking_update(
        self, db_session: AsyncSession, host_ready: User
    ):
        prop = await _create_property(db_session, host_ready)
        # Create initial config
        await property_service.configure_hourly_booking(
            db_session,
            prop.id,
            HourlyBookingConfigUpdate(
                hourly_price=Decimal("40.00"),
                min_hours=1,
                max_hours=8,
            ),
            host_ready,
        )
        # Update
        updated = await property_service.configure_hourly_booking(
            db_session,
            prop.id,
            HourlyBookingConfigUpdate(
                hourly_price=Decimal("55.00"),
                min_hours=2,
                max_hours=6,
            ),
            host_ready,
        )
        assert updated.hourly_enabled is True

    async def test_add_property_image(
        self, db_session: AsyncSession, host_ready: User
    ):
        prop = await _create_property(db_session, host_ready)
        img = await property_service.add_property_image(
            db_session, prop.id, "https://example.com/img.jpg", True, host_ready
        )
        assert img.is_primary is True

    async def test_add_property_image_replaces_primary(
        self, db_session: AsyncSession, host_ready: User
    ):
        prop = await _create_property(db_session, host_ready)
        img1 = await property_service.add_property_image(
            db_session, prop.id, "https://example.com/a.jpg", True, host_ready
        )
        img2 = await property_service.add_property_image(
            db_session, prop.id, "https://example.com/b.jpg", True, host_ready
        )
        # original img1 should no longer be primary
        assert not img1.is_primary
        assert img2.is_primary


# ===========================================================================
# review_service
# ===========================================================================

class TestReviewService:

    @pytest_asyncio.fixture
    async def host(self, db_session: AsyncSession) -> User:
        user, _, _ = await _persist_host_with_membership(db_session)
        return user

    @pytest_asyncio.fixture
    async def guest(self, db_session: AsyncSession) -> User:
        user = _make_user(role="user")
        db_session.add(user)
        await db_session.flush()
        return user

    @pytest_asyncio.fixture
    async def prop(self, db_session: AsyncSession, host: User) -> Property:
        return await _create_property(db_session, host)

    @pytest_asyncio.fixture
    async def completed_booking(
        self, db_session: AsyncSession, prop: Property, guest: User
    ) -> Booking:
        return await _create_completed_booking(db_session, prop, guest)

    async def test_create_review_success(
        self, db_session: AsyncSession, completed_booking: Booking, guest: User
    ):
        data = ReviewCreate(
            booking_id=completed_booking.id,
            rating=5,
            comment="Great place!",
        )
        review = await review_service.create_review(db_session, data, guest)
        assert review.rating == 5

    async def test_create_review_wrong_guest(
        self,
        db_session: AsyncSession,
        completed_booking: Booking,
    ):
        stranger = _make_user()
        db_session.add(stranger)
        await db_session.flush()
        data = ReviewCreate(booking_id=completed_booking.id, rating=4)
        with pytest.raises(ForbiddenError):
            await review_service.create_review(db_session, data, stranger)

    async def test_create_review_not_completed(
        self, db_session: AsyncSession, prop: Property, guest: User
    ):
        # pending booking
        booking = Booking(
            property_id=prop.id,
            guest_id=guest.id,
            host_id=prop.host_id,
            check_in=datetime.now(UTC) + timedelta(days=1),
            check_out=datetime.now(UTC) + timedelta(days=3),
            total_price=Decimal("200.00"),
            status=BookingStatus.PENDING,
        )
        db_session.add(booking)
        await db_session.flush()
        data = ReviewCreate(booking_id=booking.id, rating=3)
        with pytest.raises(BadRequestError):
            await review_service.create_review(db_session, data, guest)

    async def test_create_review_duplicate(
        self, db_session: AsyncSession, completed_booking: Booking, guest: User
    ):
        data = ReviewCreate(booking_id=completed_booking.id, rating=4)
        await review_service.create_review(db_session, data, guest)
        with pytest.raises(BadRequestError):
            await review_service.create_review(db_session, data, guest)

    async def test_create_review_invalid_booking(
        self, db_session: AsyncSession, guest: User
    ):
        data = ReviewCreate(booking_id=uuid.uuid4(), rating=5)
        with pytest.raises(NotFoundError):
            await review_service.create_review(db_session, data, guest)

    async def test_list_property_reviews(
        self,
        db_session: AsyncSession,
        completed_booking: Booking,
        guest: User,
        prop: Property,
    ):
        data = ReviewCreate(booking_id=completed_booking.id, rating=5)
        await review_service.create_review(db_session, data, guest)
        items, total = await review_service.list_property_reviews(db_session, prop.id)
        assert total == 1

    async def test_list_host_reviews(
        self,
        db_session: AsyncSession,
        completed_booking: Booking,
        guest: User,
        host: User,
        prop: Property,
    ):
        data = ReviewCreate(booking_id=completed_booking.id, rating=5)
        await review_service.create_review(db_session, data, guest)
        items, total = await review_service.list_host_reviews(db_session, host.id)
        assert total == 1

    async def test_list_empty_reviews(self, db_session: AsyncSession):
        items, total = await review_service.list_property_reviews(
            db_session, uuid.uuid4()
        )
        assert total == 0

    async def test_list_host_reviews_empty(self, db_session: AsyncSession):
        items, total = await review_service.list_host_reviews(
            db_session, uuid.uuid4()
        )
        assert total == 0


# ===========================================================================
# message_service
# ===========================================================================

class TestMessageService:

    @pytest_asyncio.fixture
    async def host(self, db_session: AsyncSession) -> User:
        user, _, _ = await _persist_host_with_membership(db_session)
        return user

    @pytest_asyncio.fixture
    async def guest(self, db_session: AsyncSession) -> User:
        user = _make_user(role="user")
        db_session.add(user)
        await db_session.flush()
        return user

    @pytest_asyncio.fixture
    async def prop(self, db_session: AsyncSession, host: User) -> Property:
        return await _create_property(db_session, host)

    @pytest_asyncio.fixture
    async def conversation(
        self, db_session: AsyncSession, prop: Property, guest: User
    ) -> dict:
        return await message_service.start_conversation(
            db_session,
            ConversationCreate(property_id=prop.id, message="Hello!"),
            guest,
        )

    async def test_start_conversation(
        self, db_session: AsyncSession, prop: Property, guest: User
    ):
        result = await message_service.start_conversation(
            db_session,
            ConversationCreate(property_id=prop.id, message="Hello!"),
            guest,
        )
        assert result["guest_id"] == guest.id
        assert result["last_message"]["content"] == "Hello!"

    async def test_start_conversation_invalid_property(
        self, db_session: AsyncSession, guest: User
    ):
        with pytest.raises(NotFoundError):
            await message_service.start_conversation(
                db_session,
                ConversationCreate(property_id=uuid.uuid4(), message="Hi"),
                guest,
            )

    async def test_start_conversation_host_messages_self(
        self, db_session: AsyncSession, prop: Property, host: User
    ):
        with pytest.raises(BadRequestError):
            await message_service.start_conversation(
                db_session,
                ConversationCreate(property_id=prop.id, message="Hi"),
                host,
            )

    async def test_start_conversation_duplicate(
        self,
        db_session: AsyncSession,
        conversation: dict,
        prop: Property,
        guest: User,
    ):
        with pytest.raises(BadRequestError):
            await message_service.start_conversation(
                db_session,
                ConversationCreate(property_id=prop.id, message="Another"),
                guest,
            )

    async def test_send_message(
        self,
        db_session: AsyncSession,
        conversation: dict,
        host: User,
    ):
        msg = await message_service.send_message(
            db_session,
            conversation["id"],
            MessageCreate(content="Reply from host"),
            host,
        )
        assert msg.content == "Reply from host"

    async def test_send_message_non_participant(
        self, db_session: AsyncSession, conversation: dict
    ):
        stranger = _make_user()
        db_session.add(stranger)
        await db_session.flush()
        with pytest.raises(ForbiddenError):
            await message_service.send_message(
                db_session,
                conversation["id"],
                MessageCreate(content="Unauthorized"),
                stranger,
            )

    async def test_list_conversations(
        self,
        db_session: AsyncSession,
        conversation: dict,
        guest: User,
        host: User,
    ):
        # second message so list_conversations has data to enrich
        await message_service.send_message(
            db_session,
            conversation["id"],
            MessageCreate(content="Reply"),
            host,
        )
        items, total = await message_service.list_conversations(db_session, guest)
        assert total == 1
        assert items[0]["unread_count"] == 1  # host's reply is unread by guest

    async def test_list_conversations_empty(self, db_session: AsyncSession):
        stranger = _make_user()
        db_session.add(stranger)
        await db_session.flush()
        items, total = await message_service.list_conversations(db_session, stranger)
        assert total == 0

    async def test_get_conversation_detail(
        self,
        db_session: AsyncSession,
        conversation: dict,
        guest: User,
    ):
        detail = await message_service.get_conversation_detail(
            db_session, conversation["id"], guest
        )
        assert detail["guest_id"] == guest.id
        assert "property_title" in detail

    async def test_get_conversation_detail_non_participant(
        self, db_session: AsyncSession, conversation: dict
    ):
        stranger = _make_user()
        db_session.add(stranger)
        await db_session.flush()
        with pytest.raises(ForbiddenError):
            await message_service.get_conversation_detail(
                db_session, conversation["id"], stranger
            )

    async def test_get_messages(
        self,
        db_session: AsyncSession,
        conversation: dict,
        guest: User,
    ):
        msgs, total = await message_service.get_messages(
            db_session, conversation["id"], guest
        )
        assert total == 1  # the initial "Hello!" message

    async def test_get_messages_non_participant(
        self, db_session: AsyncSession, conversation: dict
    ):
        stranger = _make_user()
        db_session.add(stranger)
        await db_session.flush()
        with pytest.raises(ForbiddenError):
            await message_service.get_messages(
                db_session, conversation["id"], stranger
            )

    async def test_mark_message_read(
        self,
        db_session: AsyncSession,
        conversation: dict,
        host: User,
    ):
        # The initial "Hello!" was sent by guest, so host can mark it read
        msgs, _ = await message_service.get_messages(
            db_session, conversation["id"], host
        )
        assert len(msgs) == 1
        updated = await message_service.mark_message_read(
            db_session, msgs[0].id, host
        )
        assert updated.is_read is True

    async def test_mark_own_message_read_fails(
        self,
        db_session: AsyncSession,
        conversation: dict,
        guest: User,
    ):
        msgs, _ = await message_service.get_messages(
            db_session, conversation["id"], guest
        )
        with pytest.raises(BadRequestError):
            await message_service.mark_message_read(
                db_session, msgs[0].id, guest
            )

    async def test_mark_message_read_not_found(
        self, db_session: AsyncSession, guest: User
    ):
        with pytest.raises(NotFoundError):
            await message_service.mark_message_read(
                db_session, uuid.uuid4(), guest
            )

    async def test_get_conversation_not_found(
        self, db_session: AsyncSession, guest: User
    ):
        with pytest.raises(NotFoundError):
            await message_service.get_messages(
                db_session, uuid.uuid4(), guest
            )
