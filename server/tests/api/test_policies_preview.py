import uuid
from unittest.mock import AsyncMock, MagicMock

import pytest
from httpx import ASGITransport, AsyncClient


# ── acceptance #1: router import + APIRouter 인스턴스 ─────────────────────────


def test_policies_preview_router_is_apirouter():
    from fastapi import APIRouter

    from app.api.v1.policies_preview import router

    assert isinstance(router, APIRouter)


# ── acceptance #2: router에 GET /policies/preview 라우트 존재 ─────────────────


def test_router_has_get_policies_preview_route():
    from app.api.v1.policies_preview import router

    route = next(
        (r for r in router.routes if r.path == "/policies/preview" and "GET" in r.methods),
        None,
    )
    assert route is not None, "GET /policies/preview route not found in policies_preview.router"


# ── acceptance #3: main.py가 policies_preview 라우터를 prefix='/api/v1'로 include ─


def test_main_app_has_get_api_v1_policies_preview_route(monkeypatch):
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
            and r.path == "/api/v1/policies/preview"
            and hasattr(r, "methods")
            and "GET" in r.methods
        ),
        None,
    )
    assert route is not None, "GET /api/v1/policies/preview route not found in main app"


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

    prefixes = []
    for call in include_calls:
        for kw in call.keywords:
            if kw.arg == "prefix" and isinstance(kw.value, ast.Constant):
                prefixes.append(kw.value.value)

    assert any("/api/v1" in p for p in prefixes), (
        f"prefix='/api/v1' include_router 라인 없음. found prefixes: {prefixes}"
    )


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
async def preview_client(mock_conn, monkeypatch):
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


def _make_fake_rows():
    """card_key=monthly 2건, card_key=jeonse 1건, card_key=NULL 1건"""

    class FakeRow:
        def __init__(self, card_key, monthly_amount_wan, loan_limit):
            self.id = uuid.uuid4()
            self.name = f"지원사업_{card_key}"
            self.card_key = card_key
            self.support_type = "월세"
            self.monthly_amount_wan = monthly_amount_wan
            self.loan_limit = loan_limit
            self.duration_months = 12
            self.agency_name = "기관"
            self.apply_url = "https://example.com"

    return [
        FakeRow("monthly", 100, 500),
        FakeRow("monthly", 200, 300),
        FakeRow("jeonse", None, 1000),
        FakeRow(None, 50, None),
    ]


# ── acceptance #4: 정상 파라미터 → 200 + PolicyPreviewResponse 스키마 ─────────


async def test_policies_preview_returns_200_with_valid_params(preview_client):
    rows = _make_fake_rows()
    mock_result = MagicMock()
    mock_result.__iter__ = MagicMock(return_value=iter(rows))

    client, mock_conn = preview_client
    mock_conn.execute = AsyncMock(return_value=mock_result)

    resp = await client.get(
        "/api/v1/policies/preview",
        params={"deposit_max_wan": 1000, "monthly_rent_max_wan": 50},
    )
    assert resp.status_code == 200
    body = resp.json()
    assert "by_card" in body, "응답에 by_card 없음"
    assert "summary" in body, "응답에 summary 없음"
    summary = body["summary"]
    assert "total_matched" in summary
    assert "max_monthly_support_wan" in summary
    assert "max_loan_limit_wan" in summary


# ── acceptance #5: deposit_max_wan 누락 → 422 ────────────────────────────────


async def test_policies_preview_missing_deposit_max_wan_returns_422(preview_client):
    client, _ = preview_client
    resp = await client.get(
        "/api/v1/policies/preview",
        params={"monthly_rent_max_wan": 50},
    )
    assert resp.status_code == 422, f"deposit_max_wan 누락 시 422 기대. got: {resp.status_code}"


# ── acceptance #6: monthly_rent_max_wan 누락 → 422 ───────────────────────────


async def test_policies_preview_missing_monthly_rent_max_wan_returns_422(preview_client):
    client, _ = preview_client
    resp = await client.get(
        "/api/v1/policies/preview",
        params={"deposit_max_wan": 1000},
    )
    assert resp.status_code == 422, f"monthly_rent_max_wan 누락 시 422 기대. got: {resp.status_code}"


# ── acceptance #7: by_card 그룹핑 (monthly=2, jeonse=1, other=1) ─────────────


async def test_policies_preview_by_card_grouping(preview_client):
    rows = _make_fake_rows()
    mock_result = MagicMock()
    mock_result.__iter__ = MagicMock(return_value=iter(rows))

    client, mock_conn = preview_client
    mock_conn.execute = AsyncMock(return_value=mock_result)

    resp = await client.get(
        "/api/v1/policies/preview",
        params={"deposit_max_wan": 1000, "monthly_rent_max_wan": 50},
    )
    assert resp.status_code == 200
    by_card = resp.json()["by_card"]

    assert len(by_card.get("monthly", [])) == 2, (
        f"monthly 길이=2 기대. got: {len(by_card.get('monthly', []))}"
    )
    assert len(by_card.get("jeonse", [])) == 1, (
        f"jeonse 길이=1 기대. got: {len(by_card.get('jeonse', []))}"
    )
    assert len(by_card.get("other", [])) == 1, (
        f"card_key=NULL → 'other' 키로 분류, 길이=1 기대. got: {len(by_card.get('other', []))}"
    )


# ── acceptance #8: summary 필드 값 검증 ──────────────────────────────────────


async def test_policies_preview_summary_fields(preview_client):
    rows = _make_fake_rows()
    mock_result = MagicMock()
    mock_result.__iter__ = MagicMock(return_value=iter(rows))

    client, mock_conn = preview_client
    mock_conn.execute = AsyncMock(return_value=mock_result)

    resp = await client.get(
        "/api/v1/policies/preview",
        params={"deposit_max_wan": 1000, "monthly_rent_max_wan": 50},
    )
    assert resp.status_code == 200
    summary = resp.json()["summary"]

    # total_matched = 전체 row 수
    assert summary["total_matched"] == 4, (
        f"total_matched=4 기대. got: {summary['total_matched']}"
    )
    # max_monthly_support_wan = max(100, 200, None→skip, 50) = 200
    assert summary["max_monthly_support_wan"] == 200, (
        f"max_monthly_support_wan=200 기대. got: {summary['max_monthly_support_wan']}"
    )
    # max_loan_limit_wan = max(500, 300, 1000, None→skip) = 1000
    assert summary["max_loan_limit_wan"] == 1000, (
        f"max_loan_limit_wan=1000 기대. got: {summary['max_loan_limit_wan']}"
    )


# ── acceptance #9: SQL WHERE에 rent_limit, deposit_limit 포함 ─────────────────


async def test_policies_preview_sql_contains_rent_and_deposit_limit(preview_client):
    captured_stmts: list = []

    rows = _make_fake_rows()
    mock_result = MagicMock()
    mock_result.__iter__ = MagicMock(return_value=iter(rows))

    async def capture_execute(stmt, *args, **kwargs):
        captured_stmts.append(stmt)
        return mock_result

    client, mock_conn = preview_client
    mock_conn.execute = capture_execute

    await client.get(
        "/api/v1/policies/preview",
        params={"deposit_max_wan": 1000, "monthly_rent_max_wan": 50},
    )

    assert len(captured_stmts) == 1, f"execute 1번 호출 기대. got: {len(captured_stmts)}"
    stmt = captured_stmts[0]

    compiled = stmt.compile(compile_kwargs={"literal_binds": True})
    sql_text = str(compiled).lower()

    assert "rent_limit" in sql_text, (
        f"rent_limit이 SQL WHERE에 없음. SQL: {sql_text}"
    )
    assert "deposit_limit" in sql_text, (
        f"deposit_limit이 SQL WHERE에 없음. SQL: {sql_text}"
    )
