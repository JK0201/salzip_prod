import importlib.util
from pathlib import Path
from unittest.mock import MagicMock

import sqlalchemy as sa

MIGRATION_FILE = Path("alembic/versions/0014_commute_cache_segments.py")


def _load_module():
    spec = importlib.util.spec_from_file_location("migration_0014", MIGRATION_FILE)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


# --- acceptance #1 ---
def test_migration_file_exists():
    assert MIGRATION_FILE.exists(), f"{MIGRATION_FILE} not found"


# --- acceptance #2 ---
def test_revision():
    mod = _load_module()
    assert mod.revision == "0014_commute_cache_segments"


# --- acceptance #3 ---
def test_down_revision():
    mod = _load_module()
    assert mod.down_revision == "0013_area_metrics_aggregates"


# --- acceptance #4: upgrade callable ---
def test_upgrade_is_callable():
    mod = _load_module()
    assert callable(mod.upgrade)


# --- acceptance #4: mock op → add_column 2회, transfers + total_walk_m ---
def test_upgrade_add_column_called_twice():
    mod = _load_module()
    mock_op = MagicMock()
    mod.op = mock_op

    mod.upgrade()

    assert mock_op.add_column.call_count == 2, (
        f"upgrade should call op.add_column exactly 2 times, "
        f"got {mock_op.add_column.call_count}"
    )


def test_upgrade_add_column_targets_commute_cache():
    mod = _load_module()
    mock_op = MagicMock()
    mod.op = mock_op

    mod.upgrade()

    for c in mock_op.add_column.call_args_list:
        table_name = c.args[0]
        assert table_name == "commute_cache", (
            f"op.add_column should target 'commute_cache', got {table_name!r}"
        )


def test_upgrade_add_column_includes_transfers():
    mod = _load_module()
    mock_op = MagicMock()
    mod.op = mock_op

    mod.upgrade()

    col_names = [c.args[1].name for c in mock_op.add_column.call_args_list]
    assert "transfers" in col_names, (
        f"upgrade must add 'transfers' column, found: {col_names}"
    )


def test_upgrade_add_column_includes_total_walk_m():
    mod = _load_module()
    mock_op = MagicMock()
    mod.op = mock_op

    mod.upgrade()

    col_names = [c.args[1].name for c in mock_op.add_column.call_args_list]
    assert "total_walk_m" in col_names, (
        f"upgrade must add 'total_walk_m' column, found: {col_names}"
    )


def test_upgrade_columns_are_integer_nullable():
    mod = _load_module()
    mock_op = MagicMock()
    mod.op = mock_op

    mod.upgrade()

    for c in mock_op.add_column.call_args_list:
        col: sa.Column = c.args[1]
        assert isinstance(col.type, sa.Integer), (
            f"column '{col.name}' should be Integer, got {type(col.type)}"
        )
        assert col.nullable is True, (
            f"column '{col.name}' should be nullable=True"
        )


# --- acceptance #5: downgrade callable ---
def test_downgrade_is_callable():
    mod = _load_module()
    assert callable(mod.downgrade)


# --- acceptance #5: mock op → drop_column 2회 ---
def test_downgrade_drop_column_called_twice():
    mod = _load_module()
    mock_op = MagicMock()
    mod.op = mock_op

    mod.downgrade()

    assert mock_op.drop_column.call_count == 2, (
        f"downgrade should call op.drop_column exactly 2 times, "
        f"got {mock_op.drop_column.call_count}"
    )


def test_downgrade_drop_column_targets_commute_cache():
    mod = _load_module()
    mock_op = MagicMock()
    mod.op = mock_op

    mod.downgrade()

    for c in mock_op.drop_column.call_args_list:
        table_name = c.args[0]
        assert table_name == "commute_cache", (
            f"op.drop_column should target 'commute_cache', got {table_name!r}"
        )
