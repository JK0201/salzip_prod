import importlib.util
import inspect
import re
from pathlib import Path

MIGRATION_FILE = Path("alembic/versions/0009_supports_enrich.py")

LLM_COLUMNS = [
    "monthly_amount_wan",
    "duration_months",
    "asset_limit_wan",
    "support_type",
    "is_homeless_required",
    "separate_from_parents",
]

RAW_AND_CODE_COLUMNS = [
    "agency_name",
    "operating_agency",
    "recruit_count",
    "recruit_unlimited",
    "submission_documents",
    "screening_method",
    "participation_exclusion",
    "reference_urls",
    "keyword_name",
    "view_count",
    "major_code",
    "job_code",
    "school_code",
    "business_code",
]

ALL_NEW_COLUMNS = LLM_COLUMNS + RAW_AND_CODE_COLUMNS


def _load_module():
    spec = importlib.util.spec_from_file_location("migration_0009", MIGRATION_FILE)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def _source() -> str:
    return MIGRATION_FILE.read_text(encoding="utf-8")


# --- acceptance #1 ---
def test_migration_file_exists():
    assert MIGRATION_FILE.exists(), f"{MIGRATION_FILE} not found"


# --- acceptance #2 ---
def test_revision_and_down_revision():
    mod = _load_module()
    assert mod.revision == "0009_supports_enrich"
    assert mod.down_revision == "0008_lifestyle_tags"


# --- acceptance #3 ---
def test_upgrade_and_downgrade_callable():
    mod = _load_module()
    assert callable(mod.upgrade)
    assert callable(mod.downgrade)


# --- acceptance #4 ---
def test_upgrade_source_contains_llm_columns():
    mod = _load_module()
    src = inspect.getsource(mod.upgrade)
    missing = [col for col in LLM_COLUMNS if col not in src]
    assert missing == [], f"upgrade missing LLM columns: {missing}"


# --- acceptance #5 ---
def test_upgrade_source_contains_raw_and_code_columns():
    mod = _load_module()
    src = inspect.getsource(mod.upgrade)
    missing = [col for col in RAW_AND_CODE_COLUMNS if col not in src]
    assert missing == [], f"upgrade missing raw/code columns: {missing}"


# --- acceptance #6 ---
def test_upgrade_source_has_20_add_column_calls():
    mod = _load_module()
    src = inspect.getsource(mod.upgrade)
    count = src.count("op.add_column(")
    assert count >= 20, f"upgrade has {count} op.add_column calls, expected >= 20"


# --- acceptance #7 ---
def test_downgrade_source_has_20_drop_column_calls():
    mod = _load_module()
    src = inspect.getsource(mod.downgrade)
    count = src.count("op.drop_column(")
    assert count >= 20, f"downgrade has {count} op.drop_column calls, expected >= 20"


def test_downgrade_source_contains_all_new_columns():
    mod = _load_module()
    src = inspect.getsource(mod.downgrade)
    missing = [col for col in ALL_NEW_COLUMNS if col not in src]
    assert missing == [], f"downgrade missing columns: {missing}"


# --- acceptance #8 ---
def test_upgrade_source_has_array_type_near_reference_urls():
    mod = _load_module()
    src = inspect.getsource(mod.upgrade)
    idx = src.find("reference_urls")
    assert idx != -1, "'reference_urls' not found in upgrade source"
    context = src[max(0, idx - 200) : idx + 200]
    has_array = re.search(r"ARRAY\s*\(|postgresql\.ARRAY", context)
    assert has_array, (
        f"No ARRAY(...) or postgresql.ARRAY near 'reference_urls'. Context: {context!r}"
    )
