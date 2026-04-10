"""Convert monetary Float columns to Numeric(10,2) and rating to Numeric(3,1).

Revision ID: 0005
Revises: 0004
"""

import sqlalchemy as sa

from alembic import op

revision = "0005"
down_revision = "0004_remove_offers"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # --- properties ---
    op.alter_column(
        "properties", "price_per_night",
        existing_type=sa.Float(),
        type_=sa.Numeric(precision=10, scale=2),
        existing_nullable=False,
    )

    # --- hourly_booking_configs ---
    op.alter_column(
        "hourly_booking_configs", "hourly_price",
        existing_type=sa.Float(),
        type_=sa.Numeric(precision=10, scale=2),
        existing_nullable=False,
    )

    # --- bookings ---
    op.alter_column(
        "bookings", "total_price",
        existing_type=sa.Float(),
        type_=sa.Numeric(precision=10, scale=2),
        existing_nullable=False,
    )

    # --- memberships ---
    op.alter_column(
        "memberships", "amount",
        existing_type=sa.Float(),
        type_=sa.Numeric(precision=10, scale=2),
        existing_nullable=False,
    )

    # --- reviews (rating is 1.0–5.0) ---
    op.alter_column(
        "reviews", "rating",
        existing_type=sa.Float(),
        type_=sa.Numeric(precision=3, scale=1),
        existing_nullable=False,
    )


def downgrade() -> None:
    op.alter_column("reviews", "rating", existing_type=sa.Numeric(precision=3, scale=1), type_=sa.Float(), existing_nullable=False)
    op.alter_column("memberships", "amount", existing_type=sa.Numeric(precision=10, scale=2), type_=sa.Float(), existing_nullable=False)
    op.alter_column("bookings", "total_price", existing_type=sa.Numeric(precision=10, scale=2), type_=sa.Float(), existing_nullable=False)
    op.alter_column("hourly_booking_configs", "hourly_price", existing_type=sa.Numeric(precision=10, scale=2), type_=sa.Float(), existing_nullable=False)
    op.alter_column("properties", "price_per_night", existing_type=sa.Numeric(precision=10, scale=2), type_=sa.Float(), existing_nullable=False)
