import inspect
import uuid
from unittest.mock import AsyncMock, MagicMock

from app.services.agents.locale_data import get_locale_input

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


LISTING_ROW = {"area_id": FAKE_AREA_ID}

METRICS_ROW = {
    "mart_count": 3,
    "cafe_count": 5,
    "food_count": 7,
    "hospital_count": 2,
    "pharmacy_count": 4,
    "culture_count": 1,
    "subway_count": 2,
    "park_count": 6,
}

AREA_ROW = {"emd_name": "역삼동"}


# acceptance #1: async coroutine, 파라미터 정확히 (listing_id, conn)
def test_get_locale_input_is_async_with_correct_params():
    assert inspect.iscoroutinefunction(get_locale_input)
    params = list(inspect.signature(get_locale_input).parameters.keys())
    assert params == ["listing_id", "conn"]


# acceptance #2: counts에 8개 키 모두 존재
async def test_counts_dict_has_all_8_keys():
    conn = make_conn(LISTING_ROW, METRICS_ROW, AREA_ROW)
    result = await get_locale_input(FAKE_LISTING_ID, conn)
    assert result is not None
    assert set(result["counts"].keys()) == {
        "cafe", "food", "culture", "park", "mart", "subway", "hospital", "pharmacy"
    }


# acceptance #2: counts 값이 metrics row 값과 일치
async def test_counts_values_match_metrics_row():
    conn = make_conn(LISTING_ROW, METRICS_ROW, AREA_ROW)
    result = await get_locale_input(FAKE_LISTING_ID, conn)
    assert result is not None
    counts = result["counts"]
    assert counts["cafe"] == METRICS_ROW["cafe_count"]
    assert counts["food"] == METRICS_ROW["food_count"]
    assert counts["culture"] == METRICS_ROW["culture_count"]
    assert counts["park"] == METRICS_ROW["park_count"]
    assert counts["mart"] == METRICS_ROW["mart_count"]
    assert counts["subway"] == METRICS_ROW["subway_count"]
    assert counts["hospital"] == METRICS_ROW["hospital_count"]
    assert counts["pharmacy"] == METRICS_ROW["pharmacy_count"]


# acceptance #3: subway_count > 0 → subway_access True
async def test_subway_access_true_when_subway_count_positive():
    conn = make_conn(LISTING_ROW, METRICS_ROW, AREA_ROW)  # subway_count=2
    result = await get_locale_input(FAKE_LISTING_ID, conn)
    assert result is not None
    assert result["subway_access"] is True


# acceptance #3: subway_count == 0 → subway_access False
async def test_subway_access_false_when_subway_count_zero():
    metrics_no_subway = {**METRICS_ROW, "subway_count": 0}
    conn = make_conn(LISTING_ROW, metrics_no_subway, AREA_ROW)
    result = await get_locale_input(FAKE_LISTING_ID, conn)
    assert result is not None
    assert result["subway_access"] is False


# acceptance #4: medical == hospital_count + pharmacy_count
async def test_medical_equals_hospital_plus_pharmacy():
    conn = make_conn(LISTING_ROW, METRICS_ROW, AREA_ROW)
    result = await get_locale_input(FAKE_LISTING_ID, conn)
    assert result is not None
    assert result["medical"] == METRICS_ROW["hospital_count"] + METRICS_ROW["pharmacy_count"]


# acceptance #5: convenience == cafe_count + food_count + mart_count
async def test_convenience_equals_cafe_plus_food_plus_mart():
    conn = make_conn(LISTING_ROW, METRICS_ROW, AREA_ROW)
    result = await get_locale_input(FAKE_LISTING_ID, conn)
    assert result is not None
    assert result["convenience"] == (
        METRICS_ROW["cafe_count"] + METRICS_ROW["food_count"] + METRICS_ROW["mart_count"]
    )


# acceptance #6: green == park_count
async def test_green_equals_park_count():
    conn = make_conn(LISTING_ROW, METRICS_ROW, AREA_ROW)
    result = await get_locale_input(FAKE_LISTING_ID, conn)
    assert result is not None
    assert result["green"] == METRICS_ROW["park_count"]


# acceptance #7: listing 없으면 None
async def test_returns_none_when_listing_not_found():
    conn = make_conn(None)
    result = await get_locale_input(FAKE_LISTING_ID, conn)
    assert result is None


# acceptance #7: area_metrics row 없으면 None
async def test_returns_none_when_area_metrics_not_found():
    conn = make_conn(LISTING_ROW, None)
    result = await get_locale_input(FAKE_LISTING_ID, conn)
    assert result is None


# area_name이 emd_name으로 채워지는지 검증 (spec에서 명시)
async def test_area_name_equals_emd_name():
    conn = make_conn(LISTING_ROW, METRICS_ROW, AREA_ROW)
    result = await get_locale_input(FAKE_LISTING_ID, conn)
    assert result is not None
    assert result["area_name"] == "역삼동"
