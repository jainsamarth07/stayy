# StayNest — Setup Guide

Complete guide to setting up the StayNest development environment from scratch.

---

## Table of Contents

1. [Prerequisites](#1-prerequisites)
2. [Quick Start (Docker — Recommended)](#2-quick-start-docker--recommended)
3. [Manual Local Setup](#3-manual-local-setup)
   - [3.1 Clone & Configure](#31-clone--configure)
   - [3.2 Backend Setup (Python)](#32-backend-setup-python)
   - [3.3 Frontend Setup (Node.js)](#33-frontend-setup-nodejs)
   - [3.4 Infrastructure Services](#34-infrastructure-services)
   - [3.5 MinIO Storage Bucket](#35-minio-storage-bucket)
   - [3.6 Database Migrations](#36-database-migrations)
4. [Running the Application](#4-running-the-application)
5. [Seeding Sample Data](#5-seeding-sample-data)
6. [Running Tests](#6-running-tests)
7. [Environment Variables Reference](#7-environment-variables-reference)
8. [Docker Compose Services](#8-docker-compose-services)
9. [Automated Setup Scripts](#9-automated-setup-scripts)
10. [Troubleshooting](#10-troubleshooting)
11. [Related Documentation](#11-related-documentation)

---

## 1. Prerequisites

| Tool | Minimum Version | Purpose | Install Link |
|------|----------------|---------|-------------|
| **Git** | Any | Source control | https://git-scm.com/downloads |
| **Docker Desktop** | 24.x+ | Container orchestration | https://docs.docker.com/get-docker/ |
| **Docker Compose** | v2 plugin | Multi-container setup | Bundled with Docker Desktop |
| **Python** | 3.11+ | Backend runtime | https://www.python.org/downloads/ |
| **Node.js** | 18+ (20 LTS recommended) | Frontend runtime | https://nodejs.org/ |
| **npm** | 9+ | Package manager | Bundled with Node.js |

> **Docker-only mode**: If you plan to run everything via Docker Compose, only Docker and Git are required. Python and Node.js are needed only for local development.

### Verify Prerequisites

```bash
# Check all tools
git --version          # git version 2.x+
docker --version       # Docker version 24.x+
docker compose version # Docker Compose version v2.x+
python --version       # Python 3.11+
node --version         # v18+ or v20+
npm --version          # 9+
```

---

## 2. Quick Start (Docker — Recommended)

The fastest way to get StayNest running. Starts all 6 services (API, Celery worker, PostgreSQL, Redis, MinIO, Frontend) in Docker containers.

### Step 1: Clone the Repository

```bash
git clone <repository-url> staynest
cd staynest
```

### Step 2: Run the Automated Setup Script

**Linux / macOS:**
```bash
chmod +x setup.sh
./setup.sh --docker
```

**Windows (PowerShell):**
```powershell
.\setup.ps1 -Mode Docker
```

### Step 3: Verify Services

```bash
# Check container status
docker compose ps

# Health check
curl http://localhost:8000/health
# Expected: {"status": "healthy", "version": "0.1.0"}
```

### Step 4: Create MinIO Bucket

After services start, create the image storage bucket:

```bash
# Option A: Via MinIO Console (browser)
# 1. Open http://localhost:9001
# 2. Login: minioadmin / minioadmin
# 3. Create bucket: staynest-images
# 4. Set Access Policy to "public"

# Option B: Via docker exec
docker exec <minio-container-name> mc alias set local http://localhost:9000 minioadmin minioadmin
docker exec <minio-container-name> mc mb local/staynest-images --ignore-existing
docker exec <minio-container-name> mc anonymous set download local/staynest-images
```

### Step 5: Access the Application

| Service | URL | Credentials |
|---------|-----|-------------|
| **Frontend** | http://localhost:3000 | — |
| **API** | http://localhost:8000 | — |
| **API Docs (Swagger)** | http://localhost:8000/docs | — |
| **API Docs (ReDoc)** | http://localhost:8000/redoc | — |
| **Health Check** | http://localhost:8000/health | — |
| **MinIO Console** | http://localhost:9001 | minioadmin / minioadmin |
| **PostgreSQL** | localhost:5432 | staynest / staynest_secret |
| **Redis** | localhost:6379 | — |

---

## 3. Manual Local Setup

For development where you want hot-reload, debugging, and direct access to the source.

### 3.1 Clone & Configure

```bash
git clone <repository-url> staynest
cd staynest
```

**Create environment files:**

```bash
# Backend
cp backend/.env.example backend/.env

# Frontend
cp frontend/.env.example frontend/.env.local
```

**Edit `backend/.env`** — Set a secure JWT secret:

```bash
# Linux/macOS — auto-generate
JWT_SECRET=$(openssl rand -hex 64)
sed -i "s|CHANGE-ME-use-openssl-rand-hex-64|$JWT_SECRET|" backend/.env
```

```powershell
# Windows PowerShell — auto-generate
$jwt = -join ((1..64) | ForEach-Object { "{0:x2}" -f (Get-Random -Min 0 -Max 256) })
(Get-Content backend\.env) -replace 'CHANGE-ME-use-openssl-rand-hex-64', $jwt | Set-Content backend\.env
```

Ensure `S3_PUBLIC_URL` is set in `backend/.env`:
```dotenv
S3_PUBLIC_URL=http://localhost:9000
```

### 3.2 Backend Setup (Python)

```bash
cd backend

# Create virtual environment
python -m venv .venv

# Activate (choose your OS)
source .venv/bin/activate        # Linux / macOS
.\.venv\Scripts\Activate.ps1     # Windows PowerShell
.\.venv\Scripts\activate.bat     # Windows CMD

# Install all dependencies (production + dev/test)
pip install --upgrade pip
pip install -r requirements-dev.txt
```

**What gets installed:**

| Package | Purpose |
|---------|---------|
| `fastapi` | Async web framework |
| `uvicorn[standard]` | ASGI server |
| `sqlalchemy[asyncio]` | Async ORM |
| `asyncpg` | PostgreSQL async driver |
| `alembic` | Database migration tool |
| `pydantic` / `pydantic-settings` | Data validation & config |
| `python-jose[cryptography]` | JWT token handling |
| `argon2-cffi` | Password hashing |
| `boto3` | S3/MinIO client |
| `redis` | Redis client |
| `celery` | Background task queue |
| `httpx` | Async HTTP client |
| `email-validator` | Email field validation |
| `pytest` / `pytest-asyncio` | Test framework |
| `pytest-cov` | Coverage reporting |
| `ruff` | Linter / formatter |
| `aiosqlite` | SQLite driver for tests |

### 3.3 Frontend Setup (Node.js)

```bash
cd frontend

# Install dependencies
npm install
```

**Key frameworks:**

| Package | Purpose |
|---------|---------|
| `next` 14.x | React metaframework (App Router) |
| `react` 18.x | UI library |
| `zustand` | Lightweight state management |
| `axios` | HTTP client |
| `react-hook-form` + `zod` | Form handling & validation |
| `date-fns` | Date utilities |
| `tailwindcss` | Utility-first CSS |
| `vitest` + `@testing-library/react` | Testing |

### 3.4 Infrastructure Services

The backend requires PostgreSQL, Redis, and MinIO. The easiest way to run them locally is via Docker Compose (just the infrastructure, not the app):

```bash
# Start only infrastructure services
docker compose up -d db redis minio
```

This starts:
- **PostgreSQL 16** on port `5432` (user: `staynest`, password: `staynest_secret`, database: `staynest`)
- **Redis 7** on port `6379`
- **MinIO** on ports `9000` (API) and `9001` (console)

### 3.5 MinIO Storage Bucket

StayNest stores property images in MinIO (S3-compatible). You must create a bucket:

**Option A — MinIO Console (recommended):**
1. Open http://localhost:9001
2. Login with `minioadmin` / `minioadmin`
3. Click **Create Bucket**, name it `staynest-images`
4. Under the bucket settings, set **Access Policy** to `public`

**Option B — MinIO Client (mc):**
```bash
# Install mc: https://min.io/docs/minio/linux/reference/minio-mc.html
mc alias set local http://localhost:9000 minioadmin minioadmin
mc mb local/staynest-images --ignore-existing
mc anonymous set download local/staynest-images
```

**Option C — Docker exec:**
```bash
docker exec <minio-container> mc alias set local http://localhost:9000 minioadmin minioadmin
docker exec <minio-container> mc mb local/staynest-images --ignore-existing
docker exec <minio-container> mc anonymous set download local/staynest-images
```

### 3.6 Database Migrations

Run Alembic migrations to create all tables:

```bash
cd backend
source .venv/bin/activate   # or Windows equivalent

# Apply all migrations
alembic upgrade head

# Verify current revision
alembic current
```

> **Note**: The `DATABASE_URL` in `backend/.env` must point to a running PostgreSQL instance. If using Docker infrastructure: `postgresql+asyncpg://staynest:staynest_secret@localhost:5432/staynest`

---

## 4. Running the Application

### Docker Compose (All Services)

```bash
# Start everything
docker compose up -d

# Follow logs
docker compose logs -f

# Follow specific service logs
docker compose logs -f api
docker compose logs -f frontend

# Stop everything
docker compose down

# Stop and remove volumes (reset data)
docker compose down -v
```

### Local Development (Hybrid)

Start infrastructure via Docker, then run backend and frontend locally for hot-reload:

```bash
# Terminal 1: Infrastructure
docker compose up -d db redis minio

# Terminal 2: Backend API (hot-reload)
cd backend
source .venv/bin/activate
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# Terminal 3: Celery Worker (background tasks like emails)
cd backend
source .venv/bin/activate
celery -A app.tasks.email_tasks worker --loglevel=info

# Terminal 4: Frontend (hot-reload)
cd frontend
npm run dev
```

**Windows PowerShell equivalents:**

```powershell
# Terminal 2: Backend API
cd backend; .\.venv\Scripts\Activate.ps1
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# Terminal 3: Celery Worker
cd backend; .\.venv\Scripts\Activate.ps1
celery -A app.tasks.email_tasks worker --loglevel=info

# Terminal 4: Frontend
cd frontend; npm run dev
```

---

## 5. Seeding Sample Data

### Option A: Automated Seed Script (Recommended)

The `seed_and_test.py` script registers users, creates properties, bookings, reviews, messages, and runs a full smoke test against the API:

```bash
# Ensure the API is running first (Docker or local)
python seed_and_test.py                        # default: http://localhost:8000
python seed_and_test.py http://localhost:8000   # explicit base URL
```

**What it creates:**
- A regular **user** (guest)
- A **host** with membership
- An **admin** user
- Sample property listings
- A booking (guest → host property)
- A review after checkout
- Messages between guest and host
- An offer negotiation

### Option B: SQL Seed Helpers

```bash
# Connect to the database
docker exec -it <db_container> psql -U staynest staynest

# Or locally
psql -U staynest -d staynest -f seed.sql
```

The `seed.sql` file contains useful queries for:
- Promoting a user to admin
- Making a user a host
- Inspecting users, properties, bookings

### Option C: Setup Script with Auto-Seed

```bash
# Linux / macOS
./setup.sh --seed

# Windows PowerShell
.\setup.ps1 -Mode Seed
```

This runs `--docker` mode, then automatically executes `seed_and_test.py` after all services are running.

---

## 6. Running Tests

### Backend Tests

```bash
cd backend
source .venv/bin/activate   # or Windows: .\.venv\Scripts\Activate.ps1

# Run all tests
pytest

# With coverage
pytest --cov=app --cov-report=term-missing

# Verbose output
pytest -v --tb=short

# Specific test file
pytest tests/test_auth.py -v
pytest tests/test_properties.py -v

# Run only one test
pytest tests/test_bookings.py::test_create_booking -v
```

**Backend test files:**

| File | Tests |
|------|-------|
| `tests/test_auth.py` | Registration, login, token refresh, profile, password change/reset |
| `tests/test_properties.py` | CRUD, search, filtering, sorting, hourly config |
| `tests/test_bookings.py` | Create, list, status transitions, pricing |
| `tests/test_offers.py` | Create, accept, reject, counter, withdraw, auto-booking |
| `tests/test_reviews.py` | Submit, list by property, host reviews |
| `tests/test_messages.py` | Conversations, send/read messages |
| `tests/test_memberships.py` | Plans, subscribe, current, cancel |
| `tests/test_admin.py` | Dashboard stats, user management, oversight |
| `tests/test_upload.py` | Image upload to MinIO |

> **Note**: Backend tests use `aiosqlite` (in-memory SQLite) so they don't require a running PostgreSQL instance.

### Frontend Tests

```bash
cd frontend

# Run all tests
npm test

# Watch mode (re-run on file changes)
npm run test:watch

# With coverage
npm run test:coverage

# Specific test file
npx vitest run src/__tests__/hooks/use-debounce.test.ts
```

**Frontend test categories:**

| Directory | Tests |
|-----------|-------|
| `src/__tests__/components/` | Component rendering, user interaction |
| `src/__tests__/hooks/` | Custom React hooks |
| `src/__tests__/stores/` | Zustand store logic |

---

## 7. Environment Variables Reference

### Backend (`backend/.env`)

| Variable | Default | Description |
|----------|---------|-------------|
| `APP_ENV` | `development` | Environment: development, staging, production |
| `DEBUG` | `true` | Enable debug logging |
| `DATABASE_URL` | `postgresql+asyncpg://staynest:staynest_secret@localhost:5432/staynest` | PostgreSQL connection string (async) |
| `DATABASE_ECHO` | `false` | Log all SQL queries |
| `REDIS_URL` | `redis://localhost:6379/0` | Redis connection (caching, sessions) |
| `JWT_SECRET_KEY` | `CHANGE-ME-...` | **Must change!** Secret for signing JWT tokens |
| `JWT_ALGORITHM` | `HS256` | JWT signing algorithm |
| `JWT_ACCESS_TOKEN_EXPIRE_MINUTES` | `30` | Access token lifetime |
| `JWT_REFRESH_TOKEN_EXPIRE_DAYS` | `7` | Refresh token lifetime |
| `S3_ENDPOINT_URL` | `http://localhost:9000` | MinIO / S3 endpoint (internal) |
| `S3_PUBLIC_URL` | `http://localhost:9000` | MinIO / S3 public-facing URL (for image URLs returned to client) |
| `S3_ACCESS_KEY_ID` | `minioadmin` | MinIO access key |
| `S3_SECRET_ACCESS_KEY` | `minioadmin` | MinIO secret key |
| `S3_BUCKET_NAME` | `staynest-images` | Image storage bucket name |
| `S3_REGION` | `us-east-1` | S3 region |
| `CORS_ORIGINS` | `["http://localhost:3000"]` | Allowed CORS origins (JSON array) |
| `CELERY_BROKER_URL` | `redis://localhost:6379/1` | Celery broker (Redis DB 1) |
| `RATE_LIMIT_PER_MINUTE` | `60` | API rate limit per IP per minute |

### Frontend (`frontend/.env.local`)

| Variable | Default | Description |
|----------|---------|-------------|
| `NEXT_PUBLIC_API_URL` | `http://localhost:8000/api/v1` | Backend API base URL |

---

## 8. Docker Compose Services

The `docker-compose.yml` defines 6 services:

| Service | Image | Ports | Notes |
|---------|-------|-------|-------|
| `api` | Custom (Python 3.11-slim) | 8000 | FastAPI backend, 4 Uvicorn workers |
| `celery-worker` | Same as api | — | Background task processor |
| `db` | `postgres:16-alpine` | 5432 | Persistent volume `postgres_data` |
| `redis` | `redis:7-alpine` | 6379 | Persistent volume `redis_data` |
| `minio` | `minio/minio:latest` | 9000, 9001 | S3-compatible storage, console on 9001 |
| `frontend` | Custom (Node 20-alpine) | 3000 | Next.js standalone build |

**Dependency chain:** `db` + `redis` → `api` → `celery-worker` → `frontend`

**Persistent volumes:**
- `postgres_data` — Database files
- `redis_data` — Redis AOF/RDB
- `minio_data` — Uploaded images

```bash
# Common Docker Compose commands
docker compose up -d               # Start all
docker compose down                # Stop all
docker compose down -v             # Stop + remove volumes (reset data)
docker compose restart api         # Restart one service
docker compose logs -f api         # Follow logs
docker compose exec db psql -U staynest staynest  # Connect to DB
docker compose ps                  # Show running services
```

---

## 9. Automated Setup Scripts

Two scripts are provided for one-command setup:

### Linux / macOS: `setup.sh`

```bash
chmod +x setup.sh

# Modes:
./setup.sh              # Interactive (Docker + Local)
./setup.sh --docker     # Docker only — build & start containers
./setup.sh --local      # Local only — venv, npm install, migrations, tests
./setup.sh --seed       # Docker + seed sample data after services start
./setup.sh --ci         # CI — build only, don't start services
```

### Windows: `setup.ps1`

```powershell
# If execution policy blocks:
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass

# Modes:
.\setup.ps1                # Interactive (Docker + Local)
.\setup.ps1 -Mode Docker   # Docker only
.\setup.ps1 -Mode Local    # Local only
.\setup.ps1 -Mode Seed     # Docker + seed sample data
.\setup.ps1 -Mode CI       # CI mode
```

### What the Scripts Do (8 Steps)

| Step | Description |
|------|-------------|
| 1. Prerequisites | Checks Git, Docker, Python, Node.js availability and versions |
| 2. Environment Files | Copies `.env.example` → `.env`, generates JWT secret, ensures `S3_PUBLIC_URL` |
| 3. Docker Compose | Builds images, starts containers, waits for health checks |
| 4. Backend Setup | Creates venv, installs deps, runs migrations, runs tests |
| 5. Frontend Setup | Runs `npm install`, TypeScript check, ESLint, Vitest tests |
| 6. MinIO Bucket | Creates `staynest-images` bucket with public-read policy |
| 7. Database Seeding | (--seed mode) Runs `seed_and_test.py` for sample data |
| 8. Summary | Prints quick-command reference and service URLs |

---

## 10. Troubleshooting

### Docker Issues

**"Cannot connect to the Docker daemon"**
- Ensure Docker Desktop is running
- On Linux: `sudo systemctl start docker`

**Port conflicts (address already in use)**
```bash
# Find what's using the port
lsof -i :8000   # Linux/macOS
netstat -ano | findstr :8000  # Windows

# Stop conflicting process or change ports in docker-compose.yml
```

**Container keeps restarting**
```bash
docker compose logs api   # Check error logs
docker compose restart api
```

### Backend Issues

**"Could not run migrations"**
- Ensure PostgreSQL is running: `docker compose up -d db`
- Check `DATABASE_URL` in `backend/.env`
- Verify connectivity: `psql -U staynest -h localhost staynest`

**"ModuleNotFoundError"**
- Ensure venv is activated: `source backend/.venv/bin/activate`
- Reinstall deps: `pip install -r requirements-dev.txt`

**"JWT_SECRET_KEY is placeholder"**
- Generate a proper secret: `openssl rand -hex 64`
- Update `JWT_SECRET_KEY` in `backend/.env`

### Frontend Issues

**"NEXT_PUBLIC_API_URL undefined"**
- Ensure `frontend/.env.local` exists with: `NEXT_PUBLIC_API_URL=http://localhost:8000/api/v1`
- Restart the dev server after changing env vars

**"CORS error" in browser**
- Verify `CORS_ORIGINS` in `backend/.env` includes `http://localhost:3000`

### MinIO Issues

**"Bucket not found" or image upload fails**
- Create the bucket: visit http://localhost:9001 → Create Bucket: `staynest-images`
- Set bucket Access Policy to **public**
- Verify `S3_ENDPOINT_URL` and `S3_PUBLIC_URL` are correct in `backend/.env`

**Uploaded images return 403**
- The bucket needs public-read policy: `mc anonymous set download local/staynest-images`

### Test Issues

**Backend tests fail with "database" errors**
- Backend tests use in-memory SQLite (`aiosqlite`), no database needed
- Ensure `aiosqlite` is installed: `pip install aiosqlite`

**Frontend tests fail with "ReferenceError"**
- Run `npm install` to ensure all devDependencies are present
- Check the test setup file exists: `frontend/src/__tests__/setup.tsx`

---

## 11. Related Documentation

| Document | Description |
|----------|-------------|
| [README.md](README.md) | Project overview and quickstart |
| [FEATURES_AND_ENDPOINTS.md](FEATURES_AND_ENDPOINTS.md) | Complete feature list, 48 API endpoints, role-wise breakdown |
| [DOCUMENTATION.md](DOCUMENTATION.md) | Additional project documentation |
| [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) | Architecture overview and design decisions |
| [PROJECT_REFERENCE.md](PROJECT_REFERENCE.md) | Additional project reference material |

---

*Last updated: March 2026*
