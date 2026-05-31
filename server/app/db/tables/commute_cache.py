import sqlalchemy as sa

from app.db.tables import metadata

commute_cache_table = sa.Table(
    "commute_cache",
    metadata,
    sa.Column("id", sa.UUID(), primary_key=True, server_default=sa.text("gen_random_uuid()")),
    sa.Column("origin_lat", sa.Numeric(9, 4), nullable=False),
    sa.Column("origin_lng", sa.Numeric(9, 4), nullable=False),
    sa.Column(
        "area_id",
        sa.UUID(),
        sa.ForeignKey("areas.id", ondelete="CASCADE"),
        nullable=False,
    ),
    sa.Column("total_time_min", sa.Integer(), nullable=False),
    sa.Column("transfers", sa.Integer(), nullable=True),
    sa.Column("total_walk_m", sa.Integer(), nullable=True),
    sa.Column("payment_won", sa.Integer(), nullable=True),
    sa.Column("first_lane", sa.Text(), nullable=True),
    sa.Column(
        "fetched_at",
        sa.DateTime(timezone=True),
        nullable=False,
        server_default=sa.text("now()"),
    ),
    sa.UniqueConstraint("origin_lat", "origin_lng", "area_id", name="uq_commute_cache_natural"),
    sa.Index("ix_commute_cache_fetched_at", "fetched_at"),
)
