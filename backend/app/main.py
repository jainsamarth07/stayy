"""FastAPI application factory and lifespan management."""

import logging
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.api.v1.router import api_v1_router
from app.config import settings
from app.core.csrf import CSRFMiddleware
from app.core.rate_limiter import RateLimitMiddleware

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Application lifespan: startup and shutdown events."""
    # Configure structured logging first
    from app.core.logging_config import setup_logging
    setup_logging()

    # Startup — initialise Redis for rate limiting
    try:
        import redis.asyncio as aioredis
        app.state.redis = aioredis.from_url(
            settings.REDIS_URL, decode_responses=True
        )
        await app.state.redis.ping()
    except Exception:
        app.state.redis = None  # Rate limiting falls back to no-op

    # Ensure MinIO bucket exists and has a public-read policy so browser <img>
    # tags can load uploaded images directly without 403 Access Denied errors.
    try:
        from app.services.upload_service import get_s3_client, _ensure_bucket_exists
        _ensure_bucket_exists(get_s3_client())
        logger.info("MinIO bucket policy verified on startup")
    except Exception as exc:  # noqa: BLE001
        logger.warning("Could not verify MinIO bucket policy on startup: %s", exc)

    yield

    # Shutdown — close Redis connection
    if getattr(app.state, "redis", None) is not None:
        await app.state.redis.close()


def create_app() -> FastAPI:
    """Create and configure the FastAPI application."""
    app = FastAPI(
        title=settings.APP_TITLE,
        version=settings.APP_VERSION,
        docs_url="/docs",
        redoc_url="/redoc",
        lifespan=lifespan,
    )

    # Middleware registration order matters in Starlette: add_middleware() is LIFO —
    # the LAST registered middleware becomes the OUTERMOST wrapper.
    # CORS must be outermost so that ALL responses (including CSRF 403s, rate-limit
    # 429s, and unhandled 500s) carry the Access-Control-Allow-Origin header.
    # Order: CORS (outermost) → RateLimit → CSRF → App (innermost)

    # Global rate limiting — per-IP caps on all API routes
    app.add_middleware(RateLimitMiddleware)

    # CSRF — block cross-origin state-mutating requests
    app.add_middleware(CSRFMiddleware, allowed_origins=settings.CORS_ORIGINS)

    # CORS — must be registered LAST so it wraps everything else
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.CORS_ORIGINS,
        allow_credentials=True,
        allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
        allow_headers=["Authorization", "Content-Type", "X-Webhook-Secret"],
    )

    # Simple liveness probe — no DB / Redis dependency
    @app.get("/ping", tags=["health"])
    async def ping() -> dict:
        return {"status": "ok"}

    # Routers
    app.include_router(api_v1_router, prefix="/api/v1")

    # --- Global exception handlers ---
    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(
        request: Request, exc: RequestValidationError,
    ) -> JSONResponse:
        """Return 422 with structured validation error — never expose internals."""
        return JSONResponse(
            status_code=422,
            content={"detail": exc.errors()},
        )

    @app.exception_handler(Exception)
    async def unhandled_exception_handler(request: Request, exc: Exception) -> JSONResponse:
        """Catch-all: log the real error, return a generic 500 to the client."""
        logger.exception("Unhandled error on %s %s", request.method, request.url.path)
        return JSONResponse(
            status_code=500,
            content={"detail": "Internal server error"},
        )

    @app.get("/health", tags=["health"])
    async def health_check() -> dict:
        """Deep health check — verifies DB and Redis connectivity."""
        from sqlalchemy import text

        from app.database import async_session_factory

        checks: dict[str, str] = {"version": settings.APP_VERSION}

        # Database check
        try:
            async with async_session_factory() as session:
                await session.execute(text("SELECT 1"))
            checks["database"] = "ok"
        except Exception:
            checks["database"] = "unavailable"

        # Redis check
        redis = getattr(app.state, "redis", None)
        if redis is not None:
            try:
                await redis.ping()
                checks["redis"] = "ok"
            except Exception:
                checks["redis"] = "unavailable"
        else:
            checks["redis"] = "not_configured"

        all_ok = checks.get("database") == "ok" and checks.get("redis") != "unavailable"
        checks["status"] = "healthy" if all_ok else "degraded"
        return checks

    return app


app = create_app()
