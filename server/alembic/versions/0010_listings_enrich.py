"""listings_enrich: add 6 columns to listings

Revision ID: 0010_listings_enrich
Revises: 0009_supports_enrich
Create Date: 2026-05-28

"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "0010_listings_enrich"
down_revision: str | None = "0009_supports_enrich"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column("listings", sa.Column("house_type_raw", sa.Text(), nullable=True))
    op.add_column("listings", sa.Column("pre_deposit", sa.Integer(), nullable=True))
    op.add_column("listings", sa.Column("pre_monthly_rent", sa.Integer(), nullable=True))
    op.add_column("listings", sa.Column("contract_type", sa.Text(), nullable=True))
    op.add_column("listings", sa.Column("use_rr_right", sa.Boolean(), nullable=True))
    op.add_column("listings", sa.Column("apt_seq", sa.Text(), nullable=True))


def downgrade() -> None:
    op.drop_column("listings", "apt_seq")
    op.drop_column("listings", "use_rr_right")
    op.drop_column("listings", "contract_type")
    op.drop_column("listings", "pre_monthly_rent")
    op.drop_column("listings", "pre_deposit")
    op.drop_column("listings", "house_type_raw")
