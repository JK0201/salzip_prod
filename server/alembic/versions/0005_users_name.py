"""users name column

Revision ID: 0005_users_name
Revises: 0004_profiles_user_id
Create Date: 2026-05-25

"""
from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "0005_users_name"
down_revision: str | None = "0004_profiles_user_id"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "users",
        sa.Column("name", sa.Text(), nullable=False, server_default=sa.text("''")),
    )


def downgrade() -> None:
    op.drop_column("users", "name")
