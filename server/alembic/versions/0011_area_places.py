"""area_places: create area_places table

Revision ID: 0011_area_places
Revises: 0010_listings_enrich
Create Date: 2026-05-28

"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "0011_area_places"
down_revision: str | None = "0010_listings_enrich"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table('area_places',
        sa.Column(
            'id',
            sa.UUID(),
            server_default=sa.text('gen_random_uuid()'),
            nullable=False,
        ),
        sa.Column('area_id', sa.UUID(), nullable=False),
        sa.Column('category', sa.Text(), nullable=False),
        sa.Column('kakao_id', sa.Text(), nullable=False),
        sa.Column('place_name', sa.Text(), nullable=False),
        sa.Column('road_address', sa.Text(), nullable=True),
        sa.Column('jibun_address', sa.Text(), nullable=True),
        sa.Column('lat', sa.Numeric(9, 6), nullable=True),
        sa.Column('lng', sa.Numeric(9, 6), nullable=True),
        sa.Column('distance_m', sa.Integer(), nullable=True),
        sa.Column('phone', sa.Text(), nullable=True),
        sa.Column('place_url', sa.Text(), nullable=True),
        sa.Column('category_path', sa.Text(), nullable=True),
        sa.Column(
            'created_at',
            sa.DateTime(timezone=True),
            server_default=sa.text('now()'),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(['area_id'], ['areas.id']),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('area_id', 'kakao_id', name='uq_area_places_area_id_kakao_id'),
    )
    op.create_index('ix_area_places_area_id', 'area_places', ['area_id'])
    op.create_index('ix_area_places_category_area_id', 'area_places', ['category', 'area_id'])
    op.create_index('ix_area_places_lat_lng', 'area_places', ['lat', 'lng'])


def downgrade() -> None:
    op.drop_index('ix_area_places_lat_lng', table_name='area_places')
    op.drop_index('ix_area_places_category_area_id', table_name='area_places')
    op.drop_index('ix_area_places_area_id', table_name='area_places')
    op.drop_table('area_places')
