import datetime
import inspect
import uuid
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from httpx import ASGITransport, AsyncClient


# ── acceptance #1: SessionCreateResponse 클래스 존재 + BaseModel 상속 ──────────


def test_session_create_response_class_exists_and_inherits_base_model():
    from pydantic import BaseModel

    from app.schemas.session import SessionCreateResponse

    assert issubclass(SessionCreateResponse, BaseModel)


# ── acceptance #2: token: str 필드 ────────────────────────────────────────────


def test_session_create_response_token_field_is_str():
    from app.schemas.session import SessionCreateResponse

    fields = SessionCreateResponse.model_fields
    assert "token" in fields
    assert fields["token"].annotation is str


# ── acceptance #3: expires_at: datetime 필드 ──────────────────────────────────


def test_session_create_response_expires_at_field_is_datetime():
    from app.schemas.session import SessionCreateResponse

    fields = SessionCreateResponse.model_fields
    assert "expires_at" in fields
    assert fields["expires_at"].annotation is datetime.datetime


# ── acceptance #4: router 객체 = APIRouter 인스턴스 ───────────────────────────


def test_session_module_router_is_apirouter():
    from fastapi import APIRouter

    from app.api.v1 import session as session_module

    assert isinstance(session_module.router, APIRouter)


# ── acceptance #5: create_session async 함수 존재 ─────────────────────────────


def test_create_session_is_async_function():
    from app.api.v1.session import create_session

    assert inspect.iscoroutinefunction(create_session)


# ── acceptance #6: POST /session 경로에 라우팅 ────────────────────────────────


def test_create_session_routed_to_post_slash_session():
    from app.api.v1 import session as session_module

    post_route = next(
        (
            r
            for r in session_module.router.routes
            if r.path == "/session" and "POST" in r.methods
        ),
        None,
    )
    assert post_route is not None, "POST /session route not found in session.router"


# ── acceptance #7: router.py가 session.router를 include_router로 등록 ──────────


def test_main_v1_router_includes_session_routes():
    from app.api.v1 import router as router_module

    route_paths = {r.path for r in router_module.router.routes}
    assert any(
        "/session" in p for p in route_paths
    ), f"No /session route in v1 router. Found: {route_paths}"


# ── fixture: mocked DB + api client ───────────────────────────────────────────


@pytest.fixture
def mock_conn():
    conn = AsyncMock()
    mock_result = MagicMock()
    mock_result.scalar_one.return_value = uuid.uuid4()
    conn.execute = AsyncMock(return_value=mock_result)

    mock_tx = AsyncMock()
    mock_tx.__aenter__ = AsyncMock(return_value=mock_tx)
    mock_tx.__aexit__ = AsyncMock(return_value=False)
    conn.begin = MagicMock(return_value=mock_tx)
    return conn


@pytest.fixture
async def api_client(mock_conn, monkeypatch):
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


# ── acceptance #8, #15: POST /api/v1/session → 201 + 본문 키 검증 ─────────────


async def test_post_session_returns_201(api_client):
    client, _ = api_client
    resp = await client.post("/api/v1/session")
    assert resp.status_code == 201


# ── acceptance #9, #15: 응답 본문에 token 키 (비어있지 않은 문자열) ─────────────


async def test_post_session_response_token_is_non_empty_string(api_client):
    client, _ = api_client
    resp = await client.post("/api/v1/session")
    body = resp.json()
    assert "token" in body
    assert isinstance(body["token"], str)
    assert len(body["token"]) > 0


# ── acceptance #10, #15: 응답 본문에 expires_at (ISO8601 파싱 가능) ───────────


async def test_post_session_response_expires_at_is_iso8601(api_client):
    client, _ = api_client
    resp = await client.post("/api/v1/session")
    body = resp.json()
    assert "expires_at" in body
    parsed = datetime.datetime.fromisoformat(body["expires_at"])
    assert parsed is not None


# ── acceptance #11, #16: 두 번 호출 시 서로 다른 token ───────────────────────


async def test_two_calls_return_different_tokens(api_client):
    client, _ = api_client
    resp1 = await client.post("/api/v1/session")
    resp2 = await client.post("/api/v1/session")
    assert resp1.status_code == 201
    assert resp2.status_code == 201
    assert resp1.json()["token"] != resp2.json()["token"]


# ── acceptance #12: expires_at ≈ now + SESSION_TTL_DAYS (오차 60초) ───────────


async def test_expires_at_within_60s_of_ttl(api_client):
    from app.core.config import get_settings

    settings = get_settings()
    client, _ = api_client

    before = datetime.datetime.now(datetime.timezone.utc)
    resp = await client.post("/api/v1/session")
    after = datetime.datetime.now(datetime.timezone.utc)

    body = resp.json()
    expires_at = datetime.datetime.fromisoformat(body["expires_at"])
    if expires_at.tzinfo is None:
        expires_at = expires_at.replace(tzinfo=datetime.timezone.utc)

    expected_low = before + datetime.timedelta(days=settings.SESSION_TTL_DAYS)
    expected_high = after + datetime.timedelta(days=settings.SESSION_TTL_DAYS)

    assert expected_low <= expires_at <= expected_high + datetime.timedelta(seconds=60)


# ── acceptance #13, #17: hash_session_token(token)이 sessions에 INSERT됨 ──────


async def test_token_hash_written_to_sessions_table(api_client, monkeypatch):
    from app.core.security import hash_session_token
    from app.repositories.session import SessionRepository

    client, _ = api_client
    captured_hashes: list[str] = []
    original_create = SessionRepository.create

    async def spy_create(self, token_hash: str, expires_at: datetime.datetime):
        captured_hashes.append(token_hash)
        return uuid.uuid4()

    monkeypatch.setattr(SessionRepository, "create", spy_create)

    resp = await client.post("/api/v1/session")
    assert resp.status_code == 201

    token = resp.json()["token"]
    expected_hash = hash_session_token(token)

    assert len(captured_hashes) == 1, "SessionRepository.create not called exactly once"
    assert captured_hashes[0] == expected_hash, (
        f"DB에 저장된 hash {captured_hashes[0]!r} != "
        f"expected hash_session_token(token) {expected_hash!r}"
    )
