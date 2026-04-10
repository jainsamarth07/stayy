"""Add BetterAuth tables (user, session, account, verification).

Revision ID: 0003_betterauth_tables
Revises: 0002_offer_in_messages
Create Date: 2026-03-29
"""

import sqlalchemy as sa

from alembic import op

revision = "0003_betterauth_tables"
down_revision = "0002_offer_in_messages"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # BetterAuth 'user' table (text primary key, camelCase columns)
    op.create_table(
        "user",
        sa.Column("id", sa.String(), primary_key=True, nullable=False),
        sa.Column("name", sa.String(), nullable=False),
        sa.Column("email", sa.String(), unique=True, nullable=False),
        sa.Column("emailVerified", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("image", sa.Text(), nullable=True),
        # Custom fields
        sa.Column("role", sa.String(), nullable=False, server_default="user"),
        sa.Column("phone", sa.String(), nullable=True),
        sa.Column("createdAt", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updatedAt", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )
    op.create_index("ix_user_email", "user", ["email"], unique=True)

    # BetterAuth 'session' table
    op.create_table(
        "session",
        sa.Column("id", sa.String(), primary_key=True, nullable=False),
        sa.Column("userId", sa.String(), sa.ForeignKey("user.id", ondelete="CASCADE"), nullable=False),
        sa.Column("token", sa.String(), unique=True, nullable=False),
        sa.Column("expiresAt", sa.DateTime(timezone=True), nullable=False),
        sa.Column("ipAddress", sa.String(), nullable=True),
        sa.Column("userAgent", sa.String(), nullable=True),
        sa.Column("createdAt", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updatedAt", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )
    op.create_index("ix_session_token", "session", ["token"], unique=True)
    op.create_index("ix_session_userId", "session", ["userId"])

    # BetterAuth 'account' table (social / credential provider accounts)
    op.create_table(
        "account",
        sa.Column("id", sa.String(), primary_key=True, nullable=False),
        sa.Column("userId", sa.String(), sa.ForeignKey("user.id", ondelete="CASCADE"), nullable=False),
        sa.Column("accountId", sa.String(), nullable=False),
        sa.Column("providerId", sa.String(), nullable=False),
        sa.Column("accessToken", sa.Text(), nullable=True),
        sa.Column("refreshToken", sa.Text(), nullable=True),
        sa.Column("idToken", sa.Text(), nullable=True),
        sa.Column("accessTokenExpiresAt", sa.DateTime(timezone=True), nullable=True),
        sa.Column("refreshTokenExpiresAt", sa.DateTime(timezone=True), nullable=True),
        sa.Column("scope", sa.String(), nullable=True),
        sa.Column("password", sa.Text(), nullable=True),
        sa.Column("createdAt", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updatedAt", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )
    op.create_index("ix_account_userId", "account", ["userId"])

    # BetterAuth 'verification' table (email / OTP verification tokens)
    op.create_table(
        "verification",
        sa.Column("id", sa.String(), primary_key=True, nullable=False),
        sa.Column("identifier", sa.String(), nullable=False),
        sa.Column("value", sa.String(), nullable=False),
        sa.Column("expiresAt", sa.DateTime(timezone=True), nullable=False),
        sa.Column("createdAt", sa.DateTime(timezone=True), nullable=True, server_default=sa.func.now()),
        sa.Column("updatedAt", sa.DateTime(timezone=True), nullable=True, server_default=sa.func.now()),
    )


def downgrade() -> None:
    op.drop_table("verification")
    op.drop_index("ix_account_userId", table_name="account")
    op.drop_table("account")
    op.drop_index("ix_session_userId", table_name="session")
    op.drop_index("ix_session_token", table_name="session")
    op.drop_table("session")
    op.drop_index("ix_user_email", table_name="user")
    op.drop_table("user")
