"""CSRF protection middleware.

Validates that state-mutating requests (POST, PUT, PATCH, DELETE) originate
from trusted origins.  This blocks simple cross-site form submissions that
bypass CORS pre-flight checks.
"""

import logging
from urllib.parse import urlparse

from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.requests import Request
from starlette.responses import JSONResponse, Response

logger = logging.getLogger(__name__)

# Methods that can mutate state
_UNSAFE_METHODS = frozenset({"POST", "PUT", "PATCH", "DELETE"})

# Paths that are exempt from CSRF (webhooks receive requests from external services)
_EXEMPT_PREFIXES = ("/api/v1/memberships/webhook",)


class CSRFMiddleware(BaseHTTPMiddleware):
    """Reject cross-origin state-mutating requests that lack a valid Origin/Referer.

    This is defence-in-depth on top of CORS.  Plain HTML forms and
    ``<img>`` tags cannot set custom headers, so any request that arrives
    *without* a recognised Origin/Referer on an unsafe method is suspicious.
    """

    def __init__(self, app, allowed_origins: list[str] | None = None) -> None:  # noqa: ANN001
        super().__init__(app)
        # Normalise to set of lowercase scheme+host pairs, e.g. {"http://localhost:3000"}
        self.allowed_origins: set[str] = set()
        for origin in allowed_origins or []:
            parsed = urlparse(origin)
            normalised = f"{parsed.scheme}://{parsed.netloc}".lower()
            self.allowed_origins.add(normalised)

    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        if request.method not in _UNSAFE_METHODS:
            return await call_next(request)

        # Exempt certain paths (e.g. payment webhooks)
        for prefix in _EXEMPT_PREFIXES:
            if request.url.path.startswith(prefix):
                return await call_next(request)

        origin = request.headers.get("origin")
        referer = request.headers.get("referer")

        # Determine the origin from the Origin or Referer header
        request_origin: str | None = None
        if origin:
            parsed = urlparse(origin)
            request_origin = f"{parsed.scheme}://{parsed.netloc}".lower()
        elif referer:
            parsed = urlparse(referer)
            request_origin = f"{parsed.scheme}://{parsed.netloc}".lower()

        if request_origin is None:
            # No Origin or Referer — allow ONLY if an Authorization header is present.
            # Browser-based CSRF attacks (form posts, img tags) always include
            # Origin or Referer; API clients (curl, mobile apps) may not.
            if request.headers.get("authorization"):
                return await call_next(request)
            logger.warning(
                "CSRF: blocked %s %s — no origin and no auth header",
                request.method, request.url.path,
            )
            return JSONResponse(
                status_code=403,
                content={"detail": "Origin verification failed"},
            )

        if request_origin not in self.allowed_origins:
            logger.warning(
                "CSRF: blocked %s %s — origin %s not allowed",
                request.method, request.url.path, request_origin,
            )
            return JSONResponse(
                status_code=403,
                content={"detail": "Origin verification failed"},
            )

        return await call_next(request)
