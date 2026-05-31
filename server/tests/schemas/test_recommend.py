import pytest
from pydantic import BaseModel, ValidationError

from app.schemas.recommend import (
    AreaRecommendation,
    ListingRecommendation,
    ProfileIn,
    RecommendResponse,
    SupportRecommendation,
)


# ── ProfileIn 클래스 존재 및 BaseModel 상속 ──────────────────────────────────

def test_profile_in_is_pydantic_model():
    assert issubclass(ProfileIn, BaseModel)


# ── ProfileIn 정상 페이로드 검증 통과 (acceptance #21) ──────────────────────

def test_profile_in_valid_payload():
    obj = ProfileIn(
        workplace_address="서울시 강남구 테헤란로 1",
        max_commute_minutes=30,
        life_tags=["조용한", "공원 근처"],
        rent_max=800000,
        deposit_max=50000000,
        age_band="20s",
        household_size=1,
    )
    assert obj.workplace_address == "서울시 강남구 테헤란로 1"
    assert obj.max_commute_minutes == 30
    assert obj.life_tags == ["조용한", "공원 근처"]
    assert obj.rent_max == 800000
    assert obj.deposit_max == 50000000
    assert obj.age_band == "20s"
    assert obj.household_size == 1


# ── ProfileIn 선택 필드 기본값 None ─────────────────────────────────────────

def test_profile_in_optional_fields_default_none():
    obj = ProfileIn(
        workplace_address="서울",
        max_commute_minutes=20,
        life_tags=[],
        rent_max=500000,
        deposit_max=10000000,
        age_band="30s",
        household_size=2,
    )
    assert obj.job_code is None
    assert obj.is_homeless is None
    assert obj.income_band is None


# ── ProfileIn 필드 타입 검증 ─────────────────────────────────────────────────

def test_profile_in_workplace_address_is_str():
    obj = ProfileIn(
        workplace_address="강남구",
        max_commute_minutes=30,
        life_tags=[],
        rent_max=500000,
        deposit_max=10000000,
        age_band="20s",
        household_size=1,
    )
    assert isinstance(obj.workplace_address, str)


def test_profile_in_job_code_optional_str():
    obj = ProfileIn(
        workplace_address="강남구",
        job_code="SE",
        max_commute_minutes=30,
        life_tags=[],
        rent_max=500000,
        deposit_max=10000000,
        age_band="20s",
        household_size=1,
    )
    assert obj.job_code == "SE"


def test_profile_in_max_commute_minutes_is_int():
    obj = ProfileIn(
        workplace_address="강남구",
        max_commute_minutes=45,
        life_tags=[],
        rent_max=500000,
        deposit_max=10000000,
        age_band="20s",
        household_size=1,
    )
    assert isinstance(obj.max_commute_minutes, int)


def test_profile_in_life_tags_is_list_of_str():
    obj = ProfileIn(
        workplace_address="강남구",
        max_commute_minutes=30,
        life_tags=["조용한", "녹지"],
        rent_max=500000,
        deposit_max=10000000,
        age_band="20s",
        household_size=1,
    )
    assert isinstance(obj.life_tags, list)
    assert all(isinstance(t, str) for t in obj.life_tags)


def test_profile_in_is_homeless_optional_bool():
    obj = ProfileIn(
        workplace_address="강남구",
        max_commute_minutes=30,
        life_tags=[],
        rent_max=500000,
        deposit_max=10000000,
        age_band="20s",
        household_size=1,
        is_homeless=True,
    )
    assert obj.is_homeless is True


def test_profile_in_income_band_optional_str():
    obj = ProfileIn(
        workplace_address="강남구",
        max_commute_minutes=30,
        life_tags=[],
        rent_max=500000,
        deposit_max=10000000,
        age_band="20s",
        household_size=1,
        income_band="low",
    )
    assert obj.income_band == "low"


# ── ProfileIn 필수 필드 누락 시 ValidationError (acceptance #22) ─────────────

def test_profile_in_missing_required_fields_raises_validation_error():
    with pytest.raises(ValidationError):
        ProfileIn()


@pytest.mark.parametrize("missing_field", [
    "workplace_address",
    "max_commute_minutes",
    "life_tags",
    "rent_max",
    "deposit_max",
    "age_band",
    "household_size",
])
def test_profile_in_missing_each_required_field_raises(missing_field):
    payload = {
        "workplace_address": "강남구",
        "max_commute_minutes": 30,
        "life_tags": [],
        "rent_max": 500000,
        "deposit_max": 10000000,
        "age_band": "20s",
        "household_size": 1,
    }
    del payload[missing_field]
    with pytest.raises(ValidationError):
        ProfileIn(**payload)


# ── AreaRecommendation ───────────────────────────────────────────────────────

def test_area_recommendation_is_pydantic_model():
    assert issubclass(AreaRecommendation, BaseModel)


def test_area_recommendation_fields():
    obj = AreaRecommendation(name="마포구", score=0.87, reason="공원 접근성 우수")
    assert obj.name == "마포구"
    assert isinstance(obj.score, float)
    assert obj.reason == "공원 접근성 우수"


# ── ListingRecommendation ────────────────────────────────────────────────────

def test_listing_recommendation_is_pydantic_model():
    assert issubclass(ListingRecommendation, BaseModel)


@pytest.mark.parametrize("risk_value", ["low", "mid", "high"])
def test_listing_recommendation_valid_risk(risk_value):
    obj = ListingRecommendation(title="역세권 원룸", risk=risk_value, reason="교통 편리")
    assert obj.risk == risk_value


def test_listing_recommendation_invalid_risk_rejected():
    with pytest.raises(ValidationError):
        ListingRecommendation(title="역세권 원룸", risk="invalid", reason="교통 편리")


def test_listing_recommendation_fields():
    obj = ListingRecommendation(title="강남 오피스텔", risk="low", reason="저렴함")
    assert isinstance(obj.title, str)
    assert isinstance(obj.reason, str)


# ── SupportRecommendation ────────────────────────────────────────────────────

def test_support_recommendation_is_pydantic_model():
    assert issubclass(SupportRecommendation, BaseModel)


def test_support_recommendation_fields():
    obj = SupportRecommendation(name="청년월세지원", eligible=True, reason="소득 기준 충족")
    assert obj.name == "청년월세지원"
    assert obj.eligible is True
    assert isinstance(obj.reason, str)


# ── RecommendResponse ────────────────────────────────────────────────────────

def test_recommend_response_is_pydantic_model():
    assert issubclass(RecommendResponse, BaseModel)


def test_recommend_response_fields():
    resp = RecommendResponse(
        areas=[AreaRecommendation(name="마포구", score=0.9, reason="좋음")],
        listings=[ListingRecommendation(title="원룸", risk="low", reason="저렴")],
        supports=[SupportRecommendation(name="지원금", eligible=False, reason="미해당")],
    )
    assert isinstance(resp.areas, list)
    assert isinstance(resp.listings, list)
    assert isinstance(resp.supports, list)
    assert isinstance(resp.areas[0], AreaRecommendation)
    assert isinstance(resp.listings[0], ListingRecommendation)
    assert isinstance(resp.supports[0], SupportRecommendation)


def test_recommend_response_empty_lists():
    resp = RecommendResponse(areas=[], listings=[], supports=[])
    assert resp.areas == []
    assert resp.listings == []
    assert resp.supports == []
