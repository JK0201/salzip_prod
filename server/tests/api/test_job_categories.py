import uuid
from unittest.mock import AsyncMock, MagicMock

import pytest
from httpx import ASGITransport, AsyncClient


# ── acceptance #1: router import + APIRouter 인스턴스 ─────────────────────────


def test_job_categories_router_is_apirouter():
    from fastapi import APIRouter

    from app.api.v1.job_categories import router

    assert isinstance(router, APIRouter)


# ── acceptance #2: router에 GET /job_categories 라우트 존재 ───────────────────


def test_router_has_get_job_categories_route():
    from app.api.v1.job_categories import router

    route = next(
        (r for r in router.routes if r.path == "/job_categories" and "GET" in r.methods),
        None,
    )
    assert route is not None, "GET /job_categories route not found in job_categories.router"


# ── acceptance #3: main.app에 GET /api/v1/job_categories 라우트 존재 ──────────


def test_main_app_has_get_api_v1_job_categories_route(monkeypatch):
    monkeypatch.setenv(
        "DATABASE_URL",
        "postgresql+asyncpg://postgres:postgres@localhost:5432/test",
    )
    from app.core.config import get_settings

    get_settings.cache_clear()

    from app.main import app

    route = next(
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
    assert route is not None, "GET /api/v1/job_categories route not found in main app"


# ── fixtures ──────────────────────────────────────────────────────────────────


@pytest.fixture
def mock_conn():
    conn = AsyncMock()
    mock_tx = AsyncMock()
    mock_tx.__aenter__ = AsyncMock(return_value=mock_tx)
    mock_tx.__aexit__ = AsyncMock(return_value=False)
    conn.begin = MagicMock(return_value=mock_tx)
    return conn


@pytest.fixture
async def job_cat_client(mock_conn, monkeypatch):
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


# ── acceptance #4: Authorization 헤더 없이 GET → 200 ─────────────────────────


async def test_get_job_categories_returns_200_without_auth(job_cat_client):
    FIXED_ID = uuid.uuid4()

    class FakeRow:
        id = FIXED_ID
        name = "개발"

    mock_result = MagicMock()
    mock_result.__iter__ = MagicMock(return_value=iter([FakeRow()]))

    client, mock_conn = job_cat_client
    mock_conn.execute = AsyncMock(return_value=mock_result)

    resp = await client.get("/api/v1/job_categories")
    assert resp.status_code == 200


# ── acceptance #5: 응답 body가 list + 각 항목에 id(UUID 문자열)·name 두 키만 ──


async def test_get_job_categories_response_body_shape(job_cat_client):
    FIXED_ID = uuid.uuid4()

    class FakeRow:
        id = FIXED_ID
        name = "디자인"

    mock_result = MagicMock()
    mock_result.__iter__ = MagicMock(return_value=iter([FakeRow(), FakeRow()]))

    client, mock_conn = job_cat_client
    mock_conn.execute = AsyncMock(return_value=mock_result)

    resp = await client.get("/api/v1/job_categories")
    body = resp.json()

    assert isinstance(body, list)
    for item in body:
        assert set(item.keys()) == {"id", "name"}, (
            f"항목 키가 id·name만이어야 함. got: {set(item.keys())}"
        )
        uuid.UUID(item["id"])  # UUID 형식 문자열 검증
        assert isinstance(item["name"], str)


# ── acceptance #6: SQL stmt에 order_by(sort_order) 포함 검증 ─────────────────


async def test_get_job_categories_stmt_has_order_by_sort_order(job_cat_client):
    import sqlalchemy as sa

    captured_stmts: list = []

    class FakeRow:
        id = uuid.uuid4()
        name = "기획"

    mock_result = MagicMock()
    mock_result.__iter__ = MagicMock(return_value=iter([FakeRow()]))

    async def capture_execute(stmt, *args, **kwargs):
        captured_stmts.append(stmt)
        return mock_result

    client, mock_conn = job_cat_client
    mock_conn.execute = capture_execute

    await client.get("/api/v1/job_categories")

    assert len(captured_stmts) == 1, "execute가 정확히 1번 호출되어야 함"
    stmt = captured_stmts[0]

    compiled = stmt.compile(compile_kwargs={"literal_binds": True})
    sql_text = str(compiled).lower()

    assert "order by" in sql_text, f"ORDER BY 절 없음. SQL: {sql_text}"
    assert "sort_order" in sql_text, f"sort_order 컬럼이 ORDER BY에 없음. SQL: {sql_text}"


# ── acceptance #7: main.py의 기존 라우터 include 라인 보존 ───────────────────


def test_main_py_existing_router_includes_unchanged():
    import ast
    import pathlib

    main_path = pathlib.Path(__file__).parents[2] / "app" / "main.py"
    tree = ast.parse(main_path.read_text())

    include_calls = [
        node
        for node in ast.walk(tree)
        if isinstance(node, ast.Call)
        and isinstance(node.func, ast.Attribute)
        and node.func.attr == "include_router"
    ]

    # 기존 v1_router include 라인 보존 확인
    v1_router_includes = [
        call
        for call in include_calls
        if any(
            (isinstance(arg, ast.Attribute) and arg.attr == "router")
            or (isinstance(arg, ast.Name) and arg.id == "v1_router")
            for arg in call.args
        )
    ]
    assert len(v1_router_includes) >= 1, (
        "main.py에서 기존 v1_router include_router 라인이 사라짐"
    )

    # job_categories 라우터 추가 라인 존재 확인
    prefixes = []
    for call in include_calls:
        for kw in call.keywords:
            if kw.arg == "prefix" and isinstance(kw.value, ast.Constant):
                prefixes.append(kw.value.value)

    assert any("/api/v1" in p for p in prefixes), (
        f"job_categories 라우터의 prefix='/api/v1' include_router 라인 없음. "
        f"found prefixes: {prefixes}"
    )
