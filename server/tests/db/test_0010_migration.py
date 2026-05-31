import importlib.util
import inspect
import re
from pathlib import Path

MIGRATION_FILE = Path("alembic/versions/0010_listings_enrich.py")

ALL_NEW_COLUMNS = [
    "house_type_raw",
    "pre_deposit",
    "pre_monthly_rent",
    "contract_type",
    "use_rr_right",
    "apt_seq",
]


def _load_module():
    spec = importlib.util.spec_from_file_location("migration_0010", MIGRATION_FILE)
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
    assert mod.revision == "0010_listings_enrich"
    assert mod.down_revision == "0009_supports_enrich"


# --- acceptance #3 ---
def test_upgrade_and_downgrade_callable():
    mod = _load_module()
    assert callable(mod.upgrade)
    assert callable(mod.downgrade)


# --- acceptance #4 ---
def test_upgrade_has_6_add_column_calls():
    src = _upgrade_src()
    count = src.count("op.add_column(")
    assert count >= 6, f"upgrade has {count} op.add_column calls, expected >= 6"


# --- acceptance #5 ---
def test_upgrade_contains_all_6_column_names():
    src = _upgrade_src()
    missing = [col for col in ALL_NEW_COLUMNS if col not in src]
    assert missing == [], f"upgrade missing columns: {missing}"


# --- acceptance #6 ---
def test_upgrade_type_annotations():
    src = _upgrade_src()

    for col in ("pre_deposit", "pre_monthly_rent"):
        idx = src.find(col)
        assert idx != -1, f"'{col}' not found in upgrade source"
        context = src[max(0, idx - 200) : idx + 200]
        assert re.search(r"sa\.Integer", context), (
            f"No sa.Integer near '{col}'. Context: {context!r}"
        )

    idx = src.find("use_rr_right")
    assert idx != -1, "'use_rr_right' not found in upgrade source"
    context = src[max(0, idx - 200) : idx + 200]
    assert re.search(r"sa\.Boolean", context), (
        f"No sa.Boolean near 'use_rr_right'. Context: {context!r}"
    )

    for col in ("house_type_raw", "contract_type", "apt_seq"):
        idx = src.find(col)
        assert idx != -1, f"'{col}' not found in upgrade source"
        context = src[max(0, idx - 200) : idx + 200]
        assert re.search(r"sa\.Text", context), (
            f"No sa.Text near '{col}'. Context: {context!r}"
        )


# --- acceptance #7 ---
def test_downgrade_has_6_drop_column_calls():
    src = _downgrade_src()
    count = src.count("op.drop_column(")
    assert count >= 6, f"downgrade has {count} op.drop_column calls, expected >= 6"


def test_downgrade_contains_all_6_column_names():
    src = _downgrade_src()
    missing = [col for col in ALL_NEW_COLUMNS if col not in src]
    assert missing == [], f"downgrade missing columns: {missing}"
