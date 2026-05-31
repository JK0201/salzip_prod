"""T-013: users 테이블 + sessions.user_id 마이그레이션 검증.
T-026: users.name 컬럼 + 마이그레이션 검증.
"""
import importlib.util
import os
import subprocess
from pathlib import Path
from unittest.mock import MagicMock, patch

import sqlalchemy as sa
from sqlalchemy.ext.asyncio import create_async_engine

MIGRATION_FILE = Path("alembic/versions/0003_users_user_id.py")
TEST_DB_URL = "postgresql+asyncpg://postgres:postgres@localhost:5432/test"


def _load_migration():
    spec = importlib.util.spec_from_file_location("migration_0003", MIGRATION_FILE)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


# ── Acceptance 1: 파일 존재 ───────────────────────────────────────────────────

def test_migration_file_exists():
    assert MIGRATION_FILE.exists(), f"{MIGRATION_FILE} 파일 없음"


# ── Acceptance 2: revision 정의 ──────────────────────────────────────────────

def test_migration_revision():
    module = _load_migration()
    assert module.revision == "0003_users_user_id"


# ── Acceptance 3: down_revision 정의 ─────────────────────────────────────────

def test_migration_down_revision():
    module = _load_migration()
    assert module.down_revision == "0002_profiles_match"


# ── Acceptance 4: upgrade()가 users 테이블 생성 (id/email/password_hash/created_at) ──

def test_migration_upgrade_creates_users_table():
    module = _load_migration()
    mock_op = MagicMock()
    with patch.object(module, "op", mock_op):
        module.upgrade()

    users_calls = [
        c for c in mock_op.create_table.call_args_list if c.args[0] == "users"
    ]
    assert len(users_calls) == 1, "op.create_table('users', ...) 미호출"

    col_names = {
        a.name for a in users_calls[0].args[1:] if isinstance(a, sa.Column)
    }
    assert {"id", "email", "password_hash", "created_at"} <= col_names, (
        f"users 테이블 컬럼 누락. 발견: {col_names}"
    )


# ── Acceptance 5: upgrade()가 sessions에 user_id 컬럼 추가 ───────────────────

def test_migration_upgrade_adds_user_id_to_sessions():
    module = _load_migration()
    mock_op = MagicMock()
    with patch.object(module, "op", mock_op):
        module.upgrade()

    sessions_add_calls = [
        c for c in mock_op.add_column.call_args_list if c.args[0] == "sessions"
    ]
    assert len(sessions_add_calls) >= 1, "op.add_column('sessions', ...) 미호출"

    col = sessions_add_calls[0].args[1]
    assert isinstance(col, sa.Column)
    assert col.name == "user_id", f"추가된 컬럼명: {col.name}"


# ── Acceptance 6: upgrade()가 sessions.user_id → users.id FK (ON DELETE SET NULL) ──

def test_migration_upgrade_creates_fk_set_null():
    module = _load_migration()
    mock_op = MagicMock()
    with patch.object(module, "op", mock_op):
        module.upgrade()

    fk_calls = mock_op.create_foreign_key.call_args_list
    assert len(fk_calls) >= 1, "op.create_foreign_key 미호출"

    assert any(
        c.kwargs.get("ondelete") == "SET NULL" for c in fk_calls
    ), f"ondelete='SET NULL' FK 없음. 호출: {fk_calls}"


# ── Acceptance 7: downgrade() 존재 및 역순 제거 ───────────────────────────────

def test_migration_downgrade_reverses():
    module = _load_migration()
    assert callable(module.downgrade), "downgrade 미정의"

    mock_op = MagicMock()
    with patch.object(module, "op", mock_op):
        module.downgrade()

    dropped = (
        mock_op.drop_constraint.called
        or mock_op.drop_column.called
        or mock_op.drop_table.called
    )
    assert dropped, "downgrade()에서 drop_* 호출 없음"


# ── Acceptance 8: app/db/tables/users.py 존재, users_table export ─────────────

def test_users_table_importable():
    from app.db.tables.users import users_table  # ImportError → RED

    assert isinstance(users_table, sa.Table), "users_table이 sa.Table이 아님"


# ── Acceptance 9: users_table 컬럼 id/email/password_hash/created_at 존재 ────

def test_users_table_required_columns():
    from app.db.tables.users import users_table

    col_names = {c.name for c in users_table.columns}
    assert {"id", "email", "password_hash", "created_at"} <= col_names, (
        f"컬럼 누락. 발견: {col_names}"
    )


# ── Acceptance 10: email nullable=False, unique=True ─────────────────────────

def test_users_table_email_nullable_false_and_unique():
    from app.db.tables.users import users_table

    email = users_table.c.email
    assert email.nullable is False, "email이 nullable"
    assert email.unique is True, "email이 unique 아님"


# ── Acceptance 11: id primary_key=True ───────────────────────────────────────

def test_users_table_id_is_primary_key():
    from app.db.tables.users import users_table

    assert users_table.c.id.primary_key is True, "id가 PK 아님"


# ── Acceptance 12: sessions_table에 user_id 컬럼 (nullable=True) ─────────────

def test_sessions_table_has_user_id_nullable():
    from app.db.tables.sessions import sessions_table

    assert "user_id" in sessions_table.c, "sessions_table에 user_id 컬럼 없음"
    assert sessions_table.c.user_id.nullable is True, "sessions.user_id가 nullable 아님"


# ── Acceptance 13: sessions.user_id FK → users.id, ondelete='SET NULL' ───────

def test_sessions_user_id_fk_target_and_ondelete():
    from app.db.tables.sessions import sessions_table

    fks = sessions_table.c.user_id.foreign_keys
    assert len(fks) == 1, f"user_id FK 수 이상: {len(fks)}"

    fk = next(iter(fks))
    assert fk.target_fullname == "users.id", f"FK 타겟: {fk.target_fullname}"
    assert fk.ondelete == "SET NULL", f"FK ondelete: {fk.ondelete}"


# ── Acceptance 14: 통합 테스트 — 실제 DB 마이그레이션 적용 후 검증 ─────────────

async def test_migration_applied_tables_exist(monkeypatch):
    monkeypatch.setenv("DATABASE_URL", TEST_DB_URL)
    from app.core.config import get_settings

    get_settings.cache_clear()

    env = {**os.environ, "DATABASE_URL": TEST_DB_URL}
    result = subprocess.run(
        [
            "uv",
            "run",
            "alembic",
            "upgrade",
            "0003_users_user_id",
        ],
        capture_output=True,
        text=True,
        env=env,
    )
    assert result.returncode == 0, f"alembic upgrade 실패:\n{result.stderr}"

    engine = create_async_engine(TEST_DB_URL)
    try:
        async with engine.connect() as conn:
            row = await conn.execute(
                sa.text(
                    "SELECT COUNT(*) FROM information_schema.tables"
                    " WHERE table_schema = 'public' AND table_name = 'users'"
                )
            )
            assert row.scalar() == 1, "DB에 users 테이블 없음"

            row = await conn.execute(
                sa.text(
                    "SELECT COUNT(*) FROM information_schema.columns"
                    " WHERE table_name = 'sessions' AND column_name = 'user_id'"
                )
            )
            assert row.scalar() == 1, "DB에 sessions.user_id 컬럼 없음"
    finally:
        await engine.dispose()


# ── T-026 ────────────────────────────────────────────────────────────────────

MIGRATION_0005_FILE = Path("alembic/versions/0005_users_name.py")


def _load_migration_0005():
    spec = importlib.util.spec_from_file_location("migration_0005", MIGRATION_0005_FILE)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


# ── Acceptance 1: 파일 존재 ──────────────────────────────────────────────────

def test_0005_migration_file_exists():
    assert MIGRATION_0005_FILE.exists(), f"{MIGRATION_0005_FILE} 파일 없음"


# ── Acceptance 2: revision 정의 ─────────────────────────────────────────────

def test_0005_migration_revision():
    module = _load_migration_0005()
    assert module.revision == "0005_users_name"


# ── Acceptance 3: down_revision 정의 ────────────────────────────────────────

def test_0005_migration_down_revision():
    module = _load_migration_0005()
    assert module.down_revision == "0004_profiles_user_id"


# ── Acceptance 4: upgrade()가 users에 name 컬럼 추가 (Text, not null, server_default='') ──

def test_0005_upgrade_adds_name_column_to_users():
    module = _load_migration_0005()
    mock_op = MagicMock()
    with patch.object(module, "op", mock_op):
        module.upgrade()

    users_add_calls = [
        c for c in mock_op.add_column.call_args_list if c.args[0] == "users"
    ]
    assert len(users_add_calls) >= 1, "op.add_column('users', ...) 미호출"

    col = users_add_calls[0].args[1]
    assert isinstance(col, sa.Column), "두 번째 인자가 sa.Column 아님"
    assert col.name == "name", f"컬럼명: {col.name}"
    assert isinstance(col.type, sa.Text), f"타입: {col.type}"
    assert col.nullable is False, "name 컬럼이 nullable"
    assert col.server_default is not None, "server_default 없음"
    assert col.server_default.arg.text == "''", (
        f"server_default.arg.text: {col.server_default.arg.text!r}"
    )


# ── Acceptance 5: downgrade()가 users.name 컬럼 제거 ────────────────────────

def test_0005_downgrade_drops_name_column():
    module = _load_migration_0005()
    mock_op = MagicMock()
    with patch.object(module, "op", mock_op):
        module.downgrade()

    drop_calls = [
        c for c in mock_op.drop_column.call_args_list
        if c.args[0] == "users" and c.args[1] == "name"
    ]
    assert len(drop_calls) >= 1, "op.drop_column('users', 'name') 미호출"


# ── Acceptance 6: users_table 컬럼 목록에 name 포함 ─────────────────────────

def test_users_table_has_name_column():
    from app.db.tables.users import users_table

    assert "name" in users_table.c, "users_table에 name 컬럼 없음"


# ── Acceptance 7: users_table.c.name.type가 sa.Text 인스턴스 ─────────────────

def test_users_table_name_type_is_text():
    from app.db.tables.users import users_table

    assert isinstance(users_table.c.name.type, sa.Text), (
        f"name 컬럼 타입: {users_table.c.name.type}"
    )


# ── Acceptance 8: users_table.c.name.nullable == False ──────────────────────

def test_users_table_name_nullable_false():
    from app.db.tables.users import users_table

    assert users_table.c.name.nullable is False, "users_table.c.name이 nullable"


# ── Acceptance 9: server_default.arg.text == "''" ────────────────────────────

def test_users_table_name_server_default_empty_string():
    from app.db.tables.users import users_table

    sd = users_table.c.name.server_default
    assert sd is not None, "name 컬럼에 server_default 없음"
    assert sd.arg.text == "''", f"server_default.arg.text: {sd.arg.text!r}"
