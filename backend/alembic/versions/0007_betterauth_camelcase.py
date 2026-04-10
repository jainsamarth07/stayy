"""Rename BetterAuth columns from snake_case to camelCase.

BetterAuth expects camelCase column names by default (e.g. emailVerified,
userId, createdAt).  Migration 0003 incorrectly created them as snake_case.

Revision ID: 0007
Revises: 0006
Create Date: 2026-04-07
"""

from alembic import op

revision = "0007"
down_revision = "0006"
branch_labels = None
depends_on = None

# (table, old_snake, new_camel)
_RENAMES = [
    # user table
    ("user", "email_verified", "emailVerified"),
    ("user", "created_at", "createdAt"),
    ("user", "updated_at", "updatedAt"),
    # session table
    ("session", "user_id", "userId"),
    ("session", "expires_at", "expiresAt"),
    ("session", "ip_address", "ipAddress"),
    ("session", "user_agent", "userAgent"),
    ("session", "created_at", "createdAt"),
    ("session", "updated_at", "updatedAt"),
    # account table
    ("account", "user_id", "userId"),
    ("account", "account_id", "accountId"),
    ("account", "provider_id", "providerId"),
    ("account", "access_token", "accessToken"),
    ("account", "refresh_token", "refreshToken"),
    ("account", "id_token", "idToken"),
    ("account", "access_token_expires_at", "accessTokenExpiresAt"),
    ("account", "refresh_token_expires_at", "refreshTokenExpiresAt"),
    ("account", "created_at", "createdAt"),
    ("account", "updated_at", "updatedAt"),
    # verification table
    ("verification", "expires_at", "expiresAt"),
    ("verification", "created_at", "createdAt"),
    ("verification", "updated_at", "updatedAt"),
]


def upgrade() -> None:
    for table, old, new in _RENAMES:
        op.alter_column(table, old, new_column_name=new)


def downgrade() -> None:
    for table, old, new in reversed(_RENAMES):
        op.alter_column(table, new, new_column_name=old)
