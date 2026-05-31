import sqlalchemy as sa

from app.db.tables import metadata

sessions_table = sa.Table(
    "sessions",
    metadata,
    sa.Column("id", sa.UUID(), primary_key=True, server_default=sa.text("gen_random_uuid()")),
    sa.Column("token_hash", sa.Text(), nullable=False, unique=True),
    sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
    sa.Column(
        "created_at",
        sa.DateTime(timezone=True),
        nullable=False,
        server_default=sa.text("now()"),
    ),
    sa.Column(
        "user_id",
        sa.UUID(),
        sa.ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    ),
)
