import datetime
import uuid

import pytest
from pydantic import BaseModel, ValidationError

from app.schemas.favorites import FavoriteItem, FavoritesResponse

# ── 공용 fixture ─────────────────────────────────────────────────────────────

_REQUIRED = dict(
    listing_id=uuid.uuid4(),
    kind="월세",
    deposit=5000000,
    monthly_rent=500000,
    risk_level="low",
    created_at=datetime.datetime(2024, 1, 1, 0, 0, 0),
)


# ── acceptance #1: listing_id, deposit, monthly_rent, risk_level, created_at 필드 존재 ──

def test_favorite_item_required_fields_exist():
    item = FavoriteItem(**_REQUIRED)
    assert item.listing_id == _REQUIRED["listing_id"]
    assert item.deposit == 5000000
    assert item.monthly_rent == 500000
    assert item.risk_level == "low"
    assert item.created_at == datetime.datetime(2024, 1, 1, 0, 0, 0)


def test_favorite_item_missing_listing_id_raises():
    payload = {k: v for k, v in _REQUIRED.items() if k != "listing_id"}
    with pytest.raises(ValidationError):
        FavoriteItem(**payload)


def test_favorite_item_missing_deposit_raises():
    payload = {k: v for k, v in _REQUIRED.items() if k != "deposit"}
    with pytest.raises(ValidationError):
        FavoriteItem(**payload)


def test_favorite_item_missing_monthly_rent_raises():
    payload = {k: v for k, v in _REQUIRED.items() if k != "monthly_rent"}
    with pytest.raises(ValidationError):
        FavoriteItem(**payload)


def test_favorite_item_missing_risk_level_raises():
    payload = {k: v for k, v in _REQUIRED.items() if k != "risk_level"}
    with pytest.raises(ValidationError):
        FavoriteItem(**payload)


def test_favorite_item_missing_created_at_raises():
    payload = {k: v for k, v in _REQUIRED.items() if k != "created_at"}
    with pytest.raises(ValidationError):
        FavoriteItem(**payload)


# ── acceptance #2: area_m2, floor, flood_risk, build_year, umd_name, lat, lng → None 허용 ──

@pytest.mark.parametrize("field", [
    "area_m2", "floor", "flood_risk", "build_year", "umd_name", "lat", "lng",
])
def test_favorite_item_optional_field_accepts_none(field):
    item = FavoriteItem(**_REQUIRED, **{field: None})
    assert getattr(item, field) is None


def test_favorite_item_all_optional_fields_none():
    item = FavoriteItem(**_REQUIRED)
    assert item.area_m2 is None
    assert item.floor is None
    assert item.flood_risk is None
    assert item.build_year is None
    assert item.umd_name is None
    assert item.lat is None
    assert item.lng is None


# ── acceptance #3: model_config.from_attributes == True ──────────────────────

def test_favorite_item_model_config_from_attributes():
    assert FavoriteItem.model_config.get("from_attributes") is True


# ── acceptance #4: FavoritesResponse.items → list[FavoriteItem] ──────────────

def test_favorites_response_items_field():
    item = FavoriteItem(**_REQUIRED)
    resp = FavoritesResponse(items=[item], ids=[_REQUIRED["listing_id"]])
    assert isinstance(resp.items, list)
    assert len(resp.items) == 1
    assert isinstance(resp.items[0], FavoriteItem)


def test_favorites_response_items_empty_list():
    resp = FavoritesResponse(items=[], ids=[])
    assert resp.items == []


# ── acceptance #5: FavoritesResponse.ids → list[uuid.UUID] ──────────────────

def test_favorites_response_ids_field():
    uid = uuid.uuid4()
    resp = FavoritesResponse(items=[], ids=[uid])
    assert isinstance(resp.ids, list)
    assert isinstance(resp.ids[0], uuid.UUID)
    assert resp.ids[0] == uid


def test_favorites_response_ids_empty_list():
    resp = FavoritesResponse(items=[], ids=[])
    assert resp.ids == []
