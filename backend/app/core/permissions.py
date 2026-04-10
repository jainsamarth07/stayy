"""Role-based access control constants.

All runtime role enforcement is handled by the dependency functions
in ``app.dependencies`` (``require_host``, ``require_admin``).
This module exposes a ``UserRole`` enum for type-safe role checks.
"""

from enum import StrEnum


class UserRole(StrEnum):
    """User roles on the platform."""

    USER = "user"
    HOST = "host"
    ADMIN = "admin"
