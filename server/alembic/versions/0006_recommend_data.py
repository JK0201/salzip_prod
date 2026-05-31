"""recommend data 9 tables

Revision ID: 0006_recommend_data
Revises: 0005_users_name
Create Date: 2026-05-26

"""

from collections.abc import Sequence

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

revision: str = "0006_recommend_data"
down_revision: str | None = "0005_users_name"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # 1. regions
    op.create_table(
        "regions",
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

    # 2. areas
    op.create_table(
        "areas",
        sa.Column("id", sa.UUID(), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("region_id", sa.UUID(), nullable=False),
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
        sa.ForeignKeyConstraint(["region_id"], ["regions.id"], ondelete="CASCADE"),
    )
    op.create_index("ix_areas_region_id", "areas", ["region_id"])
    op.create_index("ix_areas_lat_lng", "areas", ["lat", "lng"])

    # 3. listings
    op.create_table(
        "listings",
        sa.Column("id", sa.UUID(), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("region_id", sa.UUID(), nullable=False),
        sa.Column("area_id", sa.UUID(), nullable=True),
        sa.Column("kind", sa.Text(), nullable=False),
        sa.Column("deal_type", sa.Text(), nullable=False),
        sa.Column("building_name", sa.Text(), nullable=True),
        sa.Column("deposit", sa.Integer(), nullable=True),
        sa.Column(
            "monthly_rent", sa.Integer(), nullable=False, server_default=sa.text("0")
        ),
        sa.Column("deal_amount", sa.Integer(), nullable=True),
        sa.Column("area_m2", sa.Numeric(8, 2), nullable=True),
        sa.Column("floor", sa.Integer(), nullable=True),
        sa.Column("jibun", sa.Text(), nullable=True),
        sa.Column("road_addr", sa.Text(), nullable=True),
        sa.Column("build_year", sa.Integer(), nullable=True),
        sa.Column("umd_name", sa.Text(), nullable=True),
        sa.Column("deal_date", sa.Date(), nullable=True),
        sa.Column("lat", sa.Numeric(9, 6), nullable=True),
        sa.Column("lng", sa.Numeric(9, 6), nullable=True),
        sa.Column("source_payload", postgresql.JSONB(), nullable=True),
        sa.Column("flood_risk", sa.Boolean(), nullable=True),
        sa.Column("flood_year", sa.Integer(), nullable=True),
        sa.Column("estimated_kind", sa.Text(), nullable=True),
        sa.Column("dedup_hash", sa.CHAR(64), nullable=False, unique=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.ForeignKeyConstraint(["region_id"], ["regions.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["area_id"], ["areas.id"], ondelete="SET NULL"),
    )
    op.create_index("ix_listings_region_deal_type", "listings", ["region_id", "deal_type"])
    op.create_index("ix_listings_area_deal_type", "listings", ["area_id", "deal_type"])
    op.create_index("ix_listings_kind_dtype_date", "listings", ["kind", "deal_type", "deal_date"])
    op.create_index("ix_listings_building_area", "listings", ["building_name", "area_id"])
    op.create_index("ix_listings_deal_date", "listings", ["deal_date"])

    # 4. support_programs
    op.create_table(
        "support_programs",
        sa.Column("id", sa.UUID(), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("plcy_no", sa.Text(), nullable=False, unique=True),
        sa.Column("name", sa.Text(), nullable=False),
        sa.Column("category_l", sa.Text(), nullable=True),
        sa.Column("category_m", sa.Text(), nullable=True),
        sa.Column("age_min", sa.Integer(), nullable=True),
        sa.Column("age_max", sa.Integer(), nullable=True),
        sa.Column("income_min", sa.Integer(), nullable=True),
        sa.Column("income_max", sa.Integer(), nullable=True),
        sa.Column("marriage_cd", sa.Text(), nullable=True),
        sa.Column("support_amount", sa.Integer(), nullable=True),
        sa.Column("support_text", sa.Text(), nullable=True),
        sa.Column("apply_url", sa.Text(), nullable=True),
        sa.Column("start_date", sa.Date(), nullable=True),
        sa.Column("end_date", sa.Date(), nullable=True),
        sa.Column("region_zip_codes", sa.Text(), nullable=True),
        sa.Column("raw", postgresql.JSONB(), nullable=True),
        sa.Column("card_key", sa.Text(), nullable=True),
        sa.Column("loan_limit", sa.Integer(), nullable=True),
        sa.Column("deposit_limit", sa.Integer(), nullable=True),
        sa.Column("rent_limit", sa.Integer(), nullable=True),
        sa.Column("income_median_pct", sa.Integer(), nullable=True),
        sa.Column("income_max_annual", sa.Integer(), nullable=True),
        sa.Column("housing_types", postgresql.ARRAY(sa.Text()), nullable=True),
        sa.Column("rules_extracted", postgresql.JSONB(), nullable=True),
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
    )
    op.create_index("ix_support_programs_category_m", "support_programs", ["category_m"])
    op.create_index("ix_support_programs_age", "support_programs", ["age_min", "age_max"])
    op.create_index("ix_support_programs_card_key", "support_programs", ["card_key"])

    # 5. area_metrics
    op.create_table(
        "area_metrics",
        sa.Column("area_id", sa.UUID(), primary_key=True),
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
        sa.ForeignKeyConstraint(["area_id"], ["areas.id"], ondelete="CASCADE"),
    )

    # 6. area_trends
    op.create_table(
        "area_trends",
        sa.Column("id", sa.UUID(), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("region_id", sa.UUID(), nullable=True),
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
        sa.ForeignKeyConstraint(["region_id"], ["regions.id"], ondelete="CASCADE"),
        sa.UniqueConstraint(
            "region_label", "metric", "period", "statbl_id", name="uq_area_trends_natural"
        ),
    )
    op.create_index(
        "ix_area_trends_region_metric_period", "area_trends", ["region_id", "metric", "period"]
    )
    op.create_index(
        "ix_area_trends_label_metric_period", "area_trends", ["region_label", "metric", "period"]
    )

    # 7. hug_accidents
    op.create_table(
        "hug_accidents",
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
    )
    op.create_index("ix_hug_accidents_year_type", "hug_accidents", ["year", "guarantee_type"])

    # 8. commute_cache
    op.create_table(
        "commute_cache",
        sa.Column("id", sa.UUID(), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("origin_lat", sa.Numeric(9, 4), nullable=False),
        sa.Column("origin_lng", sa.Numeric(9, 4), nullable=False),
        sa.Column("area_id", sa.UUID(), nullable=False),
        sa.Column("total_time_min", sa.Integer(), nullable=False),
        sa.Column("payment_won", sa.Integer(), nullable=True),
        sa.Column("first_lane", sa.Text(), nullable=True),
        sa.Column(
            "fetched_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.ForeignKeyConstraint(["area_id"], ["areas.id"], ondelete="CASCADE"),
        sa.UniqueConstraint("origin_lat", "origin_lng", "area_id", name="uq_commute_cache_natural"),
    )
    op.create_index("ix_commute_cache_fetched_at", "commute_cache", ["fetched_at"])

    # 9. favorites
    op.create_table(
        "favorites",
        sa.Column("user_id", sa.UUID(), nullable=False),
        sa.Column("listing_id", sa.UUID(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["listing_id"], ["listings.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("user_id", "listing_id"),
    )
    op.create_index("ix_favorites_user_id", "favorites", ["user_id"])


def downgrade() -> None:
    op.drop_table("favorites")
    op.drop_table("commute_cache")
    op.drop_table("hug_accidents")
    op.drop_table("area_trends")
    op.drop_table("area_metrics")
    op.drop_table("support_programs")
    op.drop_table("listings")
    op.drop_table("areas")
    op.drop_table("regions")
