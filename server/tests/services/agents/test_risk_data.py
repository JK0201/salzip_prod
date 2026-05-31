import inspect
import uuid
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.services.agents.risk_data import get_risk_input

FAKE_LISTING_ID = uuid.uuid4()
FAKE_AREA_ID = uuid.uuid4()


def _exec_result_first(first_value):
    """conn.execute() 반환값 mock — .mappings().first() → first_value."""
    result = MagicMock()
    mappings_obj = MagicMock()
    mappings_obj.first.return_value = first_value
    result.mappings.return_value = mappings_obj
    return result


def _exec_result_all(all_values):
    """conn.execute() 반환값 mock — .mappings().all() → all_values."""
    result = MagicMock()
    mappings_obj = MagicMock()
    mappings_obj.all.return_value = all_values
    result.mappings.return_value = mappings_obj
    return result


def make_conn(*first_values):
    """기존 호환 헬퍼: 순서대로 .first() 반환."""
    conn = AsyncMock()
    conn.execute.side_effect = [_exec_result_first(v) for v in first_values]
    return conn


def make_conn_full(listing_row, area_row, hug_row, region_row, trend_rows):
    """5개 execute 호출 모두 모킹: 1~4는 .first(), 5번째는 .all()."""
    conn = AsyncMock()
    conn.execute.side_effect = [
        _exec_result_first(listing_row),
        _exec_result_first(area_row),
        _exec_result_first(hug_row),
        _exec_result_first(region_row),
        _exec_result_all(trend_rows),
    ]
    return conn


LISTING_ROW = {
    "flood_risk": False,
    "flood_year": None,
    "build_year": 2015,
    "area_id": FAKE_AREA_ID,
}
AREA_ROW = {"avg_jeonse_ratio": 75.0}
HUG_ROW = {"accident_count": 2}
REGION_ROW = {"sgg_name": "강남구"}
TREND_ROWS = [
    {"metric": "unsold", "period": "2024-01", "value": 100},
    {"metric": "unsold", "period": "2024-03", "value": 120},
    {"metric": "apt_tx_monthly", "period": "2024-01", "value": 500},
    {"metric": "apt_tx_monthly", "period": "2024-03", "value": 400},
    {"metric": "apt_conv_ratio", "period": "2024-01", "value": 80},
    {"metric": "apt_conv_ratio", "period": "2024-03", "value": 75},
]


# === 회귀 테스트 (acceptance #6, #7) ===

# acceptance #6: async 함수이고 파라미터 (listing_id, conn) 순서
def test_get_risk_input_is_async_with_correct_params():
    assert inspect.iscoroutinefunction(get_risk_input)
    params = list(inspect.signature(get_risk_input).parameters.keys())
    assert params == ["listing_id", "conn"]


# acceptance #7: listing 행 없으면 None 반환
async def test_get_risk_input_returns_none_when_listing_not_found():
    conn = make_conn(None)
    result = await get_risk_input(FAKE_LISTING_ID, conn)
    assert result is None


# acceptance #2 + 회귀: listing 행 있으면 compute_risk 결과 키 유지
async def test_get_risk_input_returns_compute_risk_result():
    conn = make_conn_full(LISTING_ROW, AREA_ROW, HUG_ROW, REGION_ROW, TREND_ROWS)

    expected = {"risk_pct": 20, "grade": "안전", "total_safe": 80}
    with patch("app.services.agents.risk_data.compute_risk", return_value=expected):
        result = await get_risk_input(FAKE_LISTING_ID, conn)

    assert result["risk_pct"] == 20
    assert result["grade"] == "안전"
    assert result["total_safe"] == 80


# 회귀: flood_risk, flood_year, build_year → compute_risk 인자로 전달
async def test_get_risk_input_passes_listing_fields_to_compute_risk():
    listing_row = {
        "flood_risk": True,
        "flood_year": 2019,
        "build_year": 2005,
        "area_id": FAKE_AREA_ID,
    }
    conn = make_conn_full(listing_row, AREA_ROW, HUG_ROW, REGION_ROW, TREND_ROWS)

    with patch("app.services.agents.risk_data.compute_risk", return_value={}) as mock_cr:
        await get_risk_input(FAKE_LISTING_ID, conn)

    mock_cr.assert_called_once()
    kwargs = mock_cr.call_args.kwargs
    assert kwargs["flood_risk"] is True
    assert kwargs["flood_year"] == 2019
    assert kwargs["build_year"] == 2005


# 회귀: hug accident_count → compute_risk hug_accident_count 인자
async def test_get_risk_input_passes_hug_accident_count_to_compute_risk():
    hug_row = {"accident_count": 7}
    conn = make_conn_full(LISTING_ROW, AREA_ROW, hug_row, REGION_ROW, TREND_ROWS)

    with patch("app.services.agents.risk_data.compute_risk", return_value={}) as mock_cr:
        await get_risk_input(FAKE_LISTING_ID, conn)

    mock_cr.assert_called_once()
    kwargs = mock_cr.call_args.kwargs
    assert kwargs["hug_accident_count"] == 7


# === 신규 acceptance 테스트 ===

# acceptance #1: 반환 dict에 'market_trend' 키 존재
async def test_get_risk_input_result_has_market_trend_key():
    conn = make_conn_full(LISTING_ROW, AREA_ROW, HUG_ROW, REGION_ROW, TREND_ROWS)
    with patch("app.services.agents.risk_data.compute_risk", return_value={"risk_pct": 20}):
        result = await get_risk_input(FAKE_LISTING_ID, conn)
    assert result is not None
    assert "market_trend" in result


# acceptance #2 (독립): compute_risk 결과 키가 market_trend와 함께 병합되어 반환됨
async def test_get_risk_input_merges_compute_risk_and_market_trend():
    conn = make_conn_full(LISTING_ROW, AREA_ROW, HUG_ROW, REGION_ROW, TREND_ROWS)
    compute_risk_result = {"risk_pct": 35, "grade": "주의", "total_safe": 65, "axes": {}}
    with patch("app.services.agents.risk_data.compute_risk", return_value=compute_risk_result):
        result = await get_risk_input(FAKE_LISTING_ID, conn)
    assert result["risk_pct"] == 35
    assert result["grade"] == "주의"
    assert result["total_safe"] == 65
    assert "market_trend" in result


# acceptance #3: area_trends 조회 stmt에 region_label 조건 있고 region_id 컬럼 없음
async def test_get_risk_input_area_trends_uses_region_label_not_region_id():
    conn = make_conn_full(LISTING_ROW, AREA_ROW, HUG_ROW, REGION_ROW, TREND_ROWS)
    with patch("app.services.agents.risk_data.compute_risk", return_value={}):
        await get_risk_input(FAKE_LISTING_ID, conn)

    assert conn.execute.call_count >= 5, "area_trends 조회 포함 5번 이상 execute 필요"
    area_trends_stmt = conn.execute.call_args_list[4][0][0]
    stmt_str = str(area_trends_stmt)
    assert "region_label" in stmt_str, f"region_label이 쿼리에 없음: {stmt_str}"
    assert "region_id" not in stmt_str, f"region_id가 쿼리에 포함됨(사용 금지): {stmt_str}"


# acceptance #4: area_trends metric 필터 3종 제한
async def test_get_risk_input_area_trends_filters_three_metrics():
    conn = make_conn_full(LISTING_ROW, AREA_ROW, HUG_ROW, REGION_ROW, TREND_ROWS)
    with patch("app.services.agents.risk_data.compute_risk", return_value={}):
        await get_risk_input(FAKE_LISTING_ID, conn)

    area_trends_stmt = conn.execute.call_args_list[4][0][0]
    stmt_str = str(area_trends_stmt)
    assert "unsold" in stmt_str, f"unsold metric 필터 없음: {stmt_str}"
    assert "apt_tx_monthly" in stmt_str, f"apt_tx_monthly metric 필터 없음: {stmt_str}"
    assert "apt_conv_ratio" in stmt_str, f"apt_conv_ratio metric 필터 없음: {stmt_str}"


# acceptance #5a: sgg_name 없을 때(region 행 None) 예외 없이 market_trend direction 모두 '없음'
async def test_get_risk_input_no_region_returns_no_exception_and_direction_없음():
    conn = make_conn_full(LISTING_ROW, AREA_ROW, HUG_ROW, None, [])
    with patch("app.services.agents.risk_data.compute_risk", return_value={"risk_pct": 0}):
        result = await get_risk_input(FAKE_LISTING_ID, conn)
    assert result is not None, "sgg_name None일 때 None 반환하면 안 됨"
    trend = result["market_trend"]
    for metric in ("unsold", "apt_tx_monthly", "apt_conv_ratio"):
        if metric in trend:
            assert trend[metric]["direction"] == "없음", (
                f"{metric} direction이 '없음'이 아님: {trend[metric]['direction']}"
            )


# acceptance #5b: area_trends 행 0개일 때 예외 없이 market_trend direction 모두 '없음'
async def test_get_risk_input_empty_area_trends_returns_direction_없음():
    conn = make_conn_full(LISTING_ROW, AREA_ROW, HUG_ROW, REGION_ROW, [])
    with patch("app.services.agents.risk_data.compute_risk", return_value={"risk_pct": 0}):
        result = await get_risk_input(FAKE_LISTING_ID, conn)
    assert result is not None
    trend = result["market_trend"]
    for metric in ("unsold", "apt_tx_monthly", "apt_conv_ratio"):
        if metric in trend:
            assert trend[metric]["direction"] == "없음", (
                f"{metric} direction이 '없음'이 아님: {trend[metric]['direction']}"
            )
