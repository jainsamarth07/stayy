"""Auth endpoints — register, login, refresh, profile, change password, forgot/reset password."""

from fastapi import APIRouter, Depends, Request
from pydantic import BaseModel, EmailStr, Field
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.rate_limiter import rate_limit_check
from app.database import get_db
from app.dependencies import get_current_user
from app.models.user import User
from app.schemas.user import (
    TokenRefresh,
    TokenResponse,
    UserLogin,
    UserOut,
    UserRegister,
    UserUpdate,
)
from app.services import auth_service

router = APIRouter()


@router.post("/register", response_model=UserOut, status_code=201)
async def register(
    data: UserRegister,
    request: Request,
    db: AsyncSession = Depends(get_db),
) -> User:
    """Register a new user account."""
    await rate_limit_check(request, limit=10)
    return await auth_service.register_user(db, data)


@router.post("/login", response_model=TokenResponse)
async def login(
    data: UserLogin,
    request: Request,
    db: AsyncSession = Depends(get_db),
) -> TokenResponse:
    """Authenticate and receive JWT tokens."""
    await rate_limit_check(request, limit=20)
    return await auth_service.authenticate_user(db, data.email, data.password)


@router.post("/refresh", response_model=TokenResponse)
async def refresh_token(
    data: TokenRefresh, db: AsyncSession = Depends(get_db)
) -> TokenResponse:
    """Refresh an access token using a valid refresh token."""
    return await auth_service.refresh_access_token(db, data.refresh_token)


@router.get("/me", response_model=UserOut)
async def get_profile(current_user: User = Depends(get_current_user)) -> User:
    """Get the current user's profile."""
    return current_user


@router.put("/me", response_model=UserOut)
async def update_profile(
    data: UserUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> User:
    """Update the current user's profile."""
    update_data = data.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(current_user, key, value)
    await db.flush()
    return current_user


# ---------- Change password ----------
class PasswordChange(BaseModel):
    """Schema for changing the current user's password."""
    current_password: str
    new_password: str = Field(..., min_length=8, max_length=128)


@router.put("/me/password")
async def change_password(
    data: PasswordChange,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Change the current user's password."""
    from app.core.security import hash_password, verify_password

    # BetterAuth-managed users have a marker hash — password change requires
    # the user to have registered via the local auth flow.
    if not current_user.hashed_password or current_user.hashed_password.startswith("!"):
        from app.core.exceptions import BadRequestError
        raise BadRequestError(
            "Password change unavailable — account uses external authentication"
        )

    if not verify_password(data.current_password, current_user.hashed_password):
        from app.core.exceptions import UnauthorizedError
        raise UnauthorizedError("Current password is incorrect")

    current_user.hashed_password = hash_password(data.new_password)
    current_user.password_changed_at = __import__("datetime").datetime.now(
        __import__("datetime").UTC
    )
    await db.flush()
    return {"message": "Password changed successfully"}


# ---------- Forgot / Reset password ----------
class ForgotPasswordRequest(BaseModel):
    """Schema for requesting a password reset email."""
    email: EmailStr


class ResetPasswordRequest(BaseModel):
    """Schema for resetting a password with a token."""
    token: str
    new_password: str = Field(..., min_length=8, max_length=128)


@router.post("/forgot-password")
async def forgot_password(
    data: ForgotPasswordRequest,
    request: Request,
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Request a password reset email. Always returns success to prevent email enumeration."""
    await rate_limit_check(request, limit=5)

    from datetime import timedelta

    from sqlalchemy import select

    from app.core.security import create_access_token

    result = await db.execute(select(User).where(User.email == data.email))
    user = result.scalar_one_or_none()
    if user is not None:
        # Include hash fingerprint so token is single-use — changing the
        # password invalidates outstanding tokens automatically.
        pw_fingerprint = (user.hashed_password or "")[:16]
        reset_token = create_access_token(
            {"sub": str(user.id), "type": "reset", "pwfp": pw_fingerprint},
            expires_delta=timedelta(minutes=30),
        )
        try:
            from app.tasks.email_tasks import send_password_reset_email
            send_password_reset_email.delay(user.email, reset_token)
        except Exception:
            pass  # Don't fail if Celery/Redis unavailable

    return {"message": "If an account with that email exists, a reset link has been sent."}


@router.post("/reset-password")
async def reset_password(
    data: ResetPasswordRequest,
    request: Request,
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Reset a password using a valid reset token."""
    await rate_limit_check(request, limit=10)

    import uuid

    from sqlalchemy import select

    from app.core.security import decode_token, hash_password

    payload = decode_token(data.token)
    if payload is None or payload.get("type") != "reset":
        from app.core.exceptions import UnauthorizedError
        raise UnauthorizedError("Invalid or expired reset token")

    user_id = payload.get("sub")
    result = await db.execute(select(User).where(User.id == uuid.UUID(user_id)))
    user = result.scalar_one_or_none()
    if user is None:
        from app.core.exceptions import NotFoundError
        raise NotFoundError("User not found")

    # Verify password fingerprint — ensures token is single-use
    pw_fingerprint = payload.get("pwfp", "")
    current_fingerprint = (user.hashed_password or "")[:16]
    if pw_fingerprint != current_fingerprint:
        from app.core.exceptions import UnauthorizedError
        raise UnauthorizedError("Reset token has already been used")

    user.hashed_password = hash_password(data.new_password)
    user.password_changed_at = __import__("datetime").datetime.now(
        __import__("datetime").UTC
    )
    await db.flush()
    return {"message": "Password has been reset successfully"}
