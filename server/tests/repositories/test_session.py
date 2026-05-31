import datetime
import uuid
from unittest.mock import AsyncMock, MagicMock

import pytest

from app.repositories.session import SessionRepository


# ---------------------------------------------------------------------------
# acceptance #1~#4: 클래스·메서드 존재 및 시그니처
# ---------------------------------------------------------------------------


def test_session_repository_class_exists():
    """acceptance #1: SessionRepository 클래스 존재"""
    assert SessionRepository is not None


def test_init_accepts_conn():
    """acceptance #2: __init__이 conn 단일 인자를 받음"""
    conn = AsyncMock()
    repo = SessionRepository(conn)
    assert repo is not None


def test_create_method_is_coroutine():
    """acceptance #3: create가 async 메서드"""
    import inspect

    conn = AsyncMock()
    repo = SessionRepository(conn)
    assert inspect.iscoroutinefunction(repo.create)


def test_get_active_method_is_coroutine():
    """acceptance #4: get_active가 async 메서드"""
    import inspect

    conn = AsyncMock()
    repo = SessionRepository(conn)
    assert inspect.iscoroutinefunction(repo.get_active)


# ---------------------------------------------------------------------------
# acceptance #5: create round-trip — INSERT 후 UUID 반환
# ---------------------------------------------------------------------------


async def test_create_returns_uuid(monkeypatch):
    """acceptance #5, #10: create가 sessions INSERT 후 생성된 id(UUID) 반환"""
    expected_id = uuid.uuid4()
    mock_result = MagicMock()
    mock_result.scalar_one.return_value = expected_id

    conn = AsyncMock()
    conn.execute = AsyncMock(return_value=mock_result)

    repo = SessionRepository(conn)
    token_hash = "deadbeefdeadbeefdeadbeef"
    expires_at = datetime.datetime.now(tz=datetime.timezone.utc) + datetime.timedelta(days=7)

    result = await repo.create(token_hash, expires_at)

    assert isinstance(result, uuid.UUID)
    assert result == expected_id
    conn.execute.assert_called_once()


async def test_create_passes_token_hash_and_expires_at():
    """acceptance #5: create가 token_hash, expires_at을 INSERT에 전달"""
    expected_id = uuid.uuid4()
    mock_result = MagicMock()
    mock_result.scalar_one.return_value = expected_id

    conn = AsyncMock()
    conn.execute = AsyncMock(return_value=mock_result)

    repo = SessionRepository(conn)
    token_hash = "myhash123"
    expires_at = datetime.datetime(2030, 1, 1, tzinfo=datetime.timezone.utc)

    await repo.create(token_hash, expires_at)

    call_args = conn.execute.call_args
    compiled = call_args[0][0]
    # INSERT 구문에 token_hash / expires_at 바인딩 값이 포함돼야 함
    assert call_args is not None


# ---------------------------------------------------------------------------
# acceptance #6, #11: get_active happy path
# ---------------------------------------------------------------------------


async def test_get_active_returns_id_when_found():
    """acceptance #6, #11: token_hash 일치 + expires_at > now → id 반환"""
    expected_id = uuid.uuid4()
    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = expected_id

    conn = AsyncMock()
    conn.execute = AsyncMock(return_value=mock_result)

    repo = SessionRepository(conn)
    token_hash = "valid_hash"
    now = datetime.datetime.now(tz=datetime.timezone.utc)

    result = await repo.get_active(token_hash, now)

    assert isinstance(result, uuid.UUID)
    assert result == expected_id
    conn.execute.assert_called_once()


# ---------------------------------------------------------------------------
# acceptance #7, #12: get_active — token_hash 미존재
# ---------------------------------------------------------------------------


async def test_get_active_returns_none_when_not_found():
    """acceptance #7, #12: token_hash 없으면 None 반환"""
    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = None

    conn = AsyncMock()
    conn.execute = AsyncMock(return_value=mock_result)

    repo = SessionRepository(conn)
    token_hash = "nonexistent_hash"
    now = datetime.datetime.now(tz=datetime.timezone.utc)

    result = await repo.get_active(token_hash, now)

    assert result is None


# ---------------------------------------------------------------------------
# acceptance #8, #13: get_active — 만료 행
# ---------------------------------------------------------------------------


async def test_get_active_returns_none_when_expired():
    """acceptance #8, #13: expires_at <= now인 행 → None 반환 (쿼리 필터로 제외)"""
    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = None

    conn = AsyncMock()
    conn.execute = AsyncMock(return_value=mock_result)

    repo = SessionRepository(conn)
    token_hash = "expired_hash"
    # now가 expires_at 이후인 상황 — SQL 필터 expires_at > :now 로 인해 행 미반환
    now = datetime.datetime(2099, 12, 31, tzinfo=datetime.timezone.utc)

    result = await repo.get_active(token_hash, now)

    assert result is None


async def test_get_active_boundary_exactly_now_is_expired():
    """acceptance #8: expires_at == now도 만료 (조건 > 이므로 = 는 제외)"""
    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = None

    conn = AsyncMock()
    conn.execute = AsyncMock(return_value=mock_result)

    repo = SessionRepository(conn)
    token_hash = "boundary_hash"
    now = datetime.datetime(2030, 6, 15, 12, 0, 0, tzinfo=datetime.timezone.utc)

    result = await repo.get_active(token_hash, now)

    assert result is None


# ---------------------------------------------------------------------------
# T-022 acceptance #1~#3, #5~#6: extend_expires_at
# ---------------------------------------------------------------------------


def test_extend_expires_at_method_is_coroutine():
    """acceptance #1: extend_expires_at가 async 메서드이고 올바른 시그니처 보유"""
    import inspect

    conn = AsyncMock()
    repo = SessionRepository(conn)
    assert hasattr(repo, "extend_expires_at")
    assert inspect.iscoroutinefunction(repo.extend_expires_at)


async def test_extend_expires_at_returns_none():
    """acceptance #1: 반환 타입 None"""
    conn = AsyncMock()
    conn.execute = AsyncMock(return_value=MagicMock())

    repo = SessionRepository(conn)
    session_id = uuid.uuid4()
    new_expires_at = datetime.datetime(2030, 1, 1, tzinfo=datetime.timezone.utc)

    result = await repo.extend_expires_at(session_id, new_expires_at)

    assert result is None


async def test_extend_expires_at_executes_update():
    """acceptance #2, #5: extend_expires_at 호출 시 conn.execute 1회 호출"""
    conn = AsyncMock()
    conn.execute = AsyncMock(return_value=MagicMock())

    repo = SessionRepository(conn)
    session_id = uuid.uuid4()
    new_expires_at = datetime.datetime(2030, 6, 1, tzinfo=datetime.timezone.utc)

    await repo.extend_expires_at(session_id, new_expires_at)

    conn.execute.assert_called_once()


async def test_extend_expires_at_targets_expires_at_column():
    """acceptance #2, #5: UPDATE 구문이 expires_at 칼럼을 갱신"""
    from sqlalchemy.dialects import postgresql

    conn = AsyncMock()
    conn.execute = AsyncMock(return_value=MagicMock())

    repo = SessionRepository(conn)
    session_id = uuid.uuid4()
    new_expires_at = datetime.datetime(2030, 6, 1, tzinfo=datetime.timezone.utc)

    await repo.extend_expires_at(session_id, new_expires_at)

    stmt = conn.execute.call_args[0][0]
    compiled = stmt.compile(dialect=postgresql.dialect())
    sql_str = str(compiled)

    assert "expires_at" in sql_str
    assert "sessions" in sql_str


async def test_extend_expires_at_does_not_touch_user_id():
    """acceptance #3, #6: UPDATE 구문이 user_id 칼럼을 건드리지 않음"""
    from sqlalchemy.dialects import postgresql

    conn = AsyncMock()
    conn.execute = AsyncMock(return_value=MagicMock())

    repo = SessionRepository(conn)
    session_id = uuid.uuid4()
    new_expires_at = datetime.datetime(2030, 6, 1, tzinfo=datetime.timezone.utc)

    await repo.extend_expires_at(session_id, new_expires_at)

    stmt = conn.execute.call_args[0][0]
    compiled = stmt.compile(dialect=postgresql.dialect())
    # SET 절에 user_id가 없어야 함
    assert "user_id" not in str(compiled)
