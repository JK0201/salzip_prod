"""POST /api/v1/recommend 라우터 테스트 — T-055, T-078."""

import datetime
import uuid
import uuid as _uuid
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from httpx import ASGITransport, AsyncClient

VALID_PAYLOAD = {
    "workplace_name": "카카오",
    "workplace_address": "경기도 성남시 분당구 판교역로 235",
    "job_type": "사무직",
    "max_commute_minutes": 60,
    "lifestyle_tags": ["조용한", "공원 근처"],
    "deposit_max_wan": 5000,
    "monthly_rent_max_wan": 80,
    "age": 30,
    "annual_income_wan": 3000,
    "household_type": "single",
    "home_ownerless": True,
}


@pytest.fixture
async def client(monkeypatch: pytest.MonkeyPatch) -> AsyncClient:
    monkeypatch.setenv(
        "DATABASE_URL",
        "postgresql+asyncpg://postgres:postgres@localhost:5432/test",
    )
    from app.core.config import get_settings
    get_settings.cache_clear()

    from app.core.deps import get_db_conn
    from app.main import app

    mock_conn = AsyncMock()
    app.dependency_overrides[get_db_conn] = lambda: mock_conn

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as c:
        yield c

    app.dependency_overrides.clear()


@pytest.fixture
async def authed_client(monkeypatch: pytest.MonkeyPatch) -> AsyncClient:
    monkeypatch.setenv(
        "DATABASE_URL",
        "postgresql+asyncpg://postgres:postgres@localhost:5432/test",
    )
    from app.core.config import get_settings
    get_settings.cache_clear()

    from app.core.auth import require_session, SessionContext
    from app.core.deps import get_db_conn
    from app.main import app

    mock_conn = AsyncMock()
    mock_session = SessionContext(session_id=uuid.uuid4(), token="test-token")

    app.dependency_overrides[get_db_conn] = lambda: mock_conn
    app.dependency_overrides[require_session] = lambda: mock_session

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as c:
        yield c

    app.dependency_overrides.clear()


# --- acceptance #1: RecommendRequest, RecommendResponse import 가능 ---
def test_recommend_request_importable():
    from app.api.v1.recommend import RecommendRequest  # noqa: F401


def test_recommend_response_importable():
    from app.api.v1.recommend import RecommendResponse  # noqa: F401


# --- acceptance #2: RecommendRequest 11 필드 ---
def test_recommend_request_has_required_fields():
    from app.api.v1.recommend import RecommendRequest

    fields = RecommendRequest.model_fields
    expected = {
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
    assert expected == set(fields.keys())


# --- acceptance #4: 인증 헤더 없으면 401 ---
async def test_post_recommend_no_auth_returns_401(client: AsyncClient):
    resp = await client.post("/api/v1/recommend", json=VALID_PAYLOAD)
    assert resp.status_code == 401


# --- acceptance #6: workplace_address 누락 → 422 ---
async def test_post_recommend_missing_workplace_address_returns_422(authed_client: AsyncClient):
    payload = {k: v for k, v in VALID_PAYLOAD.items() if k != "workplace_address"}
    resp = await authed_client.post("/api/v1/recommend", json=payload)
    assert resp.status_code == 422


# --- acceptance #7: AddressNotFound → 400, body.error == 'address_not_found' ---
async def test_post_recommend_address_not_found_returns_400(authed_client: AsyncClient):
    from app.core.exceptions import AddressNotFound

    with patch(
        "app.api.v1.recommend.recommend_service.recommend",
        new=AsyncMock(side_effect=AddressNotFound("address_not_found")),
    ):
        resp = await authed_client.post("/api/v1/recommend", json=VALID_PAYLOAD)

    assert resp.status_code == 400
    assert resp.json()["error"] == "address_not_found"


# ---------------------------------------------------------------------------
# T-078: recommend API 응답 areas 모양 전환
# ---------------------------------------------------------------------------

_LISTING_ITEM = {
    "id": str(_uuid.uuid4()),
    "kind": "월세",
    "deposit": 500,
    "monthly_rent": 60,
    "lat": 37.3900,
    "lng": 127.1100,
}

_VALID_AREA = {
    "area_id": str(_uuid.uuid4()),
    "rank": 1,
    "name": "판교동",
    "meta": "경기도 성남시",
    "score": 85,
    "tier": 1,
    "lat": 37.3900,
    "lng": 127.1100,
    "commuteMinutes": 25,
    "scores": {"lifestyle": 80, "commute": 90},
    "listing_count": 3,
    "flood_risk_count": 0,
    "reason": "직장 근처 조용한 동네",
    "listings": [_LISTING_ITEM, _LISTING_ITEM, _LISTING_ITEM],
    "metrics": {
        "cafe_count": 5,
        "food_count": 10,
        "culture_count": 2,
        "park_count": 1,
        "mart_count": 3,
        "subway_count": 2,
        "hospital_count": 1,
        "pharmacy_count": 2,
    },
    "safety": {
        "avg_jeonse_ratio": 0.6,
        "flood_ratio": 0.05,
        "avg_build_year": 2010,
    },
}


# acceptance #1: inline class RecommendResponse 존재하지 않음
def test_t078_recommend_response_not_defined_inline():
    import app.api.v1.recommend as _mod
    from app.api.v1.recommend import RecommendResponse

    assert RecommendResponse.__module__ != _mod.__name__


# acceptance #2: app.schemas.area_recommend.RecommendResponse를 import
def test_t078_recommend_response_imported_from_area_recommend_schema():
    from app.api.v1.recommend import RecommendResponse
    from app.schemas.area_recommend import RecommendResponse as _SchemaRR

    assert RecommendResponse is _SchemaRR


# acceptance #3: POST /api/v1/recommend mock 호출 시 200
async def test_t078_post_recommend_returns_200(authed_client: AsyncClient):
    with patch(
        "app.api.v1.recommend.recommend_service.recommend",
        new=AsyncMock(return_value=[_VALID_AREA]),
    ):
        resp = await authed_client.post("/api/v1/recommend", json=VALID_PAYLOAD)

    assert resp.status_code == 200


# acceptance #4: 응답 body 최상위 키 집합 == {areas}, hoods 없음
async def test_t078_post_recommend_response_top_level_key_is_areas_only(authed_client: AsyncClient):
    with patch(
        "app.api.v1.recommend.recommend_service.recommend",
        new=AsyncMock(return_value=[_VALID_AREA]),
    ):
        resp = await authed_client.post("/api/v1/recommend", json=VALID_PAYLOAD)

    assert resp.status_code == 200
    body = resp.json()
    assert set(body.keys()) == {"areas"}
    assert "hoods" not in body


# acceptance #5: body.areas가 list 타입
async def test_t078_post_recommend_areas_is_list(authed_client: AsyncClient):
    with patch(
        "app.api.v1.recommend.recommend_service.recommend",
        new=AsyncMock(return_value=[_VALID_AREA]),
    ):
        resp = await authed_client.post("/api/v1/recommend", json=VALID_PAYLOAD)

    assert isinstance(resp.json()["areas"], list)


# acceptance #6: 각 항목에 listings, metrics, safety 3 키 존재
async def test_t078_post_recommend_area_items_have_listings_metrics_safety(authed_client: AsyncClient):
    with patch(
        "app.api.v1.recommend.recommend_service.recommend",
        new=AsyncMock(return_value=[_VALID_AREA]),
    ):
        resp = await authed_client.post("/api/v1/recommend", json=VALID_PAYLOAD)

    areas = resp.json()["areas"]
    assert len(areas) > 0
    for item in areas:
        assert "listings" in item, f"listings 키 없음: {list(item.keys())}"
        assert "metrics" in item, f"metrics 키 없음: {list(item.keys())}"
        assert "safety" in item, f"safety 키 없음: {list(item.keys())}"


# acceptance #7: listings는 list, 길이 5 이하
async def test_t078_post_recommend_area_listings_is_list_and_max_5(authed_client: AsyncClient):
    with patch(
        "app.api.v1.recommend.recommend_service.recommend",
        new=AsyncMock(return_value=[_VALID_AREA]),
    ):
        resp = await authed_client.post("/api/v1/recommend", json=VALID_PAYLOAD)

    areas = resp.json()["areas"]
    for item in areas:
        assert isinstance(item["listings"], list)
        assert len(item["listings"]) <= 5, f"listings 길이 초과: {len(item['listings'])}"


# ---------------------------------------------------------------------------
# T-080: recommend API match_id 노출
# ---------------------------------------------------------------------------

_T080_MATCH_ID = uuid.uuid4()

_T080_SERVICE_RESULT = {
    "areas": [_VALID_AREA],
    "match_id": _T080_MATCH_ID,
}

_T080_SERVICE_RESULT_NO_MATCH = {
    "areas": [_VALID_AREA],
    "match_id": None,
}


# acceptance #1: RecommendResponse에 match_id: uuid.UUID | None 필드, 기본값 None
def test_t080_recommend_response_match_id_field_default_none():
    from app.schemas.area_recommend import RecommendResponse

    resp = RecommendResponse(areas=[])
    assert resp.match_id is None


# acceptance #1: match_id 필드가 UUID 타입 수용
def test_t080_recommend_response_match_id_field_accepts_uuid():
    from app.schemas.area_recommend import RecommendResponse

    uid = uuid.uuid4()
    resp = RecommendResponse(areas=[], match_id=uid)
    assert resp.match_id == uid


# acceptance #2: areas: list[AreaItem] 필드 유지
def test_t080_recommend_response_areas_field_still_exists():
    from app.schemas.area_recommend import RecommendResponse

    fields = RecommendResponse.model_fields
    assert "areas" in fields


# acceptance #3: post_recommend가 session.session_id를 세 번째 인자로 전달
async def test_t080_post_recommend_passes_session_id_as_third_arg(authed_client: AsyncClient):
    mock_recommend = AsyncMock(return_value=_T080_SERVICE_RESULT)
    with patch("app.api.v1.recommend.recommend_service.recommend", new=mock_recommend):
        resp = await authed_client.post("/api/v1/recommend", json=VALID_PAYLOAD)

    assert resp.status_code == 200
    assert mock_recommend.called
    call_args = mock_recommend.call_args
    pos_args = call_args.args
    kwargs = call_args.kwargs
    session_id_passed = (
        len(pos_args) >= 3 and isinstance(pos_args[2], uuid.UUID)
    ) or (
        "session_id" in kwargs and isinstance(kwargs["session_id"], uuid.UUID)
    )
    assert session_id_passed, (
        f"session_id가 3번째 인자 또는 session_id 키워드로 전달되지 않음: "
        f"args={pos_args}, kwargs={kwargs}"
    )


# acceptance #4 & #5: 응답 body에 match_id 필드 포함, 값이 UUID 문자열
async def test_t080_post_recommend_response_has_match_id_uuid_string(authed_client: AsyncClient):
    with patch(
        "app.api.v1.recommend.recommend_service.recommend",
        new=AsyncMock(return_value=_T080_SERVICE_RESULT),
    ):
        resp = await authed_client.post("/api/v1/recommend", json=VALID_PAYLOAD)

    assert resp.status_code == 200
    body = resp.json()
    assert "match_id" in body
    uuid.UUID(body["match_id"])  # ValueError if not valid UUID string


# acceptance #5: match_id None일 때 body에 null로 반환
async def test_t080_post_recommend_response_match_id_null_when_no_match(authed_client: AsyncClient):
    with patch(
        "app.api.v1.recommend.recommend_service.recommend",
        new=AsyncMock(return_value=_T080_SERVICE_RESULT_NO_MATCH),
    ):
        resp = await authed_client.post("/api/v1/recommend", json=VALID_PAYLOAD)

    assert resp.status_code == 200
    body = resp.json()
    assert "match_id" in body
    assert body["match_id"] is None


# acceptance #6: AddressNotFound → 400 (regression with new 3-arg signature)
async def test_t080_address_not_found_still_returns_400(authed_client: AsyncClient):
    from app.core.exceptions import AddressNotFound

    with patch(
        "app.api.v1.recommend.recommend_service.recommend",
        new=AsyncMock(side_effect=AddressNotFound("address_not_found")),
    ):
        resp = await authed_client.post("/api/v1/recommend", json=VALID_PAYLOAD)

    assert resp.status_code == 400
    assert resp.json()["error"] == "address_not_found"


# acceptance #7: 200 응답, areas 키가 list로 유지 (regression)
async def test_t080_post_recommend_areas_list_maintained_with_match_id(authed_client: AsyncClient):
    with patch(
        "app.api.v1.recommend.recommend_service.recommend",
        new=AsyncMock(return_value=_T080_SERVICE_RESULT),
    ):
        resp = await authed_client.post("/api/v1/recommend", json=VALID_PAYLOAD)

    assert resp.status_code == 200
    body = resp.json()
    assert "areas" in body
    assert isinstance(body["areas"], list)


# ---------------------------------------------------------------------------
# T-093: GET /recommend/latest — 세션 기반 최근 추천 복원
# ---------------------------------------------------------------------------

_T093_MATCH_ID = uuid.uuid4()

_T093_ROW = {
    "id": _T093_MATCH_ID,
    "payload": {"areas": [_VALID_AREA, _VALID_AREA, _VALID_AREA]},
    "created_at": datetime.datetime(2025, 3, 10, 9, 0, 0),
}


@pytest.fixture
async def latest_authed_client(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setenv(
        "DATABASE_URL",
        "postgresql+asyncpg://postgres:postgres@localhost:5432/test",
    )
    from app.core.config import get_settings

    get_settings.cache_clear()

    from app.core.auth import SessionContext, require_session
    from app.core.deps import get_db_conn
    from app.main import app

    mock_conn = AsyncMock()
    # 실 asyncpg result는 mappings()/first()가 sync. execute가 sync MagicMock을
    # 반환하게 해 라우트의 sync 접근(_result.mappings().first())과 일치시킨다.
    mock_conn.execute = AsyncMock(return_value=MagicMock())
    mock_conn.execute.return_value.mappings.return_value.first.return_value = None
    mock_session = SessionContext(session_id=uuid.uuid4(), token="test-token")

    app.dependency_overrides[get_db_conn] = lambda: mock_conn
    app.dependency_overrides[require_session] = lambda: mock_session

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as c:
        yield c, mock_conn

    app.dependency_overrides.clear()


# acceptance #1: GET /api/v1/recommend/latest 라우트 등록
def test_t093_latest_route_registered():
    from app.main import app

    def _find(routes):
        for r in routes:
            if (
                getattr(r, "path", None) == "/api/v1/recommend/latest"
                and "GET" in getattr(r, "methods", set())
            ):
                return True
            if _find(getattr(r, "routes", [])):
                return True
        return False

    assert _find(app.routes), "GET /api/v1/recommend/latest 라우트 미등록"


# acceptance #2: 인증 헤더 없이 GET /api/v1/recommend/latest → 401
async def test_t093_get_latest_no_auth_returns_401(client: AsyncClient):
    resp = await client.get("/api/v1/recommend/latest")
    assert resp.status_code == 401


# acceptance #3: mock conn이 areas 3개 row 반환 → body.areas 길이 3
async def test_t093_get_latest_areas_length_3(latest_authed_client):
    c, mock_conn = latest_authed_client
    mock_conn.execute.return_value.mappings.return_value.first.return_value = _T093_ROW

    resp = await c.get("/api/v1/recommend/latest")

    assert resp.status_code == 200
    assert len(resp.json()["areas"]) == 3


# acceptance #4: body.match_id == row['id'] UUID 문자열
async def test_t093_get_latest_match_id_equals_row_id(latest_authed_client):
    c, mock_conn = latest_authed_client
    mock_conn.execute.return_value.mappings.return_value.first.return_value = _T093_ROW

    resp = await c.get("/api/v1/recommend/latest")

    assert resp.status_code == 200
    assert resp.json()["match_id"] == str(_T093_MATCH_ID)


# acceptance #5: 빈 결과 → status_code 200, body.areas == []
async def test_t093_get_latest_empty_result_returns_200_empty_areas(latest_authed_client):
    c, mock_conn = latest_authed_client
    mock_conn.execute.return_value.mappings.return_value.first.return_value = None

    resp = await c.get("/api/v1/recommend/latest")

    assert resp.status_code == 200
    assert resp.json()["areas"] == []


# acceptance #6: 빈 결과 → body.match_id is None
async def test_t093_get_latest_empty_result_match_id_is_none(latest_authed_client):
    c, mock_conn = latest_authed_client
    mock_conn.execute.return_value.mappings.return_value.first.return_value = None

    resp = await c.get("/api/v1/recommend/latest")

    assert resp.json()["match_id"] is None


# acceptance #7: conn.execute에 전달된 SQL에 ORDER BY, created_at DESC, LIMIT 1 포함
async def test_t093_sql_contains_order_by_created_at_desc_limit_1(latest_authed_client):
    c, mock_conn = latest_authed_client
    mock_conn.execute.return_value.mappings.return_value.first.return_value = None

    await c.get("/api/v1/recommend/latest")

    assert mock_conn.execute.called, "conn.execute 미호출"
    stmt = mock_conn.execute.call_args.args[0]
    sql = str(stmt)
    assert "ORDER BY" in sql, f"ORDER BY 없음: {sql!r}"
    assert "created_at DESC" in sql, f"created_at DESC 없음: {sql!r}"
    assert "LIMIT 1" in sql, f"LIMIT 1 없음: {sql!r}"


# acceptance #8: WHERE 절에 session_id, user_id, OR 포함
async def test_t093_sql_where_has_session_id_and_user_id_with_or(latest_authed_client):
    c, mock_conn = latest_authed_client
    mock_conn.execute.return_value.mappings.return_value.first.return_value = None

    await c.get("/api/v1/recommend/latest")

    stmt = mock_conn.execute.call_args.args[0]
    sql = str(stmt)
    assert "session_id" in sql, f"session_id 없음: {sql!r}"
    assert "user_id" in sql, f"user_id 없음: {sql!r}"
    assert "OR" in sql, f"OR 없음: {sql!r}"


# acceptance #9: (회귀) POST /api/v1/recommend → 200, body.areas list 유지
async def test_t093_post_recommend_regression_areas_is_list(authed_client: AsyncClient):
    with patch(
        "app.api.v1.recommend.recommend_service.recommend",
        new=AsyncMock(return_value={"areas": [_VALID_AREA], "match_id": None}),
    ):
        resp = await authed_client.post("/api/v1/recommend", json=VALID_PAYLOAD)

    assert resp.status_code == 200
    assert isinstance(resp.json()["areas"], list)
