import sqlalchemy as sa
from fastapi import APIRouter

from app.core.deps import ConnDep
from app.db.tables.lifestyle_tags import lifestyle_tags_table
from app.schemas.lifestyle_tag import LifestyleTagOut

router = APIRouter(prefix="/lifestyle_tags", tags=["lifestyle_tags"])


@router.get("", response_model=list[LifestyleTagOut])
async def list_lifestyle_tags(
    conn: ConnDep,
) -> list[LifestyleTagOut]:
    stmt = sa.select(
        lifestyle_tags_table.c.id,
        lifestyle_tags_table.c.name,
    ).order_by(lifestyle_tags_table.c.sort_order)
    result = await conn.execute(stmt)
    return [LifestyleTagOut.model_validate(row._mapping) for row in result]
