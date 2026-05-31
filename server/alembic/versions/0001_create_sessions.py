"""create sessions table

Revision ID: 0001_create_sessions
Revises:
Create Date: 2026-05-21

"""
from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "0001_create_sessions"
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "sessions",
        sa.Column("id", sa.UUID(), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("token_hash", sa.Text(), nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
    )
    op.create_unique_constraint("uq_sessions_token_hash", "sessions", ["token_hash"])


def downgrade() -> None:
    op.drop_table("sessions")
