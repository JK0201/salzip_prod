import inspect
import uuid
from unittest.mock import AsyncMock, MagicMock

import pytest

from app.services.agents.sise_data import get_sise_input

FAKE_LISTING_ID = uuid.uuid4()
FAKE_AREA_ID = uuid.uuid4()


def _exec_result(first_value):
    """conn.execute() 반환값 mock — .mappings().first() → first_value."""
    result = MagicMock()
    mappings_obj = MagicMock()
    mappings_obj.first.return_value = first_value
    result.mappings.return_value = mappings_obj
    return result


def make_conn(*first_values):
    """순서대로 execute 호출 시 각 first_value 반환하는 async conn mock."""
    conn = AsyncMock()
    conn.execute.side_effect = [_exec_result(v) for v in first_values]
    return conn


def _listing(deposit=10000, monthly_rent=0, estimated_kind="아파트", deal_type="전세"):
    return {
        "deposit": deposit,
        "monthly_rent": monthly_rent,
        "area_id": FAKE_AREA_ID,
        "estimated_kind": estimated_kind,
        "deal_type": deal_type,
    }


def _dist(sample_size=10, median_conv=10000):
    return {"sample_size": sample_size, "median_conv": median_conv}


# acceptance #1: async coroutine, 파라미터 (listing_id, conn)
def test_get_sise_input_is_async_with_correct_params():
    assert inspect.iscoroutinefunction(get_sise_input)
    params = list(inspect.signature(get_sise_input).parameters.keys())
    assert params == ["listing_id", "conn"]


# acceptance #6: listing 없으면 None 반환
async def test_get_sise_input_returns_none_when_listing_not_found():
    conn = make_conn(None)
    result = await get_sise_input(FAKE_LISTING_ID, conn)
    assert result is None


# acceptance #2: 환산보증금 = deposit + monthly_rent*100
async def test_get_sise_input_target_conv_calculation():
    conn = make_conn(_listing(deposit=10000, monthly_rent=30), _dist(sample_size=10, median_conv=12000))
    result = await get_sise_input(FAKE_LISTING_ID, conn)
    assert result is not None
    assert result["target_conv"] == 13000  # 10000 + 30*100


# acceptance #2: deposit=None → 0으로 처리
async def test_get_sise_input_target_conv_null_deposit():
    conn = make_conn(_listing(deposit=None, monthly_rent=50), _dist(sample_size=10, median_conv=5000))
    result = await get_sise_input(FAKE_LISTING_ID, conn)
    assert result is not None
    assert result["target_conv"] == 5000  # 0 + 50*100


# acceptance #3: target_conv <= median*0.85 → "저렴"
async def test_get_sise_input_verdict_cheap():
    # target=8000, median=10000 → 8000 <= 8500 → 저렴
    conn = make_conn(_listing(deposit=8000, monthly_rent=0), _dist(sample_size=10, median_conv=10000))
    result = await get_sise_input(FAKE_LISTING_ID, conn)
    assert result["verdict"] == "저렴"


# acceptance #3: median*0.85 < target <= median*1.15 → "적정"
async def test_get_sise_input_verdict_appropriate():
    # target=10000, median=10000 → 적정
    conn = make_conn(_listing(deposit=10000, monthly_rent=0), _dist(sample_size=10, median_conv=10000))
    result = await get_sise_input(FAKE_LISTING_ID, conn)
    assert result["verdict"] == "적정"


# acceptance #3: target > median*1.15 → "비쌈"
async def test_get_sise_input_verdict_expensive():
    # target=12000, median=10000 → 12000 > 11500 → 비쌈
    conn = make_conn(_listing(deposit=12000, monthly_rent=0), _dist(sample_size=10, median_conv=10000))
    result = await get_sise_input(FAKE_LISTING_ID, conn)
    assert result["verdict"] == "비쌈"


# acceptance #4: sample_size < 5 → estimated_kind 조건 제거 후 재조회 (execute 3회)
async def test_get_sise_input_fallback_when_sample_size_lt_5():
    small_dist = _dist(sample_size=3, median_conv=10000)
    fallback_dist = _dist(sample_size=20, median_conv=9000)
    conn = make_conn(_listing(), small_dist, fallback_dist)
    result = await get_sise_input(FAKE_LISTING_ID, conn)
    assert result is not None
    assert result["sample_size"] == 20
    # listing(1) + initial dist(2) + fallback dist(3)
    assert conn.execute.call_count == 3


# acceptance #5: 폴백 후에도 sample_size==0 → None 또는 verdict=="비교불가"
async def test_get_sise_input_returns_none_or_uncomputable_when_fallback_empty():
    small_dist = _dist(sample_size=2, median_conv=10000)
    empty_dist = _dist(sample_size=0, median_conv=None)
    conn = make_conn(_listing(), small_dist, empty_dist)
    result = await get_sise_input(FAKE_LISTING_ID, conn)
    assert result is None or (isinstance(result, dict) and result.get("verdict") == "비교불가")


# acceptance #7: 반환 dict에 필수 키 존재
async def test_get_sise_input_return_dict_has_required_keys():
    conn = make_conn(_listing(deposit=10000, monthly_rent=0), _dist(sample_size=10, median_conv=10000))
    result = await get_sise_input(FAKE_LISTING_ID, conn)
    assert result is not None
    for key in ("target_conv", "median_conv", "sample_size", "verdict"):
        assert key in result, f"Missing key: {key}"
