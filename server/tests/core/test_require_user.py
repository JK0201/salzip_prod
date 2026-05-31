import asyncio
import inspect
import uuid
from typing import get_args, get_type_hints
from unittest.mock import AsyncMock, MagicMock, patch

import pytest


# acceptance #1: require_user async 함수 존재
def test_require_user_is_async():
    from app.core.auth import require_user

    assert asyncio.iscoroutinefunction(require_user)


# acceptance #2: UserDep = Annotated[CurrentUser, Depends(require_user)] 존재
def test_user_dep_exported():
    from app.core.auth import UserDep, require_user

    args = get_args(UserDep)
    assert len(args) >= 2
    dep = args[1]
    assert dep.dependency is require_user


# acceptance #3: require_user 인자에 SessionDep, ConnDep 사용
def test_require_user_signature_uses_session_dep_and_conn_dep():
    from app.core.auth import SessionDep, require_user
    from app.core.deps import ConnDep

    hints = get_type_hints(require_user, include_extras=True)
    params = list(inspect.signature(require_user).parameters.keys())

    assert "session" in params
    assert hints.get("session") == SessionDep

    assert "conn" in params
    assert hints.get("conn") == ConnDep


# acceptance #4: 반환 구조에 session_id, user_id 두 필드 존재
def test_current_user_has_session_id_and_user_id_fields():
    from app.core.auth import CurrentUser

    sid = uuid.uuid4()
    uid = uuid.uuid4()
    cu = CurrentUser(session_id=sid, user_id=uid)
    assert cu.session_id == sid
    assert cu.user_id == uid


# acceptance #5: require_session, SessionDep 그대로 유지
def test_require_session_and_session_dep_still_exported():
    from app.core.auth import SessionContext, SessionDep, require_session

    assert asyncio.iscoroutinefunction(require_session)
    args = get_args(SessionDep)
    assert args[0] is SessionContext


# acceptance #6 & #11: 익명 세션(user_id NULL) → UnauthorizedError (status 401)
async def test_require_user_raises_when_user_id_is_null():
    from app.core.auth import SessionContext, require_user
    from app.core.exceptions import UnauthorizedError

    session_id = uuid.uuid4()
    session = SessionContext(session_id=session_id, token="tok")
    mock_conn = MagicMock()

    with patch("app.core.auth.SessionRepository") as MockRepo:
        MockRepo.return_value.get_user_id = AsyncMock(return_value=None)
        with pytest.raises(UnauthorizedError) as exc_info:
            await require_user(session=session, conn=mock_conn)

    assert exc_info.value.status_code == 401


# acceptance #7 & #12: user_id가 채워진 세션 → CurrentUser(session_id, user_id) 반환
async def test_require_user_returns_current_user_when_user_id_present():
    from app.core.auth import CurrentUser, SessionContext, require_user

    session_id = uuid.uuid4()
    user_id = uuid.uuid4()
    session = SessionContext(session_id=session_id, token="tok")
    mock_conn = MagicMock()

    with patch("app.core.auth.SessionRepository") as MockRepo:
        MockRepo.return_value.get_user_id = AsyncMock(return_value=user_id)
        result = await require_user(session=session, conn=mock_conn)

    assert isinstance(result, CurrentUser)
    assert result.session_id == session_id
    assert result.user_id == user_id


# acceptance #8: Authorization 헤더 누락 시 require_session 단계에서 UnauthorizedError (401)
async def test_require_session_raises_when_no_authorization_header():
    from app.core.auth import require_session
    from app.core.exceptions import UnauthorizedError

    req = MagicMock()
    req.headers.get = MagicMock(return_value=None)
    mock_conn = MagicMock()

    with pytest.raises(UnauthorizedError) as exc_info:
        await require_session(request=req, conn=mock_conn)

    assert exc_info.value.status_code == 401


# acceptance #9: 만료/미존재 토큰 시 require_session 단계에서 UnauthorizedError (401)
async def test_require_session_raises_when_token_invalid_or_expired():
    from app.core.auth import require_session
    from app.core.exceptions import UnauthorizedError

    req = MagicMock()
    req.headers.get = MagicMock(return_value="Bearer expiredtoken")
    mock_conn = MagicMock()

    with patch("app.core.auth.SessionRepository") as MockRepo:
        MockRepo.return_value.get_active = AsyncMock(return_value=None)
        with pytest.raises(UnauthorizedError) as exc_info:
            await require_session(request=req, conn=mock_conn)

    assert exc_info.value.status_code == 401


# ── T-025 acceptance #3: SessionDep 타입 인자 = SessionContext ───────────────


def test_session_dep_type_arg_is_session_context():
    from app.core.auth import SessionContext, SessionDep

    args = get_args(SessionDep)
    assert args[0] is SessionContext, (
        f"SessionDep 첫 타입 인자가 SessionContext여야 함. got: {args[0]}"
    )


# ── T-025 acceptance #9: require_user 파라미터명 session_id → session ─────────


def test_require_user_has_session_param_not_session_id():
    from app.core.auth import SessionDep, require_user
    from app.core.deps import ConnDep

    hints = get_type_hints(require_user, include_extras=True)
    params = list(inspect.signature(require_user).parameters.keys())

    assert "session" in params, (
        f"require_user 파라미터에 'session'이 있어야 함. 현재: {params}"
    )
    assert "session_id" not in params, (
        f"require_user에서 'session_id' 파라미터가 제거되어야 함. 현재: {params}"
    )
    assert hints.get("session") == SessionDep

    assert "conn" in params
    assert hints.get("conn") == ConnDep


# ── T-025 acceptance #9: require_user → SessionContext.session_id로 get_user_id 호출 ─


async def test_require_user_calls_get_user_id_with_session_context_session_id():
    from app.core.auth import SessionContext, require_user

    sid = uuid.uuid4()
    uid = uuid.uuid4()
    session = SessionContext(session_id=sid, token="tok")
    mock_conn = MagicMock()

    with patch("app.core.auth.SessionRepository") as MockRepo:
        MockRepo.return_value.get_user_id = AsyncMock(return_value=uid)
        await require_user(session=session, conn=mock_conn)
        call_args = MockRepo.return_value.get_user_id.call_args
        passed_sid = call_args[0][0] if call_args[0] else call_args[1].get("session_id")
        assert passed_sid == sid, (
            f"get_user_id에 session.session_id={sid!r}가 전달되어야 함. got: {passed_sid!r}"
        )


# ── T-025 acceptance #9: 익명 세션 → UnauthorizedError (SessionContext 전달) ──


async def test_require_user_raises_unauthorized_when_session_context_has_no_user():
    from app.core.auth import SessionContext, require_user
    from app.core.exceptions import UnauthorizedError

    sid = uuid.uuid4()
    session = SessionContext(session_id=sid, token="tok")
    mock_conn = MagicMock()

    with patch("app.core.auth.SessionRepository") as MockRepo:
        MockRepo.return_value.get_user_id = AsyncMock(return_value=None)
        with pytest.raises(UnauthorizedError) as exc_info:
            await require_user(session=session, conn=mock_conn)

    assert exc_info.value.status_code == 401


# ── T-025 acceptance #9: require_user → CurrentUser(session_id, user_id) 반환 ─


async def test_require_user_returns_current_user_with_session_context_session_id():
    from app.core.auth import CurrentUser, SessionContext, require_user

    sid = uuid.uuid4()
    uid = uuid.uuid4()
    session = SessionContext(session_id=sid, token="tok")
    mock_conn = MagicMock()

    with patch("app.core.auth.SessionRepository") as MockRepo:
        MockRepo.return_value.get_user_id = AsyncMock(return_value=uid)
        result = await require_user(session=session, conn=mock_conn)

    assert isinstance(result, CurrentUser)
    assert result.session_id == sid
    assert result.user_id == uid
