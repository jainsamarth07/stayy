# StayNest — Developer & API Documentation
  
  > Comprehensive reference covering every module, API endpoint, data model,
  > configuration option, and operational procedure for the StayNest rental
  > marketplace platform.
  
  ---
  
  ## Table of Contents
  
  1. [Project Overview](#1-project-overview)
  2. [Repository Structure](#2-repository-structure)
  3. [Backend Architecture](#3-backend-architecture)
  4. [API Reference](#4-api-reference)
  5. [Database Schema & ERD](#5-database-schema--erd)
  6. [Frontend Architecture](#6-frontend-architecture)
  7. [Authentication & Authorization](#7-authentication--authorization)
  8. [State Management](#8-state-management)
  9. [Testing Strategy](#9-testing-strategy)
  10. [Configuration & Environment](#10-configuration--environment)
  11. [Docker & Infrastructure](#11-docker--infrastructure)
  12. [CI/CD Pipeline](#12-cicd-pipeline)
  13. [Coding Conventions](#13-coding-conventions)
  14. [Troubleshooting](#14-troubleshooting)
  15. [Glossary](#15-glossary)
  
  ---
  
  ## 1. Project Overview
  
  **StayNest** is a commission-free, two-sided rental marketplace. Hosts pay a
  monthly membership fee and keep 100 % of their booking revenue. Guests browse,
  book, and message hosts without extra platform fees.
  
  ### Business Model
  
  | Tier | Price | Max Listings |
  | ------- | ---------- | ------------ |
  | Basic | $29 / mo | 5 |
  | Pro | $79 / mo | 25 |
  | Premium | $199 / mo | Unlimited |
  
  ### Key User Flows
  
  ```
  Guest: Browse → Search/Filter → View Property → Book or Contact Host → Message Host → Review
  Host: Register → Subscribe → Create Listings → Manage Bookings → Respond to Messages → View Reviews
  Admin: Platform KPIs → Manage Users → Moderate Properties → View All Bookings → Manage Memberships
  ```
  
  ---
  
  ## 2. Repository Structure
  
  ```
  staynest/
  ├── .github/
  │ └── workflows/
  │ └── ci.yml # GitHub Actions CI pipeline
  ├── docs/
  │ └── ARCHITECTURE.md # High-level architecture diagrams
  ├── backend/
  │ ├── app/
  │ │ ├── __init__.py
  │ │ ├── main.py # FastAPI application factory
  │ │ ├── config.py # Pydantic Settings (12-factor)
  │ │ ├── database.py # Async SQLAlchemy engine & session
  │ │ ├── dependencies.py # Dependency injection (auth, DB session)
  │ │ ├── models/ # SQLAlchemy ORM models (11 tables)
  │ │ │ ├── __init__.py
  │ │ │ ├── user.py # User + HostProfile
  │ │ │ ├── property.py # Property + PropertyImage + HourlyBookingConfig
  │ │ │ ├── booking.py # Booking + BookingStatus/Type enums
  │ │ │ ├── membership.py # Membership + Plans + Status enum
  │ │ │ ├── message.py # Conversation + Message
  │ │ │ └── review.py # Review
  │ │ ├── schemas/ # Pydantic v2 request/response schemas
  │ │ │ ├── __init__.py
  │ │ │ ├── user.py # UserRegister, UserLogin, UserOut, etc.
  │ │ │ ├── property.py # PropertyCreate, PropertyUpdate, PropertyOut
  │ │ │ ├── booking.py # BookingCreate, BookingOut, PaginatedBookings
  │ │ │ ├── membership.py # MembershipPlanOut, MembershipOut
  │ │ │ ├── message.py # ConversationCreate, MessageOut
  │ │ │ └── review.py # ReviewCreate, ReviewOut, PaginatedReviews
  │ │ ├── api/v1/ # FastAPI route handlers
  │ │ │ ├── auth.py # POST register, login, refresh, GET me
  │ │ │ ├── properties.py # CRUD, search, image upload, hourly config
  │ │ │ ├── bookings.py # CRUD, status updates, cancellation
  │ │ │ ├── messages.py # Conversations, messages, mark-read
  │ │ │ ├── reviews.py # Create review, list by property
  │ │ │ ├── memberships.py # Plans, subscribe, current, cancel
  │ │ │ └── admin.py # Admin-only CRUD for all resources
  │ │ ├── services/ # Business logic layer
  │ │ │ ├── auth_service.py # Registration, login, token refresh
  │ │ │ ├── property_service.py# Property CRUD, search, images
  │ │ │ ├── booking_service.py # Booking creation, status transitions
  │ │ │ ├── message_service.py # Conversations & message delivery
  │ │ │ ├── review_service.py # Review validation & storage
  │ │ │ ├── membership_service.py # Subscription management
  │ │ │ └── upload_service.py # S3/MinIO image upload
  │ │ ├── core/ # Cross-cutting concerns
  │ │ │ ├── security.py # JWT encode/decode, password hashing
  │ │ │ ├── permissions.py # Role guard decorators
  │ │ │ ├── exceptions.py # Custom HTTP exceptions
  │ │ │ └── rate_limit.py # Redis-backed rate limiter
  │ │ └── tasks/ # Celery background tasks
  │ │ ├── celery_app.py # Celery instance configuration
  │ │ ├── email_tasks.py # Welcome/confirmation emails
  │ │ └── booking_tasks.py # Booking reminders, auto-expiry
  │ ├── alembic/ # Database migration scripts
  │ │ ├── env.py
  │ │ └── versions/
  │ │ └── 0001_initial.py # Creates all 11 tables
  │ ├── tests/ # Pytest test suite
  │ │ ├── conftest.py # Shared fixtures, async DB setup
  │ │ ├── test_auth.py
  │ │ ├── test_properties.py
  │ │ ├── test_bookings.py
  │ │ ├── test_messages.py
  │ │ ├── test_reviews.py
  │ │ ├── test_memberships.py
  │ │ ├── test_admin.py
  │ │ └── test_upload.py
  │ ├── Dockerfile
  │ ├── requirements.txt
  │ ├── requirements-dev.txt
  │ ├── pyproject.toml
  │ ├── alembic.ini
  │ └── .env.example
  ├── frontend/
  │ ├── src/
  │ │ ├── app/ # Next.js 14 App Router pages
  │ │ │ ├── layout.tsx # Root layout (metadata, global styles)
  │ │ │ ├── page.tsx # Landing / home page
  │ │ │ ├── loading.tsx # Global loading spinner
  │ │ │ ├── not-found.tsx # 404 page
  │ │ │ ├── error.tsx # Error boundary
  │ │ │ ├── client-providers.tsx # AuthProvider + ToastContainer shell
  │ │ │ ├── auth/ # Login, Register, Forgot/Reset password
  │ │ │ ├── properties/ # Browse, Search, Property detail
  │ │ │ ├── bookings/ # Guest booking list & detail
  │ │ │ ├── messages/ # Conversation inbox & chat
  │ │ │ ├── profile/ # User profile page
  │ │ │ ├── dashboard/ # Host dashboard (properties, bookings, reviews, membership)
  │ │ │ └── admin/ # Admin panel (users, properties, bookings, memberships)
  │ │ ├── components/
  │ │ │ ├── ui/ # Button, Input, Modal, Toast, Tabs, etc.
  │ │ │ ├── layout/ # Navbar, Footer, Sidebar
  │ │ │ ├── property/ # PropertyCard, SearchBar, ImageGallery, StarRating
  │ │ │ └── providers/ # AuthProvider, ProtectedRoute
  │ │ ├── hooks/ # useDebounce, useInfiniteScroll, useAsync, etc.
  │ │ ├── stores/ # Zustand stores (auth, property, booking, ui)
  │ │ ├── lib/api.ts # Axios client with JWT interceptors
  │ │ ├── types/index.ts # TypeScript interfaces
  │ │ └── middleware.ts # Edge middleware for route protection
  │ ├── src/__tests__/ # Vitest + React Testing Library tests
  │ ├── Dockerfile
  │ ├── package.json
  │ ├── tsconfig.json
  │ ├── next.config.js
  │ ├── tailwind.config.ts
  │ ├── vitest.config.ts
  │ └── .env.example
  ├── docker-compose.yml # Full-stack dev orchestration (6 services)
  ├── README.md # Quick-start guide
  ├── DOCUMENTATION.md # ← This file
  └── .gitignore
  ```
  
  ---
  
  ## 3. Backend Architecture
  
  ### Layered Design
  
  ```
  Route Handlers (api/v1/) ← Thin HTTP layer: parse request, call service, return response
  │
  Service Layer (services/) ← Business logic, validation rules, transactions
  │
  ORM Models (models/) ← Data access via SQLAlchemy async sessions
  │
  PostgreSQL 16 ← Persistent storage
  ```
  
  ### Application Factory
  
  `app/main.py` exposes `create_app()` which:
  
  1. Reads config from `app/config.py` (Pydantic `BaseSettings`, 12-factor env).
  2. Registers CORS middleware with configurable allowed origins.
  3. Includes all v1 route modules under the `/api/v1` prefix.
  4. Exposes a `/health` readiness check that pings the database.
  
  ### Dependency Injection
  
  | Dependency | Location | Purpose |
  | ------------------ | --------------------- | ----------------------------------------- |
  | `get_db` | `dependencies.py` | Yields an async SQLAlchemy `AsyncSession` |
  | `get_current_user` | `dependencies.py` | Decodes JWT, loads `User` from DB |
  | `require_host` | `core/permissions.py` | Raises `403` if user is not a host |
  | `require_admin` | `core/permissions.py` | Raises `403` if user is not an admin |
  
  ### Background Tasks (Celery)
  
  | Task | Trigger | Description |
  | ----------------------------- | ---------------------- | ---------------------------------- |
  | `send_welcome_email` | User registration | Sends a welcome email to new user |
  | `send_booking_confirmation` | Booking confirmed | Email to guest + host |
  | `expire_pending_bookings` | Scheduled (periodic) | Auto-cancel bookings after 48 h |
  
  ---
  
  ## 4. API Reference
  
  ### Authentication
  
  | Method | Path | Body / Params | Response | Auth |
  | ------ | -------------------------- | ------------------------------------------- | -------------------- | ------- |
  | POST | `/api/v1/auth/register` | `{ email, password, full_name, role }` | `UserOut` | Public |
  | POST | `/api/v1/auth/login` | `{ email, password }` | `TokenResponse` | Public |
  | POST | `/api/v1/auth/refresh` | `{ refresh_token }` | `TokenResponse` | Public |
  | GET | `/api/v1/auth/me` | — | `UserOut` | Bearer |
  | PUT | `/api/v1/auth/me` | `{ full_name?, phone? }` | `UserOut` | Bearer |
  
  ### Properties
  
  | Method | Path | Description | Auth |
  | ------ | ----------------------------------------- | ------------------------------ | ---------- |
  | GET | `/api/v1/properties` | Search / list with filters | Public |
  | GET | `/api/v1/properties/{id}` | Get single property | Public |
  | POST | `/api/v1/properties` | Create listing | Host |
  | PUT | `/api/v1/properties/{id}` | Update listing | Host/Owner |
  | DELETE | `/api/v1/properties/{id}` | Soft-delete listing | Host/Owner |
  | POST | `/api/v1/properties/{id}/images` | Upload image (multipart) | Host/Owner |
  | PUT | `/api/v1/properties/{id}/hourly` | Configure hourly settings | Host/Owner |
  
  **Search query params:** `location`, `check_in`, `check_out`, `guests`, `min_price`, `max_price`, `property_type`, `bedrooms`, `amenities`, `sort_by`, `page`, `page_size`
  
  ### Bookings
  
  | Method | Path | Description | Auth |
  | ------ | ----------------------------------- | ---------------------- | ----- |
  | POST | `/api/v1/bookings` | Create booking | User |
  | GET | `/api/v1/bookings` | List user's bookings | User |
  | GET | `/api/v1/bookings/{id}` | Booking detail | Owner |
  | PUT | `/api/v1/bookings/{id}/status` | Update status | Host |
  | POST | `/api/v1/bookings/{id}/cancel` | Guest cancellation | Guest |
  
  **Booking Statuses:** `pending` → `confirmed` → `completed` | `cancelled` | `rejected`
  
  ### Messaging
  
  | Method | Path | Description | Auth |
  | ------ | ----------------------------------------------- | ----------------------- | ----- |
  | POST | `/api/v1/conversations` | Start conversation | User |
  | GET | `/api/v1/conversations` | List conversations | User |
  | GET | `/api/v1/conversations/{id}/messages` | Get messages (paginated)| User |
  | POST | `/api/v1/conversations/{id}/messages` | Send message | User |
  | PUT | `/api/v1/messages/{id}/read` | Mark as read | User |
  
  ### Reviews
  
  | Method | Path | Description | Auth |
  | ------ | ------------------------------------------ | ------------------------- | ------ |
  | POST | `/api/v1/reviews` | Create review (1-5 ★) | Guest |
  | GET | `/api/v1/reviews/property/{id}` | Reviews for property | Public |
  
  ### Memberships
  
  | Method | Path | Description | Auth |
  | ------ | ---------------------------------- | -------------------------- | ------ |
  | GET | `/api/v1/memberships/plans` | List available plans | Public |
  | POST | `/api/v1/memberships/subscribe` | Subscribe to plan | Host |
  | GET | `/api/v1/memberships/current` | Current subscription | Host |
  | PUT | `/api/v1/memberships/cancel` | Cancel subscription | Host |
  
  ### Admin
  
  | Method | Path | Description | Auth |
  | ------ | ---------------------------------- | ---------------------------------- | ----- |
  | GET | `/api/v1/admin/stats` | Platform-wide KPIs | Admin |
  | GET | `/api/v1/admin/users` | List all users | Admin |
  | PUT | `/api/v1/admin/users/{id}/ban` | Ban / unban user | Admin |
  | GET | `/api/v1/admin/properties` | List all properties | Admin |
  | DELETE | `/api/v1/admin/properties/{id}` | Remove property | Admin |
  | GET | `/api/v1/admin/bookings` | List all bookings | Admin |
  | GET | `/api/v1/admin/memberships` | List all memberships | Admin |
  
  ### Common Response Shapes
  
  ```jsonc
  // Paginated list
  {
  "items": [ ... ],
  "total": 42,
  "page": 1,
  "page_size": 20
  }
  
  // Error
  {
  "detail": "Property not found"
  }
  ```
  
  ---
  
  ## 5. Database Schema & ERD
  
  ### Tables (10)
  
  | Table | Key Columns | Relations |
  | ------------------------ | -------------------------------------------------------- | -------------------------------- |
  | `users` | id (UUID PK), email (unique), password_hash, role, … | → host_profiles, bookings, … |
  | `host_profiles` | id, user_id (FK→users), business_name, bio, … | 1:1 with users |
  | `memberships` | id, host_id (FK→users), plan_type, status, dates, … | N:1 with users |
  | `properties` | id, host_id (FK→users), title, city, price_per_night, … | → images, hourly_configs |
  | `property_images` | id, property_id (FK→properties), image_url, is_primary | N:1 with properties |
  | `hourly_booking_configs` | id, property_id (FK→properties, unique), hourly_price, … | 1:1 with properties |
  | `bookings` | id, property_id, guest_id, host_id, status, total_price | N:1 with properties, users |
  | `conversations` | id, property_id, guest_id, host_id | N:1 with properties, users |
  | `messages` | id, conversation_id, sender_id, content, is_read | N:1 with conversations, users |
  | `reviews` | id, booking_id, property_id, reviewer_id, rating, … | N:1 with bookings, properties |
  
  ### Entity Relationship Diagram
  
  ```
  users ─────┬──── 1:1 ──── host_profiles
  │
  ├──── 1:N ──── memberships
  │
  ├──── 1:N ──── properties ──┬── 1:N ── property_images
  │ ├── 1:1 ── hourly_booking_configs
  │ ├── 1:N ── bookings ── 1:1 ── reviews
  │ └── 1:N ── conversations ── 1:N ── messages
  │
  ├──── 1:N ──── bookings (as guest)
  ├──── 1:N ──── messages (as sender)
  └──── 1:N ──── reviews (as reviewer)
  ```
  
  ### Cascade Rules
  
  - Deleting a `user` cascades to `host_profiles`, `properties`, `bookings`, `conversations`, `reviews`.
  - Deleting a `property` cascades to `property_images`, `hourly_booking_configs`, `bookings`, `conversations`.
  - Deleting a `conversation` cascades to its `messages`.
  
  ---
  
  ## 6. Frontend Architecture
  
  ### Technology Stack
  
  | Concern | Library / Tool |
  | ------------------- | --------------------------------- |
  | Framework | Next.js 14 (App Router) |
  | Language | TypeScript (strict mode) |
  | Styling | Tailwind CSS 3.4 |
  | State Management | Zustand 4.5 |
  | HTTP Client | Axios 1.6 (with interceptors) |
  | Form Handling | react-hook-form 7.50 + Zod 3.22 |
  | Date Utilities | date-fns 3.3 |
  | Testing | Vitest + React Testing Library |
  | Linting / Formatting| ESLint 8 + Prettier |
  
  ### Routing (App Router)
  
  | Route Pattern | Page Component | Auth Required |
  | -------------------------------------------- | ------------------------- | ------------- |
  | `/` | `HomePage` | No |
  | `/auth/login` | `LoginPage` | No |
  | `/auth/register` | `RegisterPage` | No |
  | `/auth/forgot-password` | `ForgotPasswordPage` | No |
  | `/auth/reset-password` | `ResetPasswordPage` | No |
  | `/properties` | `PropertiesPage` | No |
  | `/properties/[id]` | `PropertyDetailPage` | No |
  | `/bookings` | `BookingsPage` | Yes |
  | `/bookings/[id]` | `BookingDetailPage` | Yes |
  | `/messages` | `MessagesPage` | Yes |
  | `/messages/[id]` | `ConversationPage` | Yes |
  | `/profile` | `ProfilePage` | Yes |
  | `/dashboard` | `DashboardPage` | Host |
  | `/dashboard/properties` | `DashboardPropertiesPage` | Host |
  | `/dashboard/properties/new` | `NewPropertyPage` | Host |
  | `/dashboard/properties/[id]/edit` | `EditPropertyPage` | Host |
  | `/dashboard/bookings` | `DashboardBookingsPage` | Host |
  | `/dashboard/reviews` | `DashboardReviewsPage` | Host |
  | `/dashboard/membership` | `MembershipPage` | Host |
  | `/admin` | `AdminDashboardPage` | Admin |
  | `/admin/users` | `AdminUsersPage` | Admin |
  | `/admin/properties` | `AdminPropertiesPage` | Admin |
  | `/admin/bookings` | `AdminBookingsPage` | Admin |
  | `/admin/memberships` | `AdminMembershipsPage` | Admin |
  
  ### Component Library
  
  All UI primitives live in `src/components/ui/`:
  
  | Component | Props / Features |
  | ------------ | ------------------------------------------------------------------ |
  | `Button` | 5 variants (primary, secondary, outline, ghost, danger), 3 sizes, loading state |
  | `Input` | Label, error, helper text, left/right icons, forwardRef |
  | `Modal` | Backdrop click-to-close, 4 size presets, accessible close button |
  | `Toast` | Global toast API (`toast.success/error/info/warning`), auto-dismiss|
  | `Tabs` | Horizontal tabs with optional counts |
  | `Pagination` | Page numbers with ellipsis, Previous/Next |
  | `EmptyState` | Icon, title, description, CTA slot |
  | `Badge` | 5 colour variants |
  | `Avatar` | Image or initials fallback, 4 sizes |
  | `Spinner` | Animated SVG, 3 sizes |
  | `Card` | Rounded, optional hover shadow |
  | `Select` | Styled `<select>` with label and error |
  | `Textarea` | Styled `<textarea>` with label and error, forwardRef |
  
  ### Custom Hooks
  
  | Hook | Purpose |
  | ------------------- | ------------------------------------------------ |
  | `useDebounce(val)` | Debounce a fast-changing value (default 400 ms) |
  | `useInfiniteScroll` | Trigger callback when sentinel enters viewport |
  | `useMediaQuery` | Subscribe to a CSS media query |
  | `useClickOutside` | Detect clicks outside a ref element |
  | `useAsync` | Wrap async fn with loading/success/error tracking|
  
  ---
  
  ## 7. Authentication & Authorization
  
  ### Token Flow
  
  ```
  Login ─► API returns { access_token (30 min), refresh_token (7 days) }
  ─► Both stored in localStorage
  ─► Axios interceptor attaches Bearer token on every request
  ─► On 401, interceptor attempts silent refresh with refresh_token
  ─► On refresh failure, user redirected to /auth/login
  ```
  
  ### Role-based Access
  
  | Role | Can |
  | ------- | -------------------------------------------------------- |
  | `user` | Browse, book, send messages, write reviews |
  | `host` | Everything a user can + create listings, manage bookings, manage messages |
  | `admin` | Full platform access including user management |
  
  ### Middleware
  
  `src/middleware.ts` runs at the Edge (Next.js) and enforces:
  
  - Public paths pass through without auth check.
  - All other routes require `access_token` cookie; otherwise redirect to `/auth/login?redirect=<path>`.
  
  ---
  
  ## 8. State Management
  
  Four Zustand stores manage client-side state:
  
  | Store | Key State |
  | ------------------- | --------------------------------------------------- |
  | `useAuthStore` | `user`, `isAuthenticated`, `isLoading`, `logout()` |
  | `usePropertyStore` | `properties[]`, `filters`, `page`, `totalPages` |
  | `useBookingStore` | `bookings[]`, `activeTab`, `selectedBooking` |
  | `useUIStore` | `sidebarOpen`, `mobileMenuOpen` |
  
  All stores use the `create` pattern from Zustand and are consumed directly in
  components without providers.
  
  ---
  
  ## 9. Testing Strategy
  
  ### Backend (pytest)
  
  | File | Focus |
  | --------------------- | ---------------------------------------- |
  | `conftest.py` | Async test DB, fixtures for all roles |
  | `test_auth.py` | Register, login, refresh, profile CRUD |
  | `test_properties.py` | Property CRUD, search, image upload |
  | `test_bookings.py` | Booking lifecycle & status transitions |
  | `test_messages.py` | Conversations & messages |
  | `test_reviews.py` | Review creation, duplicate prevention |
  | `test_memberships.py` | Subscribe, upgrade, cancel |
  | `test_admin.py` | Admin-only routes, user ban |
  | `test_upload.py` | S3 upload with mocked boto3 |
  
  **Command:** `cd backend && pytest --cov=app --cov-report=term-missing`
  
  ### Frontend (Vitest)
  
  | File | Focus |
  | --------------------------------- | ------------------------------ |
  | `button.test.tsx` | Variants, sizes, loading, click|
  | `input.test.tsx` | Label, error, icons, ref |
  | `modal.test.tsx` | Open/close, backdrop, a11y |
  | `index.test.tsx` | Badge, Avatar, Spinner, Card |
  | `use-debounce.test.ts` | Debounce timing |
  | `use-async.test.ts` | Loading/success/error states |
  | `auth-store.test.ts` | setUser, logout, isAuth |
  | `property-store.test.ts` | Filters, pagination, reset |
  
  **Command:** `cd frontend && npx vitest run --coverage`
  
  ### Coverage Targets
  
  - **≥ 80 % on all new / changed code** (enforced in CI).
  - **≥ 80 % repo-wide** as a trend target.
  
  ---
  
  ## 10. Configuration & Environment
  
  ### Backend `.env` Variables
  
  | Variable | Default / Example | Description |
  | --------------------------------- | ----------------------------------------------------------- | ------------------------------- |
  | `APP_ENV` | `development` | Environment name |
  | `DEBUG` | `true` | Enable debug logging |
  | `DATABASE_URL` | `postgresql+asyncpg://staynest:staynest_secret@localhost:5432/staynest` | Async PostgreSQL DSN |
  | `DATABASE_ECHO` | `false` | Log SQL statements |
  | `REDIS_URL` | `redis://localhost:6379/0` | Redis cache / rate-limit |
  | `JWT_SECRET_KEY` | `CHANGE-ME-use-openssl-rand-hex-64` | Must be random in production |
  | `JWT_ALGORITHM` | `HS256` | JWT signing algorithm |
  | `JWT_ACCESS_TOKEN_EXPIRE_MINUTES` | `30` | Access token lifetime |
  | `JWT_REFRESH_TOKEN_EXPIRE_DAYS` | `7` | Refresh token lifetime |
  | `S3_ENDPOINT_URL` | `http://localhost:9000` | MinIO / S3 endpoint |
  | `S3_ACCESS_KEY_ID` | `minioadmin` | S3 access key |
  | `S3_SECRET_ACCESS_KEY` | `minioadmin` | S3 secret key |
  | `S3_BUCKET_NAME` | `staynest-images` | Image storage bucket |
  | `S3_REGION` | `us-east-1` | S3 region |
  | `CORS_ORIGINS` | `["http://localhost:3000"]` | Allowed CORS origins (JSON) |
  | `CELERY_BROKER_URL` | `redis://localhost:6379/1` | Celery broker |
  
  ### Frontend `.env.local` Variables
  
  | Variable | Default | Description |
  | ---------------------- | ---------------------------------- | ------------------------ |
  | `NEXT_PUBLIC_API_URL` | `http://localhost:8000/api/v1` | Backend API base URL |
  
  ---
  
  ## 11. Docker & Infrastructure
  
  ### Services (docker-compose.yml)
  
  | Service | Image / Build | Port(s) | Depends On |
  | --------------- | -------------------- | --------------- | ----------------- |
  | `api` | `./backend` | 8000 | db, redis |
  | `celery-worker` | `./backend` | — | api, redis |
  | `db` | `postgres:16-alpine` | 5432 | — |
  | `redis` | `redis:7-alpine` | 6379 | — |
  | `minio` | `minio/minio:latest` | 9000, 9001 | — |
  | `frontend` | `./frontend` | 3000 | api |
  
  ### Volumes
  
  | Volume | Purpose |
  | --------------- | ---------------------- |
  | `postgres_data` | PostgreSQL data dir |
  | `redis_data` | Redis persistence |
  | `minio_data` | Object storage files |
  
  ### Health Checks
  
  - **PostgreSQL:** `pg_isready -U staynest` every 5 s.
  - **Redis:** `redis-cli ping` every 5 s.
  - The API container waits for both to be healthy before starting.
  
  ---
  
  ## 12. CI/CD Pipeline
  
  `.github/workflows/ci.yml` runs on every push and pull request:
  
  | Job | Steps |
  | -------------- | ---------------------------------------------------- |
  | **backend** | Checkout → Python 3.11 → pip install → pytest + cov |
  | **frontend** | Checkout → Node 20 → npm ci → lint → test → build |
  | **docker** | Checkout → docker compose build (no push) |
  
  ### Quality Gates
  
  - Backend tests must pass with ≥ 80 % coverage.
  - Frontend lint (`next lint`) must pass with zero warnings.
  - Frontend tests must pass.
  - Docker images must build successfully.
  
  ---
  
  ## 13. Coding Conventions
  
  ### Python (Backend)
  
  - **Formatter:** Black (line length 88).
  - **Import order:** stdlib → third-party → local (isort enforced).
  - **Docstrings:** Google style on every module, class, and public function.
  - **Type hints:** Required on all function signatures.
  - **Async:** All DB operations use `async/await` via SQLAlchemy async sessions.
  
  ### TypeScript (Frontend)
  
  - **Formatter:** Prettier (`.prettierrc`).
  - **Linter:** ESLint with Next.js config.
  - **JSDoc:** File-level `@module` + component/function-level `@param`/`@returns`.
  - **Naming:** PascalCase components, camelCase functions/variables, UPPER_SNAKE constants.
  - **Imports:** Path alias `@/` resolves to `src/`.
  
  ### Git
  
  - **Branch naming:** `feature/<topic>`, `fix/<topic>`, `chore/<topic>`.
  - **Commit messages:**