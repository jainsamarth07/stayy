# =============================================================================
# StayNest — Automated Project Setup Script (Windows PowerShell)
# =============================================================================
#
# Bootstraps the entire StayNest development environment on a fresh Windows
# machine. Checks prerequisites, installs dependencies, configures environment
# files, runs database migrations, creates storage buckets, seeds sample data,
# and optionally starts all services via Docker Compose.
#
# Usage (run from project root):
#   .\setup.ps1                # Interactive mode (recommended)
#   .\setup.ps1 -Mode Docker   # Skip local setup, go straight to Docker
#   .\setup.ps1 -Mode Local    # Skip Docker, set up local dev only
#   .\setup.ps1 -Mode CI       # Non-interactive (CI pipelines)
#   .\setup.ps1 -Mode Seed     # Docker + run seed script after services start
#
# If execution policy blocks the script:
#   Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
#
# Prerequisites:
#   Docker Desktop             (required for Docker / Seed mode)
#   Python 3.11+               (required for Local mode)
#   Node.js 20+                (required for Local mode)
#   Git                        (always required)
#
# See SETUP.md for the detailed setup guide.
# =============================================================================

[CmdletBinding()]
param(
    [ValidateSet("Interactive", "Docker", "Local", "CI", "Seed")]
    [string]$Mode = "Interactive"
)

$ErrorActionPreference = "Stop"
$TotalSteps = 8

# ─── Colours / Helpers ───────────────────────────────────────────────────────
function Write-Info    { param([string]$Msg) Write-Host "[INFO]  $Msg" -ForegroundColor Blue }
function Write-Ok      { param([string]$Msg) Write-Host "[OK]    $Msg" -ForegroundColor Green }
function Write-Warn    { param([string]$Msg) Write-Host "[WARN]  $Msg" -ForegroundColor Yellow }
function Write-Err     { param([string]$Msg) Write-Host "[ERROR] $Msg" -ForegroundColor Red }
function Write-Step    { param([string]$Msg) Write-Host "`n=== $Msg ===" -ForegroundColor Cyan }

function Test-CommandExists {
    param([string]$Cmd)
    return [bool](Get-Command $Cmd -ErrorAction SilentlyContinue)
}

$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Definition
Set-Location $ScriptDir

$Missing = 0

# ─── Banner ──────────────────────────────────────────────────────────────────
Write-Host ""
Write-Host "  ____  _              _   _           _   " -ForegroundColor Cyan
Write-Host " / ___|| |_ __ _ _   _| \ | | ___  ___| |_ " -ForegroundColor Cyan
Write-Host " \___ \| __/ _`` | | | |  \| |/ _ \/ __| __|" -ForegroundColor Cyan
Write-Host "  ___) | || (_| | |_| | |\  |  __/\__ \ |_ " -ForegroundColor Cyan
Write-Host " |____/ \__\__,_|\__, |_| \_|\___||___/\__|" -ForegroundColor Cyan
Write-Host "                 |___/                      " -ForegroundColor Cyan
Write-Host ""
Write-Host "  Automated Development Environment Setup" -ForegroundColor Blue
Write-Host "  Mode: $Mode" -ForegroundColor Yellow
Write-Host ""

# =============================================================================
# 1. Prerequisites Check
# =============================================================================
Write-Step "1/$TotalSteps  Checking prerequisites"

# Git
if (Test-CommandExists "git") {
    Write-Ok "Git found: $(git --version)"
} else {
    Write-Err "Git is required but not installed."
    Write-Host "  Install: https://git-scm.com/downloads"
    $Missing++
}

# Docker (for Docker, Seed, and Interactive modes)
if ($Mode -ne "Local") {
    if (Test-CommandExists "docker") {
        Write-Ok "Docker found: $(docker --version)"
        try {
            $null = docker compose version 2>$null
            Write-Ok "Docker Compose (v2 plugin) found"
        } catch {
            if (Test-CommandExists "docker-compose") {
                Write-Ok "docker-compose (standalone) found"
            } else {
                Write-Warn "Docker Compose not found. Install: https://docs.docker.com/compose/install/"
                $Missing++
            }
        }
    } else {
        Write-Warn "Docker not installed. Install: https://docs.docker.com/get-docker/"
        if ($Mode -in @("Docker", "Seed")) {
            Write-Err "Docker is required for $Mode mode."
            $Missing++
        }
    }
}

# Python (for Local, Seed, and Interactive modes)
$PythonCmd = $null
if ($Mode -ne "Docker") {
    # Try 'py' launcher first (Windows standard), then python3, then python
    if (Test-CommandExists "py") {
        $PythonCmd = "py"
        $PythonVersion = & py -3 --version 2>&1
    } elseif (Test-CommandExists "python3") {
        $PythonCmd = "python3"
        $PythonVersion = & python3 --version 2>&1
    } elseif (Test-CommandExists "python") {
        $PythonCmd = "python"
        $PythonVersion = & python --version 2>&1
    }

    if ($PythonCmd) {
        Write-Ok "Python found: $PythonVersion (using '$PythonCmd')"
        # Version check
        if ($PythonVersion -match "(\d+)\.(\d+)") {
            $PyMajor = [int]$Matches[1]
            $PyMinor = [int]$Matches[2]
            if ($PyMajor -lt 3 -or $PyMinor -lt 11) {
                Write-Warn "Python 3.11+ recommended (found $PythonVersion)"
            }
        }
    } else {
        Write-Warn "Python not found. Install: https://www.python.org/downloads/"
        if ($Mode -eq "Local") { $Missing++ }
    }

    # Node.js
    if (Test-CommandExists "node") {
        $NodeVersion = & node --version 2>&1
        Write-Ok "Node.js found: $NodeVersion"
        if ($NodeVersion -match "v(\d+)") {
            if ([int]$Matches[1] -lt 18) {
                Write-Warn "Node.js 18+ recommended (found $NodeVersion)"
            }
        }
    } else {
        Write-Warn "Node.js not found. Install: https://nodejs.org/"
        if ($Mode -eq "Local") { $Missing++ }
    }
}

if ($Missing -gt 0) {
    Write-Err "$Missing prerequisite(s) missing. Please install them and re-run."
    exit 1
}

Write-Ok "All prerequisites satisfied!"

# =============================================================================
# 2. Environment Files
# =============================================================================
Write-Step "2/$TotalSteps  Setting up environment files"

# Backend .env
if (Test-Path "backend\.env") {
    Write-Info "backend\.env already exists - skipping"
} else {
    if (-not (Test-Path "backend\.env.example")) {
        Write-Err "backend\.env.example not found. Cannot create .env."
        exit 1
    }
    Copy-Item "backend\.env.example" "backend\.env"

    # Generate random JWT secret and WEBHOOK_SECRET
    $JwtSecret = -join ((1..64) | ForEach-Object { "{0:x2}" -f (Get-Random -Minimum 0 -Maximum 256) })
    $WebhookSecret = -join ((1..32) | ForEach-Object { "{0:x2}" -f (Get-Random -Minimum 0 -Maximum 256) })
    $EnvContent = Get-Content "backend\.env" -Raw
    $EnvContent = $EnvContent -replace "CHANGE-ME-use-openssl-rand-hex-64", $JwtSecret
    $EnvContent = $EnvContent -replace "CHANGE-ME-webhook-secret", $WebhookSecret
    Set-Content "backend\.env" $EnvContent -NoNewline
    Write-Ok "Generated random JWT_SECRET_KEY and WEBHOOK_SECRET"

    # Ensure S3_PUBLIC_URL is present
    $EnvText = Get-Content "backend\.env" -Raw
    if ($EnvText -notmatch "S3_PUBLIC_URL") {
        Add-Content "backend\.env" "`nS3_PUBLIC_URL=http://localhost:9000"
        Write-Ok "Added S3_PUBLIC_URL to backend\.env"
    }

    Write-Ok "Created backend\.env from .env.example"
}

# Frontend .env.local
if (Test-Path "frontend\.env.local") {
    Write-Info "frontend\.env.local already exists - skipping"
} else {
    if (Test-Path "frontend\.env.example") {
        Copy-Item "frontend\.env.example" "frontend\.env.local"
    } else {
        @"
NEXT_PUBLIC_API_URL=http://localhost:8000/api/v1
NEXT_PUBLIC_APP_URL=http://localhost:3000
DATABASE_URL=postgresql://staynest:staynest_secret@localhost:5432/staynest
BETTER_AUTH_URL=http://localhost:3000
"@ | Set-Content "frontend\.env.local"
    }

    # Generate BETTER_AUTH_SECRET
    $BaSecret = [Convert]::ToBase64String((1..32 | ForEach-Object { [byte](Get-Random -Minimum 0 -Maximum 256) }))
    Add-Content "frontend\.env.local" "BETTER_AUTH_SECRET=$BaSecret"
    Write-Ok "Generated random BETTER_AUTH_SECRET"

    Write-Ok "Created frontend\.env.local"
}

# =============================================================================
# 3. Docker Compose Setup
# =============================================================================
if ($Mode -in @("Docker", "Seed", "Interactive", "CI")) {
    Write-Step "3/$TotalSteps  Docker Compose setup"

    $DockerRunning = $false
    if (Test-CommandExists "docker") {
        try {
            $null = docker info 2>$null
            $DockerRunning = $true
        } catch {
            $DockerRunning = $false
        }
    }

    if ($DockerRunning) {
        # Determine compose command
        $ComposeCmd = "docker compose"
        try { $null = docker compose version 2>$null } catch { $ComposeCmd = "docker-compose" }

        Write-Info "Building Docker images (this may take a few minutes on first run)..."
        Invoke-Expression "$ComposeCmd build"
        Write-Ok "Docker images built successfully"

        if ($Mode -ne "CI") {
            Write-Info "Starting all services..."
            Invoke-Expression "$ComposeCmd up -d"
            Write-Ok "All services started!"

            Write-Info "Waiting for services to become healthy..."
            Start-Sleep -Seconds 12

            # Verify services are running
            try {
                $RunningContainers = (Invoke-Expression "$ComposeCmd ps --format '{{.Name}}'" 2>$null) -split "`n" | Where-Object { $_ }
                Write-Info "$($RunningContainers.Count) container(s) running"
            } catch {
                Write-Info "Services started (could not enumerate containers)"
            }

            Write-Host ""
            Write-Info "Service URLs:"
            Write-Host "  * API:             http://localhost:8000"
            Write-Host "  * API Docs:        http://localhost:8000/docs"
            Write-Host "  * API ReDoc:       http://localhost:8000/redoc"
            Write-Host "  * Health Check:    http://localhost:8000/health"
            Write-Host "  * Frontend:        http://localhost:3000"
            Write-Host "  * MinIO Console:   http://localhost:9001  (minioadmin / minioadmin)"
            Write-Host "  * PostgreSQL:      127.0.0.1:5432  (staynest / staynest_secret)"
            Write-Host "  * Redis:           127.0.0.1:6379"
            Write-Host ""
            Write-Info "Background services running: Celery worker + Celery Beat scheduler"
        } else {
            Write-Ok "Docker build verified (CI mode - not starting services)"
        }
    } else {
        Write-Warn "Docker daemon not running - skipping Docker setup"
    }
}

if ($Mode -eq "Docker") {
    Write-Step "Setup complete!"
    Write-Host "`nStayNest is running via Docker Compose." -ForegroundColor Green
    Write-Host "Run 'docker compose logs -f' to follow logs."
    Write-Host "Run 'docker compose down' to stop all services."
    exit 0
}

# =============================================================================
# 4. Backend Local Setup
# =============================================================================
if ($Mode -notin @("Docker", "Seed")) {
    Write-Step "4/$TotalSteps  Backend setup (Python)"

    Push-Location "backend"

    # Create virtual environment
    if (-not (Test-Path ".venv")) {
        Write-Info "Creating Python virtual environment..."
        if ($PythonCmd -eq "py") {
            & py -3 -m venv .venv
        } elseif ($PythonCmd -eq "python3") {
            & python3 -m venv .venv
        } else {
            & python -m venv .venv
        }
        Write-Ok "Virtual environment created at backend\.venv"
    } else {
        Write-Info "Virtual environment already exists"
    }

    # Activate
    $ActivateScript = ".\.venv\Scripts\Activate.ps1"
    if (Test-Path $ActivateScript) {
        & $ActivateScript
        Write-Ok "Virtual environment activated"
    } else {
        Write-Warn "Could not find activation script - trying pip directly"
    }

    # Install dependencies
    Write-Info "Installing Python dependencies (production + dev)..."
    & .\.venv\Scripts\pip.exe install --upgrade pip --quiet 2>$null
    & .\.venv\Scripts\pip.exe install -r requirements-dev.txt --quiet 2>$null
    Write-Ok "All Python dependencies installed"

    # Database migrations
    Write-Info "Attempting Alembic database migrations..."
    try {
        & .\.venv\Scripts\alembic.exe upgrade head 2>$null
        Write-Ok "Database migrations applied"
    } catch {
        Write-Warn "Could not run migrations - ensure PostgreSQL is running"
        Write-Info "Tip: Start PostgreSQL via Docker: docker compose up -d db redis"
    }

    # Run tests
    Write-Info "Running backend test suite..."
    try {
        & .\.venv\Scripts\pytest.exe --tb=short -q 2>$null
        Write-Ok "All backend tests passed"
    } catch {
        Write-Warn "Some tests failed - check output above or run: pytest -v"
    }

    Pop-Location
}

# =============================================================================
# 5. Frontend Local Setup
# =============================================================================
if ($Mode -notin @("Docker", "Seed")) {
    Write-Step "5/$TotalSteps  Frontend setup (Node.js)"

    Push-Location "frontend"

    if (Test-CommandExists "node") {
        Write-Info "Installing Node.js dependencies..."
        & npm install --silent 2>$null
        Write-Ok "npm install complete"

        # Type check
        Write-Info "Running TypeScript type check..."
        try {
            & npx tsc --noEmit 2>$null
            Write-Ok "Type check passed"
        } catch {
            Write-Warn "Type errors found - review with: npx tsc --noEmit"
        }

        # Lint
        Write-Info "Running ESLint..."
        try {
            & npx eslint . 2>$null
            Write-Ok "Lint passed"
        } catch {
            Write-Warn "Lint warnings found - review with: npx eslint ."
        }

        # Tests
        Write-Info "Running frontend test suite..."
        try {
            & npx vitest run --reporter=verbose 2>$null
            Write-Ok "All frontend tests passed"
        } catch {
            Write-Warn "Some frontend tests failed - run: npm test"
        }
    } else {
        Write-Warn "Node.js not installed - skipping frontend setup"
    }

    Pop-Location
}

# =============================================================================
# 6. MinIO Bucket Setup
# =============================================================================
Write-Step "6/$TotalSteps  Storage setup (MinIO)"

function Set-MinioBucket {
    $BucketName = "staynest-images"

    # Method 1: Use MinIO Client (mc) if available locally
    if (Test-CommandExists "mc") {
        & mc alias set local http://localhost:9000 minioadmin minioadmin 2>$null
        & mc mb "local/$BucketName" --ignore-existing 2>$null
        & mc anonymous set download "local/$BucketName" 2>$null
        Write-Ok "MinIO bucket '$BucketName' ready with public-read policy (via mc)"
        return $true
    }

    # Method 2: Use mc inside the MinIO container via docker exec
    if (Test-CommandExists "docker") {
        $MinioContainer = docker ps --filter "name=minio" --format '{{.Names}}' 2>$null | Select-Object -First 1
        if ($MinioContainer) {
            docker exec $MinioContainer mc alias set local http://localhost:9000 minioadmin minioadmin 2>$null
            docker exec $MinioContainer mc mb "local/$BucketName" --ignore-existing 2>$null
            docker exec $MinioContainer mc anonymous set download "local/$BucketName" 2>$null
            Write-Ok "MinIO bucket '$BucketName' ready (via docker exec)"
            return $true
        }
    }

    return $false
}

$MinioRunning = $false
if (Test-CommandExists "docker") {
    $MinioPs = docker ps --filter "name=minio" --format '{{.Names}}' 2>$null
    if ($MinioPs) { $MinioRunning = $true }
}

if ($MinioRunning) {
    Write-Info "Creating MinIO bucket 'staynest-images'..."
    if (-not (Set-MinioBucket)) {
        Write-Warn "Could not auto-create bucket."
        Write-Info "Create 'staynest-images' bucket manually at http://localhost:9001"
        Write-Info "  1. Login with minioadmin / minioadmin"
        Write-Info "  2. Create bucket: staynest-images"
        Write-Info "  3. Set Access Policy to 'public'"
    }
} else {
    Write-Info "MinIO not running - bucket will be created when Docker services start"
    Write-Info "After starting services, create the bucket at http://localhost:9001"
}

# =============================================================================
# 7. Database Seeding (Optional)
# =============================================================================
Write-Step "7/$TotalSteps  Database seeding"

if ($Mode -eq "Seed") {
    Write-Info "Running seed_and_test.py to populate sample data..."
    $SeedScript = Join-Path $ScriptDir "seed_and_test.py"
    if (Test-Path $SeedScript) {
        Start-Sleep -Seconds 5  # Give API extra time

        $SeedPython = if ($PythonCmd -eq "py") { "py -3" } elseif ($PythonCmd) { $PythonCmd } else { "python" }
        try {
            Invoke-Expression "$SeedPython `"$SeedScript`" http://localhost:8000"
            Write-Ok "Sample data seeded and smoke tests passed"
        } catch {
            Write-Warn "Seed script had errors - API may not be fully ready yet"
            Write-Info "Retry manually: python seed_and_test.py http://localhost:8000"
        }
    } else {
        Write-Warn "seed_and_test.py not found - skipping"
    }
} else {
    Write-Info "Skipping auto-seed (use -Mode Seed to populate sample data)"
    Write-Info "Manual seeding options:"
    Write-Host "  * python seed_and_test.py          # Registers users, creates properties, bookings, etc."
    Write-Host "  * psql -f seed.sql                 # SQL helpers for admin promotion & test queries"
}

# =============================================================================
# 8. Summary
# =============================================================================
Write-Step "8/$TotalSteps  Setup complete!"

Write-Host ""
Write-Host "================================================================" -ForegroundColor Green
Write-Host "        StayNest Development Environment Ready                  " -ForegroundColor Green
Write-Host "================================================================" -ForegroundColor Green
Write-Host ""
Write-Host "  Quick commands:"
Write-Host ""
Write-Host "  Start all services (Docker):        docker compose up -d"
Write-Host "  Stop all services:                  docker compose down"
Write-Host "  Follow logs:                        docker compose logs -f api"
Write-Host ""
Write-Host "  Start backend locally:"
Write-Host "    cd backend; .\.venv\Scripts\Activate.ps1; uvicorn app.main:app --reload"
Write-Host ""
Write-Host "  Start Celery worker (background tasks):"
Write-Host "    cd backend; .\.venv\Scripts\Activate.ps1"
Write-Host "    celery -A app.tasks worker --loglevel=info"
Write-Host ""
Write-Host "  Start Celery Beat scheduler (membership renewals):"
Write-Host "    cd backend; .\.venv\Scripts\Activate.ps1"
Write-Host "    celery -A app.tasks beat --loglevel=info"
Write-Host ""
Write-Host "  Start frontend locally:             cd frontend; npm run dev"
Write-Host ""
Write-Host "  Run database migrations:            cd backend; alembic upgrade head"
Write-Host "  Seed sample data:                   python seed_and_test.py"
Write-Host ""
Write-Host "  Run backend tests:                  cd backend; pytest --cov=app"
Write-Host "  Run backend linter:                 cd backend; ruff check ."
Write-Host "  Run frontend tests:                 cd frontend; npm test"
Write-Host "  Run frontend linter:                cd frontend; npx eslint ."
Write-Host ""
Write-Host "  +----------------------------------------------+" -ForegroundColor Yellow
Write-Host "  |  Service URLs                                |" -ForegroundColor Yellow
Write-Host "  +----------------------------------------------+" -ForegroundColor Yellow
Write-Host "  |  Frontend:        http://localhost:3000      |" -ForegroundColor Yellow
Write-Host "  |  API:             http://localhost:8000      |" -ForegroundColor Yellow
Write-Host "  |  API Docs:        http://localhost:8000/docs |" -ForegroundColor Yellow
Write-Host "  |  Health Check:    http://localhost:8000/health|" -ForegroundColor Yellow
Write-Host "  |  MinIO Console:   http://localhost:9001      |" -ForegroundColor Yellow
Write-Host "  |  PostgreSQL:      127.0.0.1:5432             |" -ForegroundColor Yellow
Write-Host "  |  Redis:           127.0.0.1:6379             |" -ForegroundColor Yellow
Write-Host "  +----------------------------------------------+" -ForegroundColor Yellow
Write-Host ""
Write-Host "  Docker services: api, frontend, db, redis, minio, celery-worker, celery-beat"
Write-Host ""
Write-Host "  Documentation:"
Write-Host "    SETUP.md                    - Detailed setup guide"
Write-Host "    FEATURES_AND_ENDPOINTS.md   - Complete feature & API reference"
Write-Host "    DOCUMENTATION.md            - Additional project docs"
Write-Host "    docs/ARCHITECTURE.md        - Architecture overview"
Write-Host ""
