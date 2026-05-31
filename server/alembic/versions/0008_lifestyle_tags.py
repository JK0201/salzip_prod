"""lifestyle_tags table

Revision ID: 0008_lifestyle_tags
Revises: 0007_job_categories
Create Date: 2026-05-27

"""

from collections.abc import Sequence

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

revision: str = "0008_lifestyle_tags"
down_revision: str | None = "0007_job_categories"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    lifestyle_tags_tbl = op.create_table(
        "lifestyle_tags",
        sa.Column("id", sa.UUID(), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("name", sa.Text(), nullable=False, unique=True),
        sa.Column("sort_order", sa.Integer(), nullable=False),
        sa.Column("categories", postgresql.ARRAY(sa.Text()), nullable=False),
        sa.Column("is_inverse", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
    )

    op.create_index("ix_lifestyle_tags_sort_order", "lifestyle_tags", ["sort_order"])

    op.bulk_insert(
        lifestyle_tags_tbl,
        [
            {'name': '식도락', 'sort_order': 1, 'categories': ['food'], 'is_inverse': False},
            {'name': '카페 라이프', 'sort_order': 2, 'categories': ['cafe'], 'is_inverse': False},
            {'name': '산책', 'sort_order': 3, 'categories': ['park'], 'is_inverse': False},
            {'name': '문화·여가', 'sort_order': 4, 'categories': ['culture'], 'is_inverse': False},
            {'name': '장보기 편함', 'sort_order': 5, 'categories': ['mart'], 'is_inverse': False},
            {'name': '역세권', 'sort_order': 6, 'categories': ['subway'], 'is_inverse': False},
            {'name': '의료 가까이', 'sort_order': 7, 'categories': ['hospital', 'pharmacy'], 'is_inverse': False},
            {'name': '한적함', 'sort_order': 8, 'categories': ['subway'], 'is_inverse': True},
        ],
    )


def downgrade() -> None:
    op.drop_index("ix_lifestyle_tags_sort_order", table_name="lifestyle_tags")
    op.drop_table("lifestyle_tags")
