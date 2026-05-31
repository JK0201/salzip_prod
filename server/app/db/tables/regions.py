import sqlalchemy as sa

from app.db.tables import metadata

regions_table = sa.Table(
    "regions",
    metadata,
    sa.Column("id", sa.UUID(), primary_key=True, server_default=sa.text("gen_random_uuid()")),
    sa.Column("lawd_cd", sa.CHAR(5), nullable=False, unique=True),
    sa.Column("sgg_name", sa.Text(), nullable=False),
    sa.Column("sido_name", sa.Text(), nullable=False, server_default=sa.text("'서울특별시'")),
    sa.Column(
        "created_at",
        sa.DateTime(timezone=True),
        nullable=False,
        server_default=sa.text("now()"),
    ),
)
