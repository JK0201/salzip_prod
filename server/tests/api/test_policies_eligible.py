"""tests/api/test_policies_eligible.py — T-090: eligible 라우터+등록."""

import uuid
from unittest.mock import AsyncMock, patch

import pytest
from httpx import ASGITransport, AsyncClient

from app.schemas.policy_eligible import EligiblePolicy, PoliciesEligibleResponse

_FAKE_RESPONSE = PoliciesEligibleResponse(
    policies=[
        EligiblePolicy(
            id=uuid.uuid4(),
            name="청년 월세 지원",
            card_key="monthly",
            support_type="월세",
            monthly_amount_wan=20,
            loan_limit=None,
            duration_months=12,
            agency_name="서울시",
            apply_url="https://example.com",
        )
    ]
)


# ── fixtures ──────────────────────────────────────────────────────────────────


@pytest.fixture
async def unauthed_client(monkeypatch):
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
async def authed_client(monkeypatch):
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
    mock_session = SessionContext(session_id=uuid.uuid4(), token="test-token")

    app.dependency_overrides[get_db_conn] = lambda: mock_conn
    app.dependency_overrides[require_session] = lambda: mock_session

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as c:
        yield c, mock_session

    app.dependency_overrides.clear()


# ── acceptance #1: GET /api/v1/policies/eligible 라우트 등록됨 ────────────────


def test_get_policies_eligible_route_registered_in_app(monkeypatch):
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
            and r.path == "/api/v1/policies/eligible"
            and hasattr(r, "methods")
            and "GET" in r.methods
        ),
        None,
    )
    assert route is not None, "GET /api/v1/policies/eligible 라우트가 app.routes에 없음"


# ── acceptance #2: Authorization 헤더 없이 호출 시 401 ───────────────────────


async def test_get_policies_eligible_no_auth_returns_401(unauthed_client):
    resp = await unauthed_client.get("/api/v1/policies/eligible")
    assert resp.status_code == 401, (
        f"Authorization 헤더 없이 호출 시 401 기대. got: {resp.status_code}"
    )


# ── acceptance #3: 응답 body에 policies 키 보유 ───────────────────────────────


async def test_get_policies_eligible_response_has_policies_key(authed_client):
    client, _ = authed_client
    with patch(
        "app.api.v1.policies_eligible.policies_service.eligible_policies",
        new=AsyncMock(return_value=_FAKE_RESPONSE),
    ):
        resp = await client.get("/api/v1/policies/eligible")

    assert resp.status_code == 200, f"200 기대. got: {resp.status_code}"
    body = resp.json()
    assert "policies" in body, f"응답에 policies 키 없음. keys: {list(body.keys())}"
    assert isinstance(body["policies"], list), "policies는 list여야 함"


# ── acceptance #4: 핸들러가 policies_service.eligible_policies(session.session_id, conn) 호출 ──


async def test_get_policies_eligible_calls_service_with_session_id(authed_client):
    client, mock_session = authed_client
    mock_service = AsyncMock(return_value=_FAKE_RESPONSE)

    with patch(
        "app.api.v1.policies_eligible.policies_service.eligible_policies",
        new=mock_service,
    ):
        resp = await client.get("/api/v1/policies/eligible")

    assert resp.status_code == 200, f"200 기대. got: {resp.status_code}"
    assert mock_service.called, "policies_service.eligible_policies가 호출되지 않음"

    call_args = mock_service.call_args
    pos_args = call_args.args
    kwargs = call_args.kwargs

    session_id_passed = (
        len(pos_args) >= 1 and pos_args[0] == mock_session.session_id
    ) or kwargs.get("session_id") == mock_session.session_id

    assert session_id_passed, (
        f"session_id={mock_session.session_id}가 첫 번째 인자로 전달되지 않음. "
        f"args={pos_args}, kwargs={kwargs}"
    )


# ── acceptance #5: main.py에 기존 policies_preview 라우터 등록 라인 유지 (회귀) ──


def test_main_py_policies_preview_router_registration_line_unchanged():
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

    preview_includes = [
        call
        for call in include_calls
        for arg in call.args
        if isinstance(arg, ast.Attribute)
        and arg.attr == "router"
        and isinstance(arg.value, ast.Name)
        and "policies_preview" in arg.value.id
    ]

    assert len(preview_includes) >= 1, (
        "main.py에서 policies_preview_router.router include_router 라인이 사라짐"
    )


# ── acceptance #6: 기존 GET /api/v1/policies/preview 경로 여전히 등록됨 (회귀) ──


def test_get_policies_preview_route_still_registered(monkeypatch):
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
    assert route is not None, "GET /api/v1/policies/preview 라우트가 app.routes에서 사라짐 (회귀)"
