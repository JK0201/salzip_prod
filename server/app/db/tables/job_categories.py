import sqlalchemy as sa

from app.db.tables import metadata

job_categories_table = sa.Table(
    "job_categories",
    metadata,
    sa.Column("id", sa.UUID(), primary_key=True, server_default=sa.text("gen_random_uuid()")),
    sa.Column("name", sa.Text(), nullable=False, unique=True),
    sa.Column("sort_order", sa.Integer(), nullable=False),
    sa.Column(
        "created_at",
        sa.DateTime(timezone=True),
        nullable=False,
        server_default=sa.text("now()"),
    ),
)
