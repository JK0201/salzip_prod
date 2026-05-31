import inspect
import uuid
from unittest.mock import AsyncMock, MagicMock

from app.repositories.profiles import ProfileRepository

# ---------------------------------------------------------------------------
# acceptance T-095 #1: create_for_user 존재·async
# ---------------------------------------------------------------------------


def test_create_for_user_is_async_coroutine():
    conn = AsyncMock()
    repo = ProfileRepository(conn)
    assert hasattr(repo, "create_for_user")
    assert inspect.iscoroutinefunction(repo.create_for_user)


# ---------------------------------------------------------------------------
# acceptance T-095 #2: create_for_user 시그니처 (user_id, payload)
# ---------------------------------------------------------------------------


def test_create_for_user_signature():
    sig = inspect.signature(ProfileRepository.create_for_user)
    params = list(sig.parameters.keys())
    assert "user_id" in params
    assert "payload" in params


# ---------------------------------------------------------------------------
# acceptance T-095 #3: create_for_user — sa.insert (Insert), ON CONFLICT 없음
# ---------------------------------------------------------------------------


async def test_create_for_user_uses_plain_insert_no_on_conflict():
    import sqlalchemy as sa
    from sqlalchemy.sql.dml import Insert

    expected_id = uuid.uuid4()
    mock_result = MagicMock()
    mock_result.scalar_one.return_value = expected_id

    conn = AsyncMock()
    conn.execute = AsyncMock(return_value=mock_result)

    repo = ProfileRepository(conn)
    await repo.create_for_user(uuid.uuid4(), {"key": "value"})

    stmt = conn.execute.call_args[0][0]
    assert isinstance(stmt, Insert), f"create_for_user must use sa.insert, got {type(stmt)}"

    compiled = stmt.compile(dialect=sa.dialects.postgresql.dialect())
    sql_str = str(compiled).lower()
    assert "on conflict" not in sql_str, (
        f"create_for_user must NOT have ON CONFLICT clause, got: {sql_str}"
    )


async def test_create_for_user_returns_uuid():
    expected_id = uuid.uuid4()
    mock_result = MagicMock()
    mock_result.scalar_one.return_value = expected_id

    conn = AsyncMock()
    conn.execute = AsyncMock(return_value=mock_result)

    repo = ProfileRepository(conn)
    result = await repo.create_for_user(uuid.uuid4(), {"score": 42})

    assert isinstance(result, uuid.UUID)
    assert result == expected_id


async def test_create_for_user_insert_targets_profiles_table():
    expected_id = uuid.uuid4()
    mock_result = MagicMock()
    mock_result.scalar_one.return_value = expected_id

    conn = AsyncMock()
    conn.execute = AsyncMock(return_value=mock_result)

    repo = ProfileRepository(conn)
    await repo.create_for_user(uuid.uuid4(), {"q": "a"})

    stmt = conn.execute.call_args[0][0]
    assert stmt.table.name == "profiles"


# ---------------------------------------------------------------------------
# acceptance T-095 #4: upsert_by_user 속성 부재
# ---------------------------------------------------------------------------


def test_upsert_by_user_is_removed():
    conn = AsyncMock()
    repo = ProfileRepository(conn)
    assert not hasattr(repo, "upsert_by_user"), (
        "upsert_by_user must be removed in T-095"
    )


# ---------------------------------------------------------------------------
# acceptance T-095 #5: delete_by_user 속성 부재
# ---------------------------------------------------------------------------


def test_delete_by_user_is_removed():
    conn = AsyncMock()
    repo = ProfileRepository(conn)
    assert not hasattr(repo, "delete_by_user"), (
        "delete_by_user must be removed in T-095"
    )


# ---------------------------------------------------------------------------
# acceptance T-095 #6: promote_anon_to_user 존재 (회귀 가드)
# ---------------------------------------------------------------------------


def test_promote_anon_to_user_still_exists():
    conn = AsyncMock()
    repo = ProfileRepository(conn)
    assert hasattr(repo, "promote_anon_to_user")
    assert inspect.iscoroutinefunction(repo.promote_anon_to_user)


# ---------------------------------------------------------------------------
# 회귀 가드: create 메서드 (변경 없음)
# ---------------------------------------------------------------------------


def test_create_method_is_coroutine():
    conn = AsyncMock()
    repo = ProfileRepository(conn)
    assert inspect.iscoroutinefunction(repo.create)


def test_existing_create_signature_preserved():
    sig = inspect.signature(ProfileRepository.create)
    params = list(sig.parameters.keys())
    assert "session_id" in params
    assert "payload" in params


async def test_create_returns_uuid():
    expected_id = uuid.uuid4()
    mock_result = MagicMock()
    mock_result.scalar_one.return_value = expected_id

    conn = AsyncMock()
    conn.execute = AsyncMock(return_value=mock_result)

    repo = ProfileRepository(conn)
    result = await repo.create(uuid.uuid4(), {"name": "alice"})

    assert isinstance(result, uuid.UUID)
    assert result == expected_id


# ---------------------------------------------------------------------------
# 회귀 가드: get_by_user (변경 없음)
# ---------------------------------------------------------------------------


def test_get_by_user_method_exists():
    conn = AsyncMock()
    repo = ProfileRepository(conn)
    assert hasattr(repo, "get_by_user")
    assert inspect.iscoroutinefunction(repo.get_by_user)


async def test_get_by_user_returns_profile_id():
    profile_id = uuid.uuid4()
    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = profile_id

    conn = AsyncMock()
    conn.execute = AsyncMock(return_value=mock_result)

    repo = ProfileRepository(conn)
    result = await repo.get_by_user(uuid.uuid4())

    assert isinstance(result, uuid.UUID)
    assert result == profile_id


async def test_get_by_user_returns_none_when_not_found():
    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = None

    conn = AsyncMock()
    conn.execute = AsyncMock(return_value=mock_result)

    repo = ProfileRepository(conn)
    result = await repo.get_by_user(uuid.uuid4())

    assert result is None


# ---------------------------------------------------------------------------
# 회귀 가드: get_by_session (변경 없음)
# ---------------------------------------------------------------------------


def test_get_by_session_method_exists():
    conn = AsyncMock()
    repo = ProfileRepository(conn)
    assert hasattr(repo, "get_by_session")
    assert inspect.iscoroutinefunction(repo.get_by_session)


async def test_get_by_session_returns_profile_id():
    profile_id = uuid.uuid4()
    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = profile_id

    conn = AsyncMock()
    conn.execute = AsyncMock(return_value=mock_result)

    repo = ProfileRepository(conn)
    result = await repo.get_by_session(uuid.uuid4())

    assert result == profile_id
    conn.execute.assert_called_once()


async def test_get_by_session_filters_user_id_is_null():
    import sqlalchemy as sa

    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = None

    conn = AsyncMock()
    conn.execute = AsyncMock(return_value=mock_result)

    repo = ProfileRepository(conn)
    await repo.get_by_session(uuid.uuid4())

    stmt = conn.execute.call_args[0][0]
    compiled = stmt.compile(dialect=sa.dialects.postgresql.dialect())
    where_str = str(compiled).lower()
    assert "user_id is null" in where_str, (
        f"get_by_session must filter user_id IS NULL, compiled: {where_str}"
    )


# ---------------------------------------------------------------------------
# 회귀 가드: promote_anon_to_user 동작 (변경 없음)
# ---------------------------------------------------------------------------


def test_promote_anon_to_user_signature():
    sig = inspect.signature(ProfileRepository.promote_anon_to_user)
    params = list(sig.parameters.keys())
    assert "session_id" in params
    assert "user_id" in params


async def test_promote_anon_to_user_executes_update_statement():
    from sqlalchemy.sql.dml import Update

    profile_id = uuid.uuid4()
    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = profile_id

    conn = AsyncMock()
    conn.execute = AsyncMock(return_value=mock_result)

    repo = ProfileRepository(conn)
    await repo.promote_anon_to_user(uuid.uuid4(), uuid.uuid4())

    conn.execute.assert_called_once()
    stmt = conn.execute.call_args[0][0]
    assert isinstance(stmt, Update), (
        f"promote_anon_to_user must execute UPDATE statement, got {type(stmt)}"
    )
    assert stmt.table.name == "profiles"


async def test_promote_anon_to_user_returns_profile_id():
    profile_id = uuid.uuid4()
    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = profile_id

    conn = AsyncMock()
    conn.execute = AsyncMock(return_value=mock_result)

    repo = ProfileRepository(conn)
    result = await repo.promote_anon_to_user(uuid.uuid4(), uuid.uuid4())

    assert result == profile_id
    assert isinstance(result, uuid.UUID)


async def test_promote_anon_to_user_returns_none_when_no_match():
    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = None

    conn = AsyncMock()
    conn.execute = AsyncMock(return_value=mock_result)

    repo = ProfileRepository(conn)
    result = await repo.promote_anon_to_user(uuid.uuid4(), uuid.uuid4())

    assert result is None
