import datetime
import uuid

from pydantic import BaseModel, ConfigDict


class FavoriteItem(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    listing_id: uuid.UUID
    kind: str
    estimated_kind: str | None = None
    building_name: str | None = None
    deposit: int
    monthly_rent: int
    area_m2: float | None = None
    floor: int | None = None
    flood_risk: bool | None = None
    build_year: int | None = None
    umd_name: str | None = None
    lat: float | None = None
    lng: float | None = None
    risk_level: str
    created_at: datetime.datetime


class FavoritesResponse(BaseModel):
    items: list[FavoriteItem]
    ids: list[uuid.UUID]
