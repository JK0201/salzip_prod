import sqlalchemy as sa
from fastapi import APIRouter

from app.core.deps import ConnDep
from app.db.tables.job_categories import job_categories_table
from app.schemas.job_category import JobCategoryOut

router = APIRouter(tags=["job_categories"])


@router.get("/job_categories")
async def list_job_categories(
    conn: ConnDep,
) -> list[JobCategoryOut]:
    stmt = sa.select(
        job_categories_table.c.id,
        job_categories_table.c.name,
    ).order_by(job_categories_table.c.sort_order)
    result = await conn.execute(stmt)
    return [JobCategoryOut.model_validate(row, from_attributes=True) for row in result]
