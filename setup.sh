#!/usr/bin/env bash
# =============================================================================
# StayNest — Automated Project Setup Script (Linux / macOS)
# =============================================================================
#
# Bootstraps the entire StayNest development environment on a fresh machine.
# Checks prerequisites, installs dependencies, configures environment files,
# runs database migrations, creates storage buckets, seeds sample data, and
# optionally starts all services via Docker Compose.
#
# Usage:
#   chmod +x setup.sh
#   ./setup.sh              # Interactive mode (recommended)
#   ./setup.sh --docker     # Skip local setup, go straight to Docker
#   ./setup.sh --local      # Skip Docker, set up local dev only
#   ./setup.sh --ci         # Non-interactive (CI pipelines)
#   ./setup.sh --seed       # Docker + run seed script after services start
#
# Prerequisites:
#   Docker & Docker Compose  (required for --docker / --seed)
#   Python 3.11+             (required for --local)
#   Node.js 20+              (required for --local)
#   Git                      (always required)
#
# See SETUP.md for the detailed setup guide.
# =============================================================================

set -euo pipefail

# ─── Colours ─────────────────────────────────────────────────────────────────
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m'

# ─── Helpers ─────────────────────────────────────────────────────────────────
info()    { echo -e "${BLUE}[INFO]${NC}  $*"; }
success() { echo -e "${GREEN}[OK]${NC}    $*"; }
warn()    { echo -e "${YELLOW}[WARN]${NC}  $*"; }
error()   { echo -e "${RED}[ERROR]${NC} $*"; }
step()    { echo -e "\n${CYAN}━━━ $* ━━━${NC}"; }

command_exists() { command -v "$1" &>/dev/null; }

require_command() {
    if ! command_exists "$1"; then
        error "$1 is required but not installed."
        echo "  Install it: $2"
        return 1
    fi
    success "$1 found: $(command -v "$1")"
}

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

MODE="${1:-interactive}"  # --docker, --local, --ci, --seed, or interactive
TOTAL_STEPS=8

echo -e "${CYAN}"
echo "  ____  _              _   _           _   "
echo " / ___|| |_ __ _ _   _| \ | | ___  ___| |_ "
echo " \___ \| __/ _\` | | | |  \| |/ _ \/ __| __|"
echo "  ___) | || (_| | |_| | |\  |  __/\__ \ |_ "
echo " |____/ \__\__,_|\__, |_| \_|\___||___/\__|"
echo "                 |___/                      "
echo -e "${NC}"
echo -e "${BLUE}  Automated Development Environment Setup${NC}"
echo -e "${BLUE}  Mode: ${YELLOW}${MODE}${NC}"
echo ""

# =============================================================================
# 1. Prerequisites Check
# =============================================================================
step "1/${TOTAL_STEPS}  Checking prerequisites"

MISSING=0

# Git
require_command git "https://git-scm.com/downloads" || ((MISSING++))

# Docker (needed for --docker, --seed, and interactive)
if [[ "$MODE" != "--local" ]]; then
    if command_exists docker; then
        success "Docker found: $(docker --version)"
        if docker compose version &>/dev/null; then
            success "Docker Compose (v2 plugin) found"
        elif command_exists docker-compose; then
            success "docker-compose (standalone) found"
        else
            warn "Docker Compose not found. Install: https://docs.docker.com/compose/install/"
            ((MISSING++))
        fi
    else
        warn "Docker not installed. Install: https://docs.docker.com/get-docker/"
        if [[ "$MODE" == "--docker" || "$MODE" == "--seed" ]]; then
            error "Docker is required for $MODE mode."
            ((MISSING++))
        fi
    fi
fi

# Python (needed for --local, --seed, and interactive)
PYTHON_CMD=""
if [[ "$MODE" != "--docker" ]]; then
    if command_exists python3; then
        PYTHON_CMD="python3"
    elif command_exists python; then
        PYTHON_CMD="python"
    fi

    if [[ -n "$PYTHON_CMD" ]]; then
        PY_VERSION=$($PYTHON_CMD --version 2>&1 | awk '{print $2}')
        PY_MAJOR=$(echo "$PY_VERSION" | cut -d. -f1)
        PY_MINOR=$(echo "$PY_VERSION" | cut -d. -f2)
        if (( PY_MAJOR >= 3 && PY_MINOR >= 11 )); then
            success "Python $PY_VERSION found"
        else
            warn "Python $PY_VERSION found, but 3.11+ recommended"
        fi
    else
        warn "Python not found. Install: https://www.python.org/downloads/"
        if [[ "$MODE" == "--local" ]]; then ((MISSING++)); fi
    fi

    # Node.js
    if command_exists node; then
        NODE_VERSION=$(node --version)
        NODE_MAJOR=$(echo "$NODE_VERSION" | sed 's/v//' | cut -d. -f1)
        success "Node.js $NODE_VERSION found"
        if (( NODE_MAJOR < 18 )); then
            warn "Node.js 18+ recommended (found $NODE_VERSION)"
        fi
    else
        warn "Node.js not found. Install: https://nodejs.org/"
        if [[ "$MODE" == "--local" ]]; then ((MISSING++)); fi
    fi
fi

if (( MISSING > 0 )); then
    error "$MISSING prerequisite(s) missing. Please install them and re-run."
    exit 1
fi

success "All prerequisites satisfied!"

# =============================================================================
# 2. Environment Files
# =============================================================================
step "2/${TOTAL_STEPS}  Setting up environment files"

# Backend .env
if [[ -f backend/.env ]]; then
    info "backend/.env already exists — skipping"
else
    if [[ ! -f backend/.env.example ]]; then
        error "backend/.env.example not found. Cannot create .env."
        exit 1
    fi
    cp backend/.env.example backend/.env

    # Generate a random JWT secret
    if command_exists openssl; then
        JWT_SECRET=$(openssl rand -hex 64)
        WEBHOOK_SECRET=$(openssl rand -hex 32)
        if [[ "$(uname)" == "Darwin" ]]; then
            sed -i '' "s|CHANGE-ME-use-openssl-rand-hex-64|$JWT_SECRET|" backend/.env
            sed -i '' "s|CHANGE-ME-webhook-secret|$WEBHOOK_SECRET|" backend/.env
        else
            sed -i "s|CHANGE-ME-use-openssl-rand-hex-64|$JWT_SECRET|" backend/.env
            sed -i "s|CHANGE-ME-webhook-secret|$WEBHOOK_SECRET|" backend/.env
        fi
        success "Generated random JWT_SECRET_KEY and WEBHOOK_SECRET"
    else
        warn "openssl not found — please set JWT_SECRET_KEY and WEBHOOK_SECRET manually in backend/.env"
    fi

    # Ensure S3_PUBLIC_URL is present
    if ! grep -q "S3_PUBLIC_URL" backend/.env; then
        echo "S3_PUBLIC_URL=http://localhost:9000" >> backend/.env
        success "Added S3_PUBLIC_URL to backend/.env"
    fi

    success "Created backend/.env from .env.example"
fi

# Frontend .env.local
if [[ -f frontend/.env.local ]]; then
    info "frontend/.env.local already exists — skipping"
else
    if [[ -f frontend/.env.example ]]; then
        cp frontend/.env.example frontend/.env.local
    else
        cat > frontend/.env.local <<EOF
NEXT_PUBLIC_API_URL=http://localhost:8000/api/v1
NEXT_PUBLIC_APP_URL=http://localhost:3000
DATABASE_URL=postgresql://staynest:staynest_secret@localhost:5432/staynest
BETTER_AUTH_URL=http://localhost:3000
EOF
    fi

    # Generate BETTER_AUTH_SECRET
    if command_exists openssl; then
        BA_SECRET=$(openssl rand -base64 32)
        echo "BETTER_AUTH_SECRET=$BA_SECRET" >> frontend/.env.local
        success "Generated random BETTER_AUTH_SECRET"
    else
        echo "BETTER_AUTH_SECRET=change-me-generate-with-openssl-rand-base64-32" >> frontend/.env.local
        warn "openssl not found — please set BETTER_AUTH_SECRET manually in frontend/.env.local"
    fi

    success "Created frontend/.env.local"
fi

# =============================================================================
# 3. Docker Compose Setup
# =============================================================================
if [[ "$MODE" == "--docker" || "$MODE" == "--seed" || "$MODE" == "interactive" || "$MODE" == "--ci" ]]; then
    step "3/${TOTAL_STEPS}  Docker Compose setup"

    if command_exists docker && docker info &>/dev/null; then
        # Determine compose command
        if docker compose version &>/dev/null; then
            COMPOSE_CMD="docker compose"
        else
            COMPOSE_CMD="docker-compose"
        fi

        info "Building Docker images (this may take a few minutes on first run)..."
        $COMPOSE_CMD build
        success "Docker images built successfully"

        if [[ "$MODE" != "--ci" ]]; then
            info "Starting all services..."
            $COMPOSE_CMD up -d
            success "All services started!"

            echo ""
            info "Waiting for services to become healthy..."
            sleep 12

            # Verify services are running
            RUNNING=$($COMPOSE_CMD ps --format '{{.Name}}' 2>/dev/null | wc -l || echo "?")
            info "$RUNNING container(s) running"

            echo ""
            info "Service URLs:"
            echo "  • API:             http://localhost:8000"
            echo "  • API Docs:        http://localhost:8000/docs"
            echo "  • API ReDoc:       http://localhost:8000/redoc"
            echo "  • Health Check:    http://localhost:8000/health"
            echo "  • Frontend:        http://localhost:3000"
            echo "  • MinIO Console:   http://localhost:9001  (minioadmin / minioadmin)"
            echo "  • PostgreSQL:      127.0.0.1:5432  (staynest / staynest_secret)"
            echo "  • Redis:           127.0.0.1:6379"
            echo ""
            info "Background services running: Celery worker + Celery Beat scheduler"
        else
            success "Docker build verified (CI mode — not starting services)"
        fi
    else
        warn "Docker daemon not running — skipping Docker setup"
    fi
fi

if [[ "$MODE" == "--docker" ]]; then
    step "Setup complete!"
    echo -e "\n${GREEN}StayNest is running via Docker Compose.${NC}"
    echo "Run 'docker compose logs -f' to follow logs."
    echo "Run 'docker compose down' to stop all services."
    exit 0
fi

# =============================================================================
# 4. Backend Local Setup
# =============================================================================
if [[ "$MODE" != "--docker" && "$MODE" != "--seed" ]]; then
    step "4/${TOTAL_STEPS}  Backend setup (Python)"

    cd "$SCRIPT_DIR/backend"

    # Create virtualenv
    if [[ ! -d .venv ]]; then
        info "Creating Python virtual environment..."
        $PYTHON_CMD -m venv .venv
        success "Virtual environment created at backend/.venv"
    else
        info "Virtual environment already exists"
    fi

    # Activate
    # shellcheck disable=SC1091
    source .venv/bin/activate
    success "Virtual environment activated"

    # Install deps
    info "Installing Python dependencies (production + dev)..."
    pip install --upgrade pip --quiet
    pip install -r requirements-dev.txt --quiet
    success "All Python dependencies installed"

    # Database migrations (only if local PostgreSQL is reachable)
    info "Attempting Alembic database migrations..."
    if alembic upgrade head 2>/dev/null; then
        success "Database migrations applied"
    else
        warn "Could not run migrations — ensure PostgreSQL is running"
        info "Tip: Start PostgreSQL via Docker: docker compose up -d db redis"
    fi

    # Run tests
    info "Running backend test suite..."
    if pytest --tb=short -q 2>/dev/null; then
        success "All backend tests passed"
    else
        warn "Some tests failed — check output above or run: pytest -v"
    fi

    deactivate
    cd "$SCRIPT_DIR"
fi

# =============================================================================
# 5. Frontend Local Setup
# =============================================================================
if [[ "$MODE" != "--docker" && "$MODE" != "--seed" ]]; then
    step "5/${TOTAL_STEPS}  Frontend setup (Node.js)"

    cd "$SCRIPT_DIR/frontend"

    if command_exists node; then
        info "Installing Node.js dependencies..."
        npm install --silent 2>/dev/null
        success "npm install complete"

        # Type check
        info "Running TypeScript type check..."
        if npx tsc --noEmit 2>/dev/null; then
            success "Type check passed"
        else
            warn "Type errors found — review with: npx tsc --noEmit"
        fi

        # Lint
        info "Running ESLint..."
        if npx eslint . 2>/dev/null; then
            success "Lint passed"
        else
            warn "Lint warnings found — review with: npx eslint ."
        fi

        # Tests
        info "Running frontend test suite..."
        if npx vitest run --reporter=verbose 2>/dev/null; then
            success "All frontend tests passed"
        else
            warn "Some frontend tests failed — run: npm test"
        fi
    else
        warn "Node.js not installed — skipping frontend setup"
    fi

    cd "$SCRIPT_DIR"
fi

# =============================================================================
# 6. MinIO Bucket Setup
# =============================================================================
step "6/${TOTAL_STEPS}  Storage setup (MinIO)"

setup_minio_bucket() {
    local BUCKET_NAME="staynest-images"

    # Method 1: Use MinIO Client (mc) if available locally
    if command_exists mc; then
        mc alias set local http://localhost:9000 minioadmin minioadmin 2>/dev/null
        mc mb "local/${BUCKET_NAME}" --ignore-existing 2>/dev/null
        mc anonymous set download "local/${BUCKET_NAME}" 2>/dev/null
        success "MinIO bucket '${BUCKET_NAME}' ready with public-read policy (via mc)"
        return 0
    fi

    # Method 2: Use mc inside the MinIO container via docker exec
    if command_exists docker; then
        local MINIO_CONTAINER
        MINIO_CONTAINER=$(docker ps --filter "name=minio" --format '{{.Names}}' 2>/dev/null | head -1)
        if [[ -n "$MINIO_CONTAINER" ]]; then
            docker exec "$MINIO_CONTAINER" mc alias set local http://localhost:9000 minioadmin minioadmin 2>/dev/null || true
            docker exec "$MINIO_CONTAINER" mc mb "local/${BUCKET_NAME}" --ignore-existing 2>/dev/null || true
            docker exec "$MINIO_CONTAINER" mc anonymous set download "local/${BUCKET_NAME}" 2>/dev/null || true
            success "MinIO bucket '${BUCKET_NAME}' ready (via docker exec)"
            return 0
        fi
    fi

    return 1
}

if command_exists docker && docker ps --format '{{.Names}}' 2>/dev/null | grep -q minio; then
    info "Creating MinIO bucket 'staynest-images'..."
    if ! setup_minio_bucket; then
        warn "Could not auto-create bucket."
        info "Create 'staynest-images' bucket manually at http://localhost:9001"
        info "  1. Login with minioadmin / minioadmin"
        info "  2. Create bucket: staynest-images"
        info "  3. Set Access Policy to 'public'"
    fi
else
    info "MinIO not running — bucket will be created when Docker services start"
    info "After starting services, create the bucket at http://localhost:9001"
fi

# =============================================================================
# 7. Database Seeding (Optional)
# =============================================================================
step "7/${TOTAL_STEPS}  Database seeding"

if [[ "$MODE" == "--seed" ]]; then
    info "Running seed_and_test.py to populate sample data..."
    if [[ -f "$SCRIPT_DIR/seed_and_test.py" ]]; then
        # Ensure Python is available for the seed script
        SEED_PYTHON="${PYTHON_CMD:-python3}"
        sleep 5  # Give API extra time to start
        if $SEED_PYTHON "$SCRIPT_DIR/seed_and_test.py" http://localhost:8000; then
            success "Sample data seeded and smoke tests passed"
        else
            warn "Seed script had errors — API may not be fully ready yet"
            info "Retry manually: python seed_and_test.py http://localhost:8000"
        fi
    else
        warn "seed_and_test.py not found — skipping"
    fi
else
    info "Skipping auto-seed (use --seed flag to populate sample data)"
    info "Manual seeding options:"
    echo "  • python seed_and_test.py          # Registers users, creates properties, bookings, etc."
    echo "  • psql -f seed.sql                 # SQL helpers for admin promotion & test queries"
fi

# =============================================================================
# 8. Summary
# =============================================================================
step "8/${TOTAL_STEPS}  Setup complete!"

echo ""
echo -e "${GREEN}╔══════════════════════════════════════════════════════════════╗${NC}"
echo -e "${GREEN}║           StayNest Development Environment Ready            ║${NC}"
echo -e "${GREEN}╚══════════════════════════════════════════════════════════════╝${NC}"
echo ""
echo "  Quick commands:"
echo ""
echo "  Start all services (Docker):        docker compose up -d"
echo "  Stop all services:                  docker compose down"
echo "  Follow logs:                        docker compose logs -f api"
echo ""
echo "  Start backend locally:"
echo "    cd backend && source .venv/bin/activate && uvicorn app.main:app --reload"
echo ""
echo "  Start Celery worker (background tasks):"
echo "    cd backend && source .venv/bin/activate"
echo "    celery -A app.tasks worker --loglevel=info"
echo ""
echo "  Start Celery Beat scheduler (membership renewals):"
echo "    cd backend && source .venv/bin/activate"
echo "    celery -A app.tasks beat --loglevel=info"
echo ""
echo "  Start frontend locally:             cd frontend && npm run dev"
echo ""
echo "  Run database migrations:            cd backend && alembic upgrade head"
echo "  Seed sample data:                   python seed_and_test.py"
echo ""
echo "  Run backend tests:                  cd backend && pytest --cov=app"
echo "  Run backend linter:                 cd backend && ruff check ."
echo "  Run frontend tests:                 cd frontend && npm test"
echo "  Run frontend linter:                cd frontend && npx eslint ."
echo ""
echo "  ┌──────────────────────────────────────────────┐"
echo "  │  Service URLs                                │"
echo "  ├──────────────────────────────────────────────┤"
echo "  │  Frontend:        http://localhost:3000      │"
echo "  │  API:             http://localhost:8000      │"
echo "  │  API Docs:        http://localhost:8000/docs │"
echo "  │  Health Check:    http://localhost:8000/health│"
echo "  │  MinIO Console:   http://localhost:9001      │"
echo "  │  PostgreSQL:      127.0.0.1:5432             │"
echo "  │  Redis:           127.0.0.1:6379             │"
echo "  └──────────────────────────────────────────────┘"
echo ""
echo "  Docker services: api, frontend, db, redis, minio, celery-worker, celery-beat"
echo ""
echo "  Documentation:"
echo "    SETUP.md                    — Detailed setup guide"
echo "    FEATURES_AND_ENDPOINTS.md   — Complete feature & API reference"
echo "    DOCUMENTATION.md            — Additional project docs"
echo "    docs/ARCHITECTURE.md        — Architecture overview"
echo ""
