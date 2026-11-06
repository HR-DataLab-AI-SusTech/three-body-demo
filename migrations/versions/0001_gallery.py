"""The gallery: saved setups and their ratings.

Revision ID: 0001
Revises:
"""

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects.postgresql import JSONB

revision = "0001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "setups",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("name", sa.String(60), nullable=False),
        sa.Column("description", sa.String(280)),
        sa.Column("config", JSONB, nullable=False),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
    )
    op.create_table(
        "ratings",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column(
            "setup_id", sa.Integer, sa.ForeignKey("setups.id", ondelete="CASCADE"), nullable=False
        ),
        sa.Column("stars", sa.SmallInteger, nullable=False),
        sa.Column("visitor", sa.String(64), nullable=False),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.UniqueConstraint("setup_id", "visitor", name="one_rating_per_visitor"),
        sa.CheckConstraint("stars BETWEEN 1 AND 5", name="stars_one_to_five"),
    )
    op.create_index("ix_ratings_setup_id", "ratings", ["setup_id"])


def downgrade() -> None:
    op.drop_table("ratings")
    op.drop_table("setups")
