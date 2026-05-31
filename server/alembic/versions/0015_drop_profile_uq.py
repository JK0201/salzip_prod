"""profiles: DROP ix_profiles_user_id_unique

Revision ID: 0015_drop_profile_uq
Revises: 0014_commute_cache_segments
Create Date: 2026-05-28

"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "0015_drop_profile_uq"
down_revision: str | Sequence[str] | None = "0014_commute_cache_segments"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.drop_index("ix_profiles_user_id_unique", table_name="profiles")


def downgrade() -> None:
    op.create_index(
        "ix_profiles_user_id_unique",
        "profiles",
        ["user_id"],
        unique=True,
        postgresql_where=sa.text("user_id IS NOT NULL"),
    )
