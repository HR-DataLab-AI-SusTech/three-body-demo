"""Featured setups: the lab's own presets, seeded into the gallery by `python -m threebody.seed`.

Revision ID: 0002
Revises: 0001
"""

import sqlalchemy as sa
from alembic import op

revision = "0002"
down_revision = "0001"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "setups", sa.Column("featured", sa.Boolean, nullable=False, server_default=sa.false())
    )
    # The seed finds a featured setup again by its name, so the name is unique among them.
    op.create_index(
        "uq_setups_featured_name",
        "setups",
        ["name"],
        unique=True,
        postgresql_where=sa.text("featured"),
    )


def downgrade() -> None:
    op.drop_index("uq_setups_featured_name", table_name="setups")
    op.drop_column("setups", "featured")
