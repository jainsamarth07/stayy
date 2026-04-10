# StayNest — Rental Marketplace Platform Architecture

> A commission-free rental marketplace where hosts pay membership subscriptions to list properties and keep 100% of booking revenue.

---

## 1. System Overview

```
┌──────────────────────────────────────────────────────────────────────┐
│                        CLIENTS                                       │
│   ┌──────────────┐  ┌──────────────┐  ┌──────────────────────────┐  │
│   │  Next.js Web  │  │  Mobile App  │  │  Admin Dashboard (Next)  │  │
│   └──────┬───────┘  └──────┬───────┘  └────────────┬─────────────┘  │
└──────────┼─────────────────┼───────────────────────┼────────────────┘
           │                 │                       │
           ▼                 ▼                       ▼
┌──────────────────────────────────────────────────────────────────────┐
│                     API GATEWAY / LOAD BALANCER                      │
│                     (Nginx / Traefik / ALB)                          │
└──────────────────────────────┬───────────────────────────────────────┘
                               │
                               ▼
┌──────────────────────────────────────────────────────────────────────┐
│                     FASTAPI APPLICATION LAYER                        │
│  ┌──────────┐ ┌──────────┐ ┌───────────┐ ┌──────────┐               │
│  │   Auth   │ │Listings  │ │ Bookings  │ │ Messages │               │
│  │  Module  │ │  Module  │ │  Module   │ │  Module  │               │
│  └──────────┘ └──────────┘ └───────────┘ └──────────┘               │
│  ┌──────────┐ ┌──────────┐ ┌───────────┐ ┌──────────────────────┐  │
│  │ Reviews  │ │Membership│ │  Upload   │ │   Admin Module       │  │
│  │  Module  │ │  Module  │ │  Module   │ │                      │  │
│  └──────────┘ └──────────┘ └───────────┘ └──────────────────────┘  │
└───────┬──────────────┬──────────────┬────────────────────────────────┘
        │              │              │
        ▼              ▼              ▼
┌──────────────┐ ┌───────────┐ ┌───────────────┐
│  PostgreSQL  │ │   Redis   │ │ S3-Compatible │
│  (Primary)   │ │  (Cache)  │ │    Storage    │
│              │ │           │ │   (Images)    │
│  - Users     │ │ - Sessions│ │               │
│  - Listings  │ │ - Cache   │ │               │
│  - Bookings  │ │ - Pub/Sub │ │               │
│  - Messages  │ │           │ │               │
│  - Reviews   │ │           │ │               │
│  - Members   │ │           │ │               │
└──────────────┘ └───────────┘ └───────────────┘
```

---

## 2. High-Level Architecture Decisions

| Decision                | Choice                    | Rationale                                              |
|-------------------------|---------------------------|--------------------------------------------------------|
| Backend Framework       | FastAPI (Python 3.11+)    | Async, type-safe, auto-docs, high performance          |
| Frontend Framework      | Next.js 14 (App Router)   | SSR/SSG, SEO, React ecosystem                          |
| Database                | PostgreSQL 16             | ACID, JSON support, full-text search, PostGIS ready    |
| ORM                     | SQLAlchemy 2.0 + Alembic  | Mature, async support, migration management            |
| Auth                    | JWT (access + refresh)    | Stateless, scalable, role-based                        |
| Caching                 | Redis 7                   | Session cache, query cache, rate limiting, pub/sub     |
| Image Storage           | S3-compatible (MinIO dev) | Scalable object storage, CDN-friendly                  |
| Task Queue              | Celery + Redis broker     | Async email, payment processing, notifications         |
| Containerization        | Docker + Docker Compose   | Reproducible environments, easy deployment             |
| API Documentation       | OpenAPI (auto-generated)  | Built into FastAPI                                     |

---

## 3. Revenue Model Implementation

```
┌─────────────────────────────────────────┐
│         REVENUE MODEL                    │
│                                          │
│  ┌───────────────────────────────────┐   │
│  │  Host Membership Subscriptions    │   │
│  │  ─────────────────────────────    │   │
│  │  Basic  — $29/mo  — 5 listings   │   │
│  │  Pro    — $79/mo  — 25 listings  │   │
│  │  Premium— $199/mo — Unlimited    │   │
│  └───────────────────────────────────┘   │
│                                          │
│  ✗ NO booking commissions                │
│  ✓ Hosts keep 100% booking revenue       │
│  ✓ Platform revenue = memberships only   │
└─────────────────────────────────────────┘
```

---

## 4. Database Schema (ERD)

```
┌─────────────┐     ┌──────────────────┐     ┌──────────────────┐
│   users      │────▶│  host_profiles   │────▶│  memberships     │
│─────────────│     │──────────────────│     │──────────────────│
│ id (PK)     │     │ id (PK)          │     │ id (PK)          │
│ email       │     │ user_id (FK)     │     │ host_id (FK)     │
│ password    │     │ business_name    │     │ plan_type        │
│ full_name   │     │ bio              │     │ start_date       │
│ phone       │     │ phone_visible    │     │ end_date         │
│ role        │     │ is_verified      │     │ status           │
│ is_active   │     │ avg_rating       │     │ payment_ref      │
│ created_at  │     │ created_at       │     │ auto_renew       │
└─────────────┘     └──────────────────┘     └──────────────────┘
       │
       │            ┌──────────────────┐     ┌──────────────────┐
       │            │  properties      │     │ property_images  │
       │            │──────────────────│     │──────────────────│
       └───────────▶│ id (PK)          │────▶│ id (PK)          │
                    │ host_id (FK)     │     │ property_id (FK) │
                    │ title            │     │ image_url        │
                    │ description      │     │ is_primary       │
                    │ city             │     │ sort_order       │
                    │ address          │     └──────────────────┘
                    │ latitude         │
                    │ longitude        │     ┌──────────────────────┐
                    │ price_per_night  │     │ hourly_booking_config│
                    │ max_guests       │     │──────────────────────│
                    │ amenities (JSON) │────▶│ id (PK)              │
                    │ is_active        │     │ property_id (FK)     │
                    │ hourly_enabled   │     │ hourly_price         │
                    │ created_at       │     │ min_hours            │
                    └──────────────────┘     │ max_hours            │
                           │                 │ available_from       │
                           │                 │ available_to         │
                           │                 └──────────────────────┘
                           │
       ┌───────────────────┼───────────────────┐
       ▼                                       ▼
┌──────────────┐                      ┌────────────────┐
│  bookings    │                      │  reviews       │
│──────────────│                      │────────────────│
│ id (PK)      │                      │ id (PK)        │
│ property_id  │                      │ booking_id(FK) │
│ guest_id(FK) │                      │ reviewer_id    │
│ host_id (FK) │                      │ property_id    │
│ check_in     │                      │ rating         │
│ check_out    │                      │ comment        │
│ total_price  │                      │ created_at     │
│ booking_type │                      └────────────────┘
│ hours        │
│ status       │
│ created_at   │
└──────────────┘

┌────────────────────┐     ┌────────────────────┐
│  conversations     │     │  messages          │
│────────────────────│     │────────────────────│
│ id (PK)            │────▶│ id (PK)            │
│ property_id (FK)   │     │ conversation_id    │
│ guest_id (FK)      │     │ sender_id (FK)     │
│ host_id (FK)       │     │ content            │
│ created_at         │     │ is_read            │
│ updated_at         │     │ created_at         │
└────────────────────┘     └────────────────────┘
```

---

## 5. API Design

### Authentication
| Method | Endpoint                    | Description              | Auth |
|--------|-----------------------------|--------------------------|------|
| POST   | `/api/v1/auth/register`     | Register new user        | No   |
| POST   | `/api/v1/auth/login`        | Login, return JWT tokens | No   |
| POST   | `/api/v1/auth/refresh`      | Refresh access token     | Yes  |
| GET    | `/api/v1/auth/me`           | Get current user profile | Yes  |
| PUT    | `/api/v1/auth/me`           | Update profile           | Yes  |

### Properties
| Method | Endpoint                           | Description              | Auth  |
|--------|------------------------------------|--------------------------|-------|
| GET    | `/api/v1/properties`               | Search/list properties   | No    |
| GET    | `/api/v1/properties/{id}`          | Get property details     | No    |
| POST   | `/api/v1/properties`               | Create listing           | Host  |
| PUT    | `/api/v1/properties/{id}`          | Update listing           | Host  |
| DELETE | `/api/v1/properties/{id}`          | Delete listing           | Host  |
| POST   | `/api/v1/properties/{id}/images`   | Upload images            | Host  |
| PUT    | `/api/v1/properties/{id}/hourly`   | Configure hourly booking | Host  |

### Bookings
| Method | Endpoint                        | Description              | Auth  |
|--------|---------------------------------|--------------------------|-------|
| POST   | `/api/v1/bookings`              | Create booking           | User  |
| GET    | `/api/v1/bookings`              | List user's bookings     | Yes   |
| GET    | `/api/v1/bookings/{id}`         | Booking details          | Yes   |
| PUT    | `/api/v1/bookings/{id}/status`  | Update booking status    | Host  |
| POST   | `/api/v1/bookings/{id}/cancel`  | Cancel booking           | Yes   |

### Messaging
| Method | Endpoint                              | Description              | Auth |
|--------|---------------------------------------|--------------------------|------|
| GET    | `/api/v1/conversations`               | List conversations       | Yes  |
| POST   | `/api/v1/conversations`               | Start conversation       | Yes  |
| GET    | `/api/v1/conversations/{id}/messages` | Get messages in thread   | Yes  |
| POST   | `/api/v1/conversations/{id}/messages` | Send message             | Yes  |
| PUT    | `/api/v1/messages/{id}/read`          | Mark message read        | Yes  |

### Reviews
| Method | Endpoint                           | Description              | Auth |
|--------|------------------------------------|--------------------------|------|
| POST   | `/api/v1/reviews`                  | Create review            | User |
| GET    | `/api/v1/properties/{id}/reviews`  | Get property reviews     | No   |

### Memberships
| Method | Endpoint                           | Description              | Auth |
|--------|------------------------------------|--------------------------|------|
| GET    | `/api/v1/memberships/plans`        | List available plans     | No   |
| POST   | `/api/v1/memberships/subscribe`    | Subscribe to plan        | Host |
| GET    | `/api/v1/memberships/current`      | Current membership       | Host |
| PUT    | `/api/v1/memberships/cancel`       | Cancel membership        | Host |
| POST   | `/api/v1/memberships/webhook`      | Payment gateway webhook  | No   |

### Admin
| Method | Endpoint                           | Description              | Auth  |
|--------|------------------------------------|--------------------------|-------|
| GET    | `/api/v1/admin/users`              | List all users           | Admin |
| GET    | `/api/v1/admin/properties`         | List all properties      | Admin |
| GET    | `/api/v1/admin/memberships`        | List all memberships     | Admin |
| GET    | `/api/v1/admin/dashboard`          | Platform metrics         | Admin |
| PUT    | `/api/v1/admin/users/{id}/status`  | Enable/disable user      | Admin |

---

## 6. Security Architecture

```
┌────────────────────────────────────────────────┐
│              SECURITY LAYERS                    │
│                                                 │
│  1. TRANSPORT    — HTTPS/TLS everywhere         │
│  2. AUTH         — JWT (short-lived access +    │
│                     long-lived refresh)          │
│  3. RBAC         — Role-based access control    │
│  4. RATE LIMIT   — Redis-backed per-IP/user     │
│  5. INPUT        — Pydantic validation          │
│  6. SQL INJECT   — ORM parameterized queries    │
│  7. XSS          — Output encoding, CSP headers │
│  8. CORS         — Strict origin allowlist      │
│  9. SECRETS      — Env vars, never in code      │
│ 10. PRIVACY      — Host phone hidden by default │
└────────────────────────────────────────────────┘
```

---

## 7. Scaling Strategy

### Phase 1 (0–10K users)
- Single FastAPI instance behind Nginx
- Single PostgreSQL instance
- Redis for caching
- S3 for images

### Phase 2 (10K–100K users)
- Horizontal FastAPI scaling (multiple containers)
- PostgreSQL read replicas
- Redis cluster
- CDN for static assets and images
- Celery workers for async tasks

### Phase 3 (100K+ users)
- Microservice decomposition (auth, listings, bookings, messaging)
- Event-driven architecture (Kafka/RabbitMQ)
- PostgreSQL sharding or Citus
- Elasticsearch for property search
- WebSocket gateway for real-time messaging
- Kubernetes orchestration

---

## 8. Backend Folder Structure

```
backend/
├── alembic/                    # Database migrations
│   ├── versions/
│   └── env.py
├── app/
│   ├── __init__.py
│   ├── main.py                 # FastAPI app factory
│   ├── config.py               # Settings (env-based, 12-factor)
│   ├── database.py             # DB engine & session
│   ├── dependencies.py         # Shared dependencies
│   ├── models/                 # SQLAlchemy models
│   │   ├── __init__.py
│   │   ├── user.py
│   │   ├── property.py
│   │   ├── booking.py
│   │   ├── message.py
│   │   ├── review.py
│   │   └── membership.py
│   ├── schemas/                # Pydantic schemas
│   │   ├── __init__.py
│   │   ├── user.py
│   │   ├── property.py
│   │   ├── booking.py
│   │   ├── message.py
│   │   ├── review.py
│   │   └── membership.py
│   ├── api/                    # Route handlers
│   │   ├── __init__.py
│   │   ├── v1/
│   │   │   ├── __init__.py
│   │   │   ├── router.py       # Aggregated v1 router
│   │   │   ├── auth.py
│   │   │   ├── properties.py
│   │   │   ├── bookings.py
│   │   │   ├── messages.py
│   │   │   ├── reviews.py
│   │   │   ├── memberships.py
│   │   │   └── admin.py
│   ├── services/               # Business logic
│   │   ├── __init__.py
│   │   ├── auth_service.py
│   │   ├── property_service.py
│   │   ├── booking_service.py
│   │   ├── message_service.py
│   │   ├── review_service.py
│   │   ├── membership_service.py
│   │   └── upload_service.py
│   ├── core/                   # Cross-cutting concerns
│   │   ├── __init__.py
│   │   ├── security.py         # JWT, hashing
│   │   ├── permissions.py      # RBAC decorators
│   │   ├── exceptions.py       # Custom exceptions
│   │   └── rate_limiter.py     # Redis rate limiting
│   └── tasks/                  # Celery background tasks
│       ├── __init__.py
│       ├── email_tasks.py
│       └── membership_tasks.py
├── tests/
│   ├── __init__.py
│   ├── conftest.py
│   ├── test_auth.py
│   ├── test_properties.py
│   ├── test_bookings.py
│   ├── test_messages.py
│   ├── test_reviews.py
│   └── test_memberships.py
├── alembic.ini
├── Dockerfile
├── requirements.txt
├── .env.example
└── pyproject.toml
```

---

## 9. Recommended Frontend Structure (Next.js)

```
frontend/
├── src/
│   ├── app/                        # App Router
│   │   ├── (auth)/
│   │   │   ├── login/page.tsx
│   │   │   └── register/page.tsx
│   │   ├── (main)/
│   │   │   ├── page.tsx            # Homepage / search
│   │   │   ├── properties/
│   │   │   │   ├── [id]/page.tsx   # Property detail
│   │   │   │   └── page.tsx        # Search results
│   │   │   ├── bookings/
│   │   │   │   └── page.tsx
│   │   │   ├── messages/
│   │   │   │   └── page.tsx
│   │   │   └── profile/
│   │   │       └── page.tsx
│   │   ├── host/
│   │   │   ├── dashboard/page.tsx
│   │   │   ├── listings/
│   │   │   │   ├── new/page.tsx
│   │   │   │   └── [id]/edit/page.tsx
│   │   │   └── membership/page.tsx
│   │   └── admin/
│   │       ├── dashboard/page.tsx
│   │       ├── users/page.tsx
│   │       └── memberships/page.tsx
│   ├── components/
│   │   ├── ui/                     # Reusable UI components
│   │   ├── property/               # Property-specific
│   │   ├── booking/
│   │   ├── messaging/
│   │   └── layout/
│   ├── lib/
│   │   ├── api.ts                  # API client
│   │   ├── auth.ts                 # Auth utilities
│   │   └── utils.ts
│   ├── hooks/                      # Custom React hooks
│   ├── stores/                     # Zustand state stores
│   └── types/                      # TypeScript types
├── public/
├── next.config.js
├── tailwind.config.ts
├── tsconfig.json
├── Dockerfile
└── package.json
```
