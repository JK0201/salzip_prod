import uuid
from unittest.mock import AsyncMock, MagicMock

import pytest
from httpx import ASGITransport, AsyncClient


# ── acceptance #1: router import + APIRouter 인스턴스 ─────────────────────────


def test_lifestyle_tags_router_is_apirouter():
    from fastapi import APIRouter

    from app.api.v1.lifestyle_tags import router

    assert isinstance(router, APIRouter)


# ── acceptance #2: router에 GET /lifestyle_tags 라우트 1개 등록 ───────────────


def test_router_has_get_lifestyle_tags_route():
    from app.api.v1.lifestyle_tags import router

    matching = [
        r
        for r in router.routes
        if r.path == "/lifestyle_tags" and "GET" in r.methods
    ]
    assert len(matching) == 1, (
        f"GET /lifestyle_tags route가 정확히 1개여야 함. found: {len(matching)}"
    )


# ── fixtures ──────────────────────────────────────────────────────────────────


class FakeRow:
    def __init__(self, row_id: uuid.UUID, name: str):
        self._mapping = {"id": row_id, "name": name}


@pytest.fixture
def mock_conn():
    conn = AsyncMock()
    mock_tx = AsyncMock()
    mock_tx.__aenter__ = AsyncMock(return_value=mock_tx)
    mock_tx.__aexit__ = AsyncMock(return_value=False)
    conn.begin = MagicMock(return_value=mock_tx)
    return conn


@pytest.fixture
async def lifestyle_client(mock_conn, monkeypatch):
    monkeypatch.setenv(
        "DATABASE_URL",
        "postgresql+asyncpg://postgres:postgres@localhost:5432/test",
    )
    from app.core.config import get_settings

    get_settings.cache_clear()

    from app.core import deps
    from app.main import app

    async def override_get_db_conn():
        yield mock_conn

    app.dependency_overrides[deps.get_db_conn] = override_get_db_conn

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as c:
        yield c, mock_conn

    app.dependency_overrides.clear()


def make_8_rows() -> list[FakeRow]:
    return [FakeRow(uuid.uuid4(), f"태그{i}") for i in range(8)]


# ── acceptance #3: mock conn 8개 row → status 200 ────────────────────────────


async def test_get_lifestyle_tags_returns_200_with_8_rows(lifestyle_client):
    rows = make_8_rows()
    mock_result = MagicMock()
    mock_result.__iter__ = MagicMock(return_value=iter(rows))

    client, mock_conn = lifestyle_client
    mock_conn.execute = AsyncMock(return_value=mock_result)

    resp = await client.get("/api/v1/lifestyle_tags")
    assert resp.status_code == 200


# ── acceptance #4: 응답 body가 list 타입이고 길이 8 ───────────────────────────


async def test_get_lifestyle_tags_response_body_length_8(lifestyle_client):
    rows = make_8_rows()
    mock_result = MagicMock()
    mock_result.__iter__ = MagicMock(return_value=iter(rows))

    client, mock_conn = lifestyle_client
    mock_conn.execute = AsyncMock(return_value=mock_result)

    resp = await client.get("/api/v1/lifestyle_tags")
    body = resp.json()

    assert isinstance(body, list), f"응답 body가 list여야 함. got: {type(body)}"
    assert len(body) == 8, f"길이 8이어야 함. got: {len(body)}"


# ── acceptance #5: 각 항목 키 정확히 {'id','name'} ───────────────────────────


async def test_get_lifestyle_tags_response_item_keys_exactly_id_name(lifestyle_client):
    rows = make_8_rows()
    mock_result = MagicMock()
    mock_result.__iter__ = MagicMock(return_value=iter(rows))

    client, mock_conn = lifestyle_client
    mock_conn.execute = AsyncMock(return_value=mock_result)

    resp = await client.get("/api/v1/lifestyle_tags")
    body = resp.json()

    for item in body:
        assert set(item.keys()) == {"id", "name"}, (
            f"키 집합이 정확히 {{'id','name'}}이어야 함. "
            f"categories/is_inverse 키 불허. got: {set(item.keys())}"
        )
        uuid.UUID(item["id"])  # UUID 형식 검증
        assert isinstance(item["name"], str)


# ── acceptance #6: SQL에 ORDER BY sort_order 포함 ────────────────────────────


async def test_get_lifestyle_tags_stmt_has_order_by_sort_order(lifestyle_client):
    captured_stmts: list = []

    rows = [FakeRow(uuid.uuid4(), "태그A")]
    mock_result = MagicMock()
    mock_result.__iter__ = MagicMock(return_value=iter(rows))

    async def capture_execute(stmt, *args, **kwargs):
        captured_stmts.append(stmt)
        return mock_result

    client, mock_conn = lifestyle_client
    mock_conn.execute = capture_execute

    await client.get("/api/v1/lifestyle_tags")

    assert len(captured_stmts) == 1, "execute가 정확히 1번 호출되어야 함"
    stmt = captured_stmts[0]

    compiled = stmt.compile(compile_kwargs={"literal_binds": True})
    sql_text = str(compiled).lower()

    assert "order by" in sql_text, f"ORDER BY 절 없음. SQL: {sql_text}"
    assert "sort_order" in sql_text, f"sort_order가 ORDER BY에 없음. SQL: {sql_text}"


# ── acceptance #7: 인증 헤더 없이도 200 (인증 의존성 없음) ───────────────────


async def test_get_lifestyle_tags_returns_200_without_auth_header(lifestyle_client):
    rows = [FakeRow(uuid.uuid4(), "태그X")]
    mock_result = MagicMock()
    mock_result.__iter__ = MagicMock(return_value=iter(rows))

    client, mock_conn = lifestyle_client
    mock_conn.execute = AsyncMock(return_value=mock_result)

    # Authorization 헤더 명시적으로 제외
    resp = await client.get("/api/v1/lifestyle_tags")
    assert resp.status_code == 200, (
        f"인증 헤더 없이도 200이어야 함 (Depends에 토큰 검증 없음). got: {resp.status_code}"
    )


# ── acceptance #8: 기존 job_categories 라우터 main.py에서 유지 ───────────────


def test_main_py_job_categories_router_still_registered(monkeypatch):
    monkeypatch.setenv(
        "DATABASE_URL",
        "postgresql+asyncpg://postgres:postgres@localhost:5432/test",
    )
    from app.core.config import get_settings

    get_settings.cache_clear()

    from app.main import app

    job_cat_route = next(
        (
            r
            for r in app.routes
            if hasattr(r, "path")
            and r.path == "/api/v1/job_categories"
            and hasattr(r, "methods")
            and "GET" in r.methods
        ),
        None,
    )
    assert job_cat_route is not None, (
        "main.py에서 GET /api/v1/job_categories 라우트가 사라짐 — "
        "lifestyle_tags 추가 후에도 기존 job_categories 라우터 유지 필요"
    )
