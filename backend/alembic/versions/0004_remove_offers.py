"""Remove offers table and related columns.

Revision ID: 0004_remove_offers
Revises: 0003_betterauth_tables
Create Date: 2026-04-01

The offer/negotiation feature has been removed in favor of direct messaging.
This migration drops the offers table and removes offer-related FK columns
from bookings and messages.
"""

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

revision = "0004_remove_offers"
down_revision = "0003_betterauth_tables"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Drop offer_id FK and index from messages
    op.drop_index("ix_messages_offer_id", table_name="messages")
    op.drop_constraint("messages_offer_id_fkey", "messages", type_="foreignkey")
    op.drop_column("messages", "offer_id")

    # Drop offer_id FK from bookings
    op.drop_constraint("bookings_offer_id_fkey", "bookings", type_="foreignkey")
    op.drop_column("bookings", "offer_id")

    # Drop the offers table
    op.drop_table("offers")


def downgrade() -> None:
    # Recreate the offers table
    op.create_table(
        "offers",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "property_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("properties.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "guest_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "host_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("offered_price", sa.Float(), nullable=False),
        sa.Column("message", sa.Text(), nullable=True),
        sa.Column("status", sa.String(20), nullable=False, server_default="pending"),
        sa.Column("counter_price", sa.Float(), nullable=True),
        sa.Column("counter_message", sa.Text(), nullable=True),
        sa.Column("check_in", sa.DateTime(timezone=True), nullable=False),
        sa.Column("check_out", sa.DateTime(timezone=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )

    # Re-add offer_id to bookings
    op.add_column(
        "bookings",
        sa.Column(
            "offer_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("offers.id", ondelete="SET NULL"),
            nullable=True,
        ),
    )

    # Re-add offer_id to messages
    op.add_column(
        "messages",
        sa.Column(
            "offer_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("offers.id", ondelete="SET NULL"),
            nullable=True,
        ),
    )
    op.create_index("ix_messages_offer_id", "messages", ["offer_id"])
