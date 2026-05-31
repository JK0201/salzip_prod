import importlib.util
from pathlib import Path
from unittest.mock import MagicMock

import sqlalchemy as sa

MIGRATION_FILE = Path("alembic/versions/0015_drop_profile_uq.py")


def _load_module():
    spec = importlib.util.spec_from_file_location("migration_0015", MIGRATION_FILE)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


# --- acceptance #2 ---
def test_migration_file_exists():
    assert MIGRATION_FILE.exists(), f"{MIGRATION_FILE} not found"


def test_revision():
    mod = _load_module()
    assert mod.revision == "0015_drop_profile_uq"


def test_down_revision():
    mod = _load_module()
    assert mod.down_revision == "0014_commute_cache_segments"


# --- acceptance #3 ---
def test_upgrade_calls_drop_index_with_correct_name():
    mod = _load_module()
    mock_op = MagicMock()
    mod.op = mock_op

    mod.upgrade()

    assert mock_op.drop_index.called, "upgrade()에서 op.drop_index 미호출"
    all_positional_args = [
        arg
        for c in mock_op.drop_index.call_args_list
        for arg in c.args
    ]
    assert "ix_profiles_user_id_unique" in all_positional_args, (
        f"op.drop_index 인자에 'ix_profiles_user_id_unique' 없음. "
        f"호출: {mock_op.drop_index.call_args_list}"
    )


# --- acceptance #4 ---
def test_downgrade_calls_create_index_with_correct_name():
    mod = _load_module()
    mock_op = MagicMock()
    mod.op = mock_op

    mod.downgrade()

    assert mock_op.create_index.called, "downgrade()에서 op.create_index 미호출"
    matching = [
        c for c in mock_op.create_index.call_args_list
        if c.args and c.args[0] == "ix_profiles_user_id_unique"
    ]
    assert len(matching) >= 1, (
        f"op.create_index('ix_profiles_user_id_unique', ...) 미호출. "
        f"호출: {mock_op.create_index.call_args_list}"
    )


def test_downgrade_create_index_unique_true():
    mod = _load_module()
    mock_op = MagicMock()
    mod.op = mock_op

    mod.downgrade()

    matching = [
        c for c in mock_op.create_index.call_args_list
        if c.args and c.args[0] == "ix_profiles_user_id_unique"
    ]
    assert len(matching) >= 1, "op.create_index('ix_profiles_user_id_unique', ...) 미호출"
    c = matching[0]
    assert c.kwargs.get("unique") is True, (
        f"op.create_index unique=True 아님. kwargs: {c.kwargs}"
    )


def test_downgrade_create_index_postgresql_where_not_null():
    mod = _load_module()
    mock_op = MagicMock()
    mod.op = mock_op

    mod.downgrade()

    matching = [
        c for c in mock_op.create_index.call_args_list
        if c.args and c.args[0] == "ix_profiles_user_id_unique"
    ]
    assert len(matching) >= 1, "op.create_index('ix_profiles_user_id_unique', ...) 미호출"
    c = matching[0]
    postgresql_where = c.kwargs.get("postgresql_where")
    assert postgresql_where is not None, (
        f"op.create_index postgresql_where 누락. kwargs: {c.kwargs}"
    )
    where_str = str(postgresql_where)
    assert "user_id" in where_str.lower() and "not null" in where_str.lower(), (
        f"postgresql_where에 'user_id IS NOT NULL' 없음. 값: {where_str!r}"
    )
