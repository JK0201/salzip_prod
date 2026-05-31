import datetime
import json
import uuid
from unittest.mock import AsyncMock, MagicMock, patch

import pytest


def _make_area_row():
    row = MagicMock()
    row.area_id = 1
    row.emd_name = "테스트동"
    row.lat = "37.5"
    row.lng = "127.0"
    row.sgg_name = "테스트구"
    return row


def _make_metrics_row():
    row = MagicMock()
    row.area_id = 1
    for attr in [
        "cafe_count", "food_count", "culture_count", "park_count",
        "mart_count", "subway_count", "hospital_count", "pharmacy_count",
    ]:
        setattr(row, attr, 3)
    row.avg_jeonse_ratio = 60.0
    row.flood_ratio = 5.0
    row.avg_build_year = 2015
    row.listing_count = 5
    row.flood_risk_count = 1
    return row


def _build_conn(user_id):
    """Mock conn that captures all SQL texts and params passed to execute."""
    area_row = _make_area_row()
    metrics_row = _make_metrics_row()
    profile_id = uuid.uuid4()
    match_id = uuid.uuid4()
    captured_sqls: list[str] = []
    captured_match_payloads: list[dict] = []

    async def side_effect(stmt, params=None):
        sql = str(stmt)
        captured_sqls.append(sql)

        result = MagicMock()
        result.fetchall.return_value = []
        result.scalar.return_value = None
        result.scalar_one.return_value = uuid.uuid4()
        result.__iter__ = MagicMock(return_value=iter([]))

        if "JOIN regions" in sql:
            result.fetchall.return_value = [area_row]
        elif "FROM area_metrics" in sql:
            mm = MagicMock()
            mm.all.return_value = [metrics_row]
            result.mappings.return_value = mm
        elif "lifestyle_tags" in sql:
            result.__iter__ = MagicMock(return_value=iter([]))
        elif "FROM listings" in sql:
            result.fetchall.return_value = []
        elif "FROM sessions" in sql:
            result.scalar.return_value = user_id
        elif "INSERT INTO profiles" in sql:
            result.scalar_one.return_value = profile_id
        elif "INSERT INTO match_results" in sql:
            if params and "payload" in params:
                captured_match_payloads.append(json.loads(params["payload"]))
            result.scalar_one.return_value = match_id

        return result

    conn = AsyncMock()
    conn.execute = AsyncMock(side_effect=side_effect)
    return conn, captured_sqls, captured_match_payloads, profile_id, match_id


@pytest.fixture
def req():
    from app.api.v1.recommend import RecommendRequest
    return RecommendRequest(
        workplace_name="테스트회사",
        workplace_address="서울시 강남구 테헤란로 123",
        job_type="사무직",
        max_commute_minutes=30,
        lifestyle_tags=["조용한", "카페 근처"],
        deposit_max_wan=5000,
        monthly_rent_max_wan=70,
        age=28,
        annual_income_wan=4000,
        household_type="1인",
        home_ownerless=True,
    )


# ── acceptance #1: 로그인 유저 profiles INSERT에 ON CONFLICT 없음 ──────────────

async def test_logged_in_user_profile_insert_has_no_on_conflict(req):
    import app.services.kakao as kakao_mod
    import app.services.odsay as odsay_mod
    from app.services.recommend import recommend

    user_id = uuid.uuid4()
    session_id = uuid.uuid4()
    conn, captured_sqls, _, _, _ = _build_conn(user_id=user_id)

    with (
        patch.object(kakao_mod, "geocode_address", new=AsyncMock(return_value=(37.5, 127.0))),
        patch.object(
            odsay_mod, "transit_time",
            new=AsyncMock(return_value={"min": 20, "transfers": 1, "total_walk_m": 300}),
        ),
    ):
        await recommend(req, conn, session_id=session_id)

    profile_insert_sqls = [s for s in captured_sqls if "INSERT INTO profiles" in s]
    assert len(profile_insert_sqls) >= 1, (
        "로그인 유저 경로에서 profiles INSERT가 실행되지 않음"
    )
    for sql in profile_insert_sqls:
        assert "ON CONFLICT" not in sql, (
            f"로그인 유저 profiles INSERT에 ON CONFLICT가 포함됨:\n{sql}"
        )


# ── acceptance #2: match_results payload에 areas + request 키 모두 포함 ──────────

async def test_match_results_payload_has_areas_and_request_keys(req):
    import app.services.kakao as kakao_mod
    import app.services.odsay as odsay_mod
    from app.services.recommend import recommend

    user_id = uuid.uuid4()
    session_id = uuid.uuid4()
    conn, _, captured_match_payloads, _, _ = _build_conn(user_id=user_id)

    with (
        patch.object(kakao_mod, "geocode_address", new=AsyncMock(return_value=(37.5, 127.0))),
        patch.object(
            odsay_mod, "transit_time",
            new=AsyncMock(return_value={"min": 20, "transfers": 1, "total_walk_m": 300}),
        ),
    ):
        await recommend(req, conn, session_id=session_id)

    assert len(captured_match_payloads) >= 1, (
        "match_results INSERT가 실행되지 않음 — persist 경로에 진입했는지 확인"
    )
    payload = captured_match_payloads[0]
    assert "areas" in payload, (
        f"match_results payload에 'areas' 키 없음. 실제 키: {list(payload.keys())}"
    )
    assert "request" in payload, (
        f"match_results payload에 'request' 키 없음. 실제 키: {list(payload.keys())}"
    )


# ── acceptance #3: 익명 유저 profiles INSERT에도 ON CONFLICT 없음 (회귀 가드) ──

async def test_anonymous_user_profile_insert_has_no_on_conflict(req):
    import app.services.kakao as kakao_mod
    import app.services.odsay as odsay_mod
    from app.services.recommend import recommend

    session_id = uuid.uuid4()
    conn, captured_sqls, _, _, _ = _build_conn(user_id=None)

    with (
        patch.object(kakao_mod, "geocode_address", new=AsyncMock(return_value=(37.5, 127.0))),
        patch.object(
            odsay_mod, "transit_time",
            new=AsyncMock(return_value={"min": 20, "transfers": 1, "total_walk_m": 300}),
        ),
    ):
        await recommend(req, conn, session_id=session_id)

    profile_insert_sqls = [s for s in captured_sqls if "INSERT INTO profiles" in s]
    assert len(profile_insert_sqls) >= 1, (
        "익명 경로에서 profiles INSERT가 실행되지 않음"
    )
    for sql in profile_insert_sqls:
        assert "ON CONFLICT" not in sql, (
            f"익명 유저 profiles INSERT에 ON CONFLICT가 포함됨:\n{sql}"
        )


# ── acceptance #4: session_id 있을 때 반환값이 {areas, match_id} 형태 (회귀 가드) ─

async def test_recommend_returns_areas_and_match_id_shape(req):
    import app.services.kakao as kakao_mod
    import app.services.odsay as odsay_mod
    from app.services.recommend import recommend

    user_id = uuid.uuid4()
    session_id = uuid.uuid4()
    conn, _, _, _, _ = _build_conn(user_id=user_id)

    with (
        patch.object(kakao_mod, "geocode_address", new=AsyncMock(return_value=(37.5, 127.0))),
        patch.object(
            odsay_mod, "transit_time",
            new=AsyncMock(return_value={"min": 20, "transfers": 1, "total_walk_m": 300}),
        ),
    ):
        result = await recommend(req, conn, session_id=session_id)

    assert isinstance(result, dict), (
        f"session_id 있을 때 반환값은 dict여야 함. got: {type(result).__name__}"
    )
    assert "areas" in result, f"반환값에 'areas' 키 없음: {list(result.keys())}"
    assert "match_id" in result, f"반환값에 'match_id' 키 없음: {list(result.keys())}"
    assert isinstance(result["areas"], list), (
        f"result['areas']는 list여야 함. got: {type(result['areas']).__name__}"
    )


# ── T-102 acceptance #1: RecommendResponse에 created_at 필드 존재 ─────────────

def test_recommend_response_has_created_at_field():
    from app.schemas.area_recommend import RecommendResponse

    assert "created_at" in RecommendResponse.model_fields, (
        "RecommendResponse에 created_at 필드 없음"
    )
    field = RecommendResponse.model_fields["created_at"]
    assert field.default is None, (
        f"created_at 기본값이 None이 아님: {field.default}"
    )
    # datetime.datetime 값으로 생성 가능해야 함
    dt = datetime.datetime(2025, 3, 10, 9, 0, 0)
    resp = RecommendResponse(areas=[], created_at=dt)
    assert resp.created_at == dt
    # 기본 생성 시 None
    resp_default = RecommendResponse(areas=[])
    assert resp_default.created_at is None


# ── T-102 acceptance #2: get_recommend_latest SQL에 mr.created_at 포함 ─────────

async def test_get_recommend_latest_sql_includes_created_at():
    from app.api.v1.recommend import get_recommend_latest

    session = MagicMock()
    session.session_id = uuid.uuid4()

    captured_sqls: list[str] = []

    async def mock_execute(stmt, params=None):
        captured_sqls.append(str(stmt))
        result = MagicMock()
        mm = MagicMock()
        mm.first.return_value = None
        result.mappings.return_value = mm
        return result

    conn = AsyncMock()
    conn.execute = AsyncMock(side_effect=mock_execute)

    await get_recommend_latest(session, conn)

    assert len(captured_sqls) >= 1, "conn.execute가 한 번도 호출되지 않음"
    assert any("mr.created_at" in sql for sql in captured_sqls), (
        f"SELECT에 mr.created_at 없음. 실제 SQL: {captured_sqls}"
    )


# ── T-102 acceptance #3: row 있을 때 created_at이 row 값으로 채워짐 ───────────

async def test_get_recommend_latest_returns_created_at_from_row():
    from app.api.v1.recommend import get_recommend_latest

    session = MagicMock()
    session.session_id = uuid.uuid4()
    match_id = uuid.uuid4()
    expected_dt = datetime.datetime(2025, 3, 10, 9, 0, 0)

    async def mock_execute(stmt, params=None):
        result = MagicMock()
        row = {
            "id": match_id,
            "payload": '{"areas": []}',
            "created_at": expected_dt,
        }
        mm = MagicMock()
        mm.first.return_value = row
        result.mappings.return_value = mm
        return result

    conn = AsyncMock()
    conn.execute = AsyncMock(side_effect=mock_execute)

    resp = await get_recommend_latest(session, conn)

    assert resp.created_at == expected_dt, (
        f"created_at이 row 값과 다름. expected: {expected_dt}, got: {resp.created_at}"
    )


# ── T-102 acceptance #4: row None일 때 created_at=None, areas=[], match_id=None ─

async def test_get_recommend_latest_returns_none_when_no_row():
    from app.api.v1.recommend import get_recommend_latest

    session = MagicMock()
    session.session_id = uuid.uuid4()

    async def mock_execute(stmt, params=None):
        result = MagicMock()
        mm = MagicMock()
        mm.first.return_value = None
        result.mappings.return_value = mm
        return result

    conn = AsyncMock()
    conn.execute = AsyncMock(side_effect=mock_execute)

    resp = await get_recommend_latest(session, conn)

    assert resp.created_at is None, (
        f"row가 None일 때 created_at은 None이어야 함. got: {resp.created_at}"
    )
    assert resp.areas == [], f"row가 None일 때 areas는 []이어야 함. got: {resp.areas}"
    assert resp.match_id is None, (
        f"row가 None일 때 match_id는 None이어야 함. got: {resp.match_id}"
    )


# ── T-102 acceptance #5: post_recommend 응답에 created_at unset 유지 (회귀) ────

def test_post_recommend_created_at_unset_when_not_provided():
    from app.schemas.area_recommend import RecommendResponse

    # post_recommend는 RecommendResponse(areas=...) 또는 RecommendResponse(areas=..., match_id=...)
    # created_at을 명시적으로 넘기지 않으므로 model_fields_set에 포함되면 안 됨
    resp = RecommendResponse(areas=[])
    assert "created_at" not in resp.model_fields_set, (
        "created_at이 model_fields_set에 포함됨 — "
        "response_model_exclude_unset=True 직렬화 시 노출될 것"
    )

    resp2 = RecommendResponse(areas=[], match_id=uuid.uuid4())
    assert "created_at" not in resp2.model_fields_set, (
        "match_id만 넘긴 경우에도 created_at은 unset이어야 함"
    )


# ── T-102 acceptance #6: get_recommend_latest areas, match_id 동작 유지 (회귀) ─

async def test_get_recommend_latest_areas_and_match_id_unchanged():
    from app.api.v1.recommend import get_recommend_latest

    session = MagicMock()
    session.session_id = uuid.uuid4()
    match_id = uuid.uuid4()
    created_dt = datetime.datetime(2025, 1, 1, 0, 0, 0)

    async def mock_execute(stmt, params=None):
        result = MagicMock()
        row = {
            "id": match_id,
            "payload": json.dumps({"areas": []}),
            "created_at": created_dt,
        }
        mm = MagicMock()
        mm.first.return_value = row
        result.mappings.return_value = mm
        return result

    conn = AsyncMock()
    conn.execute = AsyncMock(side_effect=mock_execute)

    resp = await get_recommend_latest(session, conn)

    assert resp.match_id == match_id, (
        f"match_id 변경됨. expected: {match_id}, got: {resp.match_id}"
    )
    assert resp.areas == [], (
        f"areas가 payload의 빈 리스트여야 함. got: {resp.areas}"
    )


# ── T-103 acceptance #1: RecommendResponse에 request 필드 존재 ───────────────

def test_recommend_response_has_request_field():
    from app.schemas.area_recommend import RecommendResponse

    assert "request" in RecommendResponse.model_fields, (
        "RecommendResponse에 request 필드 없음"
    )
    field = RecommendResponse.model_fields["request"]
    assert field.default is None, (
        f"request 기본값이 None이 아님: {field.default}"
    )
    # dict 값으로 생성 가능해야 함
    req_data = {"age": 28, "job_type": "사무직", "workplace_name": "테스트회사"}
    resp = RecommendResponse(areas=[], request=req_data)
    assert resp.request == req_data, (
        f"request 필드 값이 일치하지 않음. got: {resp.request}"
    )
    # 기본 생성 시 None
    resp_default = RecommendResponse(areas=[])
    assert resp_default.request is None, (
        f"request 기본값이 None이 아님: {resp_default.request}"
    )


# ── T-103 acceptance #2: payload에 request 있을 때 응답 request로 채워짐 ──────

async def test_get_recommend_latest_returns_request_from_payload():
    from app.api.v1.recommend import get_recommend_latest

    session = MagicMock()
    session.session_id = uuid.uuid4()
    match_id = uuid.uuid4()
    expected_request = {"age": 28, "job_type": "사무직", "workplace_name": "테스트회사"}

    async def mock_execute(stmt, params=None):
        result = MagicMock()
        row = {
            "id": match_id,
            "payload": json.dumps({"areas": [], "request": expected_request}),
            "created_at": datetime.datetime(2025, 3, 10, 9, 0, 0),
        }
        mm = MagicMock()
        mm.first.return_value = row
        result.mappings.return_value = mm
        return result

    conn = AsyncMock()
    conn.execute = AsyncMock(side_effect=mock_execute)

    resp = await get_recommend_latest(session, conn)

    assert resp.request == expected_request, (
        f"payload의 request가 응답에 매핑되지 않음. "
        f"expected: {expected_request}, got: {resp.request}"
    )


# ── T-103 acceptance #3: payload에 request 키 없을 때 응답 request가 None ──────

async def test_get_recommend_latest_returns_none_request_when_no_request_key():
    from app.api.v1.recommend import get_recommend_latest

    session = MagicMock()
    session.session_id = uuid.uuid4()
    match_id = uuid.uuid4()

    async def mock_execute(stmt, params=None):
        result = MagicMock()
        row = {
            "id": match_id,
            "payload": json.dumps({"areas": []}),  # request 키 없는 옛 레코드
            "created_at": datetime.datetime(2025, 1, 1, 0, 0, 0),
        }
        mm = MagicMock()
        mm.first.return_value = row
        result.mappings.return_value = mm
        return result

    conn = AsyncMock()
    conn.execute = AsyncMock(side_effect=mock_execute)

    resp = await get_recommend_latest(session, conn)

    assert resp.request is None, (
        f"payload에 request 키 없을 때 응답 request는 None이어야 함. got: {resp.request}"
    )


# ── T-103 acceptance #4: row None일 때 request=None, areas=[] ────────────────

async def test_get_recommend_latest_request_none_when_no_row():
    from app.api.v1.recommend import get_recommend_latest

    session = MagicMock()
    session.session_id = uuid.uuid4()

    async def mock_execute(stmt, params=None):
        result = MagicMock()
        mm = MagicMock()
        mm.first.return_value = None
        result.mappings.return_value = mm
        return result

    conn = AsyncMock()
    conn.execute = AsyncMock(side_effect=mock_execute)

    resp = await get_recommend_latest(session, conn)

    assert resp.request is None, (
        f"row가 None일 때 request는 None이어야 함. got: {resp.request}"
    )
    assert resp.areas == [], (
        f"row가 None일 때 areas는 []이어야 함. got: {resp.areas}"
    )


# ── T-103 acceptance #5: 기존 fields(areas, match_id, created_at) 매핑 유지 ──

async def test_get_recommend_latest_existing_fields_preserved_with_request():
    from app.api.v1.recommend import get_recommend_latest

    session = MagicMock()
    session.session_id = uuid.uuid4()
    match_id = uuid.uuid4()
    created_dt = datetime.datetime(2025, 3, 10, 9, 0, 0)
    request_data = {"age": 30, "job_type": "전문직"}

    async def mock_execute(stmt, params=None):
        result = MagicMock()
        row = {
            "id": match_id,
            "payload": json.dumps({"areas": [], "request": request_data}),
            "created_at": created_dt,
        }
        mm = MagicMock()
        mm.first.return_value = row
        result.mappings.return_value = mm
        return result

    conn = AsyncMock()
    conn.execute = AsyncMock(side_effect=mock_execute)

    resp = await get_recommend_latest(session, conn)

    assert resp.match_id == match_id, (
        f"match_id 변경됨. expected: {match_id}, got: {resp.match_id}"
    )
    assert resp.areas == [], (
        f"areas가 payload의 빈 리스트여야 함. got: {resp.areas}"
    )
    assert resp.created_at == created_dt, (
        f"created_at 변경됨. expected: {created_dt}, got: {resp.created_at}"
    )
    assert resp.request == request_data, (
        f"request 매핑 실패. expected: {request_data}, got: {resp.request}"
    )


# ── T-103 acceptance #6: POST /recommend 응답에 request 기본값 None ─────────

def test_post_recommend_response_request_default_none():
    from app.schemas.area_recommend import RecommendResponse

    # POST /recommend 라우트는 request를 RecommendResponse에 넘기지 않음
    resp = RecommendResponse(areas=[])
    assert resp.request is None, (
        f"RecommendResponse(areas=[]) 시 request는 None이어야 함. got: {resp.request}"
    )
    assert "request" not in resp.model_fields_set, (
        "request가 model_fields_set에 포함됨 — "
        "response_model_exclude_unset=True 직렬화 시 불필요하게 노출됨"
    )

    resp2 = RecommendResponse(areas=[], match_id=uuid.uuid4())
    assert resp2.request is None, (
        f"match_id만 넘긴 경우에도 request는 None이어야 함. got: {resp2.request}"
    )
    assert "request" not in resp2.model_fields_set, (
        "match_id만 넘긴 경우에도 request는 unset이어야 함"
    )
