"""create users and add session user_id

Revision ID: 0003_users_user_id
Revises: 0002_profiles_match
Create Date: 2026-05-21

"""
from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "0003_users_user_id"
down_revision: str | None = "0002_profiles_match"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "users",
        sa.Column("id", sa.UUID(), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("email", sa.Text(), nullable=False),
        sa.Column("password_hash", sa.Text(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
    )
    op.create_unique_constraint("uq_users_email", "users", ["email"])
    op.add_column("sessions", sa.Column("user_id", sa.UUID(), nullable=True))
    op.create_foreign_key(
        "fk_sessions_user_id_users",
        "sessions",
        "users",
        ["user_id"],
        ["id"],
        ondelete="SET NULL",
    )


def downgrade() -> None:
    op.drop_constraint("fk_sessions_user_id_users", "sessions", type_="foreignkey")
    op.drop_column("sessions", "user_id")
    op.drop_table("users")
