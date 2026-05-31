import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from app.db.tables import metadata

lifestyle_tags_table = sa.Table(
    "lifestyle_tags",
    metadata,
    sa.Column("id", sa.UUID(), primary_key=True, server_default=sa.text("gen_random_uuid()")),
    sa.Column("name", sa.Text(), nullable=False, unique=True),
    sa.Column("sort_order", sa.Integer(), nullable=False),
    sa.Column("categories", postgresql.ARRAY(sa.Text()), nullable=False),
    sa.Column("is_inverse", sa.Boolean(), nullable=False, server_default=sa.text("false")),
    sa.Column(
        "created_at",
        sa.DateTime(timezone=True),
        nullable=False,
        server_default=sa.text("now()"),
    ),
)
