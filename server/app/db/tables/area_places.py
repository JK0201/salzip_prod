import sqlalchemy as sa

from app.db.tables import metadata

area_places_table = sa.Table(
    "area_places",
    metadata,
    sa.Column("id", sa.UUID(), primary_key=True, server_default=sa.text("gen_random_uuid()")),
    sa.Column(
        "area_id",
        sa.UUID(),
        sa.ForeignKey("areas.id", ondelete="CASCADE"),
        nullable=False,
    ),
    sa.Column("category", sa.Text(), nullable=False),
    sa.Column("kakao_id", sa.Text(), nullable=False),
    sa.Column("place_name", sa.Text(), nullable=False),
    sa.Column("road_address", sa.Text(), nullable=True),
    sa.Column("jibun_address", sa.Text(), nullable=True),
    sa.Column("lat", sa.Numeric(9, 6), nullable=True),
    sa.Column("lng", sa.Numeric(9, 6), nullable=True),
    sa.Column("distance_m", sa.Integer(), nullable=True),
    sa.Column("phone", sa.Text(), nullable=True),
    sa.Column("place_url", sa.Text(), nullable=True),
    sa.Column("category_path", sa.Text(), nullable=True),
    sa.Column(
        "created_at",
        sa.DateTime(timezone=True),
        nullable=False,
        server_default=sa.text("now()"),
    ),
    sa.UniqueConstraint("area_id", "kakao_id"),
    sa.Index("ix_area_places_area_id", "area_id"),
    sa.Index("ix_area_places_category_area_id", "category", "area_id"),
    sa.Index("ix_area_places_lat_lng", "lat", "lng"),
)
