import inspect
import uuid
from unittest.mock import AsyncMock, MagicMock

from app.repositories.session import SessionRepository


# ---------------------------------------------------------------------------
# acceptance #1~#3: 메서드 존재 및 시그니처
# ---------------------------------------------------------------------------


def test_set_user_id_method_is_coroutine():
    """acceptance #1: set_user_id가 async 메서드"""
    conn = AsyncMock()
    repo = SessionRepository(conn)
    assert inspect.iscoroutinefunction(repo.set_user_id)


def test_clear_user_id_method_is_coroutine():
    """acceptance #2: clear_user_id가 async 메서드"""
    conn = AsyncMock()
    repo = SessionRepository(conn)
    assert inspect.iscoroutinefunction(repo.clear_user_id)


def test_get_user_id_method_is_coroutine():
    """acceptance #3: get_user_id가 async 메서드"""
    conn = AsyncMock()
    repo = SessionRepository(conn)
    assert inspect.iscoroutinefunction(repo.get_user_id)


def test_set_user_id_signature():
    """acceptance #1: set_user_id(session_id, user_id) 파라미터 존재"""
    sig = inspect.signature(SessionRepository.set_user_id)
    params = list(sig.parameters.keys())
    assert "session_id" in params
    assert "user_id" in params


def test_clear_user_id_signature():
    """acceptance #2: clear_user_id(session_id) 파라미터 존재"""
    sig = inspect.signature(SessionRepository.clear_user_id)
    params = list(sig.parameters.keys())
    assert "session_id" in params


def test_get_user_id_signature():
    """acceptance #3: get_user_id(session_id) 파라미터 존재"""
    sig = inspect.signature(SessionRepository.get_user_id)
    params = list(sig.parameters.keys())
    assert "session_id" in params


# ---------------------------------------------------------------------------
# acceptance #4: set_user_id 호출 후 user_id 컬럼 갱신 (execute 호출 검증)
# ---------------------------------------------------------------------------


async def test_set_user_id_executes_update():
    """acceptance #4: set_user_id가 conn.execute 호출, None 반환"""
    conn = AsyncMock()
    conn.execute = AsyncMock(return_value=MagicMock())
    repo = SessionRepository(conn)
    session_id = uuid.uuid4()
    user_id = uuid.uuid4()

    result = await repo.set_user_id(session_id, user_id)

    assert result is None
    conn.execute.assert_called_once()


# ---------------------------------------------------------------------------
# acceptance #5: clear_user_id 호출 후 user_id NULL (execute 호출 검증)
# ---------------------------------------------------------------------------


async def test_clear_user_id_executes_update():
    """acceptance #5: clear_user_id가 conn.execute 호출, None 반환"""
    conn = AsyncMock()
    conn.execute = AsyncMock(return_value=MagicMock())
    repo = SessionRepository(conn)
    session_id = uuid.uuid4()

    result = await repo.clear_user_id(session_id)

    assert result is None
    conn.execute.assert_called_once()


# ---------------------------------------------------------------------------
# acceptance #6: user_id 채워진 session → get_user_id가 uuid 반환
# ---------------------------------------------------------------------------


async def test_get_user_id_returns_uuid_when_set():
    """acceptance #6: user_id가 채워진 session → get_user_id가 그 uuid 반환"""
    expected_user_id = uuid.uuid4()
    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = expected_user_id

    conn = AsyncMock()
    conn.execute = AsyncMock(return_value=mock_result)
    repo = SessionRepository(conn)

    result = await repo.get_user_id(uuid.uuid4())

    assert isinstance(result, uuid.UUID)
    assert result == expected_user_id


# ---------------------------------------------------------------------------
# acceptance #7, #13: user_id NULL인 session → get_user_id가 None 반환
# ---------------------------------------------------------------------------


async def test_get_user_id_returns_none_when_null():
    """acceptance #7, #13: user_id가 NULL인 session → get_user_id가 None 반환"""
    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = None

    conn = AsyncMock()
    conn.execute = AsyncMock(return_value=mock_result)
    repo = SessionRepository(conn)

    result = await repo.get_user_id(uuid.uuid4())

    assert result is None


# ---------------------------------------------------------------------------
# acceptance #8: 존재하지 않는 session_id → get_user_id가 None 반환
# ---------------------------------------------------------------------------


async def test_get_user_id_returns_none_for_nonexistent_session():
    """acceptance #8: 존재하지 않는 session_id → get_user_id가 None 반환"""
    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = None

    conn = AsyncMock()
    conn.execute = AsyncMock(return_value=mock_result)
    repo = SessionRepository(conn)

    result = await repo.get_user_id(uuid.uuid4())

    assert result is None


# ---------------------------------------------------------------------------
# acceptance #9: 기존 create/get_active 동작 유지
# ---------------------------------------------------------------------------


def test_create_method_still_exists():
    """acceptance #9: create 메서드 여전히 존재"""
    conn = AsyncMock()
    repo = SessionRepository(conn)
    assert inspect.iscoroutinefunction(repo.create)


def test_get_active_method_still_exists():
    """acceptance #9: get_active 메서드 여전히 존재"""
    conn = AsyncMock()
    repo = SessionRepository(conn)
    assert inspect.iscoroutinefunction(repo.get_active)


# ---------------------------------------------------------------------------
# acceptance #11: set_user_id → get_user_id 라운드트립
# ---------------------------------------------------------------------------


async def test_set_user_id_then_get_user_id_roundtrip():
    """acceptance #11: set_user_id 후 get_user_id가 같은 uuid 반환 (라운드트립)"""
    session_id = uuid.uuid4()
    user_id = uuid.uuid4()

    set_result = MagicMock()
    get_result = MagicMock()
    get_result.scalar_one_or_none.return_value = user_id

    conn = AsyncMock()
    conn.execute = AsyncMock(side_effect=[set_result, get_result])
    repo = SessionRepository(conn)

    await repo.set_user_id(session_id, user_id)
    result = await repo.get_user_id(session_id)

    assert result == user_id
    assert conn.execute.call_count == 2


# ---------------------------------------------------------------------------
# acceptance #12: clear_user_id 후 get_user_id → None
# ---------------------------------------------------------------------------


async def test_clear_user_id_then_get_user_id_returns_none():
    """acceptance #12: clear_user_id 후 get_user_id가 None 반환"""
    session_id = uuid.uuid4()

    clear_result = MagicMock()
    get_result = MagicMock()
    get_result.scalar_one_or_none.return_value = None

    conn = AsyncMock()
    conn.execute = AsyncMock(side_effect=[clear_result, get_result])
    repo = SessionRepository(conn)

    await repo.clear_user_id(session_id)
    result = await repo.get_user_id(session_id)

    assert result is None
    assert conn.execute.call_count == 2
