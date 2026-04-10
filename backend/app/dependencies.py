"""Shared FastAPI dependencies — auth, pagination, etc."""

import logging
from datetime import UTC, datetime

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import decode_token
from app.database import get_db
from app.models.betterauth import BetterAuthSession, BetterAuthUser
from app.models.user import HostProfile, User

logger = logging.getLogger(__name__)

bearer_scheme = HTTPBearer(auto_error=False)


async def _auth_via_betterauth(
    token: str, db: AsyncSession
) -> User | None:
    """Try to authenticate via BetterAuth session table. Returns User or None."""
    session_result = await db.execute(
        select(BetterAuthSession).where(BetterAuthSession.token == token)
    )
    session = session_result.scalar_one_or_none()

    if session is None:
        return None
    if session.expires_at.replace(tzinfo=UTC) < datetime.now(UTC):
        return None

    ba_user_result = await db.execute(
        select(BetterAuthUser).where(BetterAuthUser.id == session.user_id)
    )
    ba_user = ba_user_result.scalar_one_or_none()
    if ba_user is None:
        return None

    # Find or lazily create the legacy 'users' entry (bridged by email)
    user_result = await db.execute(select(User).where(User.email == ba_user.email))
    user = user_result.scalar_one_or_none()

    if user is None:
        user = User(
            email=ba_user.email,
            full_name=ba_user.name,
            hashed_password="!betterauth",  # Marker — BetterAuth owns auth  # noqa: S106
            role=ba_user.role or "user",
            phone=ba_user.phone,
            is_active=True,
        )
        db.add(user)
        await db.flush()
    else:
        if ba_user.role and user.role != ba_user.role:
            user.role = ba_user.role
            await db.flush()

    # Auto-create HostProfile for host-role users if one doesn't exist yet.
    # This handles both new BetterAuth host registrations and existing host
    # users whose HostProfile was never created.
    if user.role in ("host", "admin"):
        profile_result = await db.execute(
            select(HostProfile).where(HostProfile.user_id == user.id)
        )
        if profile_result.scalar_one_or_none() is None:
            db.add(HostProfile(user_id=user.id))
            await db.flush()

    return user


async def _auth_via_jwt(token: str, db: AsyncSession) -> User | None:
    """Try to authenticate via JWT token. Returns User or None."""
    import uuid

    payload = decode_token(token)
    if payload is None:
        return None
    if payload.get("type") != "access":
        return None

    user_id = payload.get("sub")
    if user_id is None:
        return None

    try:
        result = await db.execute(select(User).where(User.id == uuid.UUID(user_id)))
    except (ValueError, AttributeError):
        return None
    user = result.scalar_one_or_none()

    if user is None:
        return None

    # Reject tokens issued before the last password change
    if user.password_changed_at is not None:
        token_iat = payload.get("iat")
        if token_iat is not None and token_iat < user.password_changed_at.timestamp():
            return None

    return user


async def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
    db: AsyncSession = Depends(get_db),
) -> User:
    """Authenticate via BetterAuth session token or JWT access token.

    Tries BetterAuth first (production path), falls back to JWT
    (used by the /auth/login endpoint and tests).
    """
    if credentials is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
            headers={"WWW-Authenticate": "Bearer"},
        )

    token = credentials.credentials

    # Try BetterAuth session first, then JWT fallback
    user = await _auth_via_betterauth(token, db)
    if user is None:
        user = await _auth_via_jwt(token, db)

    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Account is inactive",
        )

    return user


async def require_host(current_user: User = Depends(get_current_user)) -> User:
    """Dependency that ensures the current user has the host role."""
    if current_user.role not in ("host", "admin"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Host role required",
        )
    return current_user


async def require_admin(current_user: User = Depends(get_current_user)) -> User:
    """Dependency that ensures the current user has the admin role."""
    if current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin role required",
        )
    return current_user
