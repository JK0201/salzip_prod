import sqlalchemy as sa

from app.db.tables import metadata

area_metrics_table = sa.Table(
    "area_metrics",
    metadata,
    sa.Column(
        "area_id",
        sa.UUID(),
        sa.ForeignKey("areas.id", ondelete="CASCADE"),
        primary_key=True,
    ),
    sa.Column("mart_count", sa.Integer(), nullable=False, server_default=sa.text("0")),
    sa.Column("cafe_count", sa.Integer(), nullable=False, server_default=sa.text("0")),
    sa.Column("food_count", sa.Integer(), nullable=False, server_default=sa.text("0")),
    sa.Column("hospital_count", sa.Integer(), nullable=False, server_default=sa.text("0")),
    sa.Column("pharmacy_count", sa.Integer(), nullable=False, server_default=sa.text("0")),
    sa.Column("culture_count", sa.Integer(), nullable=False, server_default=sa.text("0")),
    sa.Column("subway_count", sa.Integer(), nullable=False, server_default=sa.text("0")),
    sa.Column("park_count", sa.Integer(), nullable=False, server_default=sa.text("0")),
    sa.Column(
        "updated_at",
        sa.DateTime(timezone=True),
        nullable=False,
        server_default=sa.text("now()"),
    ),
    sa.Column("avg_jeonse_ratio", sa.Numeric(5, 2), nullable=True),
    sa.Column("flood_ratio", sa.Numeric(5, 4), nullable=True),
    sa.Column("avg_build_year", sa.Integer(), nullable=True),
    sa.Column("listing_count", sa.Integer(), nullable=True),
    sa.Column("flood_risk_count", sa.Integer(), nullable=True),
)
