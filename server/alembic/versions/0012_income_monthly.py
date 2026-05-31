"""supports income_max_monthly_wan: ADD COLUMN

Revision ID: 0012_income_monthly
Revises: 0011_area_places
Create Date: 2026-05-28

"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "0012_income_monthly"
down_revision: str | Sequence[str] | None = "0011_area_places"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "support_programs",
        sa.Column("income_max_monthly_wan", sa.Integer(), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("support_programs", "income_max_monthly_wan")
