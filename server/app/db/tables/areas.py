import sqlalchemy as sa

from app.db.tables import metadata

areas_table = sa.Table(
    "areas",
    metadata,
    sa.Column("id", sa.UUID(), primary_key=True, server_default=sa.text("gen_random_uuid()")),
    sa.Column(
        "region_id",
        sa.UUID(),
        sa.ForeignKey("regions.id", ondelete="CASCADE"),
        nullable=False,
    ),
    sa.Column("emd_cd", sa.CHAR(8), nullable=False, unique=True),
    sa.Column("emd_name", sa.Text(), nullable=False),
    sa.Column("lat", sa.Numeric(9, 6), nullable=True),
    sa.Column("lng", sa.Numeric(9, 6), nullable=True),
    sa.Column(
        "created_at",
        sa.DateTime(timezone=True),
        nullable=False,
        server_default=sa.text("now()"),
    ),
    sa.Column(
        "updated_at",
        sa.DateTime(timezone=True),
        nullable=False,
        server_default=sa.text("now()"),
    ),
    sa.Index("ix_areas_region_id", "region_id"),
    sa.Index("ix_areas_lat_lng", "lat", "lng"),
)
