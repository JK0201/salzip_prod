"""commute_cache: ADD segments columns

Revision ID: 0014_commute_cache_segments
Revises: 0013_area_metrics_aggregates
Create Date: 2026-05-28

"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "0014_commute_cache_segments"
down_revision: str | Sequence[str] | None = "0013_area_metrics_aggregates"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "commute_cache",
        sa.Column("transfers", sa.Integer(), nullable=True),
    )
    op.add_column(
        "commute_cache",
        sa.Column("total_walk_m", sa.Integer(), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("commute_cache", "total_walk_m")
    op.drop_column("commute_cache", "transfers")
