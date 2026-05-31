from typing import Literal

from pydantic import BaseModel


class ProfileIn(BaseModel):
    workplace_address: str
    job_code: str | None = None
    max_commute_minutes: int
    life_tags: list[str]
    rent_max: int
    deposit_max: int
    age_band: str
    household_size: int
    is_homeless: bool | None = None
    income_band: str | None = None


class AreaRecommendation(BaseModel):
    name: str
    score: float
    reason: str


class ListingRecommendation(BaseModel):
    title: str
    risk: Literal["low", "mid", "high"]
    reason: str


class SupportRecommendation(BaseModel):
    name: str
    eligible: bool
    reason: str


class RecommendResponse(BaseModel):
    areas: list[AreaRecommendation]
    listings: list[ListingRecommendation]
    supports: list[SupportRecommendation]
