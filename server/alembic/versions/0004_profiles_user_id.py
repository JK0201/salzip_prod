"""profiles user_id column and session_id nullable

Revision ID: 0004_profiles_user_id
Revises: 0003_users_user_id
Create Date: 2026-05-25

"""
from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "0004_profiles_user_id"
down_revision: str | None = "0003_users_user_id"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column("profiles", sa.Column("user_id", sa.UUID(), nullable=True))
    op.create_foreign_key(
        "fk_profiles_user_id_users",
        "profiles",
        "users",
        ["user_id"],
        ["id"],
        ondelete="CASCADE",
    )
    op.create_index(
        "ix_profiles_user_id_unique",
        "profiles",
        ["user_id"],
        unique=True,
        postgresql_where=sa.text("user_id IS NOT NULL"),
    )
    op.alter_column("profiles", "session_id", nullable=True)
    op.drop_constraint("fk_profiles_session_id_sessions", "profiles", type_="foreignkey")
    op.create_foreign_key(
        "fk_profiles_session_id_sessions",
        "profiles",
        "sessions",
        ["session_id"],
        ["id"],
        ondelete="SET NULL",
    )


def downgrade() -> None:
    op.drop_constraint("fk_profiles_session_id_sessions", "profiles", type_="foreignkey")
    op.create_foreign_key(
        "fk_profiles_session_id_sessions",
        "profiles",
        "sessions",
        ["session_id"],
        ["id"],
        ondelete="CASCADE",
    )
    op.alter_column("profiles", "session_id", nullable=False)
    op.drop_index("ix_profiles_user_id_unique", table_name="profiles")
    op.drop_constraint("fk_profiles_user_id_users", "profiles", type_="foreignkey")
    op.drop_column("profiles", "user_id")
