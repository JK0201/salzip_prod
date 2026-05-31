import json

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from sqlalchemy import text

from app.core.auth import SessionDep
from app.core.deps import ConnDep
from app.core.exceptions import AddressNotFound
from app.schemas.area_recommend import RecommendResponse
from app.services import recommend as recommend_service

router = APIRouter(tags=["recommend"])


class RecommendRequest(BaseModel):
    workplace_name: str
    workplace_address: str
    job_type: str
    max_commute_minutes: int
    lifestyle_tags: list[str]
    deposit_max_wan: int
    monthly_rent_max_wan: int
    age: int
    annual_income_wan: int
    household_type: str
    home_ownerless: bool


@router.post(
    "/recommend",
    status_code=200,
    response_model=RecommendResponse,
    response_model_exclude_unset=True,
)
async def post_recommend(
    req: RecommendRequest,
    session: SessionDep,
    conn: ConnDep,
) -> RecommendResponse:
    try:
        result = await recommend_service.recommend(req, conn, session.session_id)
    except AddressNotFound:
        raise HTTPException(status_code=400, detail="address_not_found") from None
    if isinstance(result, list):
        return RecommendResponse(areas=result)
    return RecommendResponse(areas=result["areas"], match_id=result["match_id"])


@router.get("/recommend/latest", status_code=200, response_model=RecommendResponse)
async def get_recommend_latest(session: SessionDep, conn: ConnDep) -> RecommendResponse:
    stmt = text(
        "SELECT mr.id AS id, mr.payload AS payload, mr.created_at AS created_at"
        " FROM match_results mr"
        " JOIN profiles p ON p.id = mr.profile_id"
        " WHERE (p.session_id = :sid OR (p.user_id IS NOT NULL"
        " AND p.user_id = (SELECT user_id FROM sessions WHERE id = :sid)))"
        " ORDER BY mr.created_at DESC LIMIT 1"
    )
    _result = await conn.execute(stmt, {"sid": session.session_id})
    row = _result.mappings().first()
    if row is None:
        return RecommendResponse(areas=[], match_id=None)
    payload = row["payload"]
    data = payload if isinstance(payload, dict) else json.loads(payload)
    areas = data.get("areas", [])
    request_obj = data.get("request")
    return RecommendResponse(
        areas=areas, match_id=row["id"], created_at=row["created_at"], request=request_obj
    )
