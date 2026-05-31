import sqlalchemy as sa

from app.db.tables import metadata

hug_accidents_table = sa.Table(
    "hug_accidents",
    metadata,
    sa.Column("id", sa.UUID(), primary_key=True, server_default=sa.text("gen_random_uuid()")),
    sa.Column("year", sa.Integer(), nullable=False),
    sa.Column("guarantee_type", sa.Text(), nullable=False),
    sa.Column("accident_count", sa.Integer(), nullable=True),
    sa.Column("accident_amount_eok", sa.Integer(), nullable=True),
    sa.Column(
        "source",
        sa.Text(),
        nullable=False,
        server_default=sa.text("'data.go.kr 15002597'"),
    ),
    sa.Column(
        "created_at",
        sa.DateTime(timezone=True),
        nullable=False,
        server_default=sa.text("now()"),
    ),
    sa.UniqueConstraint("year", "guarantee_type", name="uq_hug_accidents_natural"),
    sa.Index("ix_hug_accidents_year_type", "year", "guarantee_type"),
)
