"""area_metrics aggregates: ADD COLUMNS

Revision ID: 0013_area_metrics_aggregates
Revises: 0012_income_monthly
Create Date: 2026-05-28

"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "0013_area_metrics_aggregates"
down_revision: str | Sequence[str] | None = "0012_income_monthly"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "area_metrics",
        sa.Column("avg_jeonse_ratio", sa.Numeric(5, 2), nullable=True),
    )
    op.add_column(
        "area_metrics",
        sa.Column("flood_ratio", sa.Numeric(5, 4), nullable=True),
    )
    op.add_column(
        "area_metrics",
        sa.Column("avg_build_year", sa.Integer(), nullable=True),
    )
    op.add_column(
        "area_metrics",
        sa.Column("listing_count", sa.Integer(), nullable=True),
    )
    op.add_column(
        "area_metrics",
        sa.Column("flood_risk_count", sa.Integer(), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("area_metrics", "flood_risk_count")
    op.drop_column("area_metrics", "listing_count")
    op.drop_column("area_metrics", "avg_build_year")
    op.drop_column("area_metrics", "flood_ratio")
    op.drop_column("area_metrics", "avg_jeonse_ratio")
