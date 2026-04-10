# StayNest — Complete Project Reference
  
  > **Commission-free vacation rental platform.** Hosts keep 100% of booking revenue; the platform monetizes through membership subscriptions.
  
  ---
  
  ## Table of Contents
  
  1. [Project Overview](#1-project-overview)
  2. [Infrastructure & DevOps](#2-infrastructure--devops)
  3. [Backend — Python / FastAPI](#3-backend--python--fastapi)
  - 3.1 [Application Factory & Entry Point](#31-application-factory--entry-point)
  - 3.2 [Configuration](#32-configuration)
  - 3.3 [Database Layer](#33-database-layer)
  - 3.4 [Dependencies (Auth Guards)](#34-dependencies-auth-guards)
  - 3.5 [Core Utilities](#35-core-utilities)
  - 3.6 [Models (SQLAlchemy ORM)](#36-models-sqlalchemy-orm)
  - 3.7 [Schemas (Pydantic)](#37-schemas-pydantic)
  - 3.8 [Services (Business Logic)](#38-services-business-logic)
  - 3.9 [API Routes (v1)](#39-api-routes-v1)
  - 3.10 [Background Tasks (Celery)](#310-background-tasks-celery)
  - 3.11 [Database Migrations (Alembic)](#311-database-migrations-alembic)
  - 3.12 [Tests](#312-tests)
  4. [Frontend — Next.js / React / TypeScript](#4-frontend--nextjs--react--typescript)
  - 4.1 [App Shell & Middleware](#41-app-shell--middleware)
  - 4.2 [API Client](#42-api-client)
  - 4.3 [TypeScript Types](#43-typescript-types)
  - 4.4 [Zustand Stores](#44-zustand-stores)
  - 4.5 [Custom Hooks](#45-custom-hooks)
  - 4.6 [Components — Layout](#46-components--layout)
  - 4.7 [Components — Property](#47-components--property)
  - 4.8 [Components — Providers](#48-components--providers)
  - 4.9 [Components — UI Primitives](#49-components--ui-primitives)
  - 4.10 [Pages — Authentication](#410-pages--authentication)
  - 4.11 [Pages — Properties (Public)](#411-pages--properties-public)
  - 4.12 [Pages — Bookings (Guest)](#412-pages--bookings-guest)
  - 4.13 [Pages — Messages](#413-pages--messages)
  - 4.14 [Pages — Profile](#414-pages--profile)
  - 4.15 [Pages — Host Dashboard](#415-pages--host-dashboard)
  - 4.16 [Pages — Admin Panel](#416-pages--admin-panel)
  - 4.17 [Root App Pages](#417-root-app-pages)
  
  ---
  
  ## 1. Project Overview
  
  **StayNest** is a full-stack vacation rental marketplace built with:
  
  | Layer | Technology |
  |-------|-----------|
  | Backend API | Python 3.12+, FastAPI, SQLAlchemy 2 (async), Pydantic v2 |
  | Database | PostgreSQL 16 (async via `asyncpg`) |
  | Cache / Broker | Redis 7 |
  | Task Queue | Celery |
  | Object Storage | MinIO (S3-compatible) |
  | Frontend | Next.js 14 (App Router), React 18, TypeScript, Tailwind CSS |
  | State Mgmt | Zustand |
  | Auth | JWT (access + refresh tokens), Argon2 password hashing |
  | Containerisation | Docker Compose |
  | Migrations | Alembic (async) |
  
  **Key Business Features:**
  - User registration with guest / host / admin roles
  - Property CRUD with image upload, search & filtering
  - Nightly **and** hourly booking system
  - Guest ↔ Host messaging system
  - Review & rating system
  - Tiered membership plans (Basic / Pro / Premium) for hosts
  - Admin dashboard with platform-wide analytics
  - Rate limiting (Redis-backed)
  - Background email and membership renewal tasks
  
  ---
  
  ## 2. Infrastructure & DevOps
  
  ### `docker-compose.yml`
  
  Defines six services:
  
  | Service | Image / Build | Port | Purpose |
  |---------|--------------|------|---------|
  | `api` | `./backend/Dockerfile` | 8000 | FastAPI backend |
  | `celery-worker` | `./backend/Dockerfile` | — | Celery background worker |
  | `db` | `postgres:16-alpine` | 5432 | PostgreSQL database |
  | `redis` | `redis:7-alpine` | 6379 | Cache + Celery broker |
  | `minio` | `minio/minio:latest` | 9000, 9001 | S3-compatible object store |
  | `frontend` | `./frontend/Dockerfile` | 3000 | Next.js frontend |
  
  **Volumes:** `postgres_data`, `redis_data`, `minio_data` for persistence.
  
  ### `setup.sh` / `setup.ps1`
  
  Shell scripts for bootstrapping the development environment (creating `.env` files, running migrations, seeding data).
  
  ### `generate_excel.py` / `setup_from_excel.py`
  
  Utility scripts for generating/loading seed data from Excel spreadsheets.
  
  ---
  
  ## 3. Backend — Python / FastAPI
  
  ### 3.1 Application Factory & Entry Point
  
  **File:** `backend/app/main.py`
  
  | Symbol | Type | Description |
  |--------|------|-------------|
  | `lifespan(app)` | Async context manager | Application lifespan handler for startup/shutdown events. |
  | `create_app()` | Function → `FastAPI` | Factory that creates and configures the FastAPI instance: sets title/version from config, adds CORS middleware (origins from settings), mounts the v1 API router at `/api/v1`, and adds a `/health` endpoint. |
  | `app` | Module-level instance | The main FastAPI application instance created by `create_app()`. |
  
  **Health endpoint:**
  - `GET /health` → `{"status": "healthy", "version": "..."}` — used by Docker healthchecks and monitoring.
  
  ---
  
  ### 3.2 Configuration
  
  **File:** `backend/app/config.py`
  
  **Class: `Settings(BaseSettings)`** — 12-factor compliant configuration loaded from environment variables / `.env`.
  
  | Setting | Default | Description |
  |---------|---------|-------------|
  | `APP_ENV` | `"development"` | Current environment |
  | `DEBUG` | `False` | Debug mode flag |
  | `APP_TITLE` | `"StayNest API"` | Shown in OpenAPI docs |
  | `APP_VERSION` | `"0.1.0"` | API version |
  | `DATABASE_URL` | `postgresql+asyncpg://...` | Async PostgreSQL connection string |
  | `DATABASE_ECHO` | `False` | SQLAlchemy SQL echo |
  | `REDIS_URL` | `redis://localhost:6379/0` | Redis connection for caching/rate limiting |
  | `JWT_SECRET_KEY` | `"CHANGE-ME-..."` | Secret for signing JWTs |
  | `JWT_ALGORITHM` | `"HS256"` | JWT signing algorithm |
  | `JWT_ACCESS_TOKEN_EXPIRE_MINUTES` | `30` | Access token TTL |
  | `JWT_REFRESH_TOKEN_EXPIRE_DAYS` | `7` | Refresh token TTL |
  | `S3_ENDPOINT_URL` | `http://localhost:9000` | MinIO/S3 endpoint |
  | `S3_ACCESS_KEY_ID` | `"minioadmin"` | S3 access key |
  | `S3_SECRET_ACCESS_KEY` | `"minioadmin"` | S3 secret key |
  | `S3_BUCKET_NAME` | `"staynest-images"` | Bucket for image uploads |
  | `S3_REGION` | `"us-east-1"` | S3 region |
  | `CORS_ORIGINS` | `["http://localhost:3000"]` | Allowed CORS origins |
  | `CELERY_BROKER_URL` | `redis://localhost:6379/1` | Celery broker URL |
  | `RATE_LIMIT_PER_MINUTE` | `60` | Requests per minute per client |
  
  **Singleton:** `settings = Settings()` — module-level instance used across the app.
  
  ---
  
  ### 3.3 Database Layer
  
  **File:** `backend/app/database.py`
  
  | Symbol | Type | Description |
  |--------|------|-------------|
  | `engine` | `AsyncEngine` | SQLAlchemy async engine with connection pooling (`pool_size=20`, `max_overflow=10`, `pool_pre_ping=True`). |
  | `async_session_factory` | `async_sessionmaker` | Factory producing `AsyncSession` instances with `expire_on_commit=False`. |
  | `Base` | `DeclarativeBase` | SQLAlchemy declarative base class — all models inherit from this. |
  | `get_db()` | Async generator → `AsyncSession` | FastAPI dependency that yields a database session, auto-commits on success, rolls back on error, and closes on exit. |
  
  ---
  
  ### 3.4 Dependencies (Auth Guards)
  
  **File:** `backend/app/dependencies.py`
  
  | Dependency | Returns | Description |
  |-----------|---------|-------------|
  | `get_current_user(credentials, db)` | `User` | Extracts the JWT bearer token, decodes it, validates the `"access"` type, looks up the user by `sub` claim, and verifies the user is active. Raises 401 on failure. |
  | `require_host(current_user)` | `User` | Ensures the current user has `"host"` or `"admin"` role. Raises 403 otherwise. |
  | `require_admin(current_user)` | `User` | Ensures the current user has `"admin"` role. Raises 403 otherwise. |
  
  ---
  
  ### 3.5 Core Utilities
  
  #### `backend/app/core/security.py` — JWT & Password Hashing
  
  | Function | Parameters | Returns | Description |
  |----------|-----------|---------|-------------|
  | `hash_password(password)` | `str` | `str` | Hashes a plaintext password using **Argon2** via `passlib`. |
  | `verify_password(plain_password, hashed_password)` | `str, str` | `bool` | Verifies a plaintext password against its Argon2 hash. |
  | `create_access_token(data, expires_delta?)` | `dict, timedelta?` | `str` | Creates a JWT access token with `"type": "access"` claim. Default expiry: 30 minutes. |
  | `create_refresh_token(data)` | `dict` | `str` | Creates a JWT refresh token with `"type": "refresh"` claim. Expiry: 7 days. |
  | `decode_token(token)` | `str` | `dict \| None` | Decodes and validates a JWT. Returns the payload dict or `None` on failure. |
  
  #### `backend/app/core/exceptions.py` — Custom HTTP Exceptions
  
  | Exception | HTTP Status | Default Detail |
  |-----------|-------------|----------------|
  | `NotFoundError` | 404 | `"Resource not found"` |
  | `ForbiddenError` | 403 | `"Access forbidden"` |
  | `ConflictError` | 409 | `"Resource conflict"` |
  | `BadRequestError` | 400 | `"Bad request"` |
  | `UnauthorizedError` | 401 | `"Invalid credentials"` (includes `WWW-Authenticate: Bearer` header) |
  | `MembershipRequiredError` | 402 | `"Active membership required to perform this action"` |
  
  #### `backend/app/core/permissions.py` — Role-Based Access Control
  
  | Symbol | Type | Description |
  |--------|------|-------------|
  | `UserRole` | `StrEnum` | Enum with `USER`, `HOST`, `ADMIN` values. |
  | `require_role(*roles)` | Decorator | Decorator factory that restricts an endpoint to specific roles. Checks `kwargs["current_user"].role` against the allowed roles. Raises 401 if no user, 403 if insufficient permissions. |
  
  #### `backend/app/core/rate_limiter.py` — Redis-Backed Rate Limiting
  
  | Function | Parameters | Description |
  |----------|-----------|-------------|
  | `rate_limit_check(request, limit=60)` | `Request, int` | Sliding-window rate limiter using Redis `INCR` + `EXPIRE`. Key format: `rate_limit:{client_ip}:{path}`. Returns 429 if limit exceeded. Falls back to no-op if Redis is unavailable. |
  
  ---
  
  ### 3.6 Models (SQLAlchemy ORM)
  
  All models are imported via `backend/app/models/__init__.py`.
  
  #### `User` — `backend/app/models/user.py`
  
  | Column | Type | Constraints | Description |
  |--------|------|-------------|-------------|
  | `id` | `UUID` | PK, auto-generated | Unique user identifier |
  | `email` | `String(255)` | Unique, indexed | User's email address |
  | `hashed_password` | `String(255)` | Not null | Argon2 password hash |
  | `full_name` | `String(255)` | Not null | Display name |
  | `phone` | `String(20)` | Nullable | Phone number |
  | `role` | `String(20)` | Default `"user"` | One of `user`, `host`, `admin` |
  | `is_active` | `Boolean` | Default `True` | Account active flag |
  | `created_at` | `DateTime(tz)` | Auto-set | Registration timestamp |
  | `updated_at` | `DateTime(tz)` | Auto-updated | Last update timestamp |
  
  **Relationships:** `host_profile` (1:1 → HostProfile), `properties` (1:many → Property), `bookings_as_guest` (1:many → Booking), `reviews` (1:many → Review).
  
  #### `HostProfile` — `backend/app/models/user.py`
  
  Extended profile for hosts with business information.
  
  | Column | Type | Description |
  |--------|------|-------------|
  | `id` | `UUID` | Primary key |
  | `user_id` | `UUID` | FK → `users.id` (unique, cascade delete) |
  | `business_name` | `String(255)` | Optional business name |
  | `bio` | `Text` | Optional biography |
  | `phone_visible` | `Boolean` | Whether phone is publicly visible |
  | `is_verified` | `Boolean` | Host verification status |
  | `avg_rating` | `Float` | Computed average rating |
  | `total_reviews` | `Integer` | Total review count |
  | `created_at` | `DateTime(tz)` | Profile creation date |
  
  **Relationships:** `user` (→ User), `membership` (1:1 → Membership).
  
  #### `Property` — `backend/app/models/property.py`
  
  | Column | Type | Description |
  |--------|------|-------------|
  | `id` | `UUID` | Primary key |
  | `host_id` | `UUID` | FK → `users.id` (indexed) |
  | `title` | `String(255)` | Listing title |
  | `description` | `Text` | Full description |
  | `city` | `String(100)` | City (indexed for search) |
  | `address` | `String(500)` | Full address |
  | `latitude` / `longitude` | `Float` | Geolocation (nullable) |
  | `price_per_night` | `Float` | Nightly price |
  | `max_guests` | `Integer` | Maximum guest capacity |
  | `amenities` | `JSON` | List of amenity strings |
  | `is_active` | `Boolean` | Listing active flag |
  | `hourly_enabled` | `Boolean` | Whether hourly booking is available |
  | `created_at` / `updated_at` | `DateTime(tz)` | Timestamps |
  
  **Relationships:** `host`, `images` (1:many → PropertyImage), `hourly_config` (1:1 → HourlyBookingConfig), `bookings`, `reviews`.
  
  #### `PropertyImage` — `backend/app/models/property.py`
  
  | Column | Type | Description |
  |--------|------|-------------|
  | `id` | `UUID` | Primary key |
  | `property_id` | `UUID` | FK → `properties.id` |
  | `image_url` | `String(1000)` | S3 image URL |
  | `is_primary` | `Boolean` | Primary image flag |
  | `sort_order` | `Integer` | Display order |
  
  #### `HourlyBookingConfig` — `backend/app/models/property.py`
  
  | Column | Type | Description |
  |--------|------|-------------|
  | `id` | `UUID` | Primary key |
  | `property_id` | `UUID` | FK → `properties.id` (unique) |
  | `hourly_price` | `Float` | Price per hour |
  | `min_hours` | `Integer` | Minimum booking hours (default: 1) |
  | `max_hours` | `Integer` | Maximum booking hours (default: 12) |
  | `available_from` | `Time` | Start of availability window (default: 08:00) |
  | `available_to` | `Time` | End of availability window (default: 22:00) |
  
  #### `Booking` — `backend/app/models/booking.py`
  
  | Column | Type | Description |
  |--------|------|-------------|
  | `id` | `UUID` | Primary key |
  | `property_id` | `UUID` | FK → `properties.id` |
  | `guest_id` | `UUID` | FK → `users.id` |
  | `host_id` | `UUID` | FK → `users.id` |
  | `check_in` / `check_out` | `DateTime(tz)` | Booking dates |
  | `total_price` | `Float` | Computed total price |
  | `booking_type` | `String(20)` | `"nightly"` or `"hourly"` |
  | `hours` | `Integer` | Hours (for hourly bookings) |
  | `status` | `String(20)` | `pending`, `confirmed`, `cancelled`, `completed`, `rejected` |
  | `created_at` / `updated_at` | `DateTime(tz)` | Timestamps |
  
  **Enums:** `BookingStatus` (pending, confirmed, cancelled, completed, rejected), `BookingType` (nightly, hourly).
  
  **Relationships:** `property`, `guest`, `host`, `review` (1:1).
  
  #### `Membership` — `backend/app/models/membership.py`
  
  | Column | Type | Description |
  |--------|------|-------------|
  | `id` | `UUID` | Primary key |
  | `host_id` | `UUID` | FK → `host_profiles.id` (unique) |
  | `plan_type` | `String(20)` | `basic`, `pro`, `premium` |
  | `start_date` / `end_date` | `DateTime(tz)` | Subscription period |
  | `status` | `String(20)` | `active`, `cancelled`, `expired`, `past_due` |
  | `auto_renew` | `Boolean` | Auto-renewal flag |
  | `payment_ref` | `String(255)` | Payment gateway reference |
  | `amount` | `Float` | Subscription amount |
  | `max_listings` | `Integer` | Maximum allowed listings |
  | `created_at` / `updated_at` | `DateTime(tz)` | Timestamps |
  
  **Enums:** `MembershipPlan` (basic, pro, premium), `MembershipStatus` (active, cancelled, expired, past_due).
  
  **Plan Configuration (`PLAN_CONFIG`):**
  | Plan | Price | Max Listings |
  |------|-------|-------------|
  | Basic | $29.00/month | 5 |
  | Pro | $79.00/month | 25 |
  | Premium | $199.00/month | Unlimited |
  
  #### `Conversation` — `backend/app/models/message.py`
  
  | Column | Type | Description |
  |--------|------|-------------|
  | `id` | `UUID` | Primary key |
  | `property_id` | `UUID` | FK → `properties.id` |
  | `guest_id` | `UUID` | FK → `users.id` |
  | `host_id` | `UUID` | FK → `users.id` |
  | `created_at` / `updated_at` | `DateTime(tz)` | Timestamps |
  
  **Relationships:** `messages` (1:many → Message, ordered by `created_at`), `property`, `guest`, `host`.
  
  #### `Message` — `backend/app/models/message.py`
  
  | Column | Type | Description |
  |--------|------|-------------|
  | `id` | `UUID` | Primary key |
  | `conversation_id` | `UUID` | FK → `conversations.id` |
  | `sender_id` | `UUID` | FK → `users.id` |
  | `content` | `Text` | Message body |
  | `is_read` | `Boolean` | Read receipt flag |
  | `created_at` | `DateTime(tz)` | Sent timestamp |
  
  #### `Review` — `backend/app/models/review.py`
  
  | Column | Type | Description |
  |--------|------|-------------|
  | `id` | `UUID` | Primary key |
  | `booking_id` | `UUID` | FK → `bookings.id` (unique — one review per booking) |
  | `property_id` | `UUID` | FK → `properties.id` |
  | `reviewer_id` | `UUID` | FK → `users.id` |
  | `rating` | `Float` | 1.0–5.0 star rating |
  | `comment` | `Text` | Optional review text |
  | `created_at` | `DateTime(tz)` | Review timestamp |
  
  ---
  
  ### 3.7 Schemas (Pydantic)
  
  #### User Schemas — `backend/app/schemas/user.py`
  
  | Schema | Purpose | Key Fields |
  |--------|---------|------------|
  | `UserRegister` | Registration request | `email` (EmailStr), `password` (8–128 chars), `full_name`, `phone?`, `role` (user\|host) |
  | `UserLogin` | Login request | `email`, `password` |
  | `TokenResponse` | JWT token pair response | `access_token`, `refresh_token`, `token_type` |
  | `TokenRefresh` | Token refresh request | `refresh_token` |
  | `UserOut` | Public user response | `id`, `email`, `full_name`, `phone?`, `role`, `is_active`, `created_at` |
  | `UserUpdate` | Profile update request | `full_name?`, `phone?` |
  | `HostProfileOut` | Host profile response | `id`, `user_id`, `business_name?`, `bio?`, `phone_visible`, `is_verified`, `avg_rating`, `total_reviews` |
  | `HostProfileUpdate` | Host profile update | `business_name?`, `bio?`, `phone_visible?` |
  
  #### Property Schemas — `backend/app/schemas/property.py`
  
  | Schema | Purpose | Key Fields |
  |--------|---------|------------|
  | `PropertyCreate` | Create listing | `title` (3–255), `description` (min 10), `city`, `address`, `price_per_night` (>0), `max_guests` (1–50), `amenities?`, `latitude?`, `longitude?` |
  | `PropertyUpdate` | Partial update | All fields optional from `PropertyCreate` plus `is_active?` |
  | `PropertyImageOut` | Image response | `id`, `image_url`, `is_primary`, `sort_order` |
  | `HourlyBookingConfigOut` | Hourly config response | `id`, `hourly_price`, `min_hours`, `max_hours`, `available_from`, `available_to` |
  | `HourlyBookingConfigUpdate` | Set/update hourly config | `hourly_price` (>0), `min_hours`, `max_hours` (1–24), `available_from`, `available_to` |
  | `PropertyOut` | Full listing response | All property fields + `images[]` + `hourly_config?` |
  | `PropertySearchParams` | Search query params | `city?`, `min_price?`, `max_price?`, `max_guests?`, `amenities?`, `hourly_available?`, `host_id?`, `page`, `page_size` |
  
  #### Booking Schemas — `backend/app/schemas/booking.py`
  
  | Schema | Purpose | Key Fields |
  |--------|---------|------------|
  | `BookingCreate` | Create booking | `property_id`, `check_in`, `check_out`, `booking_type` (nightly\|hourly), `hours?` |
  | `BookingStatusUpdate` | Status change | `status` (confirmed\|cancelled\|completed\|rejected) |
  | `BookingOut` | Booking response | All booking fields |
  | `PaginatedBookings` | Paginated list | `items[]`, `total`, `page`, `page_size` |
  
  #### Membership Schemas — `backend/app/schemas/membership.py`
  
  | Schema | Purpose | Key Fields |
  |--------|---------|------------|
  | `MembershipPlanOut` | Plan description | `plan_type`, `label`, `price`, `max_listings` |
  | `MembershipSubscribeRequest` | Subscribe request | `plan_type` (basic\|pro\|premium), `payment_token` |
  | `MembershipOut` | Membership response | All membership fields |
  | `MembershipWebhookPayload` | Payment webhook | `event_type`, `payment_ref`, `status`, `metadata?` |
  
  #### Message Schemas — `backend/app/schemas/message.py`
  
  | Schema | Purpose | Key Fields |
  |--------|---------|------------|
  | `ConversationCreate` | Start conversation | `property_id`, `message` (1–5000 chars) |
  | `MessageCreate` | Send message | `content` (1–5000 chars) |
  | `MessageOut` | Message response | `id`, `conversation_id`, `sender_id`, `content`, `is_read`, `created_at` |
  | `ConversationOut` | Conversation response | `id`, `property_id`, `guest_id`, `host_id`, `last_message?`, `unread_count` |
  | `PaginatedMessages` | Paginated messages | `items[]`, `total`, `page`, `page_size` |
  
  #### Review Schemas — `backend/app/schemas/review.py`
  
  | Schema | Purpose | Key Fields |
  |--------|---------|------------|
  | `ReviewCreate` | Submit review | `booking_id`, `rating` (1.0–5.0), `comment?` (max 2000) |
  | `ReviewOut` | Review response | `id`, `booking_id`, `property_id`, `reviewer_id`, `rating`, `comment?`, `created_at` |
  | `PaginatedReviews` | Paginated reviews | `items[]`, `total`, `page`, `page_size` |
  
  ---
  
  ### 3.8 Services (Business Logic)
  
  #### Auth Service — `backend/app/services/auth_service.py`
  
  | Function | Parameters | Returns | Description |
  |----------|-----------|---------|-------------|
  | `register_user(db, data)` | `AsyncSession, UserRegister` | `User` | Registers a new user. Checks for duplicate email (raises `ConflictError`). If role is `"host"`, also creates a `HostProfile`. Hashes the password with Argon2. |
  | `authenticate_user(db, email, password)` | `AsyncSession, str, str` | `TokenResponse` | Authenticates via email+password. Verifies the password hash, checks the user is active, and returns a JWT access+refresh token pair. Raises `UnauthorizedError` on failure. |
  | `refresh_access_token(db, refresh_token_str)` | `AsyncSession, str` | `TokenResponse` | Validates a refresh token, looks up the user, and issues a new access+refresh token pair. Raises `UnauthorizedError` if the token or user is invalid. |
  
  #### Property Service — `backend/app/services/property_service.py`
  
  | Function | Parameters | Returns | Description |
  |----------|-----------|---------|-------------|
  | `_verify_active_membership(db, user)` | Internal | `None` | Ensures the host has an active membership. Raises `ForbiddenError` if no host profile, `MembershipRequiredError` if no active membership. |
  | `_count_host_listings(db, host_id)` | Internal | `int` | Counts active property listings for a host. |
  | `create_property(db, data, host)` | `AsyncSession, PropertyCreate, User` | `Property` | Creates a new property listing. Requires the host to have an active membership. |
  | `update_property(db, property_id, data, host)` | `AsyncSession, UUID, PropertyUpdate, User` | `Property` | Updates a property listing. Verifies the caller owns the property. Only updates fields included in the request. |
  | `delete_property(db, property_id, host)` | `AsyncSession, UUID, User` | `None` | Soft-deletes (deactivates) a property by setting `is_active=False`. |
  | `get_property(db, property_id)` | `AsyncSession, UUID` | `Property` | Fetches a single property with eager-loaded images and hourly config. Raises `NotFoundError` if not found. |
  | `search_properties(db, params)` | `AsyncSession, PropertySearchParams` | `tuple[list[Property], int]` | Searches active properties with filters (city, price range, guest capacity, hourly availability, host). Returns paginated results with total count. |
  | `configure_hourly_booking(db, property_id, data, host)` | `AsyncSession, UUID, HourlyBookingConfigUpdate, User` | `Property` | Creates or updates hourly booking configuration. Sets `hourly_enabled=True` on the property. |
  | `add_property_image(db, property_id, image_url, is_primary, host)` | `AsyncSession, UUID, str, bool, User` | `PropertyImage` | Adds an image to a property. If `is_primary`, un-marks any existing primary image. |
  | `_get_property_for_host(db, property_id, host_id)` | Internal | `Property` | Fetches a property and verifies the caller is the owner. Raises `NotFoundError` or `ForbiddenError`. |
  
  #### Booking Service — `backend/app/services/booking_service.py`
  
  | Function | Parameters | Returns | Description |
  |----------|-----------|---------|-------------|
  | `create_booking(db, data, guest)` | `AsyncSession, BookingCreate, User` | `Booking` | Creates a booking with full validation: property exists and is active, guest isn't the host, dates are valid and future, no overlapping bookings. Calculates price based on nightly rate × nights or hourly rate × hours. |
  | `update_booking_status(db, booking_id, new_status, user)` | `AsyncSession, UUID, str, User` | `Booking` | Transitions booking status with permission checks: hosts can confirm/reject/complete, guests can cancel, admins can do anything. |
  | `get_booking(db, booking_id, user)` | `AsyncSession, UUID, User` | `Booking` | Retrieves a booking. Only visible to the guest, host, or admins. |
  | `list_bookings(db, user, page, page_size)` | `AsyncSession, User, int, int` | `tuple[list[Booking], int]` | Lists bookings filtered by role: guests see their bookings, hosts see bookings for their properties, admins see all. Paginated with total count. |
  
  #### Membership Service — `backend/app/services/membership_service.py`
  
  | Function | Parameters | Returns | Description |
  |----------|-----------|---------|-------------|
  | `get_available_plans()` | — | `list[MembershipPlanOut]` | Returns all available plans (Basic, Pro, Premium) with pricing and listing limits. |
  | `subscribe(db, data, host)` | `AsyncSession, MembershipSubscribeRequest, User` | `Membership` | Creates a new 30-day membership. Validates the host profile exists and no active membership is already in place. Simulates payment processing. |
  | `get_current_membership(db, host)` | `AsyncSession, User` | `Membership` | Retrieves the host's most recent membership. Raises `NotFoundError` if none exists. |
  | `cancel_membership(db, host)` | `AsyncSession, User` | `Membership` | Cancels the host's active membership and disables auto-renewal. Raises `BadRequestError` if the membership is not active. |
  | `process_webhook(db, event_type, payment_ref, status)` | `AsyncSession, str, str, str` | `None` | Processes payment gateway webhooks to update membership status: `payment.succeeded` → active, `payment.failed` → past_due, `subscription.cancelled` → cancelled. |
  
  #### Message Service — `backend/app/services/message_service.py`
  
  | Function | Parameters | Returns | Description |
  |----------|-----------|---------|-------------|
  | `start_conversation(db, data, guest)` | `AsyncSession, ConversationCreate, User` | `Conversation` | Starts a new conversation thread about a property. Validates the property exists, the guest isn't the host, and no existing conversation for this guest+property+host. Creates the conversation and its initial message. |
  | `send_message(db, conversation_id, data, sender)` | `AsyncSession, UUID, MessageCreate, User` | `Message` | Sends a message in an existing conversation. Verifies the sender is a participant. |
  | `list_conversations(db, user, page, page_size)` | `AsyncSession, User, int, int` | `tuple[list[Conversation], int]` | Lists conversations for the user (as guest or host), ordered by most recent activity, with messages eager-loaded. |
  | `get_messages(db, conversation_id, user, page, page_size)` | `AsyncSession, UUID, User, int, int` | `tuple[list[Message], int]` | Retrieves paginated messages in a conversation, ordered chronologically. Verifies the user is a participant. |
  | `mark_message_read(db, message_id, user)` | `AsyncSession, UUID, User` | `Message` | Marks a message as read. Only the recipient (not the sender) can mark messages as read. |
  | `_get_conversation_for_user(db, conversation_id, user_id)` | Internal | `Conversation` | Fetches a conversation and verifies the user is a participant. |
  
  #### Review Service — `backend/app/services/review_service.py`
  
  | Function | Parameters | Returns | Description |
  |----------|-----------|---------|-------------|
  | `create_review(db, data, reviewer)` | `AsyncSession, ReviewCreate, User` | `Review` | Creates a review for a completed booking. Validates: booking exists, reviewer is the guest, booking is completed, and no existing review. After creation, recalculates the host's average rating. |
  | `list_property_reviews(db, property_id, page, page_size)` | `AsyncSession, UUID, int, int` | `tuple[list[Review], int]` | Lists all reviews for a specific property, paginated. |
  | `list_host_reviews(db, host_id, page, page_size)` | `AsyncSession, UUID, int, int` | `tuple[list[Review], int]` | Lists all reviews for properties owned by a specific host. |
  | `_update_host_rating(db, host_user_id)` | Internal | `None` | Recalculates and updates the host's `avg_rating` and `total_reviews` in their profile. |
  
  #### Upload Service — `backend/app/services/upload_service.py`
  
  | Function | Parameters | Returns | Description |
  |----------|-----------|---------|-------------|
  | `get_s3_client()` | — | `boto3.client` | Creates an S3 client configured for the current environment (MinIO in development). |
  | `upload_image(file_bytes, content_type, folder)` | `bytes, str, str` | `str` | Uploads an image to S3 with a UUID-based key. Returns the public URL. |
  | `delete_image(image_url)` | `str` | `bool` | Deletes an image from S3 by its URL. Returns `True` on success, `False` on error. |
  
  ---
  
  ### 3.9 API Routes (v1)
  
  **Router aggregation:** `backend/app/api/v1/router.py` — Mounts all sub-routers under `/api/v1`.
  
  | Prefix | Tags | Router File |
  |--------|------|-------------|
  | `/auth` | Authentication | `auth.py` |
  | `/properties` | Properties | `properties.py` |
  | `/bookings` | Bookings | `bookings.py` |
  | (root) `/conversations`, `/messages` | Messaging | `messages.py` |
  | `/reviews` | Reviews | `reviews.py` |
  | `/memberships` | Memberships | `memberships.py` |
  | `/admin` | Admin | `admin.py` |
  
  #### Auth Routes — `backend/app/api/v1/auth.py`
  
  | Method | Path | Auth | Description |
  |--------|------|------|-------------|
  | `POST` | `/auth/register` | Public | Register a new user account. Returns `UserOut` (201). |
  | `POST` | `/auth/lo