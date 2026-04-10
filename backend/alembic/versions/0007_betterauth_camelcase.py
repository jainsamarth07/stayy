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


def _column_exists(conn, table: str, column: str) -> bool:
    result = conn.execute(
        __import__("sqlalchemy").text(
            "SELECT 1 FROM information_schema.columns "
            "WHERE table_name = :t AND column_name = :c"
        ),
        {"t": table, "c": column},
    )
    return result.fetchone() is not None


def upgrade() -> None:
    conn = op.get_bind()
    for table, old, new in _RENAMES:
        if _column_exists(conn, table, old):
            op.alter_column(table, old, new_column_name=new)


def downgrade() -> None:
    conn = op.get_bind()
    for table, old, new in reversed(_RENAMES):
        if _column_exists(conn, table, new):
            op.alter_column(table, new, new_column_name=old)
