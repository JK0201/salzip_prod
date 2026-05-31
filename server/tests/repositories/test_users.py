import inspect
import uuid
from unittest.mock import AsyncMock, MagicMock

import pytest
import sqlalchemy as sa
from sqlalchemy.exc import IntegrityError

from app.repositories.users import UserRepository, UserRow


# ---------------------------------------------------------------------------
# acceptance #1~#5: 클래스·메서드 존재 및 시그니처
# ---------------------------------------------------------------------------


def test_user_repository_class_exists():
    """acceptance #1~#2: 파일 및 UserRepository 클래스 존재"""
    assert UserRepository is not None


def test_init_stores_conn():
    """acceptance #3: __init__이 conn을 인스턴스 변수에 저장"""
    conn = AsyncMock()
    repo = UserRepository(conn)
    assert repo._conn is conn


def test_create_is_coroutine():
    """acceptance #4: create가 async 메서드"""
    conn = AsyncMock()
    repo = UserRepository(conn)
    assert inspect.iscoroutinefunction(repo.create)


def test_get_by_email_is_coroutine():
    """acceptance #5: get_by_email이 async 메서드"""
    conn = AsyncMock()
    repo = UserRepository(conn)
    assert inspect.iscoroutinefunction(repo.get_by_email)


# ---------------------------------------------------------------------------
# acceptance #12: create + get_by_email 라운드트립
# ---------------------------------------------------------------------------


async def test_create_returns_uuid():
    """acceptance #4: create 호출 시 uuid.UUID 반환"""
    expected_id = uuid.uuid4()
    mock_result = MagicMock()
    mock_result.scalar_one.return_value = expected_id

    conn = AsyncMock()
    conn.execute = AsyncMock(return_value=mock_result)

    repo = UserRepository(conn)
    result = await repo.create("user@example.com", "hashed_pw")

    assert isinstance(result, uuid.UUID)
    assert result == expected_id
    conn.execute.assert_called_once()


async def test_get_by_email_returns_userrow_with_correct_fields():
    """acceptance #8: get_by_email이 id/email/password_hash 가진 row 반환"""
    expected_id = uuid.uuid4()
    mock_row = MagicMock()
    mock_row.id = expected_id
    mock_row.email = "user@example.com"
    mock_row.password_hash = "hashed_pw"

    mock_result = MagicMock()
    mock_result.fetchone.return_value = mock_row

    conn = AsyncMock()
    conn.execute = AsyncMock(return_value=mock_result)

    repo = UserRepository(conn)
    row = await repo.get_by_email("user@example.com")

    assert row is not None
    assert row.id == expected_id
    assert row.email == "user@example.com"
    assert row.password_hash == "hashed_pw"
    assert isinstance(row, UserRow)


async def test_create_then_get_by_email_roundtrip():
    """acceptance #12: 단일 conn에서 create() 후 get_by_email()로 데이터 일관성 검증"""
    user_id = uuid.uuid4()
    email = "roundtrip@example.com"
    password_hash = "hashed_roundtrip"

    create_result = MagicMock()
    create_result.scalar_one.return_value = user_id

    get_row = MagicMock()
    get_row.id = user_id
    get_row.email = email
    get_row.password_hash = password_hash

    get_result = MagicMock()
    get_result.fetchone.return_value = get_row

    conn = AsyncMock()
    conn.execute = AsyncMock(side_effect=[create_result, get_result])

    repo = UserRepository(conn)
    created_id = await repo.create(email, password_hash)
    row = await repo.get_by_email(email)

    assert conn.execute.call_count == 2
    assert row is not None
    assert row.id == created_id
    assert row.email == email
    assert row.password_hash == password_hash
    assert isinstance(row, UserRow)


# ---------------------------------------------------------------------------
# acceptance #6, #13: email lowercase 정규화
# ---------------------------------------------------------------------------


async def test_create_lowercases_email():
    """acceptance #6, #13: create() 호출 시 email이 lowercase로 INSERT됨"""
    expected_id = uuid.uuid4()
    mock_result = MagicMock()
    mock_result.scalar_one.return_value = expected_id

    conn = AsyncMock()
    conn.execute = AsyncMock(return_value=mock_result)

    repo = UserRepository(conn)
    await repo.create("Foo@Bar.com", "hashed_pw")

    stmt = conn.execute.call_args[0][0]
    compiled = stmt.compile()
    assert compiled.params.get("email") == "foo@bar.com", (
        f"Expected 'foo@bar.com' but got {compiled.params.get('email')!r}"
    )


async def test_get_by_email_lowercases_email_for_lookup():
    """acceptance #7, #13: get_by_email()이 lowercase로 변환해 조회"""
    mock_row = MagicMock()
    mock_row.id = uuid.uuid4()
    mock_row.email = "foo@bar.com"
    mock_row.password_hash = "hashed_pw"

    mock_result = MagicMock()
    mock_result.fetchone.return_value = mock_row

    conn = AsyncMock()
    conn.execute = AsyncMock(return_value=mock_result)

    repo = UserRepository(conn)
    row = await repo.get_by_email("Foo@Bar.COM")

    stmt = conn.execute.call_args[0][0]
    compiled = stmt.compile()
    assert compiled.params.get("email_1") == "foo@bar.com" or compiled.params.get("email") == "foo@bar.com", (
        f"WHERE clause email param not lowercased: {compiled.params}"
    )
    assert row is not None


# ---------------------------------------------------------------------------
# acceptance #9, #14: 미존재 email → None
# ---------------------------------------------------------------------------


async def test_get_by_email_returns_none_when_not_found():
    """acceptance #9, #14: 미존재 email에 대해 None 반환"""
    mock_result = MagicMock()
    mock_result.fetchone.return_value = None

    conn = AsyncMock()
    conn.execute = AsyncMock(return_value=mock_result)

    repo = UserRepository(conn)
    result = await repo.get_by_email("nonexistent@example.com")

    assert result is None


# ---------------------------------------------------------------------------
# acceptance #10, #15: 중복 email → IntegrityError 전파
# ---------------------------------------------------------------------------


async def test_create_duplicate_email_propagates_integrity_error():
    """acceptance #10, #15: 동일 email 두 번 create → IntegrityError 전파"""
    conn = AsyncMock()
    conn.execute = AsyncMock(
        side_effect=IntegrityError(
            statement="INSERT INTO users ...",
            params={},
            orig=Exception("unique constraint violated"),
        )
    )

    repo = UserRepository(conn)
    with pytest.raises(IntegrityError):
        await repo.create("duplicate@example.com", "hashed_pw")


# ---------------------------------------------------------------------------
# T-027: UserRow name 필드 + create/get_by_email name 통합
# ---------------------------------------------------------------------------


def test_userrow_has_name_field():
    """acceptance #1: UserRow NamedTuple에 name: str 필드 존재"""
    row = UserRow(
        id=uuid.uuid4(),
        email="user@example.com",
        password_hash="hashed_pw",
        name="홍길동",
    )
    assert row.name == "홍길동"
    assert isinstance(row.name, str)


def test_create_signature_accepts_name_param():
    """acceptance #2: create 시그니처에 name: str 파라미터 존재"""
    sig = inspect.signature(UserRepository.create)
    assert "name" in sig.parameters


async def test_create_includes_name_in_insert_values():
    """acceptance #3: INSERT values dict에 name 키/값 포함"""
    expected_id = uuid.uuid4()
    mock_result = MagicMock()
    mock_result.scalar_one.return_value = expected_id

    conn = AsyncMock()
    conn.execute = AsyncMock(return_value=mock_result)

    repo = UserRepository(conn)
    await repo.create("user@example.com", "hashed_pw", "홍길동")

    stmt = conn.execute.call_args[0][0]
    compiled = stmt.compile()
    assert compiled.params.get("name") == "홍길동", (
        f"INSERT values에 name 없음: {compiled.params}"
    )


async def test_get_by_email_returns_userrow_with_name():
    """acceptance #4: get_by_email 반환 UserRow에 name 속성 존재 (str)"""
    expected_id = uuid.uuid4()
    mock_row = MagicMock()
    mock_row.id = expected_id
    mock_row.email = "user@example.com"
    mock_row.password_hash = "hashed_pw"
    mock_row.name = "홍길동"

    mock_result = MagicMock()
    mock_result.fetchone.return_value = mock_row

    conn = AsyncMock()
    conn.execute = AsyncMock(return_value=mock_result)

    repo = UserRepository(conn)
    row = await repo.get_by_email("user@example.com")

    assert row is not None
    assert hasattr(row, "name")
    assert isinstance(row.name, str)
    assert row.name == "홍길동"


async def test_get_by_email_select_includes_name_column():
    """acceptance #5: SELECT 컬럼 목록에 users_table.c.name 포함"""
    mock_row = MagicMock()
    mock_row.id = uuid.uuid4()
    mock_row.email = "user@example.com"
    mock_row.password_hash = "hashed_pw"
    mock_row.name = "홍길동"

    mock_result = MagicMock()
    mock_result.fetchone.return_value = mock_row

    conn = AsyncMock()
    conn.execute = AsyncMock(return_value=mock_result)

    repo = UserRepository(conn)
    await repo.get_by_email("user@example.com")

    stmt = conn.execute.call_args[0][0]
    compiled_sql = str(stmt.compile())
    assert "name" in compiled_sql, (
        f"SELECT 컬럼에 name 없음: {compiled_sql}"
    )
