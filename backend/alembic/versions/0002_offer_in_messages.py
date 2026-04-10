"""Add message_type and offer_id to messages table.

Revision ID: 0002_offer_in_messages
Revises: 0001_initial
Create Date: 2026-03-17
"""

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

# revision identifiers, used by Alembic.
revision = "0002_offer_in_messages"
down_revision = "0001_initial"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "messages",
        sa.Column("message_type", sa.String(30), nullable=False, server_default="text"),
    )
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


def downgrade() -> None:
    op.drop_index("ix_messages_offer_id", table_name="messages")
    op.drop_column("messages", "offer_id")
    op.drop_column("messages", "message_type")
