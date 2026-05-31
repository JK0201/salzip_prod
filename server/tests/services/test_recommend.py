import ast
import inspect
import pathlib
import uuid
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.core.exceptions import AddressNotFound

_RECOMMEND_SRC = pathlib.Path(__file__).parent.parent.parent / "app" / "services" / "recommend.py"

REQUIRED_KEYS = {
    "rank",
    "name",
    "meta",
    "score",
    "tier",
    "lat",
    "lng",
    "commuteMinutes",
    "scores",
    "listing_count",
    "flood_risk_count",
    "reason",
}


def make_req(**kwargs):
    defaults = dict(
        workplace_address="서울 강남구 테헤란로 1",
        max_commute_minutes=60,
        deposit_max_wan=5000,
        monthly_rent_max_wan=80,
        lifestyle_tags=[],
    )
    defaults.update(kwargs)
    return SimpleNamespace(**defaults)


def _row(**fields):
    return SimpleNamespace(**fields)


def _db_result(rows):
    result = MagicMock()
    result.fetchall.return_value = rows
    mappings = MagicMock()
    mappings.all.return_value = rows
    result.mappings.return_value = mappings
    return result


def _make_conn(area_rows, metrics_rows=None, listing_rows=None):
    conn = AsyncMock()
    conn.execute.side_effect = [
        _db_result(area_rows),
        _db_result(metrics_rows or []),
        _db_result(listing_rows or []),
    ]
    return conn


def _areas(n=1, sgg_name="강남구"):
    return [
        _row(
            area_id=uuid.uuid4(),
            emd_name=f"동{i}",
            lat=37.5 + i * 0.01,
            lng=127.0 + i * 0.01,
            sgg_name=sgg_name,
        )
        for i in range(n)
    ]


def _metrics(area_rows):
    return [
        _row(
            area_id=r.area_id,
            cafe=5,
            food=10,
            culture=3,
            park=4,
            subway=2,
            hospital=2,
            pharmacy=2,
            mart=2,
        )
        for r in area_rows
    ]


def _listings(area_rows):
    return [
        _row(
            area_id=r.area_id,
            jeonse_ratio_avg=50.0,
            flood_ratio=0.0,
            avg_build_year=2020,
            listing_count=5,
            flood_risk_count=0,
        )
        for r in area_rows
    ]


TRANSIT_OK = {"min": 20, "payment": 1000, "first_lane": None}


# acceptance #1: recommend 함수 존재
async def test_recommend_is_callable():
    from app.services.recommend import recommend

    assert callable(recommend)


# acceptance #2: geocode_address → None → AddressNotFound
async def test_recommend_raises_address_not_found_when_geocode_returns_none():
    from app.services.recommend import recommend

    conn = AsyncMock()
    with patch(
        "app.services.kakao.geocode_address",
        new=AsyncMock(return_value=None),
    ):
        with pytest.raises(AddressNotFound):
            await recommend(make_req(), conn)


# acceptance #3: 모든 transit_time → None → 빈 리스트
async def test_recommend_returns_empty_list_when_all_transit_none():
    from app.services.recommend import recommend

    areas = _areas(2)
    conn = _make_conn(areas, _metrics(areas), _listings(areas))
    with patch(
        "app.services.kakao.geocode_address",
        new=AsyncMock(return_value=(37.5, 127.0)),
    ), patch(
        "app.services.odsay.transit_time",
        new=AsyncMock(return_value=None),
    ):
        result = await recommend(make_req(), conn)
    assert result == []


# acceptance #4: commute_min > max_commute_minutes 후보 제외
async def test_recommend_excludes_candidates_over_max_commute():
    from app.services.recommend import recommend

    areas = _areas(1)
    conn = _make_conn(areas, _metrics(areas), _listings(areas))
    over_limit = {"min": 90, "payment": 1000, "first_lane": None}
    with patch(
        "app.services.kakao.geocode_address",
        new=AsyncMock(return_value=(37.5, 127.0)),
    ), patch(
        "app.services.odsay.transit_time",
        new=AsyncMock(return_value=over_limit),
    ):
        result = await recommend(make_req(max_commute_minutes=30), conn)
    assert result == []


# acceptance #5: 결과 길이 = min(통과 후보 수, 5) — 6개 후보 → 5개
async def test_recommend_caps_result_at_five():
    from app.services.recommend import recommend

    areas = _areas(6)
    conn = _make_conn(areas, _metrics(areas), _listings(areas))
    with patch(
        "app.services.kakao.geocode_address",
        new=AsyncMock(return_value=(37.5, 127.0)),
    ), patch(
        "app.services.odsay.transit_time",
        new=AsyncMock(return_value=TRANSIT_OK),
    ):
        result = await recommend(make_req(), conn)
    assert len(result) == 5


# acceptance #5: 통과 후보 < 5이면 전부 반환
async def test_recommend_returns_all_when_fewer_than_five_pass():
    from app.services.recommend import recommend

    areas = _areas(3)
    conn = _make_conn(areas, _metrics(areas), _listings(areas))
    with patch(
        "app.services.kakao.geocode_address",
        new=AsyncMock(return_value=(37.5, 127.0)),
    ), patch(
        "app.services.odsay.transit_time",
        new=AsyncMock(return_value=TRANSIT_OK),
    ):
        result = await recommend(make_req(), conn)
    assert len(result) == 3


# acceptance #6: 첫 번째 항목 rank=1, tier=1
async def test_recommend_first_item_rank1_tier1():
    from app.services.recommend import recommend

    areas = _areas(2)
    conn = _make_conn(areas, _metrics(areas), _listings(areas))
    with patch(
        "app.services.kakao.geocode_address",
        new=AsyncMock(return_value=(37.5, 127.0)),
    ), patch(
        "app.services.odsay.transit_time",
        new=AsyncMock(return_value=TRANSIT_OK),
    ):
        result = await recommend(make_req(), conn)
    assert result[0]["rank"] == 1
    assert result[0]["tier"] == 1


# acceptance #7: 반환 dict 12 키
async def test_recommend_result_dict_has_required_keys():
    from app.services.recommend import recommend

    areas = _areas(1)
    conn = _make_conn(areas, _metrics(areas), _listings(areas))
    with patch(
        "app.services.kakao.geocode_address",
        new=AsyncMock(return_value=(37.5, 127.0)),
    ), patch(
        "app.services.odsay.transit_time",
        new=AsyncMock(return_value=TRANSIT_OK),
    ):
        result = await recommend(make_req(), conn)
    assert set(result[0].keys()) == REQUIRED_KEYS


# acceptance #8: meta에 sgg_name과 '통근 {n}분' 포함
async def test_recommend_meta_contains_sgg_name_and_commute_label():
    from app.services.recommend import recommend

    areas = [_row(area_id=uuid.uuid4(), emd_name="역삼동", lat=37.5, lng=127.0, sgg_name="강남구")]
    conn = _make_conn(areas, _metrics(areas), _listings(areas))
    transit = {"min": 25, "payment": 1000, "first_lane": None}
    with patch(
        "app.services.kakao.geocode_address",
        new=AsyncMock(return_value=(37.5, 127.0)),
    ), patch(
        "app.services.odsay.transit_time",
        new=AsyncMock(return_value=transit),
    ):
        result = await recommend(make_req(), conn)
    meta = result[0]["meta"]
    assert "강남구" in meta
    assert "통근 25분" in meta


# acceptance #9: 구 심볼 삭제 확인
def test_mock_symbols_removed_from_module():
    import importlib

    import app.services.recommend as mod

    importlib.reload(mod)
    assert not hasattr(mod, "build_mock_recommendation")
    assert not hasattr(mod, "MOCK_RECOMMEND_RESPONSE")


# ── T-065: recommend tag_mapping 주입 ──────────────────────────────────────


def _tag_rows(names=("카페형", "공원형")):
    return [
        _row(
            name=n,
            categories=["cafe", "food"] if n == "카페형" else ["park"],
            is_inverse=False,
        )
        for n in names
    ]


def _iterable_result(rows):
    """lifestyle_tags SELECT 결과: `for row in result` 패턴 지원."""
    result = MagicMock()
    result.__iter__ = lambda self: iter(rows)
    return result


def _make_conn_with_tags(area_rows, tag_rows, metrics_rows=None, listing_rows=None):
    """areas → metrics → listings → lifestyle_tags 순서로 4회 execute."""
    conn = AsyncMock()
    conn.execute.side_effect = [
        _db_result(area_rows),
        _db_result(metrics_rows or []),
        _db_result(listing_rows or []),
        _iterable_result(tag_rows),
    ]
    return conn


# T-065 acceptance #1: lifestyle_tags_table import 존재
def test_lifestyle_tags_table_is_imported():
    src = _RECOMMEND_SRC.read_text()
    tree = ast.parse(src)
    imported = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom):
            for alias in node.names:
                imported.add(alias.asname or alias.name)
    assert "lifestyle_tags_table" in imported, (
        "recommend.py에 lifestyle_tags_table import 없음"
    )


# T-065 acceptance #2: score_life 호출 인자 3개
def test_score_life_call_has_three_positional_args():
    src = _RECOMMEND_SRC.read_text()
    tree = ast.parse(src)
    for node in ast.walk(tree):
        if isinstance(node, ast.Call):
            func = node.func
            is_score_life = (
                (isinstance(func, ast.Attribute) and func.attr == "score_life")
                or (isinstance(func, ast.Name) and func.id == "score_life")
            )
            if is_score_life:
                assert len(node.args) == 3, (
                    f"score_life 호출 인자 수 {len(node.args)} != 3"
                )
                return
    pytest.fail("recommend.py에서 score_life 호출을 찾을 수 없음")


# T-065 acceptance #3: lifestyle_tags SELECT 1회만 실행 (후보 3건이어도)
async def test_lifestyle_tags_select_executed_once_for_multiple_candidates():
    from app.services.recommend import recommend

    areas = _areas(3)
    conn = _make_conn_with_tags(areas, _tag_rows(), _metrics(areas), _listings(areas))
    with patch(
        "app.services.kakao.geocode_address",
        new=AsyncMock(return_value=(37.5, 127.0)),
    ), patch(
        "app.services.odsay.transit_time",
        new=AsyncMock(return_value=TRANSIT_OK),
    ):
        await recommend(make_req(), conn)

    # areas(1) + metrics(1) + listings(1) + lifestyle_tags(1) = 4
    # 루프 내 재조회 시 4 + 3 = 7이 됨
    assert conn.execute.call_count == 4, (
        f"conn.execute 호출 횟수 {conn.execute.call_count} != 4 "
        "(lifestyle_tags가 루프 내에서 재조회되고 있음)"
    )


# T-065 acceptance #4: score_life에 전달되는 tag_mapping 키 = mock row name 집합
async def test_score_life_receives_tag_mapping_matching_mock_rows():
    from app.services.recommend import recommend

    tag_names = ["카페형", "공원형"]
    areas = _areas(3)
    tags = _tag_rows(tag_names)
    conn = _make_conn_with_tags(areas, tags, _metrics(areas), _listings(areas))

    captured: list[dict] = []

    def spy_score_life(metrics, lifestyle_tags, tag_mapping):
        captured.append(dict(tag_mapping))
        return 50.0

    with patch(
        "app.services.kakao.geocode_address",
        new=AsyncMock(return_value=(37.5, 127.0)),
    ), patch(
        "app.services.odsay.transit_time",
        new=AsyncMock(return_value=TRANSIT_OK),
    ), patch(
        "app.services.scoring.score_life",
        side_effect=spy_score_life,
    ):
        await recommend(make_req(lifestyle_tags=tag_names), conn)

    assert captured, "score_life가 한 번도 호출되지 않음"
    assert set(captured[0].keys()) == set(tag_names), (
        f"tag_mapping 키 {set(captured[0].keys())} != {set(tag_names)}"
    )


# T-065 acceptance #5: recommend 함수 시그니처 회귀 (req, conn)
def test_recommend_signature_unchanged():
    from app.services.recommend import recommend

    params = list(inspect.signature(recommend).parameters.keys())
    assert params == ["req", "conn", "session_id"], (
        f"recommend 시그니처 {params} 변경됨"
    )


# T-065 acceptance #6: recommend 응답 스키마 회귀
async def test_recommend_response_schema_unchanged_after_tag_mapping():
    from app.services.recommend import recommend

    areas = _areas(1)
    conn = _make_conn_with_tags(areas, _tag_rows(), _metrics(areas), _listings(areas))
    with patch(
        "app.services.kakao.geocode_address",
        new=AsyncMock(return_value=(37.5, 127.0)),
    ), patch(
        "app.services.odsay.transit_time",
        new=AsyncMock(return_value=TRANSIT_OK),
    ):
        result = await recommend(make_req(), conn)

    assert isinstance(result, list)
    assert len(result) == 1
    assert set(result[0].keys()) == REQUIRED_KEYS


# ── T-077: recommend listings/metrics/safety 확장 ─────────────────────────

import uuid as _uuid_mod


def _t077_metrics(area_rows, avg_jeonse_ratio=50.0, flood_ratio=0.0, avg_build_year=2020):
    return [
        _row(
            area_id=r.area_id,
            cafe_count=5,
            food_count=10,
            culture_count=3,
            park_count=4,
            mart_count=2,
            subway_count=2,
            hospital_count=2,
            pharmacy_count=2,
            avg_jeonse_ratio=avg_jeonse_ratio,
            flood_ratio=flood_ratio,
            avg_build_year=avg_build_year,
            listing_count=5,
            flood_risk_count=0,
        )
        for r in area_rows
    ]


def _t077_listing_items(n=2):
    return [
        _row(
            id=_uuid_mod.uuid4(),
            kind="원룸",
            estimated_kind="오피스텔",
            building_name="테스트빌딩",
            deposit=1000,
            monthly_rent=50,
            area_m2=33.0,
            floor=3,
            lat=37.5,
            lng=127.0,
            flood_risk=False,
            build_year=2015,
            jibun="서울 강남구 역삼동 1-1",
        )
        for _ in range(n)
    ]


def _make_conn_t077(area_rows, metrics_rows, listing_rows_per_area=None):
    """areas → area_metrics(batch ANY) → listings×top5 순서로 execute mock."""
    conn = AsyncMock()
    side_effects: list = [
        _db_result(area_rows),
        _db_result(metrics_rows),
    ]
    if listing_rows_per_area is None:
        listing_rows_per_area = [[] for _ in area_rows]
    for rows in listing_rows_per_area:
        side_effects.append(_db_result(rows))
    conn.execute.side_effect = side_effects
    return conn


# acceptance #1: area_id, listings, metrics, safety 4 키 모두 존재
async def test_t077_area_dict_has_four_new_keys():
    from app.services.recommend import recommend

    areas = _areas(1)
    conn = _make_conn_t077(areas, _t077_metrics(areas), [_t077_listing_items(2)])
    with patch(
        "app.services.kakao.geocode_address",
        new=AsyncMock(return_value=(37.5, 127.0)),
    ), patch(
        "app.services.odsay.transit_time",
        new=AsyncMock(return_value=TRANSIT_OK),
    ):
        result = await recommend(make_req(), conn)

    assert len(result) == 1
    area = result[0]
    for key in ("area_id", "listings", "metrics", "safety"):
        assert key in area, f"area dict에 '{key}' 키 없음"


# acceptance #2: listings는 list 타입이고 길이 5 이하
async def test_t077_listings_is_list_max_five():
    from app.services.recommend import recommend

    areas = _areas(1)
    conn = _make_conn_t077(areas, _t077_metrics(areas), [_t077_listing_items(3)])
    with patch(
        "app.services.kakao.geocode_address",
        new=AsyncMock(return_value=(37.5, 127.0)),
    ), patch(
        "app.services.odsay.transit_time",
        new=AsyncMock(return_value=TRANSIT_OK),
    ):
        result = await recommend(make_req(), conn)

    listings = result[0]["listings"]
    assert isinstance(listings, list), f"listings 타입 {type(listings)} != list"
    assert len(listings) <= 5, f"listings 길이 {len(listings)} > 5"


# acceptance #3: metrics는 dict이며 8 카운트 키 모두 존재
async def test_t077_metrics_has_eight_count_keys():
    from app.services.recommend import recommend

    areas = _areas(1)
    conn = _make_conn_t077(areas, _t077_metrics(areas), [[]])
    with patch(
        "app.services.kakao.geocode_address",
        new=AsyncMock(return_value=(37.5, 127.0)),
    ), patch(
        "app.services.odsay.transit_time",
        new=AsyncMock(return_value=TRANSIT_OK),
    ):
        result = await recommend(make_req(), conn)

    m = result[0]["metrics"]
    assert isinstance(m, dict), f"metrics 타입 {type(m)} != dict"
    required = {
        "cafe_count", "food_count", "culture_count", "park_count",
        "mart_count", "subway_count", "hospital_count", "pharmacy_count",
    }
    missing = required - set(m.keys())
    assert not missing, f"metrics에 키 누락: {missing}"


# acceptance #4: safety는 dict이며 3 키만 존재
async def test_t077_safety_has_exactly_three_keys():
    from app.services.recommend import recommend

    areas = _areas(1)
    conn = _make_conn_t077(areas, _t077_metrics(areas), [[]])
    with patch(
        "app.services.kakao.geocode_address",
        new=AsyncMock(return_value=(37.5, 127.0)),
    ), patch(
        "app.services.odsay.transit_time",
        new=AsyncMock(return_value=TRANSIT_OK),
    ):
        result = await recommend(make_req(), conn)

    safety = result[0]["safety"]
    assert isinstance(safety, dict), f"safety 타입 {type(safety)} != dict"
    assert set(safety.keys()) == {"avg_jeonse_ratio", "flood_ratio", "avg_build_year"}, (
        f"safety 키 집합 {set(safety.keys())} != 기대 3 키"
    )


# acceptance #5: listings 1건 이상 시 7 필드 포함
async def test_t077_listing_item_has_required_fields():
    from app.services.recommend import recommend

    areas = _areas(1)
    conn = _make_conn_t077(areas, _t077_metrics(areas), [_t077_listing_items(2)])
    with patch(
        "app.services.kakao.geocode_address",
        new=AsyncMock(return_value=(37.5, 127.0)),
    ), patch(
        "app.services.odsay.transit_time",
        new=AsyncMock(return_value=TRANSIT_OK),
    ):
        result = await recommend(make_req(), conn)

    listings = result[0]["listings"]
    assert len(listings) >= 1, "listings 비어있음 — 필드 검증 불가"
    required_fields = {"id", "kind", "deposit", "monthly_rent", "area_m2", "lat", "lng"}
    for item in listings:
        assert isinstance(item, dict), f"listing item이 dict 아님: {type(item)}"
        missing = required_fields - set(item.keys())
        assert not missing, f"listing item에 필드 누락: {missing}"


# acceptance #6: avg_jeonse_ratio NULL → score_safe 1번째 인자 60(중립값)
async def test_t077_score_safe_coalesces_null_jeonse_ratio_to_60():
    from app.services import scoring
    from app.services.recommend import recommend

    areas = _areas(1)
    conn = _make_conn_t077(areas, _t077_metrics(areas, avg_jeonse_ratio=None), [[]])
    captured: list[tuple] = []
    _orig = scoring.score_safe

    def spy(jeonse_ratio_avg, flood_ratio, avg_build_year):
        captured.append((jeonse_ratio_avg, flood_ratio, avg_build_year))
        safe = 60 if jeonse_ratio_avg is None else jeonse_ratio_avg
        return _orig(safe, flood_ratio or 0, avg_build_year or 2010)

    with patch(
        "app.services.kakao.geocode_address",
        new=AsyncMock(return_value=(37.5, 127.0)),
    ), patch(
        "app.services.odsay.transit_time",
        new=AsyncMock(return_value=TRANSIT_OK),
    ), patch("app.services.scoring.score_safe", side_effect=spy):
        await recommend(make_req(), conn)

    assert captured, "score_safe가 한 번도 호출되지 않음"
    assert captured[0][0] == 60, (
        f"avg_jeonse_ratio NULL 시 1번째 인자 60 기대, 실제: {captured[0][0]}"
    )


# acceptance #7: 기존 REQUIRED_KEYS 보존
async def test_t077_existing_required_keys_preserved():
    from app.services.recommend import recommend

    areas = _areas(1)
    conn = _make_conn_t077(areas, _t077_metrics(areas), [_t077_listing_items(1)])
    with patch(
        "app.services.kakao.geocode_address",
        new=AsyncMock(return_value=(37.5, 127.0)),
    ), patch(
        "app.services.odsay.transit_time",
        new=AsyncMock(return_value=TRANSIT_OK),
    ):
        result = await recommend(make_req(), conn)

    assert result, "recommend 결과 비어있음"
    actual_keys = set(result[0].keys())
    missing = REQUIRED_KEYS - actual_keys
    assert not missing, f"기존 키 소실됨: {missing}"


# ── T-079: recommend INSERT profiles+match ─────────────────────────────────

from sqlalchemy.exc import SQLAlchemyError as _SAError

_T079_PROFILE_ID = uuid.uuid4()
_T079_MATCH_ID = uuid.uuid4()
_T079_SESSION_ID = uuid.uuid4()
_T079_USER_ID = uuid.uuid4()

_ALL_11_FIELDS = {
    "workplace_name",
    "workplace_address",
    "job_type",
    "max_commute_minutes",
    "lifestyle_tags",
    "deposit_max_wan",
    "monthly_rent_max_wan",
    "age",
    "annual_income_wan",
    "household_type",
    "home_ownerless",
}


class _FullReq:
    """RecommendRequest stub: 11 필드 + model_dump()."""

    workplace_name = "테스트직장"
    workplace_address = "서울 강남구 테헤란로 1"
    job_type = "사무직"
    max_commute_minutes = 60
    lifestyle_tags: list = []
    deposit_max_wan = 5000
    monthly_rent_max_wan = 80
    age = 30
    annual_income_wan = 4000
    household_type = "1인"
    home_ownerless = True

    def model_dump(self) -> dict:
        return {f: getattr(self, f) for f in _ALL_11_FIELDS}


def _returning_result_t079(val):
    r = MagicMock()
    r.scalar.return_value = val
    r.scalar_one.return_value = val
    r.fetchone.return_value = SimpleNamespace(id=val)
    return r


def _make_conn_t079(
    area_rows,
    metrics_rows,
    listing_rows_per_area=None,
    *,
    profile_id=_T079_PROFILE_ID,
    match_id=_T079_MATCH_ID,
    user_id=_T079_USER_ID,
):
    """areas → metrics → listings... → sessions SELECT → profiles INSERT → match_results INSERT."""
    conn = AsyncMock()
    side_effects: list = [_db_result(area_rows), _db_result(metrics_rows)]
    if listing_rows_per_area is None:
        listing_rows_per_area = [[] for _ in area_rows]
    for rows in listing_rows_per_area:
        side_effects.append(_db_result(rows))
    side_effects.append(_returning_result_t079(user_id))    # sessions SELECT
    side_effects.append(_returning_result_t079(profile_id)) # profiles INSERT RETURNING
    side_effects.append(_returning_result_t079(match_id))   # match_results INSERT RETURNING
    conn.execute.side_effect = side_effects
    return conn


def _sql_str(stmt) -> str:
    try:
        return str(stmt).upper()
    except Exception:
        return ""


def _find_insert_params(call_args_list, table_name: str):
    """call_args_list에서 'INSERT INTO {table_name}' 포함 호출의 bindparams 반환. 없으면 None."""
    marker = f"INSERT INTO {table_name.upper()}"
    for call in call_args_list:
        if not call.args:
            continue
        if marker not in _sql_str(call.args[0]):
            continue
        if len(call.args) > 1:
            return call.args[1]
        return call.kwargs.get("parameters") or {}
    return None


# T-079 acceptance #1: session_id 인자 존재
def test_t079_signature_has_session_id():
    from app.services.recommend import recommend

    params = list(inspect.signature(recommend).parameters.keys())
    assert "session_id" in params, f"recommend 파라미터 {params}에 session_id 없음"


# T-079 acceptance #2: profiles INSERT 1회
async def test_t079_profiles_insert_executed_once():
    from app.services.recommend import recommend

    areas = _areas(1)
    conn = _make_conn_t079(areas, _t077_metrics(areas), [_t077_listing_items(1)])
    with patch("app.services.kakao.geocode_address", new=AsyncMock(return_value=(37.5, 127.0))), \
         patch("app.services.odsay.transit_time", new=AsyncMock(return_value=TRANSIT_OK)):
        await recommend(_FullReq(), conn, session_id=_T079_SESSION_ID)

    profiles_calls = [
        c for c in conn.execute.call_args_list
        if c.args and "INSERT INTO PROFILES" in _sql_str(c.args[0])
    ]
    assert len(profiles_calls) == 1, f"profiles INSERT 횟수 {len(profiles_calls)} != 1"


# T-079 acceptance #3: match_results INSERT 1회
async def test_t079_match_results_insert_executed_once():
    from app.services.recommend import recommend

    areas = _areas(1)
    conn = _make_conn_t079(areas, _t077_metrics(areas), [_t077_listing_items(1)])
    with patch("app.services.kakao.geocode_address", new=AsyncMock(return_value=(37.5, 127.0))), \
         patch("app.services.odsay.transit_time", new=AsyncMock(return_value=TRANSIT_OK)):
        await recommend(_FullReq(), conn, session_id=_T079_SESSION_ID)

    match_calls = [
        c for c in conn.execute.call_args_list
        if c.args and "INSERT INTO MATCH_RESULTS" in _sql_str(c.args[0])
    ]
    assert len(match_calls) == 1, f"match_results INSERT 횟수 {len(match_calls)} != 1"


# T-079 acceptance #4: profiles INSERT bindparams에 session_id 키
async def test_t079_profiles_insert_has_session_id_in_bindparams():
    from app.services.recommend import recommend

    areas = _areas(1)
    conn = _make_conn_t079(areas, _t077_metrics(areas), [_t077_listing_items(1)])
    with patch("app.services.kakao.geocode_address", new=AsyncMock(return_value=(37.5, 127.0))), \
         patch("app.services.odsay.transit_time", new=AsyncMock(return_value=TRANSIT_OK)):
        await recommend(_FullReq(), conn, session_id=_T079_SESSION_ID)

    params = _find_insert_params(conn.execute.call_args_list, "profiles")
    assert params is not None, "profiles INSERT 호출 없음"
    assert "session_id" in params, f"profiles bindparams에 session_id 없음: {list(params.keys())}"


# T-079 acceptance #5: profiles INSERT payload에 11 필드 모두
async def test_t079_profiles_insert_payload_has_all_eleven_fields():
    from app.services.recommend import recommend

    areas = _areas(1)
    conn = _make_conn_t079(areas, _t077_metrics(areas), [_t077_listing_items(1)])
    with patch("app.services.kakao.geocode_address", new=AsyncMock(return_value=(37.5, 127.0))), \
         patch("app.services.odsay.transit_time", new=AsyncMock(return_value=TRANSIT_OK)):
        await recommend(_FullReq(), conn, session_id=_T079_SESSION_ID)

    params = _find_insert_params(conn.execute.call_args_list, "profiles")
    assert params is not None, "profiles INSERT 호출 없음"
    payload = params.get("payload", {})
    missing = _ALL_11_FIELDS - set(payload.keys())
    assert not missing, f"profiles payload 누락 필드: {missing}"


# T-079 acceptance #6: match_results profile_id == profiles RETURNING id
async def test_t079_match_results_profile_id_equals_profiles_returning():
    from app.services.recommend import recommend

    areas = _areas(1)
    profile_id = uuid.uuid4()
    conn = _make_conn_t079(areas, _t077_metrics(areas), [_t077_listing_items(1)], profile_id=profile_id)
    with patch("app.services.kakao.geocode_address", new=AsyncMock(return_value=(37.5, 127.0))), \
         patch("app.services.odsay.transit_time", new=AsyncMock(return_value=TRANSIT_OK)):
        await recommend(_FullReq(), conn, session_id=_T079_SESSION_ID)

    params = _find_insert_params(conn.execute.call_args_list, "match_results")
    assert params is not None, "match_results INSERT 호출 없음"
    assert params.get("profile_id") == profile_id, (
        f"match_results profile_id {params.get('profile_id')} != {profile_id}"
    )


# T-079 acceptance #7: match_results payload에 areas 키 + list
async def test_t079_match_results_payload_has_areas_list():
    from app.services.recommend import recommend

    areas = _areas(1)
    conn = _make_conn_t079(areas, _t077_metrics(areas), [_t077_listing_items(1)])
    with patch("app.services.kakao.geocode_address", new=AsyncMock(return_value=(37.5, 127.0))), \
         patch("app.services.odsay.transit_time", new=AsyncMock(return_value=TRANSIT_OK)):
        await recommend(_FullReq(), conn, session_id=_T079_SESSION_ID)

    params = _find_insert_params(conn.execute.call_args_list, "match_results")
    assert params is not None, "match_results INSERT 호출 없음"
    payload = params.get("payload", {})
    assert "areas" in payload, f"match_results payload에 areas 키 없음: {list(payload.keys())}"
    assert isinstance(payload["areas"], list), f"payload['areas'] 타입 {type(payload['areas'])} != list"


# T-079 acceptance #8: 반환값 dict이며 match_id가 uuid.UUID
async def test_t079_return_dict_with_uuid_match_id():
    from app.services.recommend import recommend

    areas = _areas(1)
    match_id = uuid.uuid4()
    conn = _make_conn_t079(areas, _t077_metrics(areas), [_t077_listing_items(1)], match_id=match_id)
    with patch("app.services.kakao.geocode_address", new=AsyncMock(return_value=(37.5, 127.0))), \
         patch("app.services.odsay.transit_time", new=AsyncMock(return_value=TRANSIT_OK)):
        result = await recommend(_FullReq(), conn, session_id=_T079_SESSION_ID)

    assert isinstance(result, dict), f"반환 타입 {type(result)} != dict"
    assert "match_id" in result, "반환 dict에 match_id 키 없음"
    assert isinstance(result["match_id"], uuid.UUID), (
        f"match_id 타입 {type(result.get('match_id'))} != uuid.UUID"
    )
    assert result["match_id"] == match_id, f"match_id 값 불일치: {result['match_id']} != {match_id}"


# T-079 acceptance #9: SQLAlchemyError → no propagate, match_id=None, areas는 list
async def test_t079_sqlalchemy_error_no_propagate_match_id_none():
    from app.services.recommend import recommend

    areas = _areas(1)
    metrics = _t077_metrics(areas)
    listings = _t077_listing_items(1)

    normal_results = [
        _db_result(areas),
        _db_result(metrics),
        _db_result(listings),
    ]
    call_counter = [0]

    async def _side_effect_raise_on_insert(stmt, *args, **kwargs):
        sql = _sql_str(stmt)
        if "INSERT INTO PROFILES" in sql or "INSERT INTO MATCH_RESULTS" in sql:
            raise _SAError("mock db insert error")
        if call_counter[0] < len(normal_results):
            result = normal_results[call_counter[0]]
            call_counter[0] += 1
            return result
        return _returning_result_t079(uuid.uuid4())  # sessions SELECT 등

    conn = AsyncMock()
    conn.execute.side_effect = _side_effect_raise_on_insert

    with patch("app.services.kakao.geocode_address", new=AsyncMock(return_value=(37.5, 127.0))), \
         patch("app.services.odsay.transit_time", new=AsyncMock(return_value=TRANSIT_OK)):
        result = await recommend(_FullReq(), conn, session_id=_T079_SESSION_ID)

    assert isinstance(result, dict), f"예외가 전파됨 또는 반환 타입 오류: {type(result)}"
    assert result.get("match_id") is None, f"오류 시 match_id가 None이 아님: {result.get('match_id')}"
    assert "areas" in result, "반환값에 areas 키 없음"
    assert isinstance(result["areas"], list), f"areas 타입 {type(result.get('areas'))} != list"


# ── T-085: recommend score_work 주입 ──────────────────────────────────────


def _get_score_work_call_node(src: str):
    """recommend.py AST에서 score_work Call 노드 반환. 없으면 None."""
    tree = ast.parse(src)
    for node in ast.walk(tree):
        if isinstance(node, ast.Call):
            func = node.func
            is_score_work = (
                (isinstance(func, ast.Attribute) and func.attr == "score_work")
                or (isinstance(func, ast.Name) and func.id == "score_work")
            )
            if is_score_work:
                return node
    return None


def _ast_call_str(node) -> str:
    """Call 노드를 소스 문자열로 재구성 (간이)."""
    return ast.unparse(node)


# T-085 acceptance #3: 1, 2번째 인자 유지
def test_t085_score_work_first_two_args_unchanged():
    src = _RECOMMEND_SRC.read_text()
    call = _get_score_work_call_node(src)
    assert call is not None, "recommend.py에서 score_work 호출을 찾을 수 없음"
    assert len(call.args) >= 2, f"score_work 인자 수 {len(call.args)} < 2"

    first = ast.unparse(call.args[0])
    second = ast.unparse(call.args[1])
    assert first == "transit['min']", (
        f"1번째 인자 {first!r} != \"transit['min']\""
    )
    assert second == "req.max_commute_minutes", (
        f"2번째 인자 {second!r} != 'req.max_commute_minutes'"
    )


# T-085 acceptance #1: 3번째 인자 transit.get("transfers", 0)
def test_t085_score_work_passes_transfers_arg():
    src = _RECOMMEND_SRC.read_text()
    call = _get_score_work_call_node(src)
    assert call is not None, "recommend.py에서 score_work 호출을 찾을 수 없음"
    assert len(call.args) >= 3, (
        f"score_work 인자 수 {len(call.args)} < 3 — transfers 인자 없음"
    )
    third = ast.unparse(call.args[2])
    assert third == "transit.get('transfers', 0)", (
        f"3번째 인자(transfers) {third!r} != \"transit.get('transfers', 0)\""
    )


# T-085 acceptance #2: 4번째 인자 transit.get("total_walk_m", 0)
def test_t085_score_work_passes_walk_m_arg():
    src = _RECOMMEND_SRC.read_text()
    call = _get_score_work_call_node(src)
    assert call is not None, "recommend.py에서 score_work 호출을 찾을 수 없음"
    assert len(call.args) >= 4, (
        f"score_work 인자 수 {len(call.args)} < 4 — walk_m 인자 없음"
    )
    fourth = ast.unparse(call.args[3])
    assert fourth == "transit.get('total_walk_m', 0)", (
        f"4번째 인자(walk_m) {fourth!r} != \"transit.get('total_walk_m', 0)\""
    )


# T-085 acceptance #4: scores dict work/life/safe 키 유지 (회귀)
async def test_t085_scores_dict_has_work_life_safe_keys():
    from app.services.recommend import recommend

    areas = _areas(1)
    transit_with_extras = {"min": 20, "payment": 1000, "first_lane": None, "transfers": 1, "total_walk_m": 600}

    captured_scores: list[dict] = []
    from app.services import scoring as _scoring
    _orig_compute = _scoring.compute_total

    def spy_compute(scores, priority):
        captured_scores.append(dict(scores))
        return _orig_compute(scores, priority)

    conn = _make_conn_t077(areas, _t077_metrics(areas), [[]])
    with patch("app.services.kakao.geocode_address", new=AsyncMock(return_value=(37.5, 127.0))), \
         patch("app.services.odsay.transit_time", new=AsyncMock(return_value=transit_with_extras)), \
         patch("app.services.scoring.compute_total", side_effect=spy_compute):
        result = await recommend(make_req(), conn)

    assert captured_scores, "compute_total이 한 번도 호출되지 않음"
    scores = captured_scores[0]
    assert set(scores.keys()) == {"work", "life", "safe"}, (
        f"scores 키 {set(scores.keys())} != {{'work', 'life', 'safe'}}"
    )


# T-085 acceptance #1+#2: transfers/walk_m 실제 전달 확인 (런타임 spy)
async def test_t085_score_work_receives_transfers_and_walk_m_at_runtime():
    from app.services.recommend import recommend

    areas = _areas(1)
    transit_with_extras = {"min": 30, "payment": 1000, "first_lane": None, "transfers": 2, "total_walk_m": 800}

    captured: list[tuple] = []
    from app.services import scoring as _scoring
    _orig_score_work = _scoring.score_work

    def spy_score_work(total_min, max_min, transfers=0, walk_m=0):
        captured.append((total_min, max_min, transfers, walk_m))
        return _orig_score_work(total_min, max_min, transfers, walk_m)

    conn = _make_conn_t077(areas, _t077_metrics(areas), [[]])
    with patch("app.services.kakao.geocode_address", new=AsyncMock(return_value=(37.5, 127.0))), \
         patch("app.services.odsay.transit_time", new=AsyncMock(return_value=transit_with_extras)), \
         patch("app.services.scoring.score_work", side_effect=spy_score_work):
        await recommend(make_req(), conn)

    assert captured, "score_work가 한 번도 호출되지 않음"
    total_min, max_min, transfers, walk_m = captured[0]
    assert total_min == 30, f"1번째 인자(total_min) {total_min} != 30"
    assert max_min == 60, f"2번째 인자(max_min) {max_min} != 60"
    assert transfers == 2, (
        f"3번째 인자(transfers) {transfers} != 2 — transit.get('transfers', 0) 미전달"
    )
    assert walk_m == 800, (
        f"4번째 인자(walk_m) {walk_m} != 800 — transit.get('total_walk_m', 0) 미전달"
    )


# ── T-132: nearest-K 선필터 + 세마포어 ──────────────────────────────────────

import asyncio as _asyncio


def _make_conn_nearest(area_rows, n_candidates=None):
    """areas + metrics side_effects. 이후 소진 → StopAsyncIteration (tag/listing try-except 흡수)."""
    if n_candidates is None:
        n_candidates = len(area_rows)
    metrics = _t077_metrics(area_rows[:n_candidates])
    conn = AsyncMock()
    conn.execute.side_effect = [
        _db_result(area_rows),
        _db_result(metrics),
    ]
    return conn


# T-132 acceptance #1: K=3, area 10개 → transit_time 호출 ≤ K
async def test_nearest_k_transit_time_call_count_leq_k():
    from app.services.recommend import recommend

    K = 3
    areas = _areas(10)
    conn = _make_conn_nearest(areas, K)
    transit_mock = AsyncMock(return_value=TRANSIT_OK)

    with patch("app.services.recommend.settings") as mock_cfg, \
         patch("app.services.odsay.load_cache_batch", new=AsyncMock(return_value={})), \
         patch("app.services.odsay.transit_time", new=transit_mock), \
         patch("app.services.kakao.geocode_address", new=AsyncMock(return_value=(37.5, 127.0))):
        mock_cfg.RECOMMEND_NEAREST_K = K
        mock_cfg.ODSAY_MAX_CONCURRENCY = 5
        await recommend(make_req(), conn)

    assert transit_mock.call_count <= K, (
        f"transit_time 호출 {transit_mock.call_count}회 > K={K} — nearest-K 선필터 미작동"
    )


# T-132 acceptance #2: haversine 최근접 K개만 transit_time, 먼 area 제외
async def test_nearest_k_selects_haversine_nearest():
    from app.services.recommend import recommend

    K = 2
    areas_specific = [
        _row(area_id=uuid.uuid4(), emd_name="동0", lat=37.500, lng=127.000, sgg_name="강남구"),
        _row(area_id=uuid.uuid4(), emd_name="동1", lat=37.510, lng=127.010, sgg_name="강남구"),
        _row(area_id=uuid.uuid4(), emd_name="동2", lat=37.530, lng=127.030, sgg_name="강남구"),  # FAR
        _row(area_id=uuid.uuid4(), emd_name="동3", lat=37.540, lng=127.040, sgg_name="강남구"),  # FAR
    ]
    far_area_ids = {areas_specific[2].area_id, areas_specific[3].area_id}
    conn = _make_conn_nearest(areas_specific, K)
    called_area_ids: set = set()

    async def spy_transit(origin, area_id, dest, conn_arg, client=None):
        called_area_ids.add(area_id)
        return TRANSIT_OK

    with patch("app.services.recommend.settings") as mock_cfg, \
         patch("app.services.odsay.load_cache_batch", new=AsyncMock(return_value={})), \
         patch("app.services.odsay.transit_time", new=spy_transit), \
         patch("app.services.kakao.geocode_address", new=AsyncMock(return_value=(37.5, 127.0))):
        mock_cfg.RECOMMEND_NEAREST_K = K
        mock_cfg.ODSAY_MAX_CONCURRENCY = 5
        await recommend(make_req(), conn)

    overlap = called_area_ids & far_area_ids
    assert not overlap, (
        f"먼 area {overlap} transit_time 호출됨 — haversine 선필터 미작동"
    )
    assert len(called_area_ids) == K, (
        f"transit_time 호출 area 수 {len(called_area_ids)} != K={K}"
    )


# T-132 acceptance #3: area_rows ≤ K → 전체 area 파이프라인 진입 (회귀)
async def test_nearest_k_all_areas_when_rows_leq_k():
    from app.services.recommend import recommend

    areas = _areas(3)  # 3 < default K=40
    conn = _make_conn_nearest(areas, 3)
    transit_mock = AsyncMock(return_value=TRANSIT_OK)

    with patch("app.services.odsay.load_cache_batch", new=AsyncMock(return_value={})), \
         patch("app.services.odsay.transit_time", new=transit_mock), \
         patch("app.services.kakao.geocode_address", new=AsyncMock(return_value=(37.5, 127.0))):
        await recommend(make_req(), conn)

    assert transit_mock.call_count == 3, (
        f"area≤K 시 transit_time 호출 수 {transit_mock.call_count} != 3 — 전체 area 미진입"
    )


# T-132 acceptance #4: 세마포어로 동시 transit_time 호출 ≤ ODSAY_MAX_CONCURRENCY
async def test_nearest_k_semaphore_caps_concurrency():
    from app.services.recommend import recommend

    MAX_CONCURRENCY = 2
    K = 6
    areas = _areas(K)
    conn = _make_conn_nearest(areas, K)

    max_concurrent = [0]
    current = [0]

    async def counting_transit(origin, area_id, dest, conn_arg, client=None):
        current[0] += 1
        max_concurrent[0] = max(max_concurrent[0], current[0])
        await _asyncio.sleep(0.01)
        current[0] -= 1
        return TRANSIT_OK

    with patch("app.services.recommend.settings") as mock_cfg, \
         patch("app.services.odsay.load_cache_batch", new=AsyncMock(return_value={})), \
         patch("app.services.odsay.transit_time", new=counting_transit), \
         patch("app.services.kakao.geocode_address", new=AsyncMock(return_value=(37.5, 127.0))):
        mock_cfg.RECOMMEND_NEAREST_K = K
        mock_cfg.ODSAY_MAX_CONCURRENCY = MAX_CONCURRENCY
        await recommend(make_req(), conn)

    assert max_concurrent[0] <= MAX_CONCURRENCY, (
        f"최대 동시 transit_time 호출 {max_concurrent[0]} > ODSAY_MAX_CONCURRENCY={MAX_CONCURRENCY}"
        " — 세마포어 미적용"
    )


# T-132 acceptance #5: 전부 캐시 히트 → transit_time 0회, 결과 정상 (회귀)
async def test_nearest_k_all_cache_hit_zero_transit_calls():
    from app.services.recommend import recommend

    areas = _areas(3)
    conn = _make_conn_nearest(areas, 3)
    transit_mock = AsyncMock(return_value=TRANSIT_OK)

    async def all_hit(origin, area_ids, conn_arg):
        return {aid: dict(TRANSIT_OK) for aid in area_ids}

    with patch("app.services.odsay.load_cache_batch", new=all_hit), \
         patch("app.services.odsay.transit_time", new=transit_mock), \
         patch("app.services.kakao.geocode_address", new=AsyncMock(return_value=(37.5, 127.0))):
        result = await recommend(make_req(), conn)

    assert transit_mock.call_count == 0, (
        f"전부 캐시 히트 시 transit_time {transit_mock.call_count}회 호출 — 0회여야 함"
    )
    assert isinstance(result, (list, dict)), f"반환 타입 오류: {type(result)}"


# T-132 acceptance #6: 회귀 — area≤K에서 max_commute 게이트·score 정렬 불변
async def test_nearest_k_regression_commute_gate_and_score_sort():
    from app.services.recommend import recommend

    # area 0(min=20, pass), area 1(min=90, fail), area 2(min=30, pass)
    areas = _areas(3)
    conn = _make_conn_nearest(areas, 2)

    transit_map = {
        areas[0].area_id: {"min": 20, "payment": 1000, "first_lane": None},
        areas[1].area_id: {"min": 90, "payment": 1000, "first_lane": None},
        areas[2].area_id: {"min": 30, "payment": 1000, "first_lane": None},
    }

    async def transit_by_area(origin, area_id, dest, conn_arg, client=None):
        return transit_map.get(area_id)

    with patch("app.services.odsay.load_cache_batch", new=AsyncMock(return_value={})), \
         patch("app.services.odsay.transit_time", new=transit_by_area), \
         patch("app.services.kakao.geocode_address", new=AsyncMock(return_value=(37.5, 127.0))):
        result = await recommend(make_req(max_commute_minutes=60), conn)

    areas_list = result.get("areas", result) if isinstance(result, dict) else result
    names = {item.get("name") for item in areas_list}

    assert "동1" not in names, "max_commute 초과 area(동1)가 결과에 포함됨 — 게이트 미작동"
    assert len(names) >= 1, "commute 통과 area(동0, 동2) 중 결과 없음"
