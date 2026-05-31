import uuid

import sqlalchemy as sa
from fastapi import APIRouter
from starlette.responses import StreamingResponse

from app.core.auth import SessionDep
from app.core.deps import ConnDep
from app.core.exceptions import NotFoundError
from app.db.tables.listings import listings_table
from app.services.agents import orchestrator
from app.services.agents.locale_data import get_locale_input
from app.services.agents.risk_data import get_risk_input
from app.services.agents.sise_data import get_sise_input
from app.services.agents.support_data import get_support_input

router = APIRouter(tags=["analyze"])


@router.post("/listings/{listing_id}/analyze")
async def post_analyze(
    listing_id: uuid.UUID,
    session: SessionDep,
    conn: ConnDep,
) -> StreamingResponse:
    stmt = sa.select(listings_table).where(listings_table.c.id == listing_id)
    result = await conn.execute(stmt)
    row = result.mappings().first()
    if row is None:
        raise NotFoundError(f"listing {listing_id} not found")

    risk = await get_risk_input(listing_id, conn)
    try:
        sise = await get_sise_input(listing_id, conn)
    except Exception:
        sise = None

    try:
        locale = await get_locale_input(listing_id, conn)
    except Exception:
        locale = None

    try:
        support = await get_support_input(session.session_id, conn)
    except Exception:
        support = None

    context = {
        "listing_id": str(listing_id),
        "building_name": row.building_name,
        "kind": row.kind,
        "deal_type": row.deal_type,
        "deposit": row.deposit,
        "monthly_rent": row.monthly_rent,
        "area_m2": row.area_m2,
        "floor": row.floor,
        "road_addr": row.road_addr,
    }
    # 4 도메인 키는 무조건 포함(null이라도). LLM이 자기 도메인 키 없으면
    # 다른 도메인 정보로 흉내내는 환각 방지 — 명시적 null로 case 분기 유도.
    context["risk"] = risk
    context["sise"] = sise
    context["locale"] = locale
    context["support"] = support

    stream = orchestrator.analyze_stream(context)
    first_chunk = await anext(stream)

    async def _primed_stream():
        yield first_chunk
        async for chunk in stream:
            yield chunk

    return StreamingResponse(_primed_stream(), media_type="text/event-stream")
