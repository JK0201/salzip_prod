import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB

from app.db.tables import metadata

match_results_table = sa.Table(
    "match_results",
    metadata,
    sa.Column("id", sa.UUID(), primary_key=True, server_default=sa.text("gen_random_uuid()")),
    sa.Column(
        "profile_id",
        sa.UUID(),
        sa.ForeignKey("profiles.id", ondelete="CASCADE"),
        nullable=False,
    ),
    sa.Column("payload", JSONB(), nullable=False),
    sa.Column(
        "created_at",
        sa.DateTime(timezone=True),
        nullable=False,
        server_default=sa.text("now()"),
    ),
)
