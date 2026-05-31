import datetime
import uuid
from uuid import UUID

from pydantic import BaseModel


class ListingItem(BaseModel):
    id: UUID
    kind: str
    estimated_kind: str | None = None
    building_name: str | None = None
    deposit: int
    monthly_rent: int
    area_m2: float | None = None
    floor: int | None = None
    lat: float
    lng: float
    flood_risk: bool | None = None
    build_year: int | None = None
    jibun: str | None = None


class AreaMetrics(BaseModel):
    cafe_count: int
    food_count: int
    culture_count: int
    park_count: int
    mart_count: int
    subway_count: int
    hospital_count: int
    pharmacy_count: int


class AreaSafety(BaseModel):
    avg_jeonse_ratio: float | None = None
    flood_ratio: float | None = None
    avg_build_year: int | None = None


class AreaItem(BaseModel):
    area_id: UUID
    rank: int
    name: str
    meta: str
    score: int
    tier: int
    lat: float
    lng: float
    commuteMinutes: int
    scores: dict[str, int]
    listing_count: int
    flood_risk_count: int
    reason: str
    listings: list[ListingItem]
    metrics: AreaMetrics
    safety: AreaSafety


class RecommendResponse(BaseModel):
    areas: list[AreaItem]
    match_id: uuid.UUID | None = None
    created_at: datetime.datetime | None = None
    request: dict | None = None
