# StayNest — Commission-Free Rental Marketplace

A production-grade, two-sided rental marketplace where **hosts pay membership subscriptions** to list properties and **keep 100% of their booking revenue**.

---

## Table of Contents

- [Business Model](#business-model)
- [Tech Stack](#tech-stack)
- [Architecture](#architecture)
- [Getting Started](#getting-started)
- [Backend API](#backend-api)
- [Frontend](#frontend)
- [Database Schema](#database-schema)
- [Testing](#testing)
- [Deployment](#deployment)
- [Security](#security)
- [Scaling Strategy](#scaling-strategy)
- [Environment Variables](#environment-variables)

---

## Business Model

| Aspect              | Detail                                      |
|---------------------|---------------------------------------------|
| Revenue Source      | Host membership subscriptions only          |
| Booking Commission  | **$0** — hosts keep 100%                    |
| Plans               | Basic ($29/mo), Pro ($79/mo), Premium ($199/mo) |
| Listing Limits      | 5 / 25 / Unlimited per plan                |

---

## Tech Stack

| Layer       | Technology                          |
|-------------|-------------------------------------|
| Backend     | **FastAPI** (Python 3.11+)          |
| Frontend    | **Next.js 14** (React, TypeScript)  |
| Database    | **PostgreSQL 16**                   |
| ORM         | SQLAlchemy 2.0 + Alembic            |
| Auth        | JWT (access + refresh tokens)       |
| Cache       | Redis 7                             |
| Storage     | S3-compatible (MinIO for dev)       |
| Task Queue  | Celery + Redis                      |
| Deploy      | Docker + Docker Compose             |

---

## Architecture

See [`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md) for the full system architecture, diagrams, ERD, API design, and scaling strategy.

```
┌─────────────┐     ┌─────────────┐     ┌────────────────┐
│  Next.js UI  │────▶│  FastAPI     │────▶│  PostgreSQL    │
│  (Port 3000) │     │  (Port 8000) │     │  (Port 5432)   │
└─────────────┘     └──────┬──────┘     └────────────────┘
                           │
                    ┌──────┴──────┐
                    │    Redis     │
                    │  (Port 6379) │
                    └─────────────┘
```

---

## Getting Started

### Prerequisites

- Docker & Docker Compose
- (Optional for local dev) Python 3.11+, Node.js 20+

### Quick Start with Docker

```bash
# Clone and navigate to the project
cd "agent project"

# Start all services
docker compose up --build

# Services:
#   API:      http://localhost:8000
#   Docs:     http://localhost:8000/docs
#   Frontend: http://localhost:3000
#   MinIO:    http://localhost:9001
```

### Local Development (Backend)

```bash
cd backend

# Create virtual environment
python -m venv .venv
source .venv/bin/activate  # or .venv\Scripts\activate on Windows

# Install dependencies
pip install -r requirements-dev.txt

# Copy env file
cp .env.example .env

# Run database migrations
alembic upgrade head

# Start the server
uvicorn app.main:app --reload --port 8000
```

### Local Development (Frontend)

```bash
cd frontend

npm install
npm run dev
# → http://localhost:3000
```

---

## Backend API

### Endpoints Summary

| Module       | Base Path                   | Auth     |
|--------------|-----------------------------|----------|
| Auth         | `/api/v1/auth/`             | Public   |
| Properties   | `/api/v1/properties/`       | Mixed    |
| Bookings     | `/api/v1/bookings/`         | Required |
| Messaging    | `/api/v1/conversations/`    | Required |
| Reviews      | `/api/v1/reviews/`          | Mixed    |
| Memberships  | `/api/v1/memberships/`      | Mixed    |
| Admin        | `/api/v1/admin/`            | Admin    |

### Interactive API Docs

- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

### Key Flows

**User Registration → Login:**
```
POST /api/v1/auth/register  →  POST /api/v1/auth/login  →  JWT tokens
```

**Host Membership → List Property:**
```
POST /api/v1/memberships/subscribe  →  POST /api/v1/properties
```

**Messaging → Contact:**
```
POST /api/v1/conversations  →  POST /conversations/{id}/messages
```

---

## Database Schema

**10 tables** with referential integrity and cascade deletes:

- `users` — All platform users (guests, hosts, admins)
- `host_profiles` — Extended host details
- `memberships` — Host subscription plans
- `properties` — Rental listings
- `property_images` — Images per property
- `hourly_booking_configs` — Hourly booking settings
- `bookings` — Reservations (nightly + hourly)
- `conversations` — Message threads
- `messages` — Individual messages
- `reviews` — Guest reviews

---

## Testing

```bash
cd backend

# Run full test suite with coverage
pytest

# Run specific test file
pytest tests/test_auth.py -v

# Run with coverage report
pytest --cov=app --cov-report=html
```

Tests use an isolated SQLite database, test fixtures for users/hosts/admins, and mock external services.

---

## Deployment

### Docker Compose (recommended for development)

```bash
docker compose up --build
```

### Production Deployment

1. Set proper environment variables (see below)
2. Use a managed PostgreSQL (e.g., AWS RDS, Supabase)
3. Use a managed Redis (e.g., AWS ElastiCache)
4. Deploy behind a reverse proxy (Nginx/Traefik) with HTTPS
5. Use real S3 for image storage
6. Set `JWT_SECRET_KEY` to a strong random value
7. Configure CORS for your domain

---

## Security

- **JWT Authentication** with short-lived access tokens (30 min) and refresh tokens (7 days)
- **Role-based access control** (user, host, admin)
- **Password hashing** with bcrypt
- **Input validation** via Pydantic schemas
- **SQL injection prevention** via ORM parameterized queries
- **CORS** with strict origin allowlist
- **Rate limiting** via Redis
- **Host contact privacy** — phone numbers hidden by default
- **Secrets** managed via environment variables (never in code)

---

## Scaling Strategy

| Phase | Users   | Strategy                                                 |
|-------|---------|----------------------------------------------------------|
| 1     | 0–10K   | Single instance, single DB, Redis cache                  |
| 2     | 10K–100K| Horizontal API scaling, DB read replicas, CDN            |
| 3     | 100K+   | Microservices, event-driven, Elasticsearch, WebSockets   |

---

## Environment Variables

See [`.env.example`](backend/.env.example) for all variables:

| Variable                          | Description                       |
|-----------------------------------|-----------------------------------|
| `DATABASE_URL`                    | PostgreSQL connection string      |
| `REDIS_URL`                       | Redis connection string           |
| `JWT_SECRET_KEY`                  | Secret for signing JWTs           |
| `JWT_ACCESS_TOKEN_EXPIRE_MINUTES` | Access token TTL                  |
| `S3_ENDPOINT_URL`                 | S3-compatible storage endpoint    |
| `S3_BUCKET_NAME`                  | Image storage bucket              |
| `CORS_ORIGINS`                    | Allowed frontend origins          |
| `CELERY_BROKER_URL`               | Celery task broker URL            |

---

## Project Structure

```
agent project/
├── docs/
│   └── ARCHITECTURE.md          # Full system architecture & diagrams
├── backend/
│   ├── app/
│   │   ├── main.py              # FastAPI app factory
│   │   ├── config.py            # 12-factor settings
│   │   ├── database.py          # Async DB engine
│   │   ├── dependencies.py      # Auth dependencies
│   │   ├── models/              # SQLAlchemy models (10 tables)
│   │   ├── schemas/             # Pydantic request/response schemas
│   │   ├── api/v1/              # Route handlers
│   │   ├── services/            # Business logic layer
│   │   ├── core/                # Security, permissions, exceptions
│   │   └── tasks/               # Celery background tasks
│   ├── alembic/                 # Database migrations
│   ├── tests/                   # Pytest test suite
│   ├── Dockerfile
│   └── requirements.txt
├── frontend/
│   ├── src/
│   │   ├── app/                 # Next.js App Router pages
│   │   ├── lib/api.ts           # Typed API client
│   │   ├── types/               # TypeScript types
│   │   └── stores/              # Zustand state management
│   ├── Dockerfile
│   └── package.json
└── docker-compose.yml           # Full stack orchestration
```

---

## License

Proprietary — All rights reserved.
