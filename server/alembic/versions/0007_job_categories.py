"""job_categories table

Revision ID: 0007_job_categories
Revises: 0006_recommend_data
Create Date: 2026-05-27

"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "0007_job_categories"
down_revision: str | None = "0006_recommend_data"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    job_categories_table = op.create_table(
        'job_categories',
        sa.Column("id", sa.UUID(), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("name", sa.Text(), nullable=False, unique=True),
        sa.Column("sort_order", sa.Integer(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
    )

    op.create_index("ix_job_categories_sort_order", "job_categories", ["sort_order"])

    op.bulk_insert(
        job_categories_table,
        [
            {'name': '개발', 'sort_order': 1},
            {'name': '경영', 'sort_order': 2},
            {'name': '마케팅', 'sort_order': 3},
            {'name': '디자인', 'sort_order': 4},
            {'name': '영업', 'sort_order': 5},
            {'name': '고객서비스', 'sort_order': 6},
            {'name': '미디어', 'sort_order': 7},
            {'name': 'HR', 'sort_order': 8},
            {'name': '엔지니어링', 'sort_order': 9},
            {'name': '금융', 'sort_order': 10},
            {'name': '제조', 'sort_order': 11},
            {'name': '의료', 'sort_order': 12},
            {'name': '교육', 'sort_order': 13},
            {'name': '게임', 'sort_order': 14},
            {'name': '기타', 'sort_order': 15},
        ],
    )


def downgrade() -> None:
    op.drop_table('job_categories')
