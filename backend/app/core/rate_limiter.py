"""Redis-backed rate limiter."""

import logging

from fastapi import HTTPException, Request, status
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.responses import JSONResponse, Response

logger = logging.getLogger(__name__)

# Default per-minute limits by method type
_WRITE_LIMIT = 30   # POST, PUT, PATCH, DELETE
_READ_LIMIT = 120   # GET, HEAD, OPTIONS


async def rate_limit_check(request: Request, limit: int = 60) -> None:
    """Explicit per-endpoint rate limit check (use in individual routes).

    Uses Redis INCR with TTL for fixed-window rate limiting.
    Falls back to no-op if Redis is unavailable.
    """
    redis = getattr(request.app.state, "redis", None)
    if redis is None:
        return

    client_ip = request.client.host if request.client else "unknown"
    key = f"rate_limit:{client_ip}:{request.url.path}"

    try:
        current = await redis.incr(key)
        if current == 1:
            await redis.expire(key, 60)
        if current > limit:
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail="Rate limit exceeded. Try again later.",
            )
    except HTTPException:
        raise
    except Exception:
        logger.warning("Rate limiter Redis error — allowing request through", exc_info=True)


class RateLimitMiddleware(BaseHTTPMiddleware):
    """Global rate limiter — applies default per-IP limits to all API routes.

    Write methods (POST/PUT/PATCH/DELETE) get a tighter limit than reads.
    Explicit ``rate_limit_check`` calls in auth endpoints can set even tighter caps.
    """

    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        # Only rate-limit API routes
        if not request.url.path.startswith("/api/"):
            return await call_next(request)

        redis = getattr(request.app.state, "redis", None)
        if redis is None:
            return await call_next(request)

        client_ip = request.client.host if request.client else "unknown"
        is_write = request.method in {"POST", "PUT", "PATCH", "DELETE"}
        limit = _WRITE_LIMIT if is_write else _READ_LIMIT
        key = f"rl:global:{client_ip}:{'w' if is_write else 'r'}"

        try:
            current = await redis.incr(key)
            if current == 1:
                await redis.expire(key, 60)
            if current > limit:
                return JSONResponse(
                    status_code=429,
                    content={"detail": "Rate limit exceeded. Try again later."},
                )
        except Exception:
            logger.warning("Global rate limiter Redis error", exc_info=True)

        return await call_next(request)
