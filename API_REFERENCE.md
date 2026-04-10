# API Reference — Complete Endpoint & Feature Documentation
  
  > **Base URL:** `http://localhost:8000`
  > **Swagger UI:** `http://localhost:8000/docs`
  > **ReDoc:** `http://localhost:8000/redoc`
  > **API Prefix:** `/api/v1`
  
  ---
  
  ## Table of Contents
  
  1. [Quick Start — How to Test](#quick-start--how-to-test)
  2. [Authentication Flow](#authentication-flow)
  3. [Endpoints Overview (36 Total)](#endpoints-overview)
  4. [Health](#1-health)
  5. [Auth (5 endpoints)](#2-authentication)
  6. [Properties (7 endpoints)](#3-properties)
  7. [Bookings (5 endpoints)](#4-bookings)
  8. [Messaging (5 endpoints)](#5-messaging)
  9. [Reviews (3 endpoints)](#6-reviews)
  10. [Memberships (5 endpoints)](#7-memberships)
  11. [Admin (5 endpoints)](#8-admin)
  12. [Frontend Page → Endpoint Map](#frontend-page--endpoint-map)
  13. [Features Working End-to-End](#features-working-end-to-end)
  14. [Features Not Yet Wired (Placeholder)](#features-not-yet-wired-placeholder)
  15. [Schema Reference](#schema-reference)
  
  ---
  
  ## Quick Start — How to Test
  
  ### From Swagger UI (`/docs`)
  
  1. Open `http://localhost:8000/docs` in a browser.
  2. **Register** a user via `POST /api/v1/auth/register`.
  3. **Login** via `POST /api/v1/auth/login` → copy the `access_token` from the response.
  4. Click the **Authorize 🔒** button at the top of Swagger UI → paste `Bearer <access_token>` → click **Authorize**.
  5. You are now authenticated and can test all protected endpoints.
  
  ### Authentication Header
  
  All protected endpoints require:
  
  ```
  Authorization: Bearer <access_token>
  ```
  
  ### Roles
  
  | Role | Capabilities |
  |------|-------------|
  | `user` | Browse properties, create bookings, send messages, write reviews |
  | `host` | Everything a user can do + create/manage properties, manage messages, requires membership |
  | `admin` | Full platform administration (user/property/membership management, dashboard metrics) |
  
  ---
  
  ## Authentication Flow
  
  ```
  Register → Login → Get access_token + refresh_token
  → Use access_token in Authorization header
  → When expired, POST /auth/refresh with refresh_token
  → Get new access_token
  ```
  
  ---
  
  ## Endpoints Overview
  
  | Category | Count | Auth Required |
  |----------|-------|--------------|
  | Health | 1 | No |
  | Auth | 5 | Mixed |
  | Properties | 7 | Mixed |
  | Bookings | 5 | Yes |
  | Messaging | 5 | Yes |
  | Reviews | 3 | Mixed |
  | Memberships | 5 | Mixed |
  | Admin | 5 | Yes (admin) |
  | **Total** | **36** | |
  
  ---
  
  ## 1. Health
  
  ### `GET /health`
  
  | | |
  |---|---|
  | **Auth** | None |
  | **Description** | Returns app health status and version |
  | **Frontend** | Not used directly |
  
  **Response:**
  ```json
  {
  "status": "healthy",
  "version": "1.0.0"
  }
  ```
  
  ---
  
  ## 2. Authentication
  
  ### 2.1 `POST /api/v1/auth/register`
  
  | | |
  |---|---|
  | **Auth** | None |
  | **Description** | Register a new user account |
  | **Frontend** | `frontend/src/app/auth/register/page.tsx` |
  
  **Request Body (`UserRegister`):**
  ```json
  {
  "email": "user@example.com",
  "password": "securepassword123",
  "full_name": "John Doe",
  "phone": "+1234567890",
  "role": "user"
  }
  ```
  
  | Field | Type | Required | Default | Constraints |
  |-------|------|----------|---------|-------------|
  | `email` | EmailStr | **Yes** | — | Valid email |
  | `password` | string | **Yes** | — | min 8, max 128 chars |
  | `full_name` | string | **Yes** | — | min 1, max 255 chars |
  | `phone` | string \| null | No | `null` | — |
  | `role` | string | No | `"user"` | `"user"` or `"host"` |
  
  **Response (`TokenResponse`):**
  ```json
  {
  "access_token": "eyJhbGciOiJIUzI1NiIs...",
  "refresh_token": "eyJhbGciOiJIUzI1NiIs...",
  "token_type": "bearer"
  }
  ```
  
  ---
  
  ### 2.2 `POST /api/v1/auth/login`
  
  | | |
  |---|---|
  | **Auth** | None |
  | **Description** | Authenticate and receive JWT tokens |
  | **Frontend** | `frontend/src/app/auth/login/page.tsx` |
  
  **Request Body (`UserLogin`):**
  ```json
  {
  "email": "user@example.com",
  "password": "securepassword123"
  }
  ```
  
  | Field | Type | Required |
  |-------|------|----------|
  | `email` | EmailStr | **Yes** |
  | `password` | string | **Yes** |
  
  **Response (`TokenResponse`):**
  ```json
  {
  "access_token": "eyJhbGciOiJIUzI1NiIs...",
  "refresh_token": "eyJhbGciOiJIUzI1NiIs...",
  "token_type": "bearer"
  }
  ```
  
  ---
  
  ### 2.3 `POST /api/v1/auth/refresh`
  
  | | |
  |---|---|
  | **Auth** | None |
  | **Description** | Refresh access token using a valid refresh token |
  | **Frontend** | Automatic via Axios interceptor in `frontend/src/lib/api.ts` |
  
  **Request Body (`TokenRefresh`):**
  ```json
  {
  "refresh_token": "eyJhbGciOiJIUzI1NiIs..."
  }
  ```
  
  | Field | Type | Required |
  |-------|------|----------|
  | `refresh_token` | string | **Yes** |
  
  **Response (`TokenResponse`):**
  ```json
  {
  "access_token": "new_access_token...",
  "refresh_token": "new_refresh_token...",
  "token_type": "bearer"
  }
  ```
  
  ---
  
  ### 2.4 `GET /api/v1/auth/me`
  
  | | |
  |---|---|
  | **Auth** | **Yes** — Bearer token |
  | **Description** | Get the current user's profile |
  | **Frontend** | `frontend/src/app/auth/login/page.tsx`, `frontend/src/app/auth/register/page.tsx` (called after login) |
  
  **Parameters:** None
  
  **Response (`UserOut`):**
  ```json
  {
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "email": "user@example.com",
  "full_name": "John Doe",
  "phone": "+1234567890",
  "role": "host",
  "is_active": true,
  "created_at": "2026-03-16T10:00:00Z"
  }
  ```
  
  ---
  
  ### 2.5 `PUT /api/v1/auth/me`
  
  | | |
  |---|---|
  | **Auth** | **Yes** — Bearer token |
  | **Description** | Update the current user's profile |
  | **Frontend** | `frontend/src/app/profile/page.tsx` |
  
  **Request Body (`UserUpdate`):**
  ```json
  {
  "full_name": "John Updated",
  "phone": "+0987654321"
  }
  ```
  
  | Field | Type | Required | Constraints |
  |-------|------|----------|-------------|
  | `full_name` | string \| null | No | min 1, max 255 chars |
  | `phone` | string \| null | No | — |
  
  **Response (`UserOut`):** Same as GET /auth/me
  
  ---
  
  ## 3. Properties
  
  ### 3.1 `GET /api/v1/properties`
  
  | | |
  |---|---|
  | **Auth** | None (public) |
  | **Description** | Search and filter property listings |
  | **Frontend** | `frontend/src/app/properties/page.tsx`, `frontend/src/app/dashboard/page.tsx`, `frontend/src/app/dashboard/properties/page.tsx` |
  
  **Query Parameters:**
  
  | Parameter | Type | Required | Default | Constraints |
  |-----------|------|----------|---------|-------------|
  | `city` | string | No | — | — |
  | `min_price` | float | No | — | >= 0 |
  | `max_price` | float | No | — | >= 0 |
  | `max_guests` | int | No | — | >= 1 |
  | `hourly_available` | bool | No | — | — |
  | `host_id` | UUID | No | — | Filter by host |
  | `page` | int | No | `1` | >= 1 |
  | `page_size` | int | No | `20` | 1–100 |
  
  **Example:** `GET /api/v1/properties?city=Miami&min_price=50&max_price=200&page=1&page_size=10`
  
  **Response (`PaginatedResponse<PropertyOut>`):**
  ```json
  {
  "items": [
  {
  "id": "uuid",
  "host_id": "uuid",
  "title": "Beach House Miami",
  "description": "Beautiful beachfront property...",
  "city": "Miami",
  "address": "123 Ocean Drive",
  "latitude": 25.7617,
  "longitude": -80.1918,
  "price_per_night": 150.00,
  "max_guests": 4,
  "amenities": ["wifi", "pool", "parking"],
  "is_active": true,
  "hourly_enabled": false,
  "images": [
  { "id": "uuid", "image_url": "/uploads/img.jpg", "is_primary": true, "sort_order": 0 }
  ],
  "hourly_config": null,
  "created_at": "2026-03-01T10:00:00Z",
  "updated_at": "2026-03-15T10:00:00Z"
  }
  ],
  "total": 25,
  "page": 1,
  "page_size": 10
  }
  ```
  
  ---
  
  ### 3.2 `GET /api/v1/properties/{property_id}`
  
  | | |
  |---|---|
  | **Auth** | None (public) |
  | **Description** | Get a single property by ID |
  | **Frontend** | `frontend/src/app/properties/[id]/page.tsx`, `frontend/src/app/dashboard/properties/[id]/edit/page.tsx` |
  
  **Path Parameters:**
  
  | Parameter | Type | Required |
  |-----------|------|----------|
  | `property_id` | UUID | **Yes** |
  
  **Response (`PropertyOut`):** Single property object (same shape as items in search)
  
  ---
  
  ### 3.3 `POST /api/v1/properties`
  
  | | |
  |---|---|
  | **Auth** | **Yes** — Host only (requires active membership) |
  | **Description** | Create a new property listing |
  | **Frontend** | `frontend/src/app/dashboard/properties/new/page.tsx` |
  
  **Request Body (`PropertyCreate`):**
  ```json
  {
  "title": "Cozy Apartment Downtown",
  "description": "A beautiful apartment in the heart of the city with amazing views.",
  "city": "New York",
  "address": "456 Broadway, New York, NY 10013",
  "latitude": 40.7128,
  "longitude": -74.0060,
  "price_per_night": 120.00,
  "max_guests": 2,
  "amenities": ["wifi", "kitchen", "air_conditioning"]
  }
  ```
  
  | Field | Type | Required | Default | Constraints |
  |-------|------|----------|---------|-------------|
  | `title` | string | **Yes** | — | min 3, max 255 chars |
  | `description` | string | **Yes** | — | min 10 chars |
  | `city` | string | **Yes** | — | min 1, max 100 chars |
  | `address` | string | **Yes** | — | min 5, max 500 chars |
  | `latitude` | float \| null | No | `null` | — |
  | `longitude` | float \| null | No | `null` | — |
  | `price_per_night` | float | **Yes** | — | > 0 |
  | `max_guests` | int | No | `1` | 1–50 |
  | `amenities` | list[string] \| null | No | `null` | — |
  
  **Response (`PropertyOut`):** The created property object
  
  ---
  
  ### 3.4 `PUT /api/v1/properties/{property_id}`
  
  | | |
  |---|---|
  | **Auth** | **Yes** — Host only, must be property owner |
  | **Description** | Update a property listing |
  | **Frontend** | `frontend/src/app/dashboard/properties/[id]/edit/page.tsx` |
  
  **Path Parameters:**
  
  | Parameter | Type | Required |
  |-----------|------|----------|
  | `property_id` | UUID | **Yes** |
  
  **Request Body (`PropertyUpdate`):**
  ```json
  {
  "title": "Updated Apartment Name",
  "price_per_night": 135.00,
  "amenities": ["wifi", "kitchen", "air_conditioning", "gym"]
  }
  ```
  
  | Field | Type | Required | Constraints |
  |-------|------|----------|-------------|
  | `title` | string \| null | No | min 3, max 255 |
  | `description` | string \| null | No | min 10 |
  | `city` | string \| null | No | min 1, max 100 |
  | `address` | string \| null | No | min 5, max 500 |
  | `latitude` | float \| null | No | — |
  | `longitude` | float \| null | No | — |
  | `price_per_night` | float \| null | No | > 0 |
  | `max_guests` | int \| null | No | 1–50 |
  | `amenities` | list[string] \| null | No | — |
  | `is_active` | bool \| null | No | — |
  
  **Response (`PropertyOut`):** Updated property object
  
  ---
  
  ### 3.5 `DELETE /api/v1/properties/{property_id}`
  
  | | |
  |---|---|
  | **Auth** | **Yes** — Host only, must be property owner |
  | **Description** | Delete (deactivate) a property listing |
  | **Frontend** | `frontend/src/app/dashboard/properties/page.tsx` |
  
  **Path Parameters:**
  
  | Parameter | Type | Required |
  |-----------|------|----------|
  | `property_id` | UUID | **Yes** |
  
  **Response:**
  ```json
  { "detail": "Property deleted" }
  ```
  
  ---
  
  ### 3.6 `POST /api/v1/properties/{property_id}/images`
  
  | | |
  |---|---|
  | **Auth** | **Yes** — Host only, must be property owner |
  | **Description** | Upload an image for a property |
  | **Frontend** | `frontend/src/app/dashboard/properties/new/page.tsx` |
  
  **Path Parameters:**
  
  | Parameter | Type | Required |
  |-----------|------|----------|
  | `property_id` | UUID | **Yes** |
  
  **Query Parameters:**
  
  | Parameter | Type | Required | Default |
  |-----------|------|----------|---------|
  | `is_primary` | bool | No | `false` |
  
  **Request Body:** `multipart/form-data`
  
  | Field | Type | Required |
  |-------|------|----------|
  | `file` | UploadFile (image) | **Yes** |
  
  > ⚠️ In Swagger UI, use the file upload widget. Set `Content-Type: multipart/form-data`.
  
  **Response (`PropertyImageOut`):**
  ```json
  {
  "id": "uuid",
  "image_url": "/uploads/properties/uuid/image.jpg",
  "is_primary": true,
  "sort_order": 0
  }
  ```
  
  ---
  
  ### 3.7 `PUT /api/v1/properties/{property_id}/hourly`
  
  | | |
  |---|---|
  | **Auth** | **Yes** — Host only, must be property owner |
  | **Description** | Enable and configure hourly booking for a property |
  | **Frontend** | `frontend/src/app/dashboard/properties/new/page.tsx` |
  
  **Path Parameters:**
  
  | Parameter | Type | Required |
  |-----------|------|----------|
  | `property_id` | UUID | **Yes** |
  
  **Request Body (`HourlyBookingConfigUpdate`):**
  ```json
  {
  "hourly_price": 25.00,
  "min_hours": 2,
  "max_hours": 8,
  "available_from": "09:00",
  "available_to": "21:00"
  }
  ```
  
  | Field | Type | Required | Default | Constraints |
  |-------|------|----------|---------|-------------|
  | `hourly_price` | float | **Yes** | — | > 0 |
  | `min_hours` | int | No | `1` | >= 1 |
  | `max_hours` | int | No | `12` | 1–24 |
  | `available_from` | time | No | `08:00` | HH:MM format |
  | `available_to` | time | No | `22:00` | HH:MM format |
  
  **Response (`PropertyOut`):** Updated property object with `hourly_enabled: true` and `hourly_config` populated
  
  ---
  
  ## 4. Bookings
  
  ### 4.1 `POST /api/v1/bookings`
  
  | | |
  |---|---|
  | **Auth** | **Yes** — Any authenticated user |
  | **Description** | Create a new booking (nightly or hourly) |
  | **Frontend** | `frontend/src/app/properties/[id]/page.tsx` |
  
  **Request Body (`BookingCreate`):**
  ```json
  {
  "property_id": "550e8400-e29b-41d4-a716-446655440000",
  "check_in": "2026-04-01T14:00:00Z",
  "check_out": "2026-04-05T11:00:00Z",
  "booking_type": "nightly",
  "hours": null
  }
  ```
  
  | Field | Type | Required | Default | Constraints |
  |-------|------|----------|---------|-------------|
  | `property_id` | UUID | **Yes** | — | Must exist |
  | `check_in` | datetime | **Yes** | — | ISO 8601 format |
  | `check_out` | datetime | **Yes** | — | ISO 8601, must be after check_in |
  | `booking_type` | string | No | `"nightly"` | `"nightly"` or `"hourly"` |
  | `hours` | int \| null | No | `null` | 1–24 (required if hourly) |
  
  **Response (`BookingOut`):**
  ```json
  {
  "id": "uuid",
  "property_id": "uuid",
  "guest_id": "uuid",
  "host_id": "uuid",
  "check_in": "2026-04-01T14:00:00Z",
  "check_out": "2026-04-05T11:00:00Z",
  "total_price": 600.00,
  "booking_type": "nightly",
  "hours": null,
  "status": "pending",
  "created_at": "2026-03-16T10:00:00Z",
  "updated_at": "2026-03-16T10:00:00Z"
  }
  ```
  
  ---
  
  ### 4.2 `GET /api/v1/bookings`
  
  | | |
  |---|---|
  | **Auth** | **Yes** — Any authenticated user |
  | **Description** | List bookings for the current user (as guest or host) |
  | **Frontend** | `frontend/src/app/bookings/page.tsx`, `frontend/src/app/dashboard/page.tsx`, `frontend/src/app/dashboard/bookings/page.tsx` |
  
  **Query Parameters:**
  
  | Parameter | Type | Required | Default |
  |-----------|------|----------|---------|
  | `page` | int | No | `1` |
  | `page_size` | int | No | `20` |
  
  **Response (`PaginatedBookings`):**
  ```json
  {
  "items": [ /* BookingOut objects */ ],
  "total": 15,
  "page": 1,
  "page_size": 20
  }
  ```
  
  ---
  
  ### 4.3 `GET /api/v1/bookings/{booking_id}`
  
  | | |
  |---|---|
  | **Auth** | **Yes** — Must be booking guest or property host |
  | **Description** | Get booking details |
  | **Frontend** | `frontend/src/app/bookings/[id]/page.tsx` |
  
  **Path Parameters:**
  
  | Parameter | Type | Required |
  |-----------|------|----------|
  | `booking_id` | UUID | **Yes** |
  
  **Response (`BookingOut`):** Single booking object
  
  ---
  
  ### 4.4 `PUT /api/v1/bookings/{booking_id}/status`
  
  | | |
  |---|---|
  | **Auth** | **Yes** — Must be booking participant |
  | **Description** | Update booking status (confirm, reject, cancel, complete) |
  | **Frontend** | `frontend/src/app/dashboard/bookings/page.tsx` |
  
  **Path Parameters:**
  
  | Parameter | Type | Required |
  |-----------|------|----------|
  | `booking_id` | UUID | **Yes** |
  
  **Request Body (`BookingStatusUpdate`):**
  ```json
  {
  "status": "confirmed"
  }
  ```
  
  | Field | Type | Required | Allowed Values |
  |-------|------|----------|----------------|
  | `status` | string | **Yes** | `"confirmed"`, `"cancelled"`, `"completed"`, `"rejected"` |
  
  **Response (`BookingOut`):** Updated booking object
  
  ---
  
  ### 4.5 `POST /api/v1/bookings/{booking_id}/cancel`
  
  | | |
  |---|---|
  | **Auth** | **Yes** — Must be booking guest |
  | **Description** | Cancel a booking |
  | **Frontend** | `frontend/src/app/bookings/[id]/page.tsx` |
  
  **Path Parameters:**
  
  | Parameter | Type | Required |
  |-----------|------|----------|
  | `booking_id` | UUID | **Yes** |
  
  **Request Body:** None
  
  **Response (`BookingOut`):** Updated booking with `status: "cancelled"`
  
  ---
  
  ## 5. Messaging
  
  ### 5.1 `POST /api/v1/conversations`
  
  | | |
  |---|---|
  | **Auth** | **Yes** — Any authenticated user |
  | **Description** | Start a new conversation thread about a property |
  | **Frontend** | `frontend/src/app/bookings/[id]/page.tsx` |
  
  **Request Body (`ConversationCreate`):**
  ```json
  {
  "property_id": "550e8400-e29b-41d4-a716-446655440000",
  "message": "Hi, I have a question about your property."
  }
  ```
  
  | Field | Type | Required | Constraints |
  |-------|------|----------|-------------|
  | `property_id` | UUID | **Yes** | Must exist |
  | `message` | string | **Yes** | min 1, max 5000 chars |
  
  **Response (`ConversationOut`):**
  ```json
  {
  "id": "uuid",
  "property_id": "uuid",
  "guest_id": "uuid",
  "host_id": "uuid",
  "created_at": "2026-03-16T10:00:00Z",
  "updated_at": "2026-03-16T10:00:00Z",
  "last_message": {
  "id": "uuid",
  "conversation_id": "uuid",
  "sender_id": "uuid",
  "content": "Hi, I have a question about your property.",
  "is_read": false,
  "created_at": "2026-03-16T10:00:00Z"
  },
  "unread_count": 0
  }
  ```
  
  ---
  
  ### 5.2 `GET /api/v1/conversations`
  
  | | |
  |---|---|
  | **Auth** | **Yes** — Any authenticated user |
  | **Description** | List all conversations for the current user |
  | **Frontend** | `frontend/src/app/messages/page.tsx` |
  
  **Query Parameters:**
  
  | Parameter | Type | Required | Default |
  |-----------|------|----------|---------|
  | `page` | int | No | `1` |
  | `page_size` | int | No | `20` |
  
  **Response (`PaginatedResponse<ConversationOut>`):**
  ```json
  {
  "items": [ /* ConversationOut objects */ ],
  "total": 3,
  "page": 1,
  "page_size": 20
  }
  ```
  
  ---
  
  ### 5.3 `GET /api/v1/conversations/{conversation_id}/messages`
  
  | | |
  |---|---|
  | **Auth** | **Yes** — Must be conversation participant |
  | **Description** | Get messages in a conversation thread |
  | **Frontend** | `frontend/src/app/messages/[id]/page.tsx` (polls every 10 seconds) |
  
  **Path Parameters:**
  
  | Parameter | Type | Required |
  |-----------|------|----------|
  | `conversation_id` | UUID | **Yes** |
  
  **Query Parameters:**
  
  | Parameter | Type | Required | Default |
  |-----------|------|----------|---------|
  | `page` | int | No | `1` |
  | `page_size` | int | No | `20` |
  
  **Response (`PaginatedMessages`):**
  ```json
  {
  "items": [
  {
  "id": "uuid",
  "conversation_id": "uuid",
  "sender_id": "uuid",
  "content": "Hello!",
  "is_read": true,
  "created_at": "2026-03-16T10:00:00Z"
  }
  ],
  "total": 10,
  "page": 1,
  "page_size": 20
  }
  ```
  
  ---
  
  ### 5.4 `POST /api/v1/conversations/{conversation_id}/messages`
  
  | | |
  |---|---|
  | **Auth** | **Yes** — Must be conversation participant |
  | **Description** | Send a message in an existing conversation |
  | **Frontend** | `frontend/src/app/messages/[id]/page.tsx` |
  
  **Path Parameters:**
  
  | Parameter | Type | Required |
  |-----------|------|----------|
  | `conversation_id` | UUID | **Yes** |
  
  **Request Body (`MessageCreate`):**
  ```json
  {
  "content": "Thanks for the info!"
  }
  ```
  
  | Field | Type | Required | Constraints |
  |-------|------|----------|-------------|
  | `content` | string | **Yes** | min 1, max 5000 chars |
  
  **Response (`MessageOut`):** The sent message object
  
  ---
  
  ### 5.5 `PUT /api/v1/messages/{message_id}/read`
  
  | | |
  |---|---|
  | **Auth** | **Yes** — Must be message recipient |
  | **Description** | Mark a message as read |
  | **Frontend** | Defined in `frontend/src/lib/api.ts` but **not yet used** by any page |
  
  **Path Parameters:**
  
  | Parameter | Type | Required |
  |-----------|------|----------|
  | `message_id` | UUID | **Yes** |
  
  **Request Body:** None
  
  **Response (`MessageOut`):** Updated message with `is_read: true`
  
  ---
  
  ## 6. Reviews
  
  ### 6.1 `POST /api/v1/reviews`
  
  | | |
  |---|---|
  | **Auth** | **Yes** — Must be booking guest, booking must be completed |
  | **Description** | Create a review for a completed booking |
  | **Frontend** | `frontend/src/app/bookings/[id]/page.tsx` |
  
  **Request Body (`ReviewCreate`):**
  ```json
  {
  "booking_id": "550e8400-e29b-41d4-a716-446655440000",
  "rating": 4.5,
  "comment": "Great place, very clean and well-maintained!"
  }
  ```
  
  | Field | Type | Required | Constraints |
  |-------|------|----------|-------------|
  | `booking_id` | UUID | **Yes** | Must be a completed booking |
  | `rating` | float | **Yes** | 1.0–5.0 |
  | `comment` | string \| null | No | max 2000 chars |
  
  **Response (`ReviewOut`):**
  ```json
  {
  "id": "uuid",
  "booking_id": "uuid",
  "property_id": "uuid",
  "reviewer_id": "uuid",
  "rating": 4.5,
  "comment": "Great place, very clean and well-maintained!",
  "created_at": "2026-03-16T10:00:00Z"
  }
  ```
  
  ---
  
  ### 6.2 `GET /api/v1/reviews/property/{property_id}`
  
  | | |
  |---|---|
  | **Auth** | None (public) |
  | **Description** | List reviews for a property |
  | **Frontend** | `frontend/src/app/properties/[id]/page.tsx` |
  
  **Path Parameters:**
  
  | Parameter | Type | Required |
  |-----------|------|----------|
  | `property_id` | UUID | **Yes** |
  
  **Query Parameters:**
  
  | Parameter | Type | Required | Default |
  |-----------|------|----------|---------|
  | `page` | int | No | `1` |
  | `page_size` | int | No | `20` |
  
  **Response (`PaginatedReviews`):**
  ```json
  {
  "items": [ /* ReviewOut objects */ ],
  "total": 12,
  "page": 1,
  "page_size": 20
  }
  ```
  
  ---
  
  ### 6.3 `GET /api/v1/reviews/host`
  
  | | |
  |---|---|
  | **Auth** | **Yes** — Any authenticated user |
  | **Description** | List all reviews for properties owned by the current host |
  | **Frontend** | `frontend/src/app/dashboard/reviews/page.tsx` |
  
  **Query Parameters:**
  
  | Parameter | Type | Required | Default |
  |-----------|------|----------|---------|
  | `page` | int | No | `1` |
  | `page_size` | int | No | `20` |
  
  **Response (`PaginatedReviews`):** Same as property reviews
  
  ---
  
  ## 7. Memberships
  
  ### 7.1 `GET /api/v1/memberships/plans`
  
  | | |
  |---|---|
  | **Auth** | None (public) |
  | **Description** | List all available membership plans |
  | **Frontend** | Defined in `frontend/src/lib/api.ts` but **not yet called** by the membership page (plans are hardcoded in frontend) |
  
  **Response:**
  ```json
  [
  { "plan_type": "basic", "label": "Basic", "price": 2499.00, "max_listings": 5 },
  { "plan_type": "pro", "label": "Pro", "price": 6499.00, "max_listings": 25 },
  { "plan_type": "premium", "label": "Premium", "price": 16499.00, "max_listings": 999999 }
  ]
  ```
  
  ---
  
  ### 7.2 `POST /api/v1/memberships/subscribe`
  
  | | |
  |---|---|
  | **Auth** | **Yes** — Host only |
  | **Description** | Subscribe to a membership plan |
  | **Frontend** | `frontend/src/app/dashboard/membership/page.tsx` |
  
  **Request Body (`MembershipSubscribeRequest`):**
  ```json
  {
  "plan_type": "pro",
  "payment_token": "tok_visa_4242"
  }
  ```
  
  | Field | Type | Required | Constraints |
  |-------|------|----------|-------------|
  | `plan_type` | string | **Yes** | `"basic"`, `"pro"`, or `"premium"` |
  | `payment_token` | string | **Yes** | min 1 char |
  
  **Response (`MembershipOut`):**
  ```json
  {
  "id": "uuid",
  "host_id": "uuid",
  "plan_type": "pro",
  "start_date": "2026-03-16T10:00:00Z",
  "end_date": "2026-04-16T10:00:00Z",
  "status": "active",
  "auto_renew": true,
  "amount": 6499.00,
  "max_listings": 25,
  "created_at": "2026-03-16T10:00:00Z",
  "updated_at": "2026-03-16T10:00:00Z"
  }
  ```
  
  ---
  
  ### 7.3 `GET /api/v1/memberships/current`
  
  | | |
  |---|---|
  | **Auth** | **Yes** — Host only |
  | **Description** | Get the host's current active membership |
  | **Frontend** | `frontend/src/app/dashboard/membership/page.tsx` |
  
  **Response (`MembershipOut`):** Single membership object (or 404 if none)
  
  ---
  
  ### 7.4 `PUT /api/v1/memberships/cancel`
  
  | | |
  |---|---|
  | **Auth** | **Yes** — Host only |
  | **Description** | Cancel the current membership |
  | **Frontend** | `frontend/src/app/dashboard/membership/page.tsx` |
  
  **Request Body:** None
  
  **Response (`MembershipOut`):** Updated membership with `status: "cancelled"`, `auto_renew: false`
  
  ---
  
  ### 7.5 `POST /api/v1/memberships/webhook`
  
  | | |
  |---|---|
  | **Auth** | None (signature verification in production) |
  | **Description** | Process payment gateway webhook events |
  | **Frontend** | Not used (server-to-server) |
  
  **Request Body (`MembershipWebhookPayload`):**
  ```json
  {
  "event_type": "payment.success",
  "payment_ref": "pay_abc123",
  "status": "success",
  "metadata": { "plan": "pro" }
  }
  ```
  
  | Field | Type | Required |
  |-------|------|----------|
  | `event_type` | string | **Yes** |
  | `payment_ref` | string | **Yes** |
  | `status` | string | **Yes** |
  | `metadata` | dict \| null | No |
  
  **Response:**
  ```json
  { "status": "processed" }
  ```
  
  ---
  
  ## 8. Admin
  
  > All admin endpoints require the `admin` role.
  
  ### 8.1 `GET /api/v1/admin/dashboard`
  
  | | |
  |---|---|
  | **Auth** | **Yes** — Admin only |
  | **Description** | Platform dashboard metrics |
  | **Frontend** | `frontend/src/app/admin/page.tsx` |
  
  **Response:**
  ```json
  {
  "total_users": 150,
  "total_properties": 80,
  "active_members": 30,
  "total_bookings": 220,
  "completed_bookings": 180,
  "monthly_revenue": 45000.00,
  "platform_growth": 0
  }
  ```
  
  ---
  
  ### 8.2 `GET /api/v1/admin/users`
  
  | | |
  |---|---|
  | **Auth** | **Yes** — Admin only |
  | **Description** | List all users with pagination |
  | **Frontend** | `frontend/src/app/admin/users/page.tsx` |
  
  **Query Parameters:**
  
  | Parameter | Type | Required | Default |
  |-----------|------|----------|---------|
  | `page` | int | No | `1` |
  | `page_size` | int | No | `20` |
  
  **Response:**
  ```json
  {
  "items": [ /* UserOut objects */ ],
  "total": 150,
  "page": 1,
  "page_size": 20
  }
  ```
  
  ---
  
  ### 8.3 `GET /api/v1/admin/properties`
  
  | | |
  |---|---|
  | **Auth** | **Yes** — Admin only |
  | **Description** | List all properties with pagination |
  | **Frontend** | Defined in `frontend/src/lib/api.ts` but **not yet wired** (placeholder data) |
  
  **Query Parameters:**
  
  | Parameter | Type | Required | Default |
  |-----------|------|----------|---------|
  | `page` | int | No | `1` |
  | `page_size` | int | No | `20` |
  
  **Response:** Paginated list of `PropertyOut` objects
  
  ---
  
  ### 8.4 `GET /api/v1/admin/memberships`
  
  | | |
  |---|---|
  | **Auth** | **Yes** — Admin only |
  | **Description** | List all memberships with pagination |
  | **Frontend** | Defined in `frontend/src/lib/api.ts` but **not yet wired** (placeholder data) |
  
  **Query Parameters:**
  
  | Parameter | Type | Required | Default |
  |-----------|------|----------|---------|
  | `page` | int | No | `1` |
  | `page_size` | int | No | `20` |
  
  **Response:** Paginated list of `MembershipOut` objects
  
  ---
  
  ### 8.5 `PUT /api/v1/admin/users/{user_id}/status`
  
  | | |
  |---|---|
  | **Auth** | **Yes** — Admin only |
  | **Description** | Enable or disable a user account |
  | **Frontend** | Defined in `frontend/src/lib/api.ts` but **not yet wired** |
  
  **Path Parameters:**
  
  | Parameter | Type | Required |
  |-----------|------|----------|
  | `user_id` | UUID | **Yes** |
  
  **Request Body:** None
  
  **Response (`UserOut`):** Updated user with toggled `is_active` status
  
  ---
  
  ## Frontend Page → Endpoint Map
  
  | Frontend Page | URL | Endpoints Used |
  |---------------|-----|----------------|
  | Home | `/` | None (static) |
  | Login | `/auth/login` | `POST /auth/login`, `GET /auth/me` |
  | Register | `/auth/register` | `POST /auth/register`, `POST /auth/login`, `GET /auth/me` |
  | Forgot Password | `/auth/forgot-password` | None (placeholder) |
  | Reset Password | `/auth/reset-password` | None (placeholder) |
  | Profile | `/profile` | `PUT /auth/me` |
  | Property Search | `/properties` | `GET /properties` |
  | Property Detail | `/properties/[id]` | `GET /properties/{id}`, `GET /reviews/property/{id}`, `POST /bookings`, `POST /conversations` |
  | My Bookings | `/bookings` | `GET /bookings` |
  | Booking Detail | `/bookings/[id]` | `GET /bookings/{id}`, `POST /bookings/{id}/cancel`, `POST /reviews`, `POST /conversations` |
  | Messages List