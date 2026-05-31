import asyncio
import uuid
from typing import get_args
from unittest.mock import AsyncMock, MagicMock, patch


def _make_request(auth_header: str | None) -> MagicMock:
    req = MagicMock()
    req.headers.get = MagicMock(return_value=auth_header)
    return req


async def _invoke(
    auth_header: str | None,
    get_active_result: uuid.UUID | None,
) -> uuid.UUID:
    from app.core.auth import require_session

    req = _make_request(auth_header)
    mock_conn = MagicMock()

    with patch("app.core.auth.SessionRepository") as MockRepo:
        MockRepo.return_value.get_active = AsyncMock(return_value=get_active_result)
        return await require_session(request=req, conn=mock_conn)


# acceptance #4: require_session 존재 (async)
def test_require_session_is_async():
    from app.core.auth import require_session

    assert asyncio.iscoroutinefunction(require_session)


# acceptance #5: SessionDep export
def test_session_dep_exported():
    from app.core.auth import SessionContext, SessionDep

    args = get_args(SessionDep)
    assert args[0] is SessionContext


# acceptance #6: Authorization 헤더 없을 때 UnauthorizedError
async def test_require_session_raises_when_no_authorization_header():
    from app.core.exceptions import UnauthorizedError

    with pytest.raises(UnauthorizedError):
        await _invoke(None, None)


# acceptance #7: 형식 불량 헤더 → UnauthorizedError
import pytest


@pytest.mark.parametrize(
    "bad_header",
    [
        "Token abc123",   # 잘못된 scheme
        "Bearer",          # 토큰 없음 (split 결과 1토막)
        "just-a-token",   # 공백 없음
        "Basic abc123",   # 잘못된 scheme
    ],
)
async def test_require_session_raises_on_invalid_format(bad_header: str):
    from app.core.exceptions import UnauthorizedError

    with pytest.raises(UnauthorizedError):
        await _invoke(bad_header, None)


# acceptance #8: 소문자 'bearer' → 정상 처리
async def test_require_session_accepts_lowercase_bearer():
    session_id = uuid.uuid4()
    result = await _invoke("bearer sometoken", session_id)
    assert result.session_id == session_id


# acceptance #9: 토큰 해시 DB에 없을 때 → UnauthorizedError
async def test_require_session_raises_when_token_not_in_db():
    from app.core.exceptions import UnauthorizedError

    with pytest.raises(UnauthorizedError):
        await _invoke("Bearer unknowntoken", None)


# acceptance #10: 만료된 세션 → UnauthorizedError (get_active None 반환)
async def test_require_session_raises_when_session_expired():
    from app.core.exceptions import UnauthorizedError

    with pytest.raises(UnauthorizedError):
        await _invoke("Bearer expiredtoken", None)


# acceptance #11: 유효한 토큰 → 세션 UUID 반환
async def test_require_session_returns_uuid_for_valid_token():
    session_id = uuid.uuid4()
    result = await _invoke("Bearer validtoken", session_id)
    from app.core.auth import SessionContext as _SC
    assert result.session_id == session_id
    assert isinstance(result, _SC)


# ── T-025 acceptance #1: SessionContext NamedTuple 정의 ──────────────────────


def test_session_context_is_named_tuple_subclass():
    import typing

    from app.core.auth import SessionContext

    assert issubclass(SessionContext, tuple)
    assert SessionContext._fields == ("session_id", "token")
    hints = typing.get_type_hints(SessionContext)
    assert hints["session_id"] is uuid.UUID
    assert hints["token"] is str


def test_session_context_instantiation_positional_and_keyword():
    from app.core.auth import SessionContext

    sid = uuid.uuid4()
    # positional
    ctx = SessionContext(sid, "tok")
    assert ctx.session_id == sid
    assert ctx.token == "tok"
    # keyword
    ctx2 = SessionContext(session_id=sid, token="tok2")
    assert ctx2.session_id == sid
    assert ctx2.token == "tok2"


# ── T-025 acceptance #3: SessionDep 타입 인자 = SessionContext ───────────────


def test_session_dep_type_arg_is_session_context():
    from app.core.auth import SessionContext, SessionDep

    args = get_args(SessionDep)
    assert args[0] is SessionContext, (
        f"SessionDep 첫 번째 타입 인자가 SessionContext여야 함. got: {args[0]}"
    )


# ── T-025 acceptance #2: require_session → SessionContext 반환 ───────────────


async def test_require_session_returns_session_context_instance():
    from app.core.auth import SessionContext

    session_id = uuid.uuid4()
    result = await _invoke("Bearer mytoken", session_id)
    assert isinstance(result, SessionContext), (
        f"require_session이 SessionContext를 반환해야 함. got: {type(result)}"
    )
    assert result.session_id == session_id


async def test_require_session_token_field_matches_raw_bearer_string():
    from app.core.auth import SessionContext

    session_id = uuid.uuid4()
    raw_token = "RawToken_XYZ"
    result = await _invoke(f"Bearer {raw_token}", session_id)
    assert isinstance(result, SessionContext)
    assert result.token == raw_token, (
        f"token 필드가 bearer 원문과 일치해야 함. expected={raw_token!r}, got={result.token!r}"
    )


async def test_require_session_lowercase_bearer_token_preserved():
    from app.core.auth import SessionContext

    session_id = uuid.uuid4()
    raw_token = "lowercase_token_abc"
    result = await _invoke(f"bearer {raw_token}", session_id)
    assert isinstance(result, SessionContext)
    assert result.session_id == session_id
    assert result.token == raw_token
