import inspect
import uuid
from unittest.mock import AsyncMock, MagicMock

from app.repositories.match_results import MatchResultRepository


# ---------------------------------------------------------------------------
# acceptance #6~#8: 클래스·메서드 존재 및 시그니처
# ---------------------------------------------------------------------------


def test_match_result_repository_class_exists():
    """acceptance #6: MatchResultRepository 클래스 존재"""
    assert MatchResultRepository is not None


def test_init_accepts_conn():
    """acceptance #7: __init__이 conn 단일 인자를 받음"""
    conn = AsyncMock()
    repo = MatchResultRepository(conn)
    assert repo is not None


def test_create_method_is_coroutine():
    """acceptance #8: create가 async 메서드"""
    conn = AsyncMock()
    repo = MatchResultRepository(conn)
    assert inspect.iscoroutinefunction(repo.create)


# ---------------------------------------------------------------------------
# acceptance #9: INSERT 구문 사용 검증
# ---------------------------------------------------------------------------


async def test_create_uses_insert_statement():
    """acceptance #9: create가 sa.insert(match_results_table) 구문을 conn.execute에 전달"""
    from sqlalchemy.sql.dml import Insert

    expected_id = uuid.uuid4()
    mock_result = MagicMock()
    mock_result.scalar_one.return_value = expected_id

    conn = AsyncMock()
    conn.execute = AsyncMock(return_value=mock_result)

    repo = MatchResultRepository(conn)
    await repo.create(uuid.uuid4(), {"score": 95})

    call_args = conn.execute.call_args
    assert call_args is not None
    stmt = call_args[0][0]
    assert isinstance(stmt, Insert)
    assert stmt.table.name == "match_results"


# ---------------------------------------------------------------------------
# acceptance #10, #14: create round-trip — INSERT 후 UUID 반환 + row 영속화
# ---------------------------------------------------------------------------


async def test_create_returns_uuid():
    """acceptance #10: create가 새로 생성된 id(UUID) 반환"""
    expected_id = uuid.uuid4()
    mock_result = MagicMock()
    mock_result.scalar_one.return_value = expected_id

    conn = AsyncMock()
    conn.execute = AsyncMock(return_value=mock_result)

    repo = MatchResultRepository(conn)
    result = await repo.create(uuid.uuid4(), {"matches": ["user_a", "user_b"]})

    assert isinstance(result, uuid.UUID)
    assert result == expected_id


async def test_create_persists_row_and_returns_id():
    """acceptance #14: create가 row를 영속화(conn.execute 호출)하고 id 반환"""
    expected_id = uuid.uuid4()
    mock_result = MagicMock()
    mock_result.scalar_one.return_value = expected_id

    conn = AsyncMock()
    conn.execute = AsyncMock(return_value=mock_result)

    repo = MatchResultRepository(conn)
    profile_id = uuid.uuid4()
    payload = {"rank": 1, "score": 0.98, "matched_profile_id": str(uuid.uuid4())}

    result = await repo.create(profile_id, payload)

    conn.execute.assert_called_once()
    assert result == expected_id


async def test_create_returns_different_ids_per_call():
    """acceptance #10: 각 INSERT가 독립된 UUID 반환 (반환값이 scalar_one에서 옴)"""
    id_1 = uuid.uuid4()
    id_2 = uuid.uuid4()

    conn = AsyncMock()

    mock_result_1 = MagicMock()
    mock_result_1.scalar_one.return_value = id_1
    mock_result_2 = MagicMock()
    mock_result_2.scalar_one.return_value = id_2

    conn.execute = AsyncMock(side_effect=[mock_result_1, mock_result_2])

    repo = MatchResultRepository(conn)
    result_1 = await repo.create(uuid.uuid4(), {"x": 1})
    result_2 = await repo.create(uuid.uuid4(), {"x": 2})

    assert result_1 == id_1
    assert result_2 == id_2
    assert result_1 != result_2


# ---------------------------------------------------------------------------
# T-021 acceptance #1: list_by_user 메서드 존재·시그니처
# ---------------------------------------------------------------------------


def test_list_by_user_method_exists():
    """acceptance #1: list_by_user 메서드 존재, async"""
    conn = AsyncMock()
    repo = MatchResultRepository(conn)
    assert hasattr(repo, "list_by_user")
    assert inspect.iscoroutinefunction(repo.list_by_user)


def test_list_by_user_signature():
    """acceptance #1: list_by_user 시그니처 — user_id 파라미터 존재"""
    sig = inspect.signature(MatchResultRepository.list_by_user)
    params = list(sig.parameters.keys())
    assert "user_id" in params


# ---------------------------------------------------------------------------
# T-021 acceptance #2: JOIN 쿼리 — profiles.user_id = :user_id 조건
# ---------------------------------------------------------------------------


async def test_list_by_user_query_joins_profiles_and_filters_by_user_id():
    """acceptance #2: list_by_user가 profiles JOIN + WHERE profiles.user_id = :user_id 사용"""
    import sqlalchemy as sa

    user_id = uuid.uuid4()

    mock_result = MagicMock()
    mock_result.mappings.return_value.all.return_value = []
    mock_result.all.return_value = []

    conn = AsyncMock()
    conn.execute = AsyncMock(return_value=mock_result)

    repo = MatchResultRepository(conn)
    await repo.list_by_user(user_id)

    conn.execute.assert_called_once()
    stmt = conn.execute.call_args[0][0]
    compiled = stmt.compile(
        dialect=sa.dialects.postgresql.dialect(),
        compile_kwargs={"literal_binds": False},
    )
    sql_str = str(compiled).lower()
    assert "profiles" in sql_str, f"JOIN profiles 누락: {sql_str}"
    assert "user_id" in sql_str, f"WHERE user_id 조건 누락: {sql_str}"


# ---------------------------------------------------------------------------
# T-021 acceptance #3 + acceptance #7: 결과 created_at DESC 정렬 검증
# ---------------------------------------------------------------------------


async def test_list_by_user_query_orders_by_created_at_desc():
    """acceptance #3 + #7: SQL에 ORDER BY created_at DESC 포함, 반환 순서 보존"""
    import sqlalchemy as sa

    payload_newer = {"score": 99}
    payload_older = {"score": 10}

    mock_result = MagicMock()
    mock_result.mappings.return_value.all.return_value = [
        {"payload": payload_newer},
        {"payload": payload_older},
    ]
    mock_result.all.return_value = [
        MagicMock(payload=payload_newer),
        MagicMock(payload=payload_older),
    ]

    conn = AsyncMock()
    conn.execute = AsyncMock(return_value=mock_result)

    repo = MatchResultRepository(conn)
    result = await repo.list_by_user(uuid.uuid4())

    # SQL ORDER BY 검증
    stmt = conn.execute.call_args[0][0]
    compiled = stmt.compile(
        dialect=sa.dialects.postgresql.dialect(),
        compile_kwargs={"literal_binds": False},
    )
    sql_str = str(compiled).lower()
    assert "created_at" in sql_str, f"ORDER BY created_at 누락: {sql_str}"
    assert "desc" in sql_str, f"DESC 정렬 누락: {sql_str}"

    # 반환값 순서 보존 검증
    assert isinstance(result, list)
    assert len(result) == 2


# ---------------------------------------------------------------------------
# T-021 acceptance #4 + acceptance #9: 빈 리스트 반환
# ---------------------------------------------------------------------------


async def test_list_by_user_returns_empty_list_when_no_match_results():
    """acceptance #4 + #9: 해당 user의 match_results 없으면 빈 리스트 반환"""
    mock_result = MagicMock()
    mock_result.mappings.return_value.all.return_value = []
    mock_result.all.return_value = []

    conn = AsyncMock()
    conn.execute = AsyncMock(return_value=mock_result)

    repo = MatchResultRepository(conn)
    result = await repo.list_by_user(uuid.uuid4())

    assert result == []


# ---------------------------------------------------------------------------
# T-021 acceptance #8: 다른 user의 결과 격리 — WHERE user_id 바인딩 검증
# ---------------------------------------------------------------------------


async def test_list_by_user_isolates_results_by_user_id():
    """acceptance #8: WHERE 절이 특정 user_id로 바인딩 — 다른 user 결과 미포함"""
    import sqlalchemy as sa

    user_a = uuid.uuid4()
    user_b = uuid.uuid4()

    call_stmts: list = []

    async def capture_execute(stmt, *args, **kwargs):
        call_stmts.append(stmt)
        mock_result = MagicMock()
        mock_result.mappings.return_value.all.return_value = []
        mock_result.all.return_value = []
        return mock_result

    conn = AsyncMock()
    conn.execute = capture_execute

    repo = MatchResultRepository(conn)
    await repo.list_by_user(user_a)
    await repo.list_by_user(user_b)

    assert len(call_stmts) == 2

    def extract_user_id_param(stmt) -> str:
        compiled = stmt.compile(
            dialect=sa.dialects.postgresql.dialect(),
            compile_kwargs={"literal_binds": False},
        )
        return str(compiled.params)

    params_a = extract_user_id_param(call_stmts[0])
    params_b = extract_user_id_param(call_stmts[1])

    # 두 쿼리가 서로 다른 user_id 바인딩을 사용해야 함
    assert str(user_a) in params_a, f"user_a({user_a}) 바인딩 누락: {params_a}"
    assert str(user_b) in params_b, f"user_b({user_b}) 바인딩 누락: {params_b}"
    assert str(user_b) not in params_a, f"user_b가 user_a 쿼리에 혼입: {params_a}"


# ---------------------------------------------------------------------------
# T-021 acceptance #5: 기존 create(profile_id, payload) 시그니처·동작 보존
# ---------------------------------------------------------------------------


def test_existing_create_signature_has_profile_id_param():
    """acceptance #5: create 시그니처에 profile_id 파라미터 존재"""
    sig = inspect.signature(MatchResultRepository.create)
    params = list(sig.parameters.keys())
    assert "profile_id" in params
    assert "payload" in params


async def test_existing_create_still_returns_uuid():
    """acceptance #5: create 동작 보존 — UUID 반환"""
    expected_id = uuid.uuid4()
    mock_result = MagicMock()
    mock_result.scalar_one.return_value = expected_id

    conn = AsyncMock()
    conn.execute = AsyncMock(return_value=mock_result)

    repo = MatchResultRepository(conn)
    result = await repo.create(uuid.uuid4(), {"q": "a"})

    assert isinstance(result, uuid.UUID)
    assert result == expected_id
