import importlib.util
import inspect
import re
from pathlib import Path

MIGRATION_FILE = Path("alembic/versions/0013_area_metrics_aggregates.py")

AGGREGATE_COLUMNS = [
    "avg_jeonse_ratio",
    "flood_ratio",
    "avg_build_year",
    "listing_count",
    "flood_risk_count",
]


def _load_module():
    spec = importlib.util.spec_from_file_location("migration_0013", MIGRATION_FILE)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def _upgrade_src() -> str:
    mod = _load_module()
    return inspect.getsource(mod.upgrade)


def _downgrade_src() -> str:
    mod = _load_module()
    return inspect.getsource(mod.downgrade)


# --- acceptance #1 ---
def test_migration_file_exists():
    assert MIGRATION_FILE.exists(), f"{MIGRATION_FILE} not found"


# --- acceptance #2 ---
def test_revision_and_down_revision():
    mod = _load_module()
    assert mod.revision == "0013_area_metrics_aggregates"
    assert mod.down_revision == "0012_income_monthly"


# --- acceptance #3 ---
def test_upgrade_contains_all_five_column_names():
    src = _upgrade_src()
    missing = [col for col in AGGREGATE_COLUMNS if col not in src]
    assert missing == [], f"upgrade missing columns: {missing}"


# --- acceptance #4 ---
def test_upgrade_has_numeric_5_2_for_avg_jeonse_ratio():
    src = _upgrade_src()
    # NUMERIC(5, 2) or Numeric(5, 2) — spaces optional
    has_5_2 = bool(re.search(r"(?:NUMERIC|Numeric)\s*\(\s*5\s*,\s*2\s*\)", src))
    assert has_5_2, "upgrade must use NUMERIC(5, 2) for avg_jeonse_ratio"


def test_upgrade_has_numeric_5_4_for_flood_ratio():
    src = _upgrade_src()
    has_5_4 = bool(re.search(r"(?:NUMERIC|Numeric)\s*\(\s*5\s*,\s*4\s*\)", src))
    assert has_5_4, "upgrade must use NUMERIC(5, 4) for flood_ratio"


# --- acceptance #5 ---
def test_upgrade_has_at_least_five_add_column_calls():
    src = _upgrade_src()
    count = src.count("op.add_column(")
    assert count >= 5, f"upgrade has {count} op.add_column calls, expected >= 5"


def test_upgrade_add_column_calls_target_area_metrics():
    src = _upgrade_src()
    # Every op.add_column( ... ) block must reference 'area_metrics'
    # Find all add_column call segments and check each contains area_metrics
    matches = re.findall(r"op\.add_column\([^)]*\)", src, re.DOTALL)
    assert len(matches) >= 5, f"found only {len(matches)} op.add_column blocks"
    for m in matches:
        assert "area_metrics" in m, f"op.add_column call does not reference 'area_metrics': {m!r}"


# --- acceptance #6 ---
def test_downgrade_has_at_least_five_drop_column_calls():
    src = _downgrade_src()
    count = src.count("op.drop_column(")
    assert count >= 5, f"downgrade has {count} op.drop_column calls, expected >= 5"


def test_downgrade_contains_all_five_column_names():
    src = _downgrade_src()
    missing = [col for col in AGGREGATE_COLUMNS if col not in src]
    assert missing == [], f"downgrade missing columns: {missing}"
