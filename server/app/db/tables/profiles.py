import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB

from app.db.tables import metadata

profiles_table = sa.Table(
    "profiles",
    metadata,
    sa.Column("id", sa.UUID(), primary_key=True, server_default=sa.text("gen_random_uuid()")),
    sa.Column(
        "session_id",
        sa.UUID(),
        sa.ForeignKey("sessions.id", ondelete="SET NULL"),
        nullable=True,
    ),
    sa.Column(
        "user_id",
        sa.UUID(),
        sa.ForeignKey("users.id", ondelete="CASCADE"),
        nullable=True,
    ),
    sa.Column("payload", JSONB(), nullable=False),
    sa.Column(
        "created_at",
        sa.DateTime(timezone=True),
        nullable=False,
        server_default=sa.text("now()"),
    ),
)
