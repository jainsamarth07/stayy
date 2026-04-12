# PROJECT REFERENCE
 
 > Auto-generated April 2026. Optimized for LLM consumption. App name: **StayNest** — commission-free rental platform.
 
 ---
 
 ## Stack & Config
 
 ### Backend
 | Layer | Tech |
 |---|---|
 | Framework | FastAPI ≥0.109, Python 3.14 |
 | ORM | SQLAlchemy 2.x async (`asyncpg`) |
 | DB | PostgreSQL (async engine, pool_size=20, max_overflow=10) |
 | Migrations | Alembic |
 | Auth | Dual: **BetterAuth sessions** (primary) + **JWT fallback** |
 | Password hashing | Argon2 (`argon2-cffi`) via passlib |
 | Async tasks | Celery + Redis (broker: db=1) |
 | Storage | S3-compatible (MinIO default) via boto3 |
 | Rate limiting | Redis-backed fixed-window (per-IP) |
 | Validation | Pydantic v2 + pydantic-settings |
 | HTTP client | httpx (tests) |
 
 ### Frontend
 | Layer | Tech |
 |---|---|
 | Framework | Next.js 15 (App Router), React 19, TypeScript 5 |
 | Auth | BetterAuth v1.5 client+server (`better-auth`) |
 | State | Zustand v4 |
 | HTTP | Axios v1 |
 | Forms | react-hook-form v7 + zod v3 |
 | Styles | Tailwind CSS v3, Nunito font |
 | Animation | framer-motion v12 |
 | Testing | Vitest v4 + @testing-library/react v16 |
 
 ### Key Config Files
 - `backend/.env.example` — canonical env var list
 - `backend/app/config.py` — `Settings(BaseSettings)`, loaded from `.env`
 - `frontend/.env.local` / `frontend/.env.example` — Next.js env
 - `docker-compose.yml` — services: `api`, `celery-worker`, `db` (postgres), `redis`, `minio`, `frontend`
 - `backend/alembic.ini` + `backend/alembic/` — DB migrations
 
 ---
 
 ## Project Structure
 
 ```
 .
 ├── backend/
 │ ├── app/
 │ │ ├── main.py # FastAPI app factory, lifespan, middleware
 │ │ ├── config.py # Settings (pydantic-settings, 12-factor)
 │ │ ├── database.py # Async engine, session factory, Base, get_db dep
 │ │ ├── dependencies.py # Auth deps: get_current_user, require_host, require_admin
 │ │ ├── api/v1/
 │ │ │ ├── router.py # Aggregates all sub-routers under /api/v1
 │ │ │ ├── auth.py # Register, login, refresh, profile, pw-change, forgot/reset
 │ │ │ ├── properties.py # Property CRUD, image upload, hourly config
 │ │ │ ├── bookings.py # Booking create/list/get/status/cancel
 │ │ │ ├── messages.py # Conversation + message CRUD
 │ │ │ ├── reviews.py # Review create, list by property/host
 │ │ │ ├── memberships.py # Plans, subscribe, cancel, payment webhook
 │ │ │ └── admin.py # Admin-only: users, properties, memberships, bookings, stats
 │ │ ├── models/
 │ │ │ ├── user.py # User, HostProfile
 │ │ │ ├── property.py # Property, PropertyImage, HourlyBookingConfig
 │ │ │ ├── booking.py # Booking, BookingStatus, BookingType enums
 │ │ │ ├── membership.py # Membership, PLAN_CONFIG, enums
 │ │ │ ├── review.py # Review
 │ │ │ ├── message.py # Conversation, Message
 │ │ │ └── betterauth.py # BetterAuthUser, BetterAuthSession (read-only, bridges auth)
 │ │ ├── schemas/
 │ │ │ ├── __init__.py # DecimalFloat type alias (Decimal → float in JSON)
 │ │ │ ├── user.py # UserRegister/Login/Out/Update, TokenResponse, HostProfileOut
 │ │ │ ├── property.py # PropertyCreate/Update/Out, HourlyConfig schemas
 │ │ │ ├── booking.py # BookingCreate/Out/StatusUpdate, PaginatedBookings
 │ │ │ ├── membership.py # MembershipOut/PlanOut/SubscribeRequest/WebhookPayload
 │ │ │ ├── message.py # ConversationCreate, MessageCreate/Out, PaginatedMessages
 │ │ │ └── review.py # ReviewCreate/Out, PaginatedReviews
 │ │ ├── services/
 │ │ │ ├── auth_service.py # register_user, authenticate_user, refresh_access_token
 │ │ │ ├── property_service.py # create/update/delete/search_properties, upload, hourly
 │ │ │ ├── booking_service.py # create_booking, list_bookings, update_booking_status
 │ │ │ ├── membership_service.py # subscribe, cancel, process_webhook, get_available_plans
 │ │ │ ├── message_service.py # start_conversation, list/get conversations, send/read messages
 │ │ │ ├── review_service.py # create_review, list_property_reviews, list_host_reviews
 │ │ │ └── upload_service.py # S3 upload via boto3
 │ │ ├── core/
 │ │ │ ├── security.py # hash_password, verify_password, create/decode JWT tokens
 │ │ │ ├── exceptions.py # NotFoundError, ForbiddenError, ConflictError, BadRequestError, UnauthorizedError, MembershipRequiredError
 │ │ │ ├── permissions.py # UserRole enum (USER/HOST/ADMIN)
 │ │ │ ├── rate_limiter.py # RateLimitMiddleware + rate_limit_check() helper
 │ │ │ ├── csrf.py # CSRFMiddleware (blocks cross-origin state mutations)
 │ │ │ ├── email.py # Email sending (console or SMTP backend)
 │ │ │ └── logging_config.py # Structured JSON logging setup
 │ │ └── tasks/
 │ │ ├── email_tasks.py # Celery tasks: send_welcome_email, booking notifications
 │ │ └── membership_tasks.py # Celery tasks: expire memberships, renewal reminders
 │ ├── tests/
 │ │ ├── conftest.py # pytest fixtures: SQLite test DB, async client, user/host/admin factories
 │ │ ├── test_auth.py # Unit: registration, login, token refresh, pw-change
 │ │ ├── test_auth_integration.py
 │ │ ├── test_properties.py # Unit: CRUD, image upload, hourly config
 │ │ ├── test_properties_integration.py
 │ │ ├── test_bookings.py # Unit: nightly/hourly create, status machine, overlap
 │ │ ├── test_bookings_integration.py
 │ │ ├── test_memberships.py # Unit: subscribe, cancel, webhook, plan limits
 │ │ ├── test_memberships_integration.py
 │ │ ├── test_messages.py # Unit: conversation + message flows
 │ │ ├── test_messages_integration.py
 │ │ ├── test_reviews.py # Unit: create review, list by property/host
 │ │ ├── test_reviews_integration.py
 │ │ ├── test_admin.py # Unit: admin endpoints
 │ │ ├── test_admin_integration.py
 │ │ ├── test_services_unit.py # Pure service-layer unit tests (no HTTP)
 │ │ └── test_upload.py # Upload endpoint tests
 │ ├── requirements.txt # Production deps
 │ ├── requirements-dev.txt # Test/lint deps (pytest-asyncio, aiosqlite, etc.)
 │ └── pyproject.toml # Tool config (ruff, mypy, pytest)
 ├── frontend/
 │ ├── src/
 │ │ ├── app/ # Next.js App Router pages
 │ │ │ ├── layout.tsx # Root layout (Nunito font, ClientProviders wrapper)
 │ │ │ ├── page.tsx # Home / landing page
 │ │ │ ├── globals.css # Tailwind base
 │ │ │ ├── client-providers.tsx # Wraps children with BetterAuth session sync + Zustand
 │ │ │ ├── auth/ # login, register, forgot-password pages
 │ │ │ ├── properties/ # listing browse + [id] detail
 │ │ │ ├── bookings/ # booking list + [id] detail
 │ │ │ ├── messages/ # conversations list + [id] thread
 │ │ │ ├── dashboard/ # host dashboard (listings, bookings, stats)
 │ │ │ ├── profile/ # user profile edit
 │ │ │ ├── admin/ # admin panel pages
 │ │ │ └── api/auth/[...all]/route.ts # BetterAuth catch-all API route
 │ │ ├── components/
 │ │ │ ├── layout/ # Navbar, Footer, Sidebar
 │ │ │ ├── property/ # PropertyCard, PropertyFilters, ImageUpload, HourlyConfig
 │ │ │ ├── ui/ # Button, Input, Modal, Badge, Spinner, etc. (shared primitives)
 │ │ │ └── providers/ # ProtectedRoute, SessionProvider
 │ │ ├── hooks/
 │ │ │ ├── index.ts # re-exports all hooks
 │ │ │ ├── use-async.ts # generic async state handler
 │ │ │ ├── use-debounce.ts
 │ │ │ ├── use-infinite-scroll.ts
 │ │ │ ├── use-click-outside.ts
 │ │ │ └── use-media-query.ts
 │ │ ├── lib/
 │ │ │ ├── api.ts # Axios instance + interceptors + typed API method groups
 │ │ │ ├── auth-client.ts # BetterAuth client (signIn/Up/Out, useSession)
 │ │ │ └── auth.ts # BetterAuth server config (DB pool, social providers, custom fields)
 │ │ ├── stores/
 │ │ │ ├── auth-store.ts # Zustand: user, sessionToken, isAuthenticated, setSession/logout
 │ │ │ ├── property-store.ts # Zustand: property search results, filters
 │ │ │ ├── booking-store.ts # Zustand: booking list cache
 │ │ │ └── ui-store.ts # Zustand: global UI state (modals, toasts)
 │ │ ├── types/index.ts # All TS interfaces matching backend Pydantic schemas
 │ │ └── middleware.ts # Next.js edge middleware — session cookie gating
 │ ├── package.json
 │ ├── next.config.js
 │ ├── tailwind.config.ts
 │ └── vitest.config.ts
 ├── docker-compose.yml
 ├── seed.sql # DB seed data
 └── setup_from_excel.py # Utility: recreate project files from Project_Files.xlsx
 ```
 
 ---
 
 ## Architecture & Data Flow
 
 ### Auth Flow (Dual-Auth Pattern)
 ```
 Browser → BetterAuth (Next.js /api/auth/*) → Writes: user table, session table (camelCase)
 Browser → API requests → Bearer: <session_token>
 FastAPI dependency (get_current_user):
  1. Try BetterAuth path: session table lookup → BetterAuthUser → bridge to/create users row
  2. Fallback: decode JWT → lookup users row
  3. Auto-create HostProfile if role=host|admin and none exists
 ```
 
 - BetterAuth runs **server-side in Next.js** and owns `user`/`session`/`account`/`verification` tables.
 - FastAPI reads those tables **read-only** to validate sessions.
 - The `users` table is the backend's own user table; bridged by email match.
 - `hashed_password = "!betterauth"` is a sentinel marking BetterAuth-managed accounts.
 
 ### Request Lifecycle
 ```
 Client → Next.js middleware (cookie gate) → Next.js page/API
 Client → Axios (attaches Bearer sessionToken from Zustand) → FastAPI
 FastAPI: RateLimitMiddleware → CSRFMiddleware → CORSMiddleware → Router
 Router → Auth dep (get_current_user) → Service layer → DB (async SQLAlchemy) → Response
 ```
 
 ### State Management (Frontend)
 - **BetterAuth** owns session lifecycle via `useSession()` hook
 - **`client-providers.tsx`** syncs BetterAuth session → Zustand `auth-store` on mount/change
 - **`auth-store`** exposes `sessionToken` → picked up by Axios request interceptor
 - `backendId` in `AuthUser` is the UUID from the backend `users` table (differs from BetterAuth's string ID)
 
 ### Booking State Machine
 ```
 PENDING → CONFIRMED | REJECTED | CANCELLED
 CONFIRMED → CANCELLED | COMPLETED
 COMPLETED, CANCELLED, REJECTED → (terminal)
 ```
 Overlap check uses `SELECT ... FOR UPDATE` on Postgres to prevent double-booking race conditions. Degrades gracefully for SQLite (tests).
 
 ### Membership & Listing Gate
 - Hosts need an **active, non-expired** `Membership` to create/manage properties.
 - `membership.max_listings` enforced at create time (`_count_host_listings` + cap check).
 - Plans: `basic` (5 listings, ₹2499), `pro` (25 listings, ₹6499), `premium` (∞, ₹16499).
 
 ---
 
 ## File-by-File Summary
 
 ### Backend
 
 **`app/main.py`**
 - **Purpose**: App factory (`create_app()`), lifespan (Redis init/teardown), CORS/CSRF/RateLimit middleware, global exception handlers, `/ping` + `/health` routes.
 - **Exports**: `app = create_app()`
 - **Key logic**: Redis unavailability → rate limiter no-ops gracefully. `/health` checks DB + Redis.
 
 **`app/config.py`**
 - **Purpose**: All settings loaded from env vars via pydantic-settings. `validate_secrets()` blocks startup in non-dev if placeholder secrets remain.
 - **Exports**: `settings: Settings`
 
 **`app/database.py`**
 - **Purpose**: Async SQLAlchemy engine, session factory, `Base`, `get_db` dependency.
 - **Exports**: `engine`, `async_session_factory`, `Base`, `get_db`
 - **Key logic**: `get_db` auto-commits on success, rolls back on exception.
 
 **`app/dependencies.py`**
 - **Purpose**: FastAPI auth dependencies. Dual-auth: BetterAuth sessions first, JWT fallback. Exports `get_current_user`, `require_host`, `require_admin`.
 - **Key logic**: BetterAuth → lazily creates `users` row on first API call. Auto-creates `HostProfile` for host/admin roles.
 
 **`app/core/security.py`**
 - **Exports**: `hash_password(pw)→str`, `verify_password(plain, hashed)→bool`, `create_access_token(data, expires_delta)→str`, `create_refresh_token(data)→str`, `decode_token(token)→dict|None`
 - **Key logic**: Argon2 hashing. JWT `type` claim: `"access"` or `"refresh"`. `password_changed_at` on User invalidates pre-rotation tokens.
 
 **`app/core/exceptions.py`**
 - **Exports**: `NotFoundError(404)`, `ForbiddenError(403)`, `ConflictError(409)`, `BadRequestError(400)`, `UnauthorizedError(401)`, `MembershipRequiredError(402)`
 
 **`app/core/rate_limiter.py`**
 - **Key logic**: Redis `INCR`+`EXPIRE` fixed-window. Global middleware: writes=30/min, reads=120/min. Per-endpoint `rate_limit_check(request, limit)` for tighter caps on auth routes.
 
 **`app/services/property_service.py`**
 - **Key logic**: `create_property` requires active membership + checks `max_listings` cap. `delete_property` sets `is_active=False` (soft delete). `search_properties` supports city/price/guests/hourly filters + pagination.
 
 **`app/services/booking_service.py`**
 - **Key logic**: Overlap detection via `FOR UPDATE` lock. Price calc: nightly = `price_per_night * nights`, hourly = `hourly_price * hours`. Cannot book own property. `update_booking_status` validates against `VALID_TRANSITIONS` state machine.
 
 **`app/services/membership_service.py`**
 - **Key logic**: `subscribe` upserts — finds existing row (unique constraint on `host_id`) and reactivates/switches rather than inserting. Webhook `process_webhook` updates by `payment_ref`.
 
 **`app/models/betterauth.py`**
 - **Purpose**: Read-only SQLAlchemy models for BetterAuth's `user` and `session` tables. Column names are camelCase (SQLAlchemy `mapped_column("camelCaseName", ...)` pattern).
 
 ### Frontend
 
 **`src/lib/api.ts`**
 - **Purpose**: Axios instance (baseURL=`NEXT_PUBLIC_API_URL`), request interceptor attaches Bearer token from Zustand, response interceptor redirects to `/auth/login` on 401. Exports typed API groups: `profileApi`, `propertyApi`, `bookingApi`, `messageApi`, `reviewApi`, `membershipApi`, `adminApi`.
 - **Exports**: `default api`, `getApiError(err)→string`, `profileApi`, `propertyApi`, `bookingApi`, etc.
 
 **`src/lib/auth-client.ts`**
 - **Purpose**: BetterAuth client (`createAuthClient`). Provides `signIn`, `signUp`, `signOut`, `useSession`.
 
 **`src/lib/auth.ts`**
 - **Purpose**: BetterAuth server instance. Connects to same PostgreSQL DB. Configures email/password auth, optional Google/GitHub OAuth, custom user fields (`role`, `phone`). Session expires in 7 days.
 
 **`src/stores/auth-store.ts`**
 - **Purpose**: Zustand auth state. `AuthUser` shape includes `backendId` (backend UUID). `setSession(user, token)` called by `client-providers.tsx` on session change.
 
 **`src/middleware.ts`**
 - **Purpose**: Edge middleware — allows public paths, checks BetterAuth session cookie, redirects unauthenticated users to login. Role enforcement delegated to `ProtectedRoute` component.
 
 ---
 
 ## Data Models & Types
 
 ### Backend SQLAlchemy Models
 
 ```python
 User: {id: UUID(pk), email: str(unique), hashed_password: str, full_name: str,
  phone: str|None, role: 'user'|'host'|'admin', is_active: bool,
  created_at: datetime, updated_at: datetime, password_changed_at: datetime|None}
 
 HostProfile: {id: UUID(pk), user_id: UUID(fk→users, unique), business_name: str|None,
  bio: str|None, phone_visible: bool, is_verified: bool,
  avg_rating: float, total_reviews: int, created_at: datetime}
 
 Property: {id: UUID(pk), host_id: UUID(fk→users), title: str, description: str,
  city: str, address: str, latitude: float|None, longitude: float|None,
  price_per_night: Decimal(10,2), max_guests: int, amenities: JSON|None,
  is_active: bool, hourly_enabled: bool, created_at, updated_at}
 
 PropertyImage: {id: UUID(pk), property_id: UUID(fk→properties), image_url: str,
  is_primary: bool, sort_order: int}
 
 HourlyBookingConfig: {id: UUID(pk), property_id: UUID(fk, unique), hourly_price: Decimal(10,2),
  min_hours: int, max_hours: int, available_from: time, available_to: time}
 
 Booking: {id: UUID(pk), property_id: UUID(fk), guest_id: UUID(fk→users),
  host_id: UUID(fk→users), check_in: datetime, check_out: datetime,
  total_price: Decimal(10,2), booking_type: 'nightly'|'hourly',
  hours: int|None, status: BookingStatus, created_at, updated_at}
 
 Membership: {id: UUID(pk), host_id: UUID(fk→host_profiles, unique), plan_type: 'basic'|'pro'|'premium',
  start_date: datetime, end_date: datetime, status: 'active'|'cancelled'|'expired'|'past_due',
  auto_renew: bool, payment_ref: str|None, amount: Decimal(10,2),
  max_listings: int, created_at, updated_at}
 
 Review: {id: UUID(pk), booking_id: UUID(fk, unique), property_id: UUID(fk),
  reviewer_id: UUID(fk→users), rating: Decimal(3,1), comment: str|None, created_at}
 
 Conversation: {id: UUID(pk), property_id: UUID(fk), guest_id: UUID(fk→users),
  host_id: UUID(fk→users), created_at, updated_at}
 
 Message: {id: UUID(pk), conversation_id: UUID(fk), sender_id: UUID(fk→users),
  content: str, message_type: 'text', is_read: bool, created_at}
 
 BetterAuthUser: {id: str(pk), name: str, email: str, emailVerified: bool,
  image: str|None, role: str, phone: str|None, createdAt, updatedAt}
 BetterAuthSession: {id: str(pk), userId: str(fk→user), token: str(unique),
  expiresAt: datetime, ipAddress: str|None, userAgent: str|None}
 ```
 
 ### Frontend TypeScript Types (`src/types/index.ts`)
 
 ```typescript
 User: {id, email, full_name, phone?, role: 'user'|'host'|'admin', is_active, created_at}
 AuthUser: {id, backendId: string|null, email, full_name, name, phone?, role, image?} // Zustand
 Property: {id, host_id, title, description, city, address, lat?, lng?,
  price_per_night, max_guests, amenities?, is_active, hourly_enabled,
  images: PropertyImage[], hourly_config?, created_at, updated_at, host_name?}
 PropertyImage: {id, image_url, is_primary, sort_order}
 HourlyBookingConfig: {id, hourly_price, min_hours, max_hours, available_from, available_to}
 Booking: {id, property_id, guest_id, host_id, check_in, check_out, total_price,
  booking_type: 'nightly'|'hourly', hours?, status, created_at, updated_at,
  property_title?, guest_name?}
 Conversation: {id, property_id, guest_id, host_id, property_title?, other_party_name?,
  created_at, updated_at, last_message?, unread_count}
 Message: {id, conversation_id, sender_id, content, message_type: 'text', is_read, created_at}
 Review: {id, booking_id, property_id, reviewer_id, rating, comment?, created_at}
 Membership: {id, plan_type, start_date, end_date, status, auto_renew, amount, max_listings}
 HostProfile: {id, user_id, business_name?, bio?, phone_visible, is_verified, avg_rating, total_reviews}
 ```
 
 ### Membership Plan Config (hardcoded in `models/membership.py`)
 ```python
 PLAN_CONFIG = {
  'basic': {price: 2499.00, max_listings: 5, label: 'Basic'},
  'pro': {price: 6499.00, max_listings: 25, label: 'Pro'},
  'premium': {price: 16499.00, max_listings: 999999, label: 'Premium'},
 }
 ```
 
 ---
 
 ## API & Interfaces
 
 All routes prefixed `/api/v1`. Auth via `Authorization: Bearer <token>`.
 
 ### Auth — `/api/v1/auth`
 | Method | Path | Auth | Body/Params | Returns |
 |---|---|---|---|---|
 | POST | `/register` | — | `{email, password, full_name, phone?, role:'user'\|'host'}` | `UserOut` 201 |
 | POST | `/login` | — | `{email, password}` | `TokenResponse` |
 | POST | `/refresh` | — | `{refresh_token}` | `TokenResponse` |
 | GET | `/me` | ✓ | — | `UserOut` |
 | PUT | `/me` | ✓ | `{full_name?, phone?}` | `UserOut` |
 | PUT | `/me/password` | ✓ | `{current_password, new_password}` | `{message}` |
 | POST | `/me/forgot-password` | — | `{email}` | `{message}` |
 | POST | `/me/reset-password` | — | `{token, new_password}` | `{message}` |
 
 ### Properties — `/api/v1/properties`
 | Method | Path | Auth | Body/Params | Returns |
 |---|---|---|---|---|
 | GET | `` | — | `?city&min_price&max_price&max_guests&hourly_available&host_id&page&page_size` | `{items:[PropertyOut], total, page, page_size}` |
 | GET | `/{id}` | — | — | `PropertyOut` |
 | POST | `` | host | `PropertyCreate` | `PropertyOut` 201 |
 | PUT | `/{id}` | host(owner) | `PropertyUpdate` | `PropertyOut` |
 | DELETE | `/{id}` | host(owner) | — | 204 |
 | POST | `/{id}/images` | host(owner) | `file` (multipart), `?is_primary` | `{image_url, is_primary}` 201 |
 | PUT | `/{id}/hourly` | host(owner) | `HourlyBookingConfigUpdate` | hourly config |
 
 ### Bookings — `/api/v1/bookings`
 | Method | Path | Auth | Body/Params | Returns |
 |---|---|---|---|---|
 | POST | `` | user | `{property_id, check_in, check_out, booking_type, hours?}` | `BookingOut` 201 |
 | GET | `` | user | `?page&page_size` | `PaginatedBookings` |
 | GET | `/{id}` | user(participant) | — | `BookingOut` |
 | PUT | `/{id}/status` | user(participant) | `{status}` | `BookingOut` |
 | POST | `/{id}/cancel` | user(participant) | — | `BookingOut` |
 
 ### Messaging
 | Method | Path | Auth | Returns |
 |---|---|---|---|
 | POST | `/conversations` | user | conversation dict 201 |
 | GET | `/conversations` | user | `{items, total, page, page_size}` |
 | GET | `/conversations/{id}` | user(participant) | conversation detail dict |
 | GET | `/conversations/{id}/messages` | user(participant) | `PaginatedMessages` |
 | POST | `/conversations/{id}/messages` | user(participant) | `MessageOut` 201 |
 | PUT | `/messages/{id}/read` | user(participant) | `MessageOut` |
 
 ### Reviews — `/api/v1/reviews`
 | Method | Path | Auth | Returns |
 |---|---|---|---|
 | POST | `` | user | `ReviewOut` 201 |
 | GET | `/property/{id}` | — | `PaginatedReviews` |
 | GET | `/host` | host | `PaginatedReviews` |
 
 ### Memberships — `/api/v1/memberships`
 | Method | Path | Auth | Returns |
 |---|---|---|---|
 | GET | `/plans` | — | `[MembershipPlanOut]` |
 | POST | `/subscribe` | host | `MembershipOut` 201 |
 | GET | `/current` | host | `MembershipOut` |
 | PUT | `/cancel` | host | `MembershipOut` |
 | POST | `/webhook` | header:`x-webhook-secret` | `{status:'processed'}` |
 
 ### Admin — `/api/v1/admin` (requires `role=admin`)
 | Method | Path | Returns |
 |---|---|---|
 | GET | `/users` | paginated users |
 | GET | `/properties` | paginated properties (with host_name) |
 | GET | `/memberships` | paginated memberships |
 | GET | `/bookings` | paginated bookings (with property_title, guest_name) |
 | GET | `/stats` | `{total_users, total_properties, total_bookings, active_memberships}` |
 | PUT | `/users/{id}/role` | updated user |
 | PUT | `/users/{id}/active` | updated user |
 | DELETE | `/properties/{id}` | 204 |
 
 ### Health
 - `GET /ping` → `{status:'ok'}` (no deps)
 - `GET /health` → `{status:'ok', db:bool, redis:bool}`
 
 ### BetterAuth (Next.js, not FastAPI)
 - `POST /api/auth/sign-in/email`
 - `POST /api/auth/sign-up/email`
 - `POST /api/auth/sign-out`
 - `GET /api/auth/session`
 - OAuth callbacks: `/api/auth/callback/google`, `/api/auth/callback/github`
 
 ---
 
 ## Constants & Config Values
 
 ### Backend Env Vars (`backend/app/config.py`)
 ```
 APP_ENV=development|staging|production
 DEBUG=false
 DATABASE_URL=postgresql+asyncpg://user:pass@host:5432/db
 DATABASE_ECHO=false
 REDIS_URL=redis://localhost:6379/0
 CELERY_BROKER_URL=redis://localhost:6379/1
 JWT_SECRET_KEY=<64-byte hex> # MUST change in non-dev
 JWT_ALGORITHM=HS256
 JWT_ACCESS_TOKEN_EXPIRE_MINUTES=30
 JWT_REFRESH_TOKEN_EXPIRE_DAYS=7
 S3_ENDPOINT_URL=http://localhost:9000
 S3_PUBLIC_URL=http://localhost:9000
 S3_ACCESS_KEY_ID=minioadmin
 S3_SECRET_ACCESS_KEY=minioadmin
 S3_BUCKET_NAME=staynest-images
 S3_REGION=us-east-1
 CORS_ORIGINS=["http://localhost:3000"]
 WEBHOOK_SECRET=<secret> # MUST change in non-dev
 EMAIL_BACKEND=console|smtp
 SMTP_HOST, SMTP_PORT=587, SMTP_TLS=true, SMTP_USER, SMTP_PASSWORD
 SMTP_FROM=noreply@staynest.com
 RATE_LIMIT_PER_MINUTE=60
 ```
 
 ### Frontend Env Vars
 ```
 NEXT_PUBLIC_API_URL=http://localhost:8000/api/v1
 NEXT_PUBLIC_APP_URL=http://localhost:3000
 DATABASE_URL=postgresql://... # BetterAuth server-side DB connection
 GOOGLE_CLIENT_ID / GOOGLE_CLIENT_SECRET # optional OAuth
 GITHUB_CLIENT_ID / GITHUB_CLIENT_SECRET # optional OAuth
 ```
 
 ### Rate Limits
 - Global middleware: GET/HEAD=120/min, POST/PUT/PATCH/DELETE=30/min (per IP)
 - `/auth/register`: 10/min; `/auth/login`: 20/min
 
 ### Image Upload Constraints
 - Max size: 10 MB per image
 - Allowed MIME: `image/jpeg`, `image/png`, `image/webp`, `image/gif`
 
 ---
 
 ## Known Patterns & Conventions
 
 ### Naming
 - Backend: `snake_case` everywhere; router files plural (`properties.py`), model files singular (`property.py`)
 - Frontend: `kebab-case` files, `PascalCase` components, `camelCase` functions
 - All UUIDs as `string` in frontend, `uuid.UUID` in backend schemas
 
 ### Pagination Pattern
 All list endpoints return: `{items:[...], total:int, page:int, page_size:int}`
 Default: `page=1`, `page_size=20`. Max `page_size=100` (messages: 200).
 
 ### Service Layer Pattern
 - Routes are thin: validate input → call service → serialize output
 - Services own all business logic; raise from `app.core.exceptions`
 - Services receive `db: AsyncSession` — DB session never passed to schemas
 
 ### `DecimalFloat` Pattern
 All `Decimal` fields in response schemas use `DecimalFloat = Annotated[Decimal, PlainSerializer(float)]` to serialize as JSON number (not string).
 
 ### Auth Dependency Chain
 ```python
 get_current_user → tries BetterAuth then JWT → returns User or raises 401
 require_host → get_current_user + role in ('host','admin') or 403
 require_admin → get_current_user + role == 'admin' or 403
 ```
 
 ### Test Setup
 - Unit tests: SQLite in-memory (`sqlite+aiosqlite:///./test.db`), recreated per test via `autouse` fixture
 - `conftest.py` provides: `db_session`, `client` (AsyncClient + dependency overrides), `user_factory`, `host_factory`, `admin_factory` fixtures
 - Auth injected directly via dependency override — bypasses real JWT/BetterAuth in all unit tests
 - Integration test files (`test_*_integration.py`) use separate fixtures/DB
 
 ### Celery Task Resilience
 All `task.delay()` calls inside services are wrapped in `try/except` — task queue failure never blocks the HTTP response.
 
 ### Soft Delete
 Properties use `is_active=False` (never hard-deleted via API). DB-level cascade deletes cascade from `properties` → `bookings`, `reviews`, `messages`, `images`.
 
 ---
 
 ## Gotchas & Non-obvious Details
 
 1. **Dual Auth Identity Mismatch**: `AuthUser.id` = BetterAuth string ID; `AuthUser.backendId` = UUID from backend `users` table. Always use `backendId` for API-level filtering (booking ownership, property host_id comparisons, etc.).
 
 2. **BetterAuth Table Naming**: BetterAuth tables use camelCase column names (`emailVerified`, `createdAt`, `userId`). SQLAlchemy models in `betterauth.py` map them with `mapped_column("camelCaseName", ...)`. Do NOT rename these columns.
 
 3. **Lazy HostProfile Creation**: When a BetterAuth `role=host` user hits any authenticated backend endpoint for the first time, `_auth_via_betterauth()` auto-creates their `HostProfile`. They still need an active `Membership` before creating listings.
 
 4. **Membership Unique Constraint**: `memberships.host_id` has a unique constraint. Never `INSERT` a new membership — always use `membership_service.subscribe()` which upserts the existing row.
 
 5. **Password Sentinel**: BetterAuth-managed users have `hashed_password = "!betterauth"`. The change-password endpoint checks `hashed_password.startswith("!")` and rejects with 400. Never try to `verify_password()` against this value.
 
 6. **SQLite FOR UPDATE Guard**: Booking overlap check uses `SELECT ... FOR UPDATE` but degrades for SQLite via `if "sqlite" not in str(db.bind.url)`. Replicate this guard if adding other `FOR UPDATE` queries.
 
 7. **`password_changed_at` JWT Invalidation**: After password change, JWT `iat` is compared to `password_changed_at`. JWTs issued before the change are rejected. BetterAuth sessions are unaffected.
 
 8. **CORS Allowed Headers**: Only `Authorization`, `Content-Type`, `X-Webhook-Secret` are in allowed headers. Adding custom headers requires updating `main.py` CORS config or preflight will fail.
 
 9. **Redis Unavailability is Silent**: Both global middleware and `rate_limit_check()` silently no-op when Redis is unavailable. Rate limiting is best-effort only.
 
 10. **Hourly Price Calculation**: `hourly`: uses `HourlyBookingConfig.hourly_price * hours`. Requires `prop.hourly_enabled=True` and a config row. `nightly`: `price_per_night * (check_out - check_in).days`, min 1 night enforced.
 
 11. **Middleware Role Gap**: Next.js edge middleware only checks for presence of a session cookie (no DB lookup possible at edge). Role enforcement (`host`/`admin` routes) is done client-side by `ProtectedRoute` component — there is no server-side role gate in middleware.
 
 12. **Missing `DecimalFloat` = String Bug**: If a new response schema uses plain `Decimal` instead of `DecimalFloat`, Pydantic will serialize it as a string (e.g., `"24.99"` instead of `24.99`). Always import and use `DecimalFloat` from `app.schemas`.