"""User-related Pydantic schemas."""

import uuid
from datetime import datetime

from pydantic import BaseModel, EmailStr, Field


# ---------- Auth ----------
class UserRegister(BaseModel):
    """Schema for new user registration requests."""

    email: EmailStr
    password: str = Field(..., min_length=8, max_length=128)
    full_name: str = Field(..., min_length=1, max_length=255)
    phone: str | None = None
    role: str = Field(default="user", pattern="^(user|host)$")


class UserLogin(BaseModel):
    """Schema for user login (email + password)."""

    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    """JWT token pair returned after successful authentication."""

    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class TokenRefresh(BaseModel):
    """Schema for refreshing an expired access token."""

    refresh_token: str


# ---------- User ----------
class UserOut(BaseModel):
    """Public user representation returned by API responses."""

    id: uuid.UUID
    email: str
    full_name: str
    phone: str | None = None
    role: str
    is_active: bool
    created_at: datetime

    model_config = {"from_attributes": True}


class UserUpdate(BaseModel):
    """Schema for updating mutable user profile fields."""

    full_name: str | None = Field(None, min_length=1, max_length=255)
    phone: str | None = None


# ---------- Host Profile ----------
class HostProfileOut(BaseModel):
    """Public host profile data including verification and rating."""

    id: uuid.UUID
    user_id: uuid.UUID
    business_name: str | None = None
    bio: str | None = None
    phone_visible: bool
    is_verified: bool
    avg_rating: float
    total_reviews: int
    created_at: datetime

    model_config = {"from_attributes": True}


class HostProfileUpdate(BaseModel):
    """Schema for updating host profile business details."""

    business_name: str | None = None
    bio: str | None = None
    phone_visible: bool | None = None
