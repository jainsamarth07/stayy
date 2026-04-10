# StayNest — Deep Code-Level Reference
 
 > Generated purely from source code analysis. Every name, type, and path is exact.
 
 ---
 
 ## Table of Contents
 
 1. [Architecture Overview](#1-architecture-overview)
 2. [Database Layer (Models + Migrations)](#2-database-layer)
 3. [Pydantic Schemas](#3-pydantic-schemas)
 4. [Services](#4-services)
 5. [API Routes](#5-api-routes)
 6. [Auth & Security](#6-auth--security)
 7. [Background Tasks](#7-background-tasks)
 8. [Frontend API Client](#8-frontend-api-client)
 9. [TypeScript Types](#9-typescript-types)
 10. [Zustand Stores](#10-zustand-stores)
 11. [Custom Hooks](#11-custom-hooks)
 12. [Frontend Components](#12-frontend-components)
 13. [Frontend Pages](#13-frontend-pages)
 14. [Middleware](#14-middleware)
 15. [Docker & Infrastructure](#15-docker--infrastructure)
 16. [Test Infrastructure](#16-test-infrastructure)
 17. [Full Cross-Reference Table](#17-full-cross-reference-table)
 18. [Observations](#18-observations)
 
 ---
 
 ## 1. Architecture Overview
 
 ```
 ┌─────────────────────┐ ┌────────────────┐ ┌──────────┐
 │ Next.js Frontend │────▶│ FastAPI Backend│────▶│PostgreSQL│
 │ (port 3000) │ │ (port 8000) │ │(port 5432│
 │ BetterAuth client │ │ │ └──────────┘
 └─────────────────────┘ │ SQLAlchemy ORM │ ┌──────────┐
  │ │ Alembic migr. │────▶│ Redis │
  │ BetterAuth │ Celery tasks │ │(port 6379│
  │ server-side └────────────────┘ └──────────┘
  │ (same Postgres) ┌──────────┐
  └──────────────────────────────────────────▶│ MinIO │
  │(port 9000│
  └──────────┘
 ```
 
 **Backend**: Python 3.11+, FastAPI, SQLAlchemy 2.0 (async), Alembic, Celery, Argon2 hashing, JWT (python-jose), S3 via boto3.
 
 **Frontend**: Next.js 16, React 18, TypeScript, Tailwind CSS 3.4, Zustand 4.5, Axios, BetterAuth, Framer Motion, Lucide icons, Vitest.
 
 **Auth Model**: BetterAuth manages `user`/`session`/`account`/`verification` tables. The FastAPI backend reads the BetterAuth `session` table to validate Bearer tokens (session tokens). A "bridge" in `dependencies.py` lazily creates/syncs rows in the legacy `users` table so all FK relationships work.
 
 ---
 
 ## 2. Database Layer
 
 ### 2.1 Entity-Relationship Diagram
 
 ```mermaid
 erDiagram
  user ||--o{ session : "has"
  user ||--o{ account : "has"
 
  users ||--o| host_profiles : "has"
  users ||--o{ properties : "hosts"
  users ||--o{ bookings : "guest"
  users ||--o{ reviews : "writes"
  users ||--o{ conversations : "guest/host"
  users ||--o{ messages : "sends"
 
  host_profiles ||--o| memberships : "subscribes"
 
  properties ||--o{ property_images : "has"
  properties ||--o| hourly_booking_configs : "has"
  properties ||--o{ bookings : "reserved"
  properties ||--o{ reviews : "reviewed"
  properties ||--o{ conversations : "about"
 
  bookings ||--o| reviews : "reviewed"
 
  conversations ||--o{ messages : "contains"
 ```
 
 ### 2.2 BetterAuth Tables
 
 #### Table: `user`
 | Column | Python Type | SQL Type | PK | Nullable | Unique | Index | Default |
 |--------|-----------|----------|-----|----------|--------|-------|---------|
 | `id` | `str` | `String` | ✅ | ❌ | — | — | — |
 | `name` | `str` | `String` | — | ❌ | — | — | — |
 | `email` | `str` | `String` | — | ❌ | ✅ | ✅ | — |
 | `email_verified` | `bool` | `Boolean` | — | ❌ | — | — | `false` |
 | `image` | `str\|None` | `Text` | — | ✅ | — | — | — |
 | `role` | `str` | `String` | — | ❌ | — | — | `server_default="user"` |
 | `phone` | `str\|None` | `String` | — | ✅ | — | — | — |
 | `created_at` | `datetime` | `DateTime(tz)` | — | ❌ | — | — | `now()` |
 | `updated_at` | `datetime` | `DateTime(tz)` | — | ❌ | — | — | `now()` |
 
 Model class: `BetterAuthUser` in `app/models/betterauth.py`
 
 #### Table: `session`
 | Column | Python Type | SQL Type | PK | Nullable | Unique | Index | FK |
 |--------|-----------|----------|-----|----------|--------|-------|----|
 | `id` | `str` | `String` | ✅ | ❌ | — | — | — |
 | `user_id` | `str` | `String` | — | ❌ | — | ✅ | `user.id CASCADE` |
 | `token` | `str` | `String` | — | ❌ | ✅ | ✅ | — |
 | `expires_at` | `datetime` | `DateTime(tz)` | — | ❌ | — | — | — |
 | `ip_address` | `str\|None` | `String` | — | ✅ | — | — | — |
 | `user_agent` | `str\|None` | `String` | — | ✅ | — | — | — |
 | `created_at` | `datetime` | `DateTime(tz)` | — | ❌ | — | — | `now()` |
 | `updated_at` | `datetime` | `DateTime(tz)` | — | ❌ | — | — | `now()` |
 
 Model class: `BetterAuthSession` in `app/models/betterauth.py`
 
 ### 2.3 Application Tables
 
 #### Table: `users`
 | Column | Python Type | SQL Type | PK | Nullable | Unique | Index | Default |
 |--------|-----------|----------|-----|----------|--------|-------|---------|
 | `id` | `uuid.UUID` | `UUID` | ✅ | ❌ | — | — | `uuid4()` |
 | `email` | `str` | `String(255)` | — | ❌ | ✅ | ✅ | — |
 | `hashed_password` | `str` | `String(255)` | — | ❌ | — | — | — |
 | `full_name` | `str` | `String(255)` | — | ❌ | — | — | — |
 | `phone` | `str\|None` | `String(20)` | — | ✅ | — | — | — |
 | `role` | `str` | `String(20)` | — | ❌ | — | — | `"user"` |
 | `is_active` | `bool` | `Boolean` | — | ❌ | — | — | `True` |
 | `created_at` | `datetime` | `DateTime(tz)` | — | ❌ | — | — | `now(utc)` |
 | `updated_at` | `datetime` | `DateTime(tz)` | — | ❌ | — | — | `now(utc)` / `onupdate` |
 
 **Relationships**: `host_profile` (1:1 HostProfile), `properties` (1:N Property), `bookings_as_guest` (1:N Booking via `guest_id`), `reviews` (1:N Review)
 
 Model class: `User` in `app/models/user.py`
 
 #### Table: `host_profiles`
 | Column | Python Type | SQL Type | PK | Nullable | Unique | Index | FK |
 |--------|-----------|----------|-----|----------|--------|-------|----|
 | `id` | `uuid.UUID` | `UUID` | ✅ | ❌ | — | — | — |
 | `user_id` | `uuid.UUID` | `UUID` | — | ❌ | ✅ | — | `users.id CASCADE` |
 | `business_name` | `str\|None` | `String(255)` | — | ✅ | — | — | — |
 | `bio` | `str\|None` | `Text` | — | ✅ | — | — | — |
 | `phone_visible` | `bool` | `Boolean` | — | ❌ | — | — | `False` |
 | `is_verified` | `bool` | `Boolean` | — | ❌ | — | — | `False` |
 | `avg_rating` | `float` | `Float` | — | ❌ | — | — | `0.0` |
 | `total_reviews` | `int` | `Integer` | — | ❌ | — | — | `0` |
 | `created_at` | `datetime` | `DateTime(tz)` | — | ❌ | — | — | `now(utc)` |
 
 **Relationships**: `user` (N:1 User), `membership` (1:1 Membership)
 
 Model class: `HostProfile` in `app/models/user.py`
 
 #### Table: `properties`
 | Column | Python Type | SQL Type | PK | Nullable | Unique | Index | FK |
 |--------|-----------|----------|-----|----------|--------|-------|----|
 | `id` | `uuid.UUID` | `UUID` | ✅ | ❌ | — | — | — |
 | `host_id` | `uuid.UUID` | `UUID` | — | ❌ | — | ✅ | `users.id CASCADE` |
 | `title` | `str` | `String(255)` | — | ❌ | — | — | — |
 | `description` | `str` | `Text` | — | ❌ | — | — | — |
 | `city` | `str` | `String(100)` | — | ❌ | — | ✅ | — |
 | `address` | `str` | `String(500)` | — | ❌ | — | — | — |
 | `latitude` | `float\|None` | `Float` | — | ✅ | — | — | — |
 | `longitude` | `float\|None` | `Float` | — | ✅ | — | — | — |
 | `price_per_night` | `float` | `Float` | — | ❌ | — | — | — |
 | `max_guests` | `int` | `Integer` | — | ❌ | — | — | `1` |
 | `amenities` | `list\|None` | `JSON` | — | ✅ | — | — | `list` |
 | `is_active` | `bool` | `Boolean` | — | ❌ | — | — | `True` |
 | `hourly_enabled` | `bool` | `Boolean` | — | ❌ | — | — | `False` |
 | `created_at` | `datetime` | `DateTime(tz)` | — | ❌ | — | — | `now(utc)` |
 | `updated_at` | `datetime` | `DateTime(tz)` | — | ❌ | — | — | `now(utc)` / `onupdate` |
 
 **Relationships**: `host` (N:1 User), `images` (1:N PropertyImage, cascade `all, delete-orphan`), `hourly_config` (1:1 HourlyBookingConfig, cascade `all, delete-orphan`), `bookings` (1:N Booking), `reviews` (1:N Review)
 
 Model class: `Property` in `app/models/property.py`
 
 #### Table: `property_images`
 | Column | Python Type | SQL Type | PK | Nullable | Index | FK |
 |--------|-----------|----------|-----|----------|-------|----|
 | `id` | `uuid.UUID` | `UUID` | ✅ | ❌ | — | — |
 | `property_id` | `uuid.UUID` | `UUID` | — | ❌ | ✅ | `properties.id CASCADE` |
 | `image_url` | `str` | `String(1000)` | — | ❌ | — | — |
 | `is_primary` | `bool` | `Boolean` | — | ❌ | — | `False` |
 | `sort_order` | `int` | `Integer` | — | ❌ | — | `0` |
 
 #### Table: `hourly_booking_configs`
 | Column | Python Type | SQL Type | PK | Nullable | Unique | FK |
 |--------|-----------|----------|-----|----------|--------|----|
 | `id` | `uuid.UUID` | `UUID` | ✅ | ❌ | — | — |
 | `property_id` | `uuid.UUID` | `UUID` | — | ❌ | ✅ | `properties.id CASCADE` |
 | `hourly_price` | `float` | `Float` | — | ❌ | — | — |
 | `min_hours` | `int` | `Integer` | — | ❌ | — | default `1` |
 | `max_hours` | `int` | `Integer` | — | ❌ | — | default `12` |
 | `available_from` | `time` | `Time` | — | ❌ | — | default `08:00` |
 | `available_to` | `time` | `Time` | — | ❌ | — | default `22:00` |
 
 #### Table: `bookings`
 | Column | Python Type | SQL Type | PK | Nullable | Index | FK |
 |--------|-----------|----------|-----|----------|-------|----|
 | `id` | `uuid.UUID` | `UUID` | ✅ | ❌ | — | — |
 | `property_id` | `uuid.UUID` | `UUID` | — | ❌ | ✅ | `properties.id CASCADE` |
 | `guest_id` | `uuid.UUID` | `UUID` | — | ❌ | ✅ | `users.id CASCADE` |
 | `host_id` | `uuid.UUID` | `UUID` | — | ❌ | ✅ | `users.id CASCADE` |
 | `check_in` | `datetime` | `DateTime(tz)` | — | ❌ | — | — |
 | `check_out` | `datetime` | `DateTime(tz)` | — | ❌ | — | — |
 | `total_price` | `float` | `Float` | — | ❌ | — | — |
 | `booking_type` | `str` | `String(20)` | — | ❌ | — | default `"nightly"` |
 | `hours` | `int\|None` | `Integer` | — | ✅ | — | — |
 | `status` | `str` | `String(20)` | — | ❌ | ✅ | default `"pending"` |
 | `created_at` | `datetime` | `DateTime(tz)` | — | ❌ | — | `now(utc)` |
 | `updated_at` | `datetime` | `DateTime(tz)` | — | ❌ | — | `now(utc)` / `onupdate` |
 
 **Relationships**: `property`, `guest`, `host`, `review` (1:1)
 
 #### Table: `conversations`
 | Column | Python Type | SQL Type | PK | Nullable | Index | FK |
 |--------|-----------|----------|-----|----------|-------|----|
 | `id` | `uuid.UUID` | `UUID` | ✅ | ❌ | — | — |
 | `property_id` | `uuid.UUID` | `UUID` | — | ❌ | ✅ | `properties.id CASCADE` |
 | `guest_id` | `uuid.UUID` | `UUID` | — | ❌ | ✅ | `users.id CASCADE` |
 | `host_id` | `uuid.UUID` | `UUID` | — | ❌ | ✅ | `users.id CASCADE` |
 | `created_at` / `updated_at` | `datetime` | `DateTime(tz)` | — | ❌ | — | — |
 
 **Relationships**: `messages` (1:N, cascade `all, delete-orphan`, ordered by `Message.created_at`), `property`, `guest`, `host`
 
 #### Table: `messages`
 | Column | Python Type | SQL Type | PK | Nullable | Index | FK |
 |--------|-----------|----------|-----|----------|-------|----|
 | `id` | `uuid.UUID` | `UUID` | ✅ | ❌ | — | — |
 | `conversation_id` | `uuid.UUID` | `UUID` | — | ❌ | ✅ | `conversations.id CASCADE` |
 | `sender_id` | `uuid.UUID` | `UUID` | — | ❌ | — | `users.id CASCADE` |
 | `content` | `str` | `Text` | — | ❌ | — | — |
 | `message_type` | `str` | `String(30)` | — | ❌ | — | default `"text"` |
 | `is_read` | `bool` | `Boolean` | — | ❌ | — | `False` |
 | `created_at` | `datetime` | `DateTime(tz)` | — | ❌ | — | — |
 
 **Relationships**: `conversation`, `sender` (User)
 
 #### Table: `reviews`
 | Column | Python Type | SQL Type | PK | Nullable | Unique | Index | FK |
 |--------|-----------|----------|-----|----------|--------|-------|----|
 | `id` | `uuid.UUID` | `UUID` | ✅ | ❌ | — | — | — |
 | `booking_id` | `uuid.UUID` | `UUID` | — | ❌ | ✅ | — | `bookings.id CASCADE` |
 | `property_id` | `uuid.UUID` | `UUID` | — | ❌ | — | ✅ | `properties.id CASCADE` |
 | `reviewer_id` | `uuid.UUID` | `UUID` | — | ❌ | — | ✅ | `users.id CASCADE` |
 | `rating` | `float` | `Float` | — | ❌ | — | — | — |
 | `comment` | `str\|None` | `Text` | — | ✅ | — | — | — |
 | `created_at` | `datetime` | `DateTime(tz)` | — | ❌ | — | — | — |
 
 #### Table: `memberships`
 | Column | Python Type | SQL Type | PK | Nullable | Unique | Index | FK |
 |--------|-----------|----------|-----|----------|--------|-------|----|
 | `id` | `uuid.UUID` | `UUID` | ✅ | ❌ | — | — | — |
 | `host_id` | `uuid.UUID` | `UUID` | — | ❌ | ✅ | — | `host_profiles.id CASCADE` |
 | `plan_type` | `str` | `String(20)` | — | ❌ | — | — | default `"basic"` |
 | `start_date` | `datetime` | `DateTime(tz)` | — | ❌ | — | — | — |
 | `end_date` | `datetime` | `DateTime(tz)` | — | ❌ | — | — | — |
 | `status` | `str` | `String(20)` | — | ❌ | — | ✅ | default `"active"` |
 | `auto_renew` | `bool` | `Boolean` | — | ❌ | — | — | `True` |
 | `payment_ref` | `str\|None` | `String(255)` | — | ✅ | — | — | — |
 | `amount` | `float` | `Float` | — | ❌ | — | — | — |
 | `max_listings` | `int` | `Integer` | — | ❌ | — | — | default `5` |
 | `created_at` / `updated_at` | `datetime` | `DateTime(tz)` | — | ❌ | — | — | — |
 
 ### 2.4 Enums
 
 | Enum Class | Values | Used By |
 |-----------|--------|---------|
 | `BookingStatus` | `pending`, `confirmed`, `cancelled`, `completed`, `rejected` | `bookings.status` |
 | `BookingType` | `nightly`, `hourly` | `bookings.booking_type` |
 | `MembershipPlan` | `basic`, `pro`, `premium` | `memberships.plan_type` |
 | `MembershipStatus` | `active`, `cancelled`, `expired`, `past_due` | `memberships.status` |
 | `MessageType` | `text` | `messages.message_type` |
 | `UserRole` | `user`, `host`, `admin` | `core/permissions.py` (not stored as SQL enum) |
 
 ### 2.5 Plan Configuration (in-code)
 
 ```python
 PLAN_CONFIG = {
  MembershipPlan.BASIC: {"price": 29.00, "max_listings": 5, "label": "Basic"},
  MembershipPlan.PRO: {"price": 79.00, "max_listings": 25, "label": "Pro"},
  MembershipPlan.PREMIUM: {"price": 199.00, "max_listings": 999999, "label": "Premium"},
 }
 ```
 
 ### 2.6 Alembic Migration Chain
 
 | Revision | Parent | Date | Operations |
 |----------|--------|------|-----------|
 | `0001_initial` | `None` | 2026-03-12 | Creates all 11 core tables: `users`, `host_profiles`, `properties`, `property_images`, `hourly_booking_configs`, `offers`, `bookings`, `conversations`, `messages`, `reviews`, `memberships` |
 | `0002_offer_in_messages` | `0001_initial` | 2026-03-17 | Adds `message_type` (String(30), default "text") and `offer_id` (UUID FK→offers) columns to `messages`; creates index `ix_messages_offer_id` |
 | `0003_betterauth_tables` | `0002_offer_in_messages` | 2026-03-29 | Creates BetterAuth tables: `user`, `session`, `account`, `verification`; creates indexes `ix_user_email`, `ix_session_token`, `ix_session_user_id`, `ix_account_user_id` |
 | `0004_remove_offers` | `0003_betterauth_tables` | 2026-04-05 | Drops `offers` table; removes `offer_id` column from `bookings` and `messages` tables; drops `ix_messages_offer_id` index |
 
 ---
 
 ## 3. Pydantic Schemas
 
 ### 3.1 User Schemas (`app/schemas/user.py`)
 
 | Schema | Parent | Purpose | Fields |
 |--------|--------|---------|--------|
 | `UserRegister` | `BaseModel` | Registration request | `email: EmailStr`, `password: str (min=8, max=128)`, `full_name: str (min=1, max=255)`, `phone: str\|None`, `role: str (default="user", pattern="^(user\|host)$")` |
 | `UserLogin` | `BaseModel` | Login request | `email: EmailStr`, `password: str` |
 | `TokenResponse` | `BaseModel` | JWT pair response | `access_token: str`, `refresh_token: str`, `token_type: str = "bearer"` |
 | `TokenRefresh` | `BaseModel` | Refresh request | `refresh_token: str` |
 | `UserOut` | `BaseModel` | Public user response | `id: UUID`, `email: str`, `full_name: str`, `phone: str\|None`, `role: str`, `is_active: bool`, `created_at: datetime`; `from_attributes=True` |
 | `UserUpdate` | `BaseModel` | Profile update | `full_name: str\|None (min=1, max=255)`, `phone: str\|None` |
 | `HostProfileOut` | `BaseModel` | Host profile response | `id, user_id: UUID`, `business_name, bio: str\|None`, `phone_visible: bool`, `is_verified: bool`, `avg_rating: float`, `total_reviews: int`, `created_at: datetime` |
 | `HostProfileUpdate` | `BaseModel` | Host profile update | `business_name, bio: str\|None`, `phone_visible: bool\|None` |
 
 ### 3.2 Property Schemas (`app/schemas/property.py`)
 
 | Schema | Purpose | Key Fields |
 |--------|---------|-----------|
 | `PropertyCreate` | Create listing | `title (min=3, max=255)`, `description (min=10)`, `city (min=1, max=100)`, `address (min=5, max=500)`, `latitude/longitude: float\|None`, `price_per_night: float (gt=0)`, `max_guests: int (1-50)`, `amenities: list[str]\|None` |
 | `PropertyUpdate` | Partial update | All fields optional, same constraints; adds `is_active: bool\|None` |
 | `PropertyImageOut` | Image response | `id: UUID`, `image_url: str`, `is_primary: bool`, `sort_order: int` |
 | `HourlyBookingConfigOut` | Hourly config | `id: UUID`, `hourly_price: float`, `min_hours/max_hours: int`, `available_from/available_to: time` |
 | `HourlyBookingConfigUpdate` | Update hourly | `hourly_price: float (gt=0)`, `min_hours: int (ge=1)`, `max_hours: int (1-24)`, `available_from/available_to: time` |
 | `PropertyOut` | Full response | All Property fields + `images: list[PropertyImageOut]`, `hourly_config: HourlyBookingConfigOut\|None` |
 | `PropertySearchParams` | Query params | `city: str\|None`, `min_price/max_price: float\|None`, `max_guests: int\|None`, `amenities: list[str]\|None`, `hourly_available: bool\|None`, `host_id: UUID\|None`, `page: int (ge=1)`, `page_size: int (1-100, default=20)` |
 
 ### 3.3 Booking Schemas (`app/schemas/booking.py`)
 
 | Schema | Purpose | Key Fields |
 |--------|---------|-----------|
 | `BookingCreate` | Create booking | `property_id: UUID`, `check_in/check_out: datetime`, `booking_type: str (pattern nightly\|hourly)`, `hours: int\|None (1-24)` |
 | `BookingStatusUpdate` | Status change | `status: str (pattern confirmed\|cancelled\|completed\|rejected)` |
 | `BookingOut` | Response | All booking fields; `from_attributes=True` |
 | `PaginatedBookings` | Paginated | `items: list[BookingOut]`, `total, page, page_size: int` |
 
 ### 3.4 Membership Schemas (`app/schemas/membership.py`)
 
 | Schema | Purpose | Key Fields |
 |--------|---------|-----------|
 | `MembershipPlanOut` | Plan info | `plan_type, label: str`, `price: float`, `max_listings: int` |
 | `MembershipSubscribeRequest` | Subscribe | `plan_type: str (pattern basic\|pro\|premium)`, `payment_token: str (min=1)` |
 | `MembershipOut` | Response | All membership fields; `from_attributes=True` |
 | `MembershipWebhookPayload` | Webhook | `event_type, payment_ref, status: str`, `metadata: dict\|None` |
 
 ### 3.5 Message Schemas (`app/schemas/message.py`)
 
 | Schema | Purpose | Key Fields |
 |--------|---------|-----------|
 | `ConversationCreate` | Start conversation | `property_id: UUID`, `message: str (1-5000)` |
 | `MessageCreate` | Send message | `content: str (1-5000)` |
 | `MessageOut` | Response | All message fields; `from_attributes=True` |
 | `ConversationOut` | Response | All conversation fields + `last_message: MessageOut\|None`, `unread_count: int` |
 | `PaginatedMessages` | Paginated | `items: list[MessageOut]`, `total, page, page_size: int` |
 
 ### 3.6 Review Schemas (`app/schemas/review.py`)
 
 | Schema | Purpose | Key Fields |
 |--------|---------|-----------|
 | `ReviewCreate` | Create review | `booking_id: UUID`, `rating: float (1.0-5.0)`, `comment: str\|None (max=2000)` |
 | `ReviewOut` | Response | All review fields; `from_attributes=True` |
 | `PaginatedReviews` | Paginated | `items: list[ReviewOut]`, `total, page, page_size: int` |
 
 ### 3.7 `schemas/__init__.py`
 Empty re-export file. Contains only docstring `"""Pydantic schemas package."""`.
 
 ---
 
 ## 4. Services
 
 ### 4.1 `auth_service.py`
 
 | Function | Signature | DB Operations | Raises | Notes |
 |----------|-----------|--------------|--------|-------|
 | `register_user` | `(db: AsyncSession, data: UserRegister) → User` | SELECT users WHERE email; INSERT user; INSERT host_profile if host | `ConflictError` if email exists | Triggers `send_welcome_email.delay()` |
 | `authenticate_user` | `(db: AsyncSession, email: str, password: str) → TokenResponse` | SELECT users WHERE email | `UnauthorizedError` if not found/wrong password/inactive | Returns JWT access+refresh tokens |
 | `refresh_access_token` | `(db: AsyncSession, refresh_token_str: str) → TokenResponse` | SELECT users WHERE id | `UnauthorizedError` if invalid token/user inactive | Decodes JWT, checks type="refresh" |
 
 ### 4.2 `property_service.py`
 
 | Function | Signature | DB Operations | Raises | Notes |
 |----------|-----------|--------------|--------|-------|
 | `_verify_active_membership` | `(db, user) → Membership` | SELECT host_profiles; SELECT memberships | `ForbiddenError`, `MembershipRequiredError` | Also expires stale memberships |
 | `_count_host_listings` | `(db, host_id) → int` | SELECT COUNT properties WHERE active | — | — |
 | `create_property` | `(db, data: PropertyCreate, host: User) → Property` | Calls `_verify_active_membership`, `_count_host_listings`; INSERT property; SELECT with eager load | `ForbiddenError` if listing cap exceeded | Enforces plan-based listing limit |
 | `update_property` | `(db, property_id, data: PropertyUpdate, host) → Property` | SELECT property; UPDATE fields | `NotFoundError`, `ForbiddenError` | Owner-only |
 | `delete_property` | `(db, property_id, host) → None` | UPDATE `is_active=False` | `NotFoundError`, `ForbiddenError` | Soft-delete |
 | `get_property` | `(db, property_id) → Property` | SELECT with `selectinload(images, hourly_config)` | `NotFoundError` | Public |
 | `search_properties` | `(db, params: PropertySearchParams) → tuple[list, int]` | SELECT with ilike city, price range, max_guests, hourly filters | — | Paginated, ordered by `created_at DESC` |
 | `configure_hourly_booking` | `(db, property_id, data, host) → Property` | SELECT/INSERT/UPDATE HourlyBookingConfig | `NotFoundError`, `ForbiddenError` | Sets `hourly_enabled=True` |
 | `add_property_image` | `(db, property_id, image_url, is_primary, host) → PropertyImage` | Un-marks existing primary; INSERT image | — | Owner-only |
 | `_get_property_for_host` | `(db, property_id, host_id) → Property` | SELECT property | `NotFoundError`, `ForbiddenError` | Internal helper |
 
 ### 4.3 `booking_service.py`
 
 **State machine** (`VALID_TRANSITIONS`):
 ```
 pending → {confirmed, rejected, cancelled}
 confirmed → {cancelled, completed}
 completed → {} (terminal)
 cancelled → {} (terminal)
 rejected → {} (terminal)
 ```
 
 | Function | Signature | DB Operations | Raises | Notes |
 |----------|-----------|--------------|--------|-------|
 | `create_booking` | `(db, data: BookingCreate, guest) → Booking` | SELECT property; SELECT overlapping bookings; SELECT hourly config; INSERT booking | `NotFoundError`, `BadRequestError` (own property, date validation, overlap, hourly constraints) | Price: `nights * price_per_night` or `hours * hourly_price`; triggers `send_booking_confirmation.delay()` |
 | `update_booking_status` | `(db, booking_id, new_status, user) → Booking` | SELECT booking; UPDATE status | `NotFoundError`, `BadRequestError` (invalid transition), `ForbiddenError` (permission) | Host: confirm/reject/complete; Guest+Host: cancel; Admin: all |
 | `get_booking` | `(db, booking_id, user) → Booking` | SELECT booking | `NotFoundError`, `ForbiddenError` | Participants + admin only |
 | `list_bookings` | `(db, user, page, page_size) → tuple[list, int]` | SELECT with role-based filter | — | Admin sees all; host sees sent+received; user sees guest bookings |
 
 ### 4.4 `membership_service.py`
 
 | Function | Signature | DB Operations | Raises |
 |----------|-----------|--------------|--------|
 | `get_available_plans` | `() → list[MembershipPlanOut]` | None (reads `PLAN_CONFIG`) | — |
 | `subscribe` | `(db, data: MembershipSubscribeRequest, host) → Membership` | SELECT host_profile; SELECT existing membership; INSERT or UPDATE membership | `NotFoundError` |
 | `get_current_membership` | `(db, host) → Membership` | SELECT host_profile; SELECT membership | `NotFoundError` |
 | `cancel_membership` | `(db, host) → Membership` | Read current; UPDATE status=cancelled, auto_renew=False | `BadRequestError` if not active |
 | `process_webhook` | `(db, event_type, payment_ref, status) → None` | SELECT membership by payment_ref; UPDATE status | — |
 
 ### 4.5 `message_service.py`
 
 | Function | Signature | DB Operations | Raises |
 |----------|-----------|--------------|--------|
 | `start_conversation` | `(db, data: ConversationCreate, guest) → dict` | SELECT property; SELECT existing conv; INSERT conversation + message | `NotFoundError`, `BadRequestError` (self/duplicate) |
 | `send_message` | `(db, conversation_id, data: MessageCreate, sender) → Message` | Verify user in conversation; INSERT message; UPDATE `conversation.updated_at` | `NotFoundError`, `ForbiddenError` |
 | `list_conversations` | `(db, user, page, page_size) → tuple[list[dict], int]` | SELECT conversations; for each: last message, unread count, property title, other party name | — |
 | `get_conversation_detail` | `(db, conversation_id, user) → dict` | SELECT conversation + property title + other party name | `NotFoundError`, `ForbiddenError` |
 | `get_messages` | `(db, conversation_id, user, page, page_size) → tuple[list, int]` | SELECT messages ordered ASC | `NotFoundError`, `ForbiddenError` |
 | `mark_message_read` | `(db, message_id, user) → Message` | SELECT message; UPDATE is_read=True | `NotFoundError`, `BadRequestError` (own message), `ForbiddenError` |
 
 ### 4.6 `review_service.py`
 
 | Function | Signature | DB Operations | Raises |
 |----------|-----------|--------------|--------|
 | `create_review` | `(db, data: ReviewCreate, reviewer) → Review` | SELECT booking; SELECT existing review; INSERT review; update host rating | `NotFoundError`, `ForbiddenError` (not guest), `BadRequestError` (not completed/duplicate) |
 | `list_property_reviews` | `(db, property_id, page, page_size) → tuple[list, int]` | SELECT reviews WHERE property_id | — |
 | `list_host_reviews` | `(db, host_id, page, page_size) → tuple[list, int]` | SELECT reviews WHERE property in host's properties | — |
 | `_update_host_rating` | `(db, host_user_id) → None` | SELECT AVG(rating), COUNT; UPDATE host_profile | — |
 
 ### 4.7 `upload_service.py`
 
 | Function | Signature | Returns |
 |----------|-----------|---------|
 | `get_s3_client` | `() → boto3.client` | S3 client configured from `settings` |
 | `_ensure_bucket_exists` | `(s3) → None` | Creates bucket with public-read policy if missing |
 | `upload_image` | `(file_bytes: bytes, content_type: str, folder: str = "properties") → str` | Public URL string |
 | `delete_image` | `(image_url: str) → bool` | `True` on success, `False` on `ClientError` |
 
 ---
 
 ## 5. API Routes
 
 **Base prefix**: `/api/v1` (configured in `app/main.py`)
 
 ### 5.1 Route Inventory
 
 | Method | Full Path | Auth | Rate Limit | Request Body | Response | Status | Service Call |
 |--------|----------|------|-----------|-------------|----------|--------|-------------|
 | `GET` | `/health` | — | — | — | `{"status","version"}` | 200 | — |
 | **Auth** | | | | | | | |
 | `POST` | `/api/v1/auth/register` | — | 10/min | `UserRegister` | `UserOut` | 201 | `auth_service.register_user` |
 | `POST` | `/api/v1/auth/login` | — | 20/min | `UserLogin` | `TokenResponse` | 200 | `auth_service.authenticate_user` |
 | `POST` | `/api/v1/auth/refresh` | — | — | `TokenRefresh` | `TokenResponse` | 200 | `auth_service.refresh_access_token` |
 | `GET` | `/api/v1/auth/me` | `get_current_user` | — | — | `UserOut` | 200 | — (returns user) |
 | `PUT` | `/api/v1/auth/me` | `get_current_user` | — | `UserUpdate` | `UserOut` | 200 | inline update |
 | `PUT` | `/api/v1/auth/me/password` | `get_current_user` | — | `PasswordChange` | `{"message"}` | 200 | inline (verify+hash) |
 | `POST` | `/api/v1/auth/forgot-password` | — | 5/min | `ForgotPasswordRequest` | `{"message"}` | 200 | stub (anti-enumeration) |
 | `POST` | `/api/v1/auth/reset-password` | — | — | `ResetPasswordRequest` | `{"message"}` | 200 | decode token + hash |
 | **Properties** | | | | | | | |
 | `GET` | `/api/v1/properties` | — | — | Query params | `dict{items,total,page,page_size}` | 200 | `property_service.search_properties` |
 | `GET` | `/api/v1/properties/{property_id}` | — | — | — | `PropertyOut` | 200 | `property_service.get_property` |
 | `POST` | `/api/v1/properties` | `require_host` | — | `PropertyCreate` | `PropertyOut` | 201 | `property_service.create_property` |
 | `PUT` | `/api/v1/properties/{property_id}` | `require_host` | — | `PropertyUpdate` | `PropertyOut` | 200 | `property_service.update_property` |
 | `DELETE` | `/api/v1/properties/{property_id}` | `require_host` | — | — | — | 204 | `property_service.delete_property` |
 | `POST` | `/api/v1/properties/{property_id}/images` | `require_host` | — | `UploadFile` + `is_primary` query | `dict{id,image_url,is_primary}` | 201 | `upload_service.upload_image` + `property_service.add_property_image` |
 | `PUT` | `/api/v1/properties/{property_id}/hourly` | `require_host` | — | `HourlyBookingConfigUpdate` | `PropertyOut` | 200 | `property_service.configure_hourly_booking` |
 | **Bookings** | | | | | | | |
 | `POST` | `/api/v1/bookings` | `get_current_user` | — | `BookingCreate` | `BookingOut` | 201 | `booking_service.create_booking` |
 | `GET` | `/api/v1/bookings` | `get_current_user` | — | `page, page_size` | `PaginatedBookings` | 200 | `booking_service.list_bookings` |
 | `GET` | `/api/v1/bookings/{booking_id}` | `get_current_user` | — | — | `BookingOut` | 200 | `booking_service.get_booking` |
 | `PUT` | `/api/v1/bookings/{booking_id}/status` | `get_current_user` | — | `BookingStatusUpdate` | `BookingOut` | 200 | `booking_service.update_booking_status` |
 | `POST` | `/api/v1/bookings/{booking_id}/cancel` | `get_current_user` | — | — | `BookingOut` | 200 | `booking_service.update_booking_status("cancelled")` |
 | **Messaging** | | | | | | | |
 | `POST` | `/api/v1/conversations` | `get_current_user` | — | `ConversationCreate` | `dict` | 201 | `message_service.start_conversation` |
 | `GET` | `/api/v1/conversations` | `get_current_user` | — | `page, page_size` | `dict` | 200 | `message_service.list_conversations` |
 | `GET` | `/api/v1/conversations/{cid}` | `get_current_user` | — | — | `dict` | 200 | `message_service.get_conversation_detail` |
 | `GET` | `/api/v1/conversations/{cid}/messages` | `get_current_user` | — | `page, page_size` | `PaginatedMessages` | 200 | `message_service.get_messages` |
 | `POST` | `/api/v1/conversations/{cid}/messages` | `get_current_user` | — | `MessageCreate` | `MessageOut` | 201 | `message_service.send_message` |
 | `PUT` | `/api/v1/messages/{mid}/read` | `get_current_user` | — | — | `MessageOut` | 200 | `message_service.mark_message_read` |
 | **Reviews** | | | | | | | |
 | `POST` | `/api/v1/reviews` | `get_current_user` | — | `ReviewCreate` | `ReviewOut` | 201 | `review_service.create_review` |
 | `GET` | `/api/v1/reviews/property/{pid}` | — | — | `page, page_size` | `PaginatedReviews` | 200 | `review_service.list_property_reviews` |
 | `GET` | `/api/v1/reviews/host` | `get_current_user` | — | `page, page_size` | `PaginatedReviews` | 200 | `review_service.list_host_reviews` |
 | **Memberships** | | | | | | | |
 | `GET` | `/api/v1/memberships/plans` | — | — | — | `list[MembershipPlanOut]` | 200 | `membership_service.get_available_plans` |
 | `POST` | `/api/v1/memberships/subscribe` | `require_host` | — | `MembershipSubscribeRequest` | `MembershipOut` | 201 | `membership_service.subscribe` |
 | `GET` | `/api/v1/memberships/current` | `require_host` | — | — | `MembershipOut` | 200 | `membership_service.get_current_membership` |
 | `PUT` | `/api/v1/memberships/cancel` | `require_host` | — | — | `MembershipOut` | 200 | `membership_service.cancel_membership` |
 | `POST` | `/api/v1/memberships/webhook` | — | — | `MembershipWebhookPayload` | `{"status":"processed"}` | 200 | `membership_service.process_webhook` |
 | **Admin** | | | | | | | |
 | `GET` | `/api/v1/admin/users` | `require_admin` | — | `page, page_size` | `dict` | 200 | inline SELECT |
 | `GET` | `/api/v1/admin/properties` | `require_admin` | — | `page, page_size` | `dict` | 200 | inline SELECT |
 | `GET` | `/api/v1/admin/memberships` | `require_admin` | — | `page, page_size` | `dict` | 200 | inline SELECT |
 | `GET` | `/api/v1/admin/bookings` | `require_admin` | — | `page, page_size` | `dict` | 200 | inline SELECT |
 | `GET` | `/api/v1/admin/dashboard` | `require_admin` | — | — | `dict` (7 KPIs) | 200 | inline aggregate queries |
 | `PUT` | `/api/v1/admin/users/{user_id}/status` | `require_admin` | — | — | `dict{id, is_active}` | 200 | toggle `user.is_active` |
 
 ---
 
 ## 6. Auth & Security
 
 ### 6.1 Password Hashing (`core/security.py`)
 - Library: `passlib.context.CryptContext`
 - Scheme: **Argon2** (`schemes=["argon2"]`)
 - Functions: `hash_password(password) → str`, `verify_password(plain, has