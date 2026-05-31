import datetime
import uuid
from unittest.mock import AsyncMock, MagicMock

import pytest
from httpx import ASGITransport, AsyncClient

FIXED_SESSION_ID = uuid.UUID("11111111-1111-1111-1111-111111111111")
FIXED_USER_ID = uuid.UUID("22222222-2222-2222-2222-222222222222")
FIXED_EXPIRES_AT = datetime.datetime(2030, 1, 1, tzinfo=datetime.UTC)
EXPECTED_LOGIN_ERROR = "invalid email or password"

# T-023 상수
FIXED_EXTENDED_EXPIRES_AT = datetime.datetime(2026, 6, 25, tzinfo=datetime.UTC)
BEFORE_LOGIN_EXPIRES_AT = datetime.datetime(2026, 5, 26, tzinfo=datetime.UTC)
FIXED_TOKEN = "fixed-test-bearer-token-abc123"


# ── acceptance #1: app/api/v1/auth.py 존재 + router: APIRouter 인스턴스 ────────


def test_auth_module_router_is_apirouter():
    from fastapi import APIRouter

    from app.api.v1 import auth as auth_module

    assert isinstance(auth_module.router, APIRouter)


# ── acceptance #2: signup → POST /auth/signup ────────────────────────────────


def test_signup_routed_to_post_auth_signup():
    from app.api.v1 import auth as auth_module

    route = next(
        (r for r in auth_module.router.routes if r.path == "/signup" and "POST" in r.methods),
        None,
    )
    assert route is not None, "POST /signup route not found in auth.router"


# ── acceptance #3: login → POST /auth/login ──────────────────────────────────


def test_login_routed_to_post_auth_login():
    from app.api.v1 import auth as auth_module

    route = next(
        (r for r in auth_module.router.routes if r.path == "/login" and "POST" in r.methods),
        None,
    )
    assert route is not None, "POST /login route not found in auth.router"


# ── acceptance #4: logout → POST /auth/logout ────────────────────────────────


def test_logout_routed_to_post_auth_logout():
    from app.api.v1 import auth as auth_module

    route = next(
        (r for r in auth_module.router.routes if r.path == "/logout" and "POST" in r.methods),
        None,
    )
    assert route is not None, "POST /logout route not found in auth.router"


# ── acceptance #5: router.py가 auth.router include_router로 등록 ──────────────


def test_v1_router_includes_auth_routes():
    from app.api.v1 import router as router_module

    route_paths = {r.path for r in router_module.router.routes}
    assert any("/auth" in p for p in route_paths), (
        f"No /auth route in v1 router. Found: {route_paths}"
    )


# ── fixtures ─────────────────────────────────────────────────────────────────


@pytest.fixture
def mock_conn():
    conn = AsyncMock()
    mock_tx = AsyncMock()
    mock_tx.__aenter__ = AsyncMock(return_value=mock_tx)
    mock_tx.__aexit__ = AsyncMock(return_value=False)
    conn.begin = MagicMock(return_value=mock_tx)
    return conn


@pytest.fixture
async def auth_client(mock_conn, monkeypatch):
    """Client with mocked DB + session overridden to FIXED_SESSION_ID."""
    monkeypatch.setenv(
        "DATABASE_URL",
        "postgresql+asyncpg://postgres:postgres@localhost:5432/test",
    )
    from app.core.config import get_settings

    get_settings.cache_clear()

    from app.core import auth, deps
    from app.main import app

    async def override_get_db_conn():
        yield mock_conn

    async def override_require_session():
        from app.core.auth import SessionContext
        return SessionContext(session_id=FIXED_SESSION_ID, token=FIXED_TOKEN)

    app.dependency_overrides[deps.get_db_conn] = override_get_db_conn
    app.dependency_overrides[auth.require_session] = override_require_session

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as c:
        yield c, mock_conn

    app.dependency_overrides.clear()


@pytest.fixture
async def anon_client(mock_conn, monkeypatch):
    """Client with mocked DB but NO session override — tests unauthorized paths."""
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
        yield c

    app.dependency_overrides.clear()


# ── acceptance #6: 익명 세션 + 정상 SignupRequest → 201 ──────────────────────


async def test_signup_returns_201(auth_client, monkeypatch):
    from app.repositories.session import SessionRepository
    from app.repositories.users import UserRepository

    monkeypatch.setattr(UserRepository, "create", AsyncMock(return_value=FIXED_USER_ID))
    monkeypatch.setattr(SessionRepository, "set_user_id", AsyncMock())
    monkeypatch.setattr(
        SessionRepository,
        "get_expires_at",
        AsyncMock(return_value=FIXED_EXPIRES_AT),
        raising=False,
    )

    client, _ = auth_client
    resp = await client.post(
        "/api/v1/auth/signup",
        json={"email": "test@example.com", "password": "password123", "name": "Tester"},
    )
    assert resp.status_code == 201


# ── acceptance #7: signup 응답에 user.id, user.email, expires_at 모두 존재 ────


async def test_signup_response_has_user_id_email_expires_at(auth_client, monkeypatch):
    from app.repositories.session import SessionRepository
    from app.repositories.users import UserRepository

    monkeypatch.setattr(UserRepository, "create", AsyncMock(return_value=FIXED_USER_ID))
    monkeypatch.setattr(SessionRepository, "set_user_id", AsyncMock())
    monkeypatch.setattr(
        SessionRepository,
        "get_expires_at",
        AsyncMock(return_value=FIXED_EXPIRES_AT),
        raising=False,
    )

    client, _ = auth_client
    resp = await client.post(
        "/api/v1/auth/signup",
        json={"email": "test@example.com", "password": "password123", "name": "Tester"},
    )
    body = resp.json()
    assert "user" in body
    assert "id" in body["user"]
    assert "email" in body["user"]
    assert "expires_at" in body
    uuid.UUID(body["user"]["id"])  # must be valid UUID string


# ── acceptance #8: signup → users INSERT 시 email lowercase 저장 ──────────────


async def test_signup_stores_email_as_lowercase_in_db(auth_client, monkeypatch):
    from app.repositories.session import SessionRepository
    from app.repositories.users import UserRepository

    captured: dict = {}

    async def spy_create(self, email: str, password_hash: str, name: str) -> uuid.UUID:
        captured["email"] = email
        return FIXED_USER_ID

    monkeypatch.setattr(UserRepository, "create", spy_create)
    monkeypatch.setattr(SessionRepository, "set_user_id", AsyncMock())
    monkeypatch.setattr(
        SessionRepository,
        "get_expires_at",
        AsyncMock(return_value=FIXED_EXPIRES_AT),
        raising=False,
    )

    client, _ = auth_client
    resp = await client.post(
        "/api/v1/auth/signup",
        json={"email": "Test@Example.COM", "password": "password123", "name": "Tester"},
    )
    assert resp.status_code == 201
    assert captured["email"] == "test@example.com"


# ── acceptance #9: signup 성공 후 sessions.user_id가 새 user.id로 갱신 ─────────


async def test_signup_sets_session_user_id(auth_client, monkeypatch):
    from app.repositories.session import SessionRepository
    from app.repositories.users import UserRepository

    called_with: dict = {}

    async def spy_set_user_id(self, session_id: uuid.UUID, user_id: uuid.UUID) -> None:
        called_with["session_id"] = session_id
        called_with["user_id"] = user_id

    monkeypatch.setattr(UserRepository, "create", AsyncMock(return_value=FIXED_USER_ID))
    monkeypatch.setattr(SessionRepository, "set_user_id", spy_set_user_id)
    monkeypatch.setattr(
        SessionRepository,
        "get_expires_at",
        AsyncMock(return_value=FIXED_EXPIRES_AT),
        raising=False,
    )

    client, _ = auth_client
    await client.post(
        "/api/v1/auth/signup",
        json={"email": "test@example.com", "password": "password123", "name": "Tester"},
    )

    assert called_with.get("session_id") == FIXED_SESSION_ID
    assert called_with.get("user_id") == FIXED_USER_ID


# ── acceptance #10: signup → password_hash 평문 아님 + verify_password True ───


async def test_signup_stores_hashed_password_not_plaintext(auth_client, monkeypatch):
    from app.core.security import verify_password
    from app.repositories.session import SessionRepository
    from app.repositories.users import UserRepository

    captured: dict = {}
    raw_password = "password123"

    async def spy_create(self, email: str, password_hash: str, name: str) -> uuid.UUID:
        captured["password_hash"] = password_hash
        return FIXED_USER_ID

    monkeypatch.setattr(UserRepository, "create", spy_create)
    monkeypatch.setattr(SessionRepository, "set_user_id", AsyncMock())
    monkeypatch.setattr(
        SessionRepository,
        "get_expires_at",
        AsyncMock(return_value=FIXED_EXPIRES_AT),
        raising=False,
    )

    client, _ = auth_client
    resp = await client.post(
        "/api/v1/auth/signup",
        json={"email": "test@example.com", "password": raw_password, "name": "Tester"},
    )
    assert resp.status_code == 201
    assert captured["password_hash"] != raw_password
    assert verify_password(raw_password, captured["password_hash"])


# ── acceptance #11: 동일 email 두 번째 signup → 409 ──────────────────────────


async def test_signup_duplicate_email_returns_409(auth_client, monkeypatch):
    from sqlalchemy.exc import IntegrityError

    from app.repositories.users import UserRepository

    monkeypatch.setattr(
        UserRepository,
        "create",
        AsyncMock(side_effect=IntegrityError("", {}, Exception("unique constraint"))),
    )

    client, _ = auth_client
    resp = await client.post(
        "/api/v1/auth/signup",
        json={"email": "existing@example.com", "password": "password123", "name": "Tester"},
    )
    assert resp.status_code == 409


# ── acceptance #12: Authorization 헤더 없이 signup → 401 ─────────────────────


async def test_signup_without_auth_header_returns_401(anon_client):
    resp = await anon_client.post(
        "/api/v1/auth/signup",
        json={"email": "test@example.com", "password": "password123", "name": "Tester"},
    )
    assert resp.status_code == 401


# ── acceptance #13: password 7자 signup → 422 ─────────────────────────────────


async def test_signup_short_password_returns_422(auth_client):
    client, _ = auth_client
    resp = await client.post(
        "/api/v1/auth/signup",
        json={"email": "test@example.com", "password": "1234567", "name": "Tester"},  # 7자, min_length=8
    )
    assert resp.status_code == 422


# ── acceptance #14: 정상 login → 200 + user/expires_at 반환 ──────────────────


async def test_login_returns_200_with_user_and_expires_at(auth_client, monkeypatch):
    from app.core.security import hash_password
    from app.repositories.session import SessionRepository
    from app.repositories.users import UserRepository, UserRow

    stored_hash = hash_password("validpassword123")
    monkeypatch.setattr(
        UserRepository,
        "get_by_email",
        AsyncMock(return_value=UserRow(FIXED_USER_ID, "test@example.com", stored_hash, "Tester")),
    )
    monkeypatch.setattr(SessionRepository, "set_user_id", AsyncMock())
    monkeypatch.setattr(
        SessionRepository,
        "get_expires_at",
        AsyncMock(return_value=FIXED_EXPIRES_AT),
        raising=False,
    )

    client, _ = auth_client
    resp = await client.post(
        "/api/v1/auth/login",
        json={"email": "test@example.com", "password": "validpassword123"},
    )
    assert resp.status_code == 200
    body = resp.json()
    assert "user" in body
    assert "id" in body["user"]
    assert "email" in body["user"]
    assert "expires_at" in body


# ── acceptance #15: login 성공 후 sessions.user_id 갱신 ──────────────────────


async def test_login_sets_session_user_id(auth_client, monkeypatch):
    from app.core.security import hash_password
    from app.repositories.session import SessionRepository
    from app.repositories.users import UserRepository, UserRow

    stored_hash = hash_password("validpassword123")
    called_with: dict = {}

    async def spy_set_user_id(self, session_id: uuid.UUID, user_id: uuid.UUID) -> None:
        called_with["session_id"] = session_id
        called_with["user_id"] = user_id

    monkeypatch.setattr(
        UserRepository,
        "get_by_email",
        AsyncMock(return_value=UserRow(FIXED_USER_ID, "test@example.com", stored_hash, "Tester")),
    )
    monkeypatch.setattr(SessionRepository, "set_user_id", spy_set_user_id)
    monkeypatch.setattr(
        SessionRepository,
        "get_expires_at",
        AsyncMock(return_value=FIXED_EXPIRES_AT),
        raising=False,
    )

    client, _ = auth_client
    resp = await client.post(
        "/api/v1/auth/login",
        json={"email": "test@example.com", "password": "validpassword123"},
    )
    assert resp.status_code == 200
    assert called_with.get("session_id") == FIXED_SESSION_ID
    assert called_with.get("user_id") == FIXED_USER_ID


# ── acceptance #16: 없는 email로 login → 401 + generic 메시지 ────────────────


async def test_login_unknown_email_returns_401_with_generic_message(auth_client, monkeypatch):
    from app.repositories.users import UserRepository

    monkeypatch.setattr(UserRepository, "get_by_email", AsyncMock(return_value=None))

    client, _ = auth_client
    resp = await client.post(
        "/api/v1/auth/login",
        json={"email": "nobody@example.com", "password": "anypassword"},
    )
    assert resp.status_code == 401
    error_msg = resp.json().get("error", "")
    assert EXPECTED_LOGIN_ERROR in error_msg


# ── acceptance #17: 잘못된 password로 login → 401 + 동일 generic 메시지 ───────


async def test_login_wrong_password_returns_401_with_same_message(auth_client, monkeypatch):
    from app.core.security import hash_password
    from app.repositories.users import UserRepository, UserRow

    stored_hash = hash_password("correctpassword")
    monkeypatch.setattr(
        UserRepository,
        "get_by_email",
        AsyncMock(return_value=UserRow(FIXED_USER_ID, "test@example.com", stored_hash, "Tester")),
    )

    client, _ = auth_client
    resp = await client.post(
        "/api/v1/auth/login",
        json={"email": "test@example.com", "password": "wrongpassword"},
    )
    assert resp.status_code == 401
    error_msg = resp.json().get("error", "")
    assert EXPECTED_LOGIN_ERROR in error_msg


# ── acceptance #18: login email 대소문자 무시 ─────────────────────────────────


async def test_login_case_insensitive_email_matches(auth_client, monkeypatch):
    from app.core.security import hash_password
    from app.repositories.session import SessionRepository
    from app.repositories.users import UserRepository, UserRow

    stored_hash = hash_password("validpassword123")
    monkeypatch.setattr(
        UserRepository,
        "get_by_email",
        AsyncMock(return_value=UserRow(FIXED_USER_ID, "foo@bar.com", stored_hash, "Tester")),
    )
    monkeypatch.setattr(SessionRepository, "set_user_id", AsyncMock())
    monkeypatch.setattr(
        SessionRepository,
        "get_expires_at",
        AsyncMock(return_value=FIXED_EXPIRES_AT),
        raising=False,
    )

    client, _ = auth_client
    resp = await client.post(
        "/api/v1/auth/login",
        json={"email": "FOO@bar.COM", "password": "validpassword123"},
    )
    assert resp.status_code == 200


# ── acceptance #19: POST /api/v1/auth/logout → 204 + 빈 본문 ─────────────────


async def test_logout_returns_204_with_empty_body(auth_client, monkeypatch):
    from app.repositories.session import SessionRepository

    monkeypatch.setattr(SessionRepository, "clear_user_id", AsyncMock())

    client, _ = auth_client
    resp = await client.post("/api/v1/auth/logout")
    assert resp.status_code == 204
    assert resp.content == b""
def test_auth_response_schema_has_token_field():

    from app.schemas.auth import AuthResponse

    hints = {}
    try:
        hints = AuthResponse.__annotations__
    except AttributeError:
        import typing
        hints = typing.get_type_hints(AuthResponse)

    assert "token" in hints, (
        f"AuthResponse에 'token' 필드가 없음. 현재 필드: {list(hints.keys())}"
    )
    assert "user" in hints, "AuthResponse에 기존 'user' 필드 보존 필요"
    assert "expires_at" in hints, "AuthResponse에 기존 'expires_at' 필드 보존 필요"
async def test_logout_clear_user_id_called_with_session_context_session_id(
    auth_client, monkeypatch
):
    from app.repositories.session import SessionRepository

    called_with: dict = {}

    async def spy_clear(self, session_id: uuid.UUID) -> None:
        called_with["session_id"] = session_id

    monkeypatch.setattr(SessionRepository, "clear_user_id", spy_clear)

    client, _ = auth_client
    resp = await client.post("/api/v1/auth/logout")
    assert resp.status_code == 204
    assert called_with.get("session_id") == FIXED_SESSION_ID, (
        f"clear_user_id에 session.session_id={FIXED_SESSION_ID!r}가 전달되어야 함. "
        f"got: {called_with.get('session_id')!r}"
    )


# ── acceptance #20: logout 후 require_user 보호 라우트 → 401 ─────────────────


async def test_logout_then_require_user_protected_route_returns_401(monkeypatch):
    monkeypatch.setenv(
        "DATABASE_URL",
        "postgresql+asyncpg://postgres:postgres@localhost:5432/test",
    )
    from app.core.config import get_settings

    get_settings.cache_clear()

    from fastapi import FastAPI

    from app.core.auth import UserDep, require_session
    from app.core.deps import get_db_conn
    from app.core.exceptions import register_exception_handlers
    from app.repositories.session import SessionRepository

    test_app = FastAPI()
    register_exception_handlers(test_app)

    @test_app.get("/protected-test")
    async def _protected(user: UserDep):
        return {"ok": True}

    mock_conn = AsyncMock()
    mock_tx = AsyncMock()
    mock_tx.__aenter__ = AsyncMock(return_value=mock_tx)
    mock_tx.__aexit__ = AsyncMock(return_value=False)
    mock_conn.begin = MagicMock(return_value=mock_tx)

    async def override_get_db_conn():
        yield mock_conn

    async def override_require_session():
        from app.core.auth import SessionContext
        return SessionContext(session_id=FIXED_SESSION_ID, token=FIXED_TOKEN)

    test_app.dependency_overrides[get_db_conn] = override_get_db_conn
    test_app.dependency_overrides[require_session] = override_require_session

    # Simulate post-logout state: get_user_id returns None
    monkeypatch.setattr(SessionRepository, "get_user_id", AsyncMock(return_value=None))

    async with AsyncClient(transport=ASGITransport(app=test_app), base_url="http://test") as c:
        resp = await c.get("/protected-test")

    assert resp.status_code == 401
async def test_signup_without_name_returns_422(auth_client):
    client, _ = auth_client
    resp = await client.post(
        "/api/v1/auth/signup",
        json={"email": "test@example.com", "password": "password123"},
    )
    assert resp.status_code == 422, (
        f"name 누락 시 422이어야 함. got: {resp.status_code}"
    )
def test_auth_module_does_not_import_password_functions():
    import ast
    import pathlib

    auth_path = pathlib.Path(__file__).parents[3] / "app" / "api" / "v1" / "auth.py"
    tree = ast.parse(auth_path.read_text())

    forbidden = {"hash_password", "verify_password"}
    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom):
            names = {alias.name for alias in node.names}
            overlap = names & forbidden
            assert not overlap, (
                f"auth.py가 {overlap}을 import함 — auth_service로 위임되어야 함"
            )


# ── T-046 acceptance #2: auth.py에서 Repository imports 없음 ──────────────────


def test_auth_module_does_not_import_repositories():
    import ast
    import pathlib

    auth_path = pathlib.Path(__file__).parents[3] / "app" / "api" / "v1" / "auth.py"
    tree = ast.parse(auth_path.read_text())

    forbidden = {"UserRepository", "ProfileRepository", "SessionRepository"}
    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom):
            names = {alias.name for alias in node.names}
            overlap = names & forbidden
            assert not overlap, (
                f"auth.py가 {overlap}을 import함 — auth_service로 위임되어야 함"
            )


# ── T-046 acceptance #3: auth.py에서 IntegrityError import 없음 ──────────────


def test_auth_module_does_not_import_integrity_error():
    import ast
    import pathlib

    auth_path = pathlib.Path(__file__).parents[3] / "app" / "api" / "v1" / "auth.py"
    tree = ast.parse(auth_path.read_text())

    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom):
            names = {alias.name for alias in node.names}
            assert "IntegrityError" not in names, (
                "auth.py가 IntegrityError를 import함 — auth_service로 위임되어야 함"
            )


# ── T-046 acceptance #4: signup이 auth_service.register_user 호출 ─────────────


async def test_signup_calls_auth_service_register_user(auth_client, monkeypatch):
    import app.services.auth as _auth_svc

    mock_register = AsyncMock(return_value=(FIXED_USER_ID, FIXED_EXPIRES_AT))
    monkeypatch.setattr(_auth_svc, "register_user", mock_register)

    client, _ = auth_client
    resp = await client.post(
        "/api/v1/auth/signup",
        json={"email": "test@example.com", "password": "password123", "name": "Tester"},
    )

    mock_register.assert_called_once()
    assert resp.status_code == 201


# ── T-046 acceptance #5: login이 auth_service.login_user 호출 ───────────────


async def test_login_calls_auth_service_login_user(auth_client, monkeypatch):
    from types import SimpleNamespace

    import app.services.auth as _auth_svc

    mock_user = SimpleNamespace(id=FIXED_USER_ID, email="test@example.com", name="Tester")
    mock_login = AsyncMock(return_value=(mock_user, FIXED_EXPIRES_AT))
    monkeypatch.setattr(_auth_svc, "login_user", mock_login)

    client, _ = auth_client
    resp = await client.post(
        "/api/v1/auth/login",
        json={"email": "test@example.com", "password": "validpassword123"},
    )

    mock_login.assert_called_once()
    assert resp.status_code == 200


# ── T-046 acceptance #6: logout이 auth_service.logout_user 호출 ─────────────


async def test_logout_calls_auth_service_logout_user(auth_client, monkeypatch):
    import app.services.auth as _auth_svc

    mock_logout = AsyncMock(return_value=None)
    monkeypatch.setattr(_auth_svc, "logout_user", mock_logout)

    client, _ = auth_client
    resp = await client.post("/api/v1/auth/logout")

    mock_logout.assert_called_once()
    assert resp.status_code == 204


# ── T-046 acceptance #7: signup/login/logout 응답 스키마 회귀 (service mock 기준) ─


async def test_signup_201_auth_response_structure_with_service_mock(auth_client, monkeypatch):
    import app.services.auth as _auth_svc

    monkeypatch.setattr(
        _auth_svc, "register_user", AsyncMock(return_value=(FIXED_USER_ID, FIXED_EXPIRES_AT))
    )

    client, _ = auth_client
    resp = await client.post(
        "/api/v1/auth/signup",
        json={"email": "test@example.com", "password": "password123", "name": "Tester"},
    )
    assert resp.status_code == 201
    body = resp.json()
    assert set(body.keys()) == {"user", "expires_at", "token"}, (
        f"signup 응답 키 불일치: {set(body.keys())}"
    )
    assert {"id", "email", "name"} <= set(body["user"].keys()), (
        f"signup 응답 user 키 불일치: {set(body['user'].keys())}"
    )


async def test_login_200_auth_response_structure_with_service_mock(auth_client, monkeypatch):
    from types import SimpleNamespace

    import app.services.auth as _auth_svc

    mock_user = SimpleNamespace(id=FIXED_USER_ID, email="test@example.com", name="Tester")
    monkeypatch.setattr(
        _auth_svc, "login_user", AsyncMock(return_value=(mock_user, FIXED_EXPIRES_AT))
    )

    client, _ = auth_client
    resp = await client.post(
        "/api/v1/auth/login",
        json={"email": "test@example.com", "password": "validpassword123"},
    )
    assert resp.status_code == 200
    body = resp.json()
    assert set(body.keys()) == {"user", "expires_at", "token"}, (
        f"login 응답 키 불일치: {set(body.keys())}"
    )
    assert {"id", "email", "name"} <= set(body["user"].keys()), (
        f"login 응답 user 키 불일치: {set(body['user'].keys())}"
    )


async def test_logout_204_empty_body_with_service_mock(auth_client, monkeypatch):
    import app.services.auth as _auth_svc

    monkeypatch.setattr(_auth_svc, "logout_user", AsyncMock(return_value=None))

    client, _ = auth_client
    resp = await client.post("/api/v1/auth/logout")
    assert resp.status_code == 204
    assert resp.content == b""
