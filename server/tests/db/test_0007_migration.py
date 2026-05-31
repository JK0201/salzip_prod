import importlib.util
import inspect
import re
from pathlib import Path

MIGRATION_FILE = Path("alembic/versions/0007_job_categories.py")

EXPECTED_CATEGORIES = [
    "개발", "경영", "마케팅", "디자인", "영업",
    "고객서비스", "미디어", "HR", "엔지니어링", "금융",
    "제조", "의료", "교육", "게임", "기타",
]


def _load_module():
    spec = importlib.util.spec_from_file_location("migration_0007", MIGRATION_FILE)
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
    assert mod.revision == "0007_job_categories"
    assert mod.down_revision == "0006_recommend_data"


# --- acceptance #3 ---
def test_upgrade_and_downgrade_callable():
    mod = _load_module()
    assert callable(mod.upgrade)
    assert callable(mod.downgrade)


# --- acceptance #4 ---
def test_source_contains_create_table_job_categories():
    src = _source()
    assert "op.create_table(" in src
    assert "'job_categories'" in src


# --- acceptance #5 ---
def test_source_contains_bulk_insert():
    src = _source()
    assert src.count("op.bulk_insert(") >= 1


# --- acceptance #6 ---
def test_source_contains_all_15_category_names():
    src = _source()
    missing = [name for name in EXPECTED_CATEGORIES if name not in src]
    assert missing == [], f"Missing category names in source: {missing}"


# --- acceptance #7 ---
def test_source_contains_sort_order_values_1_to_15():
    src = _source()
    missing = []
    for n in range(1, 16):
        pattern = rf"'sort_order'\s*:\s*{n}\b"
        if not re.search(pattern, src):
            missing.append(n)
    assert missing == [], f"Missing sort_order values in source: {missing}"


# --- acceptance #8 ---
def test_downgrade_source_contains_drop_table_job_categories():
    mod = _load_module()
    src = inspect.getsource(mod.downgrade)
    assert "drop_table" in src
    assert "'job_categories'" in src
