"""supports_enrich: add 20 columns to support_programs

Revision ID: 0009_supports_enrich
Revises: 0008_lifestyle_tags
Create Date: 2026-05-28

"""

from collections.abc import Sequence

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

revision: str = "0009_supports_enrich"
down_revision: str | None = "0008_lifestyle_tags"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # LLM 추출 6개
    op.add_column("support_programs", sa.Column("monthly_amount_wan", sa.Integer(), nullable=True))
    op.add_column("support_programs", sa.Column("duration_months", sa.Integer(), nullable=True))
    op.add_column("support_programs", sa.Column("asset_limit_wan", sa.Integer(), nullable=True))
    op.add_column("support_programs", sa.Column("support_type", sa.Text(), nullable=True))
    op.add_column("support_programs", sa.Column("is_homeless_required", sa.Boolean(), nullable=True))
    op.add_column("support_programs", sa.Column("separate_from_parents", sa.Boolean(), nullable=True))
    # raw 메타 10개
    op.add_column("support_programs", sa.Column("agency_name", sa.Text(), nullable=True))
    op.add_column("support_programs", sa.Column("operating_agency", sa.Text(), nullable=True))
    op.add_column("support_programs", sa.Column("recruit_count", sa.Integer(), nullable=True))
    op.add_column("support_programs", sa.Column("recruit_unlimited", sa.Boolean(), nullable=True))
    op.add_column("support_programs", sa.Column("submission_documents", sa.Text(), nullable=True))
    op.add_column("support_programs", sa.Column("screening_method", sa.Text(), nullable=True))
    op.add_column("support_programs", sa.Column("participation_exclusion", sa.Text(), nullable=True))
    op.add_column("support_programs", sa.Column("reference_urls", postgresql.ARRAY(sa.Text()), nullable=True))
    op.add_column("support_programs", sa.Column("keyword_name", sa.Text(), nullable=True))
    op.add_column("support_programs", sa.Column("view_count", sa.Integer(), nullable=True))
    # 코드 4개
    op.add_column("support_programs", sa.Column("major_code", sa.Text(), nullable=True))
    op.add_column("support_programs", sa.Column("job_code", sa.Text(), nullable=True))
    op.add_column("support_programs", sa.Column("school_code", sa.Text(), nullable=True))
    op.add_column("support_programs", sa.Column("business_code", sa.Text(), nullable=True))


def downgrade() -> None:
    op.drop_column("support_programs", "business_code")
    op.drop_column("support_programs", "school_code")
    op.drop_column("support_programs", "job_code")
    op.drop_column("support_programs", "major_code")
    op.drop_column("support_programs", "view_count")
    op.drop_column("support_programs", "keyword_name")
    op.drop_column("support_programs", "reference_urls")
    op.drop_column("support_programs", "participation_exclusion")
    op.drop_column("support_programs", "screening_method")
    op.drop_column("support_programs", "submission_documents")
    op.drop_column("support_programs", "recruit_unlimited")
    op.drop_column("support_programs", "recruit_count")
    op.drop_column("support_programs", "operating_agency")
    op.drop_column("support_programs", "agency_name")
    op.drop_column("support_programs", "separate_from_parents")
    op.drop_column("support_programs", "is_homeless_required")
    op.drop_column("support_programs", "support_type")
    op.drop_column("support_programs", "asset_limit_wan")
    op.drop_column("support_programs", "duration_months")
    op.drop_column("support_programs", "monthly_amount_wan")
