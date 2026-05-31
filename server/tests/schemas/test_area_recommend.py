import uuid
from uuid import UUID

import pytest
from pydantic import BaseModel, ValidationError

from app.schemas.area_recommend import (
    AreaItem,
    AreaMetrics,
    AreaSafety,
    ListingItem,
    RecommendResponse,
)


# ── acceptance #1: ListingItem import 가능 ────────────────────────────────────

def test_listing_item_importable():
    assert issubclass(ListingItem, BaseModel)


# ── acceptance #2: AreaMetrics, AreaSafety, AreaItem, RecommendResponse import 가능

def test_area_classes_importable():
    assert issubclass(AreaMetrics, BaseModel)
    assert issubclass(AreaSafety, BaseModel)
    assert issubclass(AreaItem, BaseModel)
    assert issubclass(RecommendResponse, BaseModel)


# ── acceptance #3: ListingItem 필드 집합 ──────────────────────────────────────

def test_listing_item_field_set():
    expected = {
        "id", "kind", "estimated_kind", "building_name", "deposit",
        "monthly_rent", "area_m2", "floor", "lat", "lng",
        "flood_risk", "build_year", "jibun",
    }
    assert set(ListingItem.model_fields.keys()) == expected


def test_listing_item_valid_construction():
    item = ListingItem(
        id=uuid.uuid4(),
        kind="원룸",
        deposit=10_000_000,
        monthly_rent=500_000,
        lat=37.5,
        lng=127.0,
    )
    assert isinstance(item.id, UUID)
    assert item.kind == "원룸"
    assert item.deposit == 10_000_000
    assert item.monthly_rent == 500_000


def test_listing_item_optional_fields_default_none():
    item = ListingItem(
        id=uuid.uuid4(),
        kind="오피스텔",
        deposit=5_000_000,
        monthly_rent=300_000,
        lat=37.1,
        lng=127.1,
    )
    assert item.estimated_kind is None
    assert item.building_name is None
    assert item.area_m2 is None
    assert item.floor is None
    assert item.flood_risk is None
    assert item.build_year is None
    assert item.jibun is None


def test_listing_item_missing_required_id_raises():
    with pytest.raises(ValidationError):
        ListingItem(kind="원룸", deposit=1_000_000, monthly_rent=400_000, lat=37.5, lng=127.0)


# ── acceptance #4: AreaMetrics 필드 집합 ──────────────────────────────────────

def test_area_metrics_field_set():
    expected = {
        "cafe_count", "food_count", "culture_count", "park_count",
        "mart_count", "subway_count", "hospital_count", "pharmacy_count",
    }
    assert set(AreaMetrics.model_fields.keys()) == expected


def test_area_metrics_valid_construction():
    m = AreaMetrics(
        cafe_count=5,
        food_count=10,
        culture_count=2,
        park_count=3,
        mart_count=4,
        subway_count=1,
        hospital_count=2,
        pharmacy_count=3,
    )
    assert m.cafe_count == 5
    assert m.subway_count == 1
    assert m.pharmacy_count == 3


# ── acceptance #5: AreaSafety 필드 집합 (모두 Optional) ───────────────────────

def test_area_safety_field_set():
    expected = {"avg_jeonse_ratio", "flood_ratio", "avg_build_year"}
    assert set(AreaSafety.model_fields.keys()) == expected


def test_area_safety_all_optional_default_none():
    s = AreaSafety()
    assert s.avg_jeonse_ratio is None
    assert s.flood_ratio is None
    assert s.avg_build_year is None


def test_area_safety_with_values():
    s = AreaSafety(avg_jeonse_ratio=0.75, flood_ratio=0.05, avg_build_year=2005)
    assert s.avg_jeonse_ratio == 0.75
    assert s.flood_ratio == 0.05
    assert s.avg_build_year == 2005


# ── acceptance #6: AreaItem 필드 집합 ─────────────────────────────────────────

def test_area_item_field_set():
    expected = {
        "area_id", "rank", "name", "meta", "score", "tier",
        "lat", "lng", "commuteMinutes", "scores", "listing_count",
        "flood_risk_count", "reason", "listings", "metrics", "safety",
    }
    assert set(AreaItem.model_fields.keys()) == expected


def _make_area_item(**overrides) -> AreaItem:
    listing = ListingItem(
        id=uuid.uuid4(),
        kind="원룸",
        deposit=5_000_000,
        monthly_rent=300_000,
        lat=37.5,
        lng=127.0,
    )
    metrics = AreaMetrics(
        cafe_count=3, food_count=5, culture_count=1, park_count=2,
        mart_count=2, subway_count=1, hospital_count=1, pharmacy_count=2,
    )
    safety = AreaSafety()
    defaults = dict(
        area_id=uuid.uuid4(),
        rank=1,
        name="마포구",
        meta="서울 서북부",
        score=85,
        tier=1,
        lat=37.55,
        lng=126.91,
        commuteMinutes=25,
        scores={"lifestyle": 80, "safety": 90},
        listing_count=10,
        flood_risk_count=2,
        reason="교통이 편리합니다",
        listings=[listing],
        metrics=metrics,
        safety=safety,
    )
    defaults.update(overrides)
    return AreaItem(**defaults)


def test_area_item_valid_construction():
    area = _make_area_item()
    assert area.rank == 1
    assert area.name == "마포구"
    assert isinstance(area.area_id, UUID)
    assert isinstance(area.listings, list)
    assert isinstance(area.listings[0], ListingItem)
    assert isinstance(area.metrics, AreaMetrics)
    assert isinstance(area.safety, AreaSafety)
    assert isinstance(area.scores, dict)


def test_area_item_scores_is_dict_str_int():
    area = _make_area_item(scores={"commute": 70, "park": 95})
    assert area.scores["commute"] == 70
    assert area.scores["park"] == 95


def test_area_item_missing_required_raises():
    with pytest.raises(ValidationError):
        AreaItem()


# ── acceptance #7: RecommendResponse 필드는 areas 1개뿐, list[AreaItem] 타입 ──

def test_recommend_response_field_set():
    assert set(RecommendResponse.model_fields.keys()) == {"areas", "match_id", "created_at"}


def test_recommend_response_areas_is_list_of_area_item():
    area = _make_area_item()
    resp = RecommendResponse(areas=[area])
    assert isinstance(resp.areas, list)
    assert isinstance(resp.areas[0], AreaItem)


def test_recommend_response_empty_areas():
    resp = RecommendResponse(areas=[])
    assert resp.areas == []


def test_recommend_response_missing_areas_raises():
    with pytest.raises(ValidationError):
        RecommendResponse()
