"""
SQLAlchemy read-only models for BetterAuth tables.

BetterAuth manages these tables via its own schema migration.
The backend reads from them to validate session tokens.
Column names are camelCase to match BetterAuth's default naming.
"""

from datetime import datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class BetterAuthUser(Base):
    """Maps to BetterAuth's 'user' table (text PK, camelCase columns)."""

    __tablename__ = "user"

    id: Mapped[str] = mapped_column(String, primary_key=True)
    name: Mapped[str] = mapped_column(String, nullable=False)
    email: Mapped[str] = mapped_column(
        String, unique=True, nullable=False, index=True,
    )
    email_verified: Mapped[bool] = mapped_column(
        "emailVerified", Boolean, default=False, nullable=False,
    )
    image: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Custom fields added via BetterAuth additionalFields
    role: Mapped[str] = mapped_column(
        String, nullable=False, server_default="user",
    )
    phone: Mapped[str | None] = mapped_column(String, nullable=True)

    created_at: Mapped[datetime] = mapped_column(
        "createdAt", DateTime(timezone=True), nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        "updatedAt", DateTime(timezone=True), nullable=False,
    )


class BetterAuthSession(Base):
    """Maps to BetterAuth's 'session' table (camelCase columns)."""

    __tablename__ = "session"

    id: Mapped[str] = mapped_column(String, primary_key=True)
    user_id: Mapped[str] = mapped_column(
        "userId",
        String,
        ForeignKey("user.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    token: Mapped[str] = mapped_column(
        String, unique=True, nullable=False, index=True,
    )
    expires_at: Mapped[datetime] = mapped_column(
        "expiresAt", DateTime(timezone=True), nullable=False,
    )
    ip_address: Mapped[str | None] = mapped_column(
        "ipAddress", String, nullable=True,
    )
    user_agent: Mapped[str | None] = mapped_column(
        "userAgent", String, nullable=True,
    )
    created_at: Mapped[datetime] = mapped_column(
        "createdAt", DateTime(timezone=True), nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        "updatedAt", DateTime(timezone=True), nullable=False,
    )
