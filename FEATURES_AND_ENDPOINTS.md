# StayNest — Features & API Endpoint Reference
  
  > **Last updated:** March 16, 2026 
  > **Backend:** FastAPI 0.115 (Python 3.12) · **Frontend:** Next.js 14 (React 18, TypeScript) 
  > **Database:** PostgreSQL 16 · **Cache/Broker:** Redis 7 · **Storage:** MinIO (S3-compatible)
  
  ---
  
  ## Table of Contents
  
  1. [Architecture Overview](#1-architecture-overview)
  2. [Authentication & Security](#2-authentication--security)
  3. [Properties](#3-properties)
  4. [Bookings](#4-bookings)
  5. [Reviews & Ratings](#5-reviews--ratings)
  6. [Messaging](#6-messaging)
  7. [Memberships](#7-memberships)
  8. [Admin Panel](#8-admin-panel)
  9. [Background Tasks](#9-background-tasks)
  10. [File Uploads](#10-file-uploads)
  11. [Frontend Pages & Routing](#11-frontend-pages--routing)
  12. [Database Models](#12-database-models)
  13. [Environment Variables](#13-environment-variables)
  14. [Docker Services](#14-docker-services)
  
  ---
  
  ## 1. Architecture Overview
  
  ```
  ┌─────────────┐ ┌─────────────┐ ┌─────────────┐
  │ Next.js 14 │───▶│ FastAPI │───▶│ PostgreSQL │
  │ Frontend │ │ Backend │ │ 16 │
  │ Port 3000 │ │ Port 8000 │ │ Port 5432 │
  └─────────────┘ └──────┬───────┘ └─────────────┘
  │
  ┌───────────┼──────────┐
  ▼ ▼ ▼
  ┌──────────┐ ┌────────┐ ┌────────┐
  │ Redis 7 │ │ MinIO │ │ Celery │
  │ Port 6379│ │ 9000 │ │ Worker │
  └──────────┘ └────────┘ └────────┘
  ```
  
  **API Base URL:** `http://localhost:8000/api/v1` 
  **Health check:** `GET /health` → `{"status": "healthy", "version": "0.1.0"}`
  
  **User Roles:**
  | Role | Capabilities |
  |------|-------------|
  | `user` | Browse properties, make bookings, write reviews, send messages |
  | `host` | Everything a user can do, plus: create/manage property listings, manage bookings, manage messages, requires active membership |
  | `admin` | Full platform access: dashboard metrics, user management (enable/disable), view all bookings/properties/memberships |
  
  ---
  
  ## 1A. Role-Wise Feature & Endpoint Breakdown
  
  ### Guest / User Role (`role: "user"`)
  
  Users (guests) can browse, book, review, and communicate.
  
  #### Features Available
  | Feature | Description |
  |---------|-------------|
  | **Browse Properties** | Search & filter the full property catalog by city, price, guests, hourly availability |
  | **View Property Detail** | View images, amenities, hourly config, reviews, and host info for any active listing |
  | **Create Bookings** | Book nightly or hourly stays; system auto-prices based on duration |
  | **View / Cancel Bookings** | List personal bookings (upcoming, past, cancelled), view detail, cancel pending/confirmed |
  | **Write Reviews** | Rate (1–5 stars) and comment on completed bookings; one review per booking |
  | **Messaging** | Start conversations with hosts about properties; send & receive messages; real-time polling |
  | **Profile Management** | Edit name and phone; change password |
  | **Password Recovery** | Request and complete password reset via email |
  
  #### Endpoints Accessible
  
  | Method | Endpoint | Purpose |
  |--------|----------|---------|
  | `POST` | `/auth/register` | Register as user |
  | `POST` | `/auth/login` | Login |
  | `POST` | `/auth/refresh` | Refresh token |
  | `GET` | `/auth/me` | View profile |
  | `PUT` | `/auth/me` | Update profile |
  | `PUT` | `/auth/me/password` | Change password |
  | `POST` | `/auth/forgot-password` | Request reset link |
  | `POST` | `/auth/reset-password` | Reset password |
  | `GET` | `/properties` | Search properties |
  | `GET` | `/properties/{id}` | View property detail |
  | `POST` | `/bookings` | Create a booking |
  | `GET` | `/bookings` | List my bookings |
  | `GET` | `/bookings/{id}` | View booking detail |
  | `PUT` | `/bookings/{id}/status` | Cancel booking (status=`cancelled`) |
  | `POST` | `/bookings/{id}/cancel` | Cancel booking (shortcut) |
  | `POST` | `/reviews` | Submit a review |
  | `GET` | `/reviews/property/{id}` | View property reviews |
  | `POST` | `/conversations` | Start conversation with host |
  | `GET` | `/conversations` | List conversations |
  | `GET` | `/conversations/{id}` | View conversation detail |
  | `GET` | `/conversations/{id}/messages` | Read messages |
  | `POST` | `/conversations/{id}/messages` | Send message |
  | `PUT` | `/messages/{id}/read` | Mark message as read |
  | `GET` | `/memberships/plans` | View membership plans (informational) |
  
  #### Frontend Pages
  
  | Route | Page |
  |-------|------|
  | `/` | Home (featured properties, search) |
  | `/properties` | Property listing with search/filter/sort |
  | `/properties/[id]` | Property detail, booking form, Contact Host, reviews |
  | `/bookings` | My trips — upcoming / past / cancelled tabs |
  | `/bookings/[id]` | Booking detail with property info |
  | `/messages` | Conversation inbox with unread badges |
  | `/messages/[id]` | Chat thread with real-time polling |
  | `/profile` | Edit personal info, change password |
  | `/auth/login` | Login |
  | `/auth/register` | Registration |
  | `/auth/forgot-password` | Request password reset |
  
  ---
  
  ### Host Role (`role: "host"`)
  
  Hosts have all user capabilities **plus** property management, booking management, reviews dashboard, and membership management.
  
  #### Additional Features (beyond User)
  | Feature | Description |
  |---------|-------------|
  | **Create Listings** | Multi-step wizard: Details → Location → Pricing & Rules → Photos |
  | **Manage Listings** | Edit, deactivate, re-activate properties |
  | **Upload Images** | Drag-and-drop photos with primary selection; JPEG/PNG/WebP/GIF, max 10 MB |
  | **Hourly Booking Config** | Enable hourly mode with custom rate, min/max hours, and available time window |
  | **Manage Bookings** | Confirm, reject, or mark bookings as completed |
  | **View Guest Reviews** | Dashboard showing all reviews across hosted properties with average rating |
  | **Membership Subscription** | Subscribe to Basic / Pro / Premium plans to unlock listing capacity |
  | **Switch / Cancel Plan** | Upgrade, downgrade, or cancel membership |
  | **Host Dashboard** | KPI overview — properties count, active bookings, total earnings, avg rating |
  
  #### Additional Endpoints (beyond User)
  
  | Method | Endpoint | Purpose |
  |--------|----------|---------|
  | `POST` | `/properties` | Create property listing |
  | `PUT` | `/properties/{id}` | Update property |
  | `DELETE` | `/properties/{id}` | Delete (deactivate) property |
  | `POST` | `/properties/{id}/images` | Upload property image |
  | `PUT` | `/properties/{id}/hourly` | Configure hourly booking |
  | `PUT` | `/bookings/{id}/status` | Confirm / reject / complete bookings |
  | `GET` | `/reviews/host` | List reviews for all hosted properties |
  | `POST` | `/memberships/subscribe` | Subscribe to plan |
  | `GET` | `/memberships/current` | View current membership |
  | `PUT` | `/memberships/cancel` | Cancel membership |
  
  #### Frontend Pages (Host Dashboard)
  
  | Route | Page |
  |-------|------|
  | `/dashboard` | Host dashboard — KPIs (properties, bookings, earnings, rating) |
  | `/dashboard/properties` | My property listings with management actions |
  | `/dashboard/properties/new` | 4-step property creation wizard |
  | `/dashboard/properties/[id]` | Edit existing property |
  | `/dashboard/bookings` | Incoming bookings — confirm / reject / complete |
  | `/dashboard/reviews` | Guest review dashboard with average rating |
  | `/dashboard/membership` | Membership management — view plan, upgrade, cancel |
  
  #### Business Rules for Hosts
  - **Active membership required** to create listings → `402 Payment Required` if missing or expired
  - **Listing limit enforced** per plan — Basic: 5, Pro: 25, Premium: unlimited → `403 Forbidden` if exceeded
  - **Membership expiry auto-detected** — expired memberships are flagged on property creation
  - Email notifications sent to host when a new booking arrives
  
  ---
  
  ### Admin Role (`role: "admin"`)
  
  Admins have **full platform access** including all user + host capabilities plus platform management.
  
  #### Admin-Exclusive Features
  | Feature | Description |
  |---------|-------------|
  | **Platform Dashboard** | Real-time KPIs: total users, properties, bookings, active members, monthly revenue, platform growth |
  | **User Management** | View all users paginated with search (name/email/role), enable/disable accounts |
  | **Property Oversight** | View all properties on the platform with active status |
  | **Booking Oversight** | View all bookings with full details (property, guest, host, dates, price, status) |
  | **Membership Oversight** | View all memberships with plan type, status, and amounts |
  | **User Status Toggle** | Enable or disable any user account |
  
  #### Admin-Exclusive Endpoints
  
  | Method | Endpoint | Purpose |
  |--------|----------|---------|
  | `GET` | `/admin/dashboard` | Platform-wide KPIs |
  | `GET` | `/admin/users` | List all users (paginated) |
  | `PUT` | `/admin/users/{id}/status` | Enable/disable user account |
  | `GET` | `/admin/properties` | List all properties |
  | `GET` | `/admin/bookings` | List all bookings |
  | `GET` | `/admin/memberships` | List all memberships |
  
  #### Frontend Pages (Admin Panel)
  
  | Route | Page |
  |-------|------|
  | `/admin` | Admin dashboard — platform KPIs |
  | `/admin/users` | User management — searchable table, role badges, status toggle |
  | `/admin/properties` | All platform properties |
  | `/admin/bookings` | All platform bookings |
  | `/admin/memberships` | All platform memberships |
  
  #### Admin Access Control
  - API: `require_admin` dependency → `403` if `role != "admin"`
  - Edge middleware: `/admin/*` routes check JWT role claim → redirect to `/` if not admin
  - Client-side: `<ProtectedRoute requiredRole="admin">` wrapper on admin layout
  - Admin can access all host routes (admin bypasses host role requirement)
  
  ---
  
  ### Role Permissions Matrix
  
  | Action | Guest (`user`) | Host (`host`) | Admin (`admin`) |
  |--------|:-:|:-:|:-:|
  | Browse / search properties | ✅ | ✅ | ✅ |
  | View property detail | ✅ | ✅ | ✅ |
  | Create booking | ✅ | ✅ | ✅ |
  | View own bookings | ✅ | ✅ | ✅ |
  | Cancel own booking | ✅ | ✅ | ✅ |
  | Write review | ✅ | ✅ | ✅ |
  | Send messages | ✅ | ✅ | ✅ |
  | Manage profile / password | ✅ | ✅ | ✅ |
  | Create property listing | ❌ | ✅ | ✅ |
  | Edit / delete own property | ❌ | ✅ | ✅ |
  | Upload property images | ❌ | ✅ | ✅ |
  | Confirm / reject bookings | ❌ | ✅ | ✅ |
  | Complete bookings | ❌ | ✅ | ✅ |
  | Subscribe to membership plan | ❌ | ✅ | ✅ |
  | Cancel membership | ❌ | ✅ | ✅ |
  | View host reviews dashboard | ❌ | ✅ | ✅ |
  | Access host dashboard | ❌ | ✅ | ✅ |
  | View all users | ❌ | ❌ | ✅ |
  | Enable / disable users | ❌ | ❌ | ✅ |
  | View all platform bookings | ❌ | ❌ | ✅ |
  | View all platform properties | ❌ | ❌ | ✅ |
  | View all memberships | ❌ | ❌ | ✅ |
  | Platform KPI dashboard | ❌ | ❌ | ✅ |
  
  ---
  
  ## 2. Authentication & Security
  
  ### Features
  - **JWT Authentication:** HS256 access tokens (30 min TTL) + refresh tokens (7 day TTL)
  - **Password Hashing:** Argon2 via `passlib`
  - **Token Refresh:** Automatic client-side refresh on 401, with retry of the original request
  - **Rate Limiting:** Redis-backed sliding window per IP per endpoint
  - **Role-based Access Control:** Three-tier dependency chain (`get_current_user` → `require_host` → `require_admin`)
  - **Edge Middleware:** Next.js middleware decodes JWT to enforce route-level role checks without a round-trip
  - **Session Hydration:** `AuthProvider` restores user state from stored token on page load
  
  ### Endpoints
  
  #### `POST /api/v1/auth/register`
  
  | Field | Detail |
  |-------|--------|
  | **Auth** | Public |
  | **Rate Limit** | 10 requests/minute per IP |
  | **Request Body** | `email` (valid email, required), `password` (string, 8–128 chars), `full_name` (string, 1–255 chars), `phone` (string, optional), `role` (`"user"` or `"host"`, default `"user"`) |
  | **Response** | `201` — `UserOut`: `{id, email, full_name, phone, role, is_active, created_at}` |
  | **Side Effects** | Creates `HostProfile` if role is `"host"`. Triggers `send_welcome_email` Celery task. |
  | **Errors** | `409` — email already registered |
  
  #### `POST /api/v1/auth/login`
  
  | Field | Detail |
  |-------|--------|
  | **Auth** | Public |
  | **Rate Limit** | 20 requests/minute per IP |
  | **Request Body** | `email` (valid email), `password` (string) |
  | **Response** | `200` — `{access_token, refresh_token, token_type: "bearer"}` |
  | **JWT Claims** | `sub` (user UUID), `role` (user/host/admin), `type` ("access"/"refresh"), `exp` |
  | **Errors** | `401` — incorrect email or password, or account deactivated |
  
  #### `POST /api/v1/auth/refresh`
  
  | Field | Detail |
  |-------|--------|
  | **Auth** | Public (valid refresh token in body) |
  | **Request Body** | `refresh_token` (string) |
  | **Response** | `200` — `{access_token, refresh_token, token_type}` |
  | **Errors** | `401` — invalid/expired token, user not found or inactive |
  
  #### `GET /api/v1/auth/me`
  
  | Field | Detail |
  |-------|--------|
  | **Auth** | Bearer token required |
  | **Response** | `200` — `UserOut` |
  
  #### `PUT /api/v1/auth/me`
  
  | Field | Detail |
  |-------|--------|
  | **Auth** | Bearer token required |
  | **Request Body** | `full_name` (string, optional), `phone` (string, optional) |
  | **Response** | `200` — `UserOut` (updated) |
  
  #### `PUT /api/v1/auth/me/password`
  
  | Field | Detail |
  |-------|--------|
  | **Auth** | Bearer token required |
  | **Request Body** | `current_password` (string), `new_password` (string, 8–128 chars) |
  | **Response** | `200` — `{"message": "Password changed successfully"}` |
  | **Errors** | `401` — current password incorrect |
  
  #### `POST /api/v1/auth/forgot-password`
  
  | Field | Detail |
  |-------|--------|
  | **Auth** | Public |
  | **Rate Limit** | 5 requests/minute per IP |
  | **Request Body** | `email` (valid email) |
  | **Response** | `200` — `{"message": "If an account with that email exists, a reset link has been sent."}` |
  | **Note** | Always returns success to prevent email enumeration |
  
  #### `POST /api/v1/auth/reset-password`
  
  | Field | Detail |
  |-------|--------|
  | **Auth** | Public |
  | **Request Body** | `token` (string — JWT with `type: "reset"`), `new_password` (string, 8–128 chars) |
  | **Response** | `200` — `{"message": "Password has been reset successfully"}` |
  | **Errors** | `401` — invalid/expired token. `404` — user not found |
  
  ---
  
  ## 3. Properties
  
  ### Features
  - **Public Search & Browse:** Filter by city (case-insensitive), price range, guest capacity, hourly availability
  - **Multi-step Creation Wizard:** 4-step form (Details → Location → Pricing & Rules → Photos)
  - **Image Management:** Drag-and-drop upload, primary image selection, in-gallery reorder
  - **Hourly Booking Config:** Optional hourly booking mode with configurable rates and time windows
  - **Listing Limits:** Enforced per membership plan (Basic: 5, Pro: 25, Premium: unlimited)
  - **Soft-delete:** Properties are deactivated, not destroyed
  - **Client-side Sort:** Recommended, price low→high, price high→low, newest
  
  ### Endpoints
  
  #### `GET /api/v1/properties`
  
  | Field | Detail |
  |-------|--------|
  | **Auth** | Public |
  | **Query Params** | `city` (string), `min_price` (float ≥ 0), `max_price` (float ≥ 0), `max_guests` (int ≥ 1), `hourly_available` (bool), `host_id` (UUID string), `page` (int, default 1), `page_size` (int, 1–100, default 20) |
  | **Response** | `{"items": [PropertyOut], "total": int, "page": int, "page_size": int}` |
  | **Filters** | Only active properties. City uses `ILIKE` (partial match). `max_guests` filters properties where `Property.max_guests >= value`. |
  | **Sorting** | `created_at DESC` (server-side). Client adds: price low/high, newest |
  
  **PropertyOut schema:**
  ```json
  {
  "id": "uuid",
  "host_id": "uuid",
  "title": "string",
  "description": "string",
  "city": "string",
  "address": "string",
  "latitude": null | float,
  "longitude": null | float,
  "price_per_night": float,
  "max_guests": int,
  "amenities": ["string"] | null,
  "is_active": bool,
  "hourly_enabled": bool,
  "images": [{"id": "uuid", "image_url": "string", "is_primary": bool, "sort_order": int}],
  "hourly_config": null | {"id": "uuid", "hourly_price": float, "min_hours": int, "max_hours": int, "available_from": "HH:MM", "available_to": "HH:MM"},
  "created_at": "ISO datetime",
  "updated_at": "ISO datetime"
  }
  ```
  
  #### `GET /api/v1/properties/{property_id}`
  
  | Field | Detail |
  |-------|--------|
  | **Auth** | Public |
  | **Response** | `200` — `PropertyOut` (with eager-loaded `images` and `hourly_config`) |
  | **Errors** | `404` — not found or inactive |
  
  #### `POST /api/v1/properties`
  
  | Field | Detail |
  |-------|--------|
  | **Auth** | Host or Admin |
  | **Request Body** | `title` (3–255 chars), `description` (min 10 chars), `city` (1–100 chars), `address` (5–500 chars), `latitude` (float, optional), `longitude` (float, optional), `price_per_night` (float > 0), `max_guests` (int, 1–50, default 1), `amenities` (list of strings, optional) |
  | **Response** | `201` — `PropertyOut` |
  | **Business Logic** | 1) Verify active, non-expired membership → `402`. 2) Count current active listings vs plan limit → `403` if exceeded. 3) Create property + eager-load relations for response. |
  | **Errors** | `402` — no active membership. `403` — listing limit exceeded |
  
  #### `PUT /api/v1/properties/{property_id}`
  
  | Field | Detail |
  |-------|--------|
  | **Auth** | Host (owner only) |
  | **Request Body** | Same as create, all fields optional, plus `is_active` (bool, optional) |
  | **Response** | `200` — `PropertyOut` |
  | **Errors** | `403` — not the property owner. `404` — not found |
  
  #### `DELETE /api/v1/properties/{property_id}`
  
  | Field | Detail |
  |-------|--------|
  | **Auth** | Host (owner only) |
  | **Response** | `204 No Content` |
  | **Business Logic** | Soft-delete: sets `is_active = false` |
  
  #### `POST /api/v1/properties/{property_id}/images`
  
  | Field | Detail |
  |-------|--------|
  | **Auth** | Host (owner only) |
  | **Content-Type** | `multipart/form-data` |
  | **Request** | `file` (binary, required), `is_primary` (bool query param, default false) |
  | **Validation** | Allowed types: `image/jpeg`, `image/png`, `image/webp`, `image/gif`. Max size: **10 MB** |
  | **Response** | `201` — `{"id": "uuid", "image_url": "string", "is_primary": bool}` |
  | **Business Logic** | If `is_primary=true`, all other images for this property are un-marked. Uploads to MinIO via S3 API. |
  | **Errors** | `400` — invalid file type or file too large. `403` — not the owner |
  
  #### `PUT /api/v1/properties/{property_id}/hourly`
  
  | Field | Detail |
  |-------|--------|
  | **Auth** | Host (owner only) |
  | **Request Body** | `hourly_price` (float > 0), `min_hours` (int ≥ 1, default 1), `max_hours` (int 1–24, default 12), `available_from` (time, default "08:00"), `available_to` (time, default "22:00") |
  | **Response** | `200` — `PropertyOut` |
  | **Business Logic** | Creates or updates `HourlyBookingConfig`. Sets `property.hourly_enabled = true` |
  
  ---
  
  ## 4. Bookings
  
  ### Features
  - **Nightly & Hourly Bookings:** Full support for both booking types with different pricing
  - **Date Overlap Prevention:** Checks against existing pending/confirmed bookings
  - **State Machine:** Enforced transitions — `pending → confirmed/rejected/cancelled`, `confirmed → cancelled/completed`
  - **Host Actions:** Confirm, reject, or mark as completed
  - **Guest Actions:** Cancel bookings
  - **Automatic Email Notifications:** Booking confirmation email via Celery
  
  ### Endpoints
  
  #### `POST /api/v1/bookings`
  
  | Field | Detail |
  |-------|--------|
  | **Auth** | Authenticated |
  | **Request Body** | `property_id` (UUID), `check_in` (ISO datetime), `check_out` (ISO datetime), `booking_type` (`"nightly"` or `"hourly"`, default `"nightly"`), `hours` (int 1–24, optional — required for hourly) |
  | **Response** | `201` — `BookingOut` |
  | **Pricing** | **Nightly:** `price_per_night × number_of_nights`. **Hourly:** `hourly_price × hours` |
  | **Validations** | Property must be active. Cannot book own property. `check_out > check_in`. `check_in` in the future. No overlapping bookings. Hourly bookings require `hourly_enabled` property with valid config and hours within `[min_hours, max_hours]` |
  | **Side Effects** | Triggers `send_booking_confirmation` Celery task |
  | **Errors** | `404` — property not found. `400` — validation failures |
  
  **BookingOut schema:**
  ```json
  {
  "id": "uuid",
  "property_id": "uuid",
  "guest_id": "uuid",
  "host_id": "uuid",
  "check_in": "ISO datetime",
  "check_out": "ISO datetime",
  "total_price": float,
  "booking_type": "nightly" | "hourly",
  "hours": null | int,
  "status": "pending" | "confirmed" | "cancelled" | "completed" | "rejected",
  "created_at": "ISO datetime",
  "updated_at": "ISO datetime"
  }
  ```
  
  #### `GET /api/v1/bookings`
  
  | Field | Detail |
  |-------|--------|
  | **Auth** | Authenticated |
  | **Query Params** | `page` (int, default 1), `page_size` (int, 1–100, default 20) |
  | **Response** | `{"items": [BookingOut], "total": int, "page": int, "page_size": int}` |
  | **Visibility** | **Admin:** all bookings. **Host:** bookings where `host_id` or `guest_id` matches. **Guest:** bookings where `guest_id` matches. Sorted by `created_at DESC` |
  
  #### `GET /api/v1/bookings/{booking_id}`
  
  | Field | Detail |
  |-------|--------|
  | **Auth** | Authenticated (guest, host, or admin) |
  | **Response** | `200` — `BookingOut` |
  | **Errors** | `404` — not found. `403` — not a participant |
  
  #### `PUT /api/v1/bookings/{booking_id}/status`
  
  | Field | Detail |
  |-------|--------|
  | **Auth** | Authenticated |
  | **Request Body** | `status` (`"confirmed"`, `"cancelled"`, `"completed"`, or `"rejected"`) |
  | **Response** | `200` — `BookingOut` |
  | **State Machine** | `pending` → `confirmed` / `rejected` / `cancelled`. `confirmed` → `cancelled` / `completed`. Terminal states: `completed`, `cancelled`, `rejected` |
  | **Permissions** | `confirmed` / `rejected` / `completed` — host or admin only. `cancelled` — guest, host, or admin |
  | **Errors** | `400` — invalid transition. `403` — insufficient role |
  
  #### `POST /api/v1/bookings/{booking_id}/cancel`
  
  | Field | Detail |
  |-------|--------|
  | **Auth** | Authenticated |
  | **Response** | `200` — `BookingOut` |
  | **Business Logic** | Convenience alias for setting status to `"cancelled"` |
  
  ---
  
  ## 5. Reviews & Ratings
  
  ### Features
  - **Guest Reviews:** Only guests can review completed bookings
  - **One Review Per Booking:** Duplicate review prevention
  - **Star Rating:** 1.0 – 5.0 scale
  - **Host Rating Aggregation:** Host's `avg_rating` and `total_reviews` auto-updated on new review
  - **Property Reviews:** Public listing of reviews per property
  - **Host Review Dashboard:** View all reviews across all hosted properties
  
  ### Endpoints
  
  #### `POST /api/v1/reviews`
  
  | Field | Detail |
  |-------|--------|
  | **Auth** | Authenticated |
  | **Request Body** | `booking_id` (UUID), `rating` (float, 1.0–5.0), `comment` (string, max 2000 chars, optional) |
  | **Response** | `201` — `ReviewOut`: `{id, booking_id, property_id, reviewer_id, rating, comment, created_at}` |
  | **Business Logic** | Booking must exist and belong to the reviewer. Booking must be `completed`. One review per booking. Updates host's `HostProfile.avg_rating` and `total_reviews` |
  | **Errors** | `404` — booking not found. `403` — not the guest. `400` — booking not completed or already reviewed |
  
  #### `GET /api/v1/reviews/property/{property_id}`
  
  | Field | Detail |
  |-------|--------|
  | **Auth** | Public |
  | **Query Params** | `page`, `page_size` |
  | **Response** | `{"items": [ReviewOut], "total", "page", "page_size"}` |
  
  #### `GET /api/v1/reviews/host`
  
  | Field | Detail |
  |-------|--------|
  | **Auth** | Authenticated |
  | **Query Params** | `page`, `page_size` |
  | **Response** | `{"items": [ReviewOut], "total", "page", "page_size"}` |
  | **Business Logic** | Lists reviews across all properties owned by the current user |
  
  ---
  
  ## 6. Messaging
  
  ### Features
  - **Property-based Conversations:** Conversations are scoped to a specific property between guest and host
  - **Real-time Polling:** Chat view polls for new messages every 10 seconds
  - **Unread Count:** Each conversation shows unread message count for the current user
  - **Read Receipts:** Messages can be marked as read by the recipient
  - **Enriched Conversations:** List view shows other party name, property title, last message preview, and timestamp
  - **Contact Host:** Property detail page has a "Contact Host" button to start conversations
  
  ### Endpoints
  
  #### `POST /api/v1/conversations`
  
  | Field | Detail |
  |-------|--------|
  | **Auth** | Authenticated |
  | **Request Body** | `property_id` (UUID), `message` (string, 1–5000 chars) |
  | **Response** | `201` — Enriched conversation dict with `last_message` and `unread_count` |
  | **Business Logic** | Property must be active. Cannot message yourself. One conversation per (property, guest, host) triple. Creates conversation + initial message |
  | **Errors** | `404` — property not found. `400` — conversation already exists or messaging yourself |
  
  #### `GET /api/v1/conversations`
  
  | Field | Detail |
  |-------|--------|
  | **Auth** | Authenticated |
  | **Query Params** | `page` (default 1), `page_size` (default 20) |
  | **Response** | `{"items": [...], "total", "page", "page_size"}` |
  | **Item Fields** | `id`, `property_id`, `guest_id`, `host_id`, `property_title`, `other_party_name`, `created_at`, `updated_at`, `last_message` (MessageOut or null), `unread_count` (int) |
  | **Sorting** | `updated_at DESC` (most recently active first) |
  
  #### `GET /api/v1/conversations/{conversation_id}`
  
  | Field | Detail |
  |-------|--------|
  | **Auth** | Authenticated (participant only) |
  | **Response** | `200` — `{id, property_id, guest_id, host_id, property_title, other_party_name, created_at, updated_at}` |
  | **Errors** | `404` — not found. `403` — not a participant |
  
  #### `GET /api/v1/conversations/{conversation_id}/messages`
  
  | Field | Detail |
  |-------|--------|
  | **Auth** | Authenticated (participant only) |
  | **Query Params** | `page` (default 1), `page_size` (default 50, max 200) |
  | **Response** | `{"items": [MessageOut], "total", "page", "page_size"}` |
  | **MessageOut** | `{id, conversation_id, sender_id, content, is_read, created_at}` |
  | **Sorting** | `created_at ASC` (chronological) |
  
  #### `POST /api/v1/conversations/{conversation_id}/messages`
  
  | Field | Detail |
  |-------|--------|
  | **Auth** | Authenticated (participant only) |
  | **Request Body** | `content` (string, 1–5000 chars) |
  | **Response** | `201` — `MessageOut` |
  | **Side Effects** | Bumps `conversation.updated_at` so it sorts to top |
  
  #### `PUT /api/v1/messages/{message_id}/read`
  
  | Field | Detail |
  |-------|--------|
  | **Auth** | Authenticated |
  | **Response** | `200` — `MessageOut` |
  | **Business Logic** | Only the **recipient** can mark as read (not the sender → 400). Verifies user is in the conversation |
  
  ---
  
  ## 7. Memberships
  
  ### Features
  - **Three Tiers:** Basic ($29/mo, 5 listings), Professional ($79/mo, 25 listings), Premium ($199/mo, unlimited)
  - **Plan Switching:** Existing members can switch plans in-place
  - **Listing Enforcement:** Property creation checks listing c