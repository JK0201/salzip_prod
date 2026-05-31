import sqlalchemy as sa

from app.db.tables import metadata

area_trends_table = sa.Table(
    "area_trends",
    metadata,
    sa.Column("id", sa.UUID(), primary_key=True, server_default=sa.text("gen_random_uuid()")),
    sa.Column(
        "region_id",
        sa.UUID(),
        sa.ForeignKey("regions.id", ondelete="CASCADE"),
        nullable=True,
    ),
    sa.Column("region_label", sa.Text(), nullable=False),
    sa.Column("metric", sa.Text(), nullable=False),
    sa.Column("period", sa.Date(), nullable=False),
    sa.Column("value", sa.Numeric(14, 4), nullable=True),
    sa.Column("unit", sa.Text(), nullable=True),
    sa.Column("statbl_id", sa.Text(), nullable=False),
    sa.Column(
        "created_at",
        sa.DateTime(timezone=True),
        nullable=False,
        server_default=sa.text("now()"),
    ),
    sa.UniqueConstraint(
        "region_label", "metric", "period", "statbl_id", name="uq_area_trends_natural"
    ),
    sa.Index("ix_area_trends_region_metric_period", "region_id", "metric", "period"),
    sa.Index("ix_area_trends_label_metric_period", "region_label", "metric", "period"),
)
