import importlib.util
import inspect
import re
from pathlib import Path

import pytest

MIGRATION_FILE = Path("alembic/versions/0008_lifestyle_tags.py")

EXPECTED_TAG_NAMES = [
    "식도락",
    "카페 라이프",
    "산책",
    "문화·여가",
    "장보기 편함",
    "역세권",
    "의료 가까이",
    "한적함",
]


def _load_module():
    spec = importlib.util.spec_from_file_location("migration_0008", MIGRATION_FILE)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def _source() -> str:
    return MIGRATION_FILE.read_text(encoding="utf-8")


def _entry_context(src: str, tag_name: str) -> str:
    """bulk_insert 리스트 내 tag_name 이 포함된 dict 블록 추출."""
    idx = src.find(repr(tag_name))
    if idx == -1:
        return ""
    brace_open = src.rfind("{", 0, idx)
    brace_close = src.find("}", idx)
    if brace_open == -1 or brace_close == -1:
        return ""
    return src[brace_open : brace_close + 1]


# --- acceptance #1 ---
def test_migration_file_exists():
    assert MIGRATION_FILE.exists(), f"{MIGRATION_FILE} not found"


# --- acceptance #2 ---
def test_revision_and_down_revision():
    mod = _load_module()
    assert mod.revision == "0008_lifestyle_tags"
    assert mod.down_revision == "0007_job_categories"


# --- acceptance #3 ---
def test_upgrade_and_downgrade_callable():
    mod = _load_module()
    assert callable(mod.upgrade)
    assert callable(mod.downgrade)


# --- acceptance #4 ---
def test_source_contains_bulk_insert():
    src = _source()
    assert src.count("op.bulk_insert(") >= 1


# --- acceptance #5: SELECT count(*) FROM lifestyle_tags = 8 ---
def test_source_contains_all_8_tag_names():
    src = _source()
    missing = [name for name in EXPECTED_TAG_NAMES if repr(name) not in src]
    assert missing == [], f"Missing tag names in source: {missing}"


def test_source_contains_sort_order_values_1_to_8():
    src = _source()
    missing = []
    for n in range(1, 9):
        pattern = rf"'sort_order'\s*:\s*{n}\b"
        if not re.search(pattern, src):
            missing.append(n)
    assert missing == [], f"Missing sort_order values in source: {missing}"


# --- acceptance #6: ORDER BY sort_order LIMIT 3 → 식도락, 카페 라이프, 산책 ---
def test_first_three_tags_appear_in_sort_order():
    src = _source()
    positions = {}
    for name in ["식도락", "카페 라이프", "산책"]:
        idx = src.find(repr(name))
        assert idx != -1, f"'{name}' not found in source"
        positions[name] = idx

    # 소스 내 출현 순서가 sort_order 1→2→3 순이어야 함
    assert positions["식도락"] < positions["카페 라이프"], (
        "'식도락'(sort_order=1) must appear before '카페 라이프'(sort_order=2) in source"
    )
    assert positions["카페 라이프"] < positions["산책"], (
        "'카페 라이프'(sort_order=2) must appear before '산책'(sort_order=3) in source"
    )


def test_first_tag_has_sort_order_1():
    src = _source()
    idx = src.find(repr("식도락"))
    assert idx != -1, "'식도락' not found in source"
    brace_open = src.rfind("{", 0, idx)
    brace_close = src.find("}", idx)
    context = src[brace_open : brace_close + 1]
    assert re.search(r"'sort_order'\s*:\s*1\b", context), (
        f"'식도락' entry missing sort_order=1. Context: {context}"
    )


# --- acceptance #7: WHERE is_inverse = true → 한적함 only ---
def test_hanjeokham_is_inverse_true():
    src = _source()
    context = _entry_context(src, "한적함")
    assert context, "'한적함' entry not found in source"
    assert "True" in context, (
        f"'한적함' entry missing is_inverse=True. Context: {context}"
    )


@pytest.mark.parametrize("name", [
    "식도락", "카페 라이프", "산책", "문화·여가",
    "장보기 편함", "역세권", "의료 가까이",
])
def test_non_inverse_tags_have_is_inverse_false(name):
    src = _source()
    context = _entry_context(src, name)
    assert context, f"'{name}' entry not found in source"
    assert "False" in context, (
        f"'{name}' entry missing is_inverse=False. Context: {context}"
    )


# --- acceptance #8: 의료 가까이 categories에 hospital + pharmacy ---
def test_uiryo_categories_contains_hospital_and_pharmacy():
    src = _source()
    context = _entry_context(src, "의료 가까이")
    assert context, "'의료 가까이' entry not found in source"
    assert "hospital" in context, (
        f"'hospital' not in '의료 가까이' entry. Context: {context}"
    )
    assert "pharmacy" in context, (
        f"'pharmacy' not in '의료 가까이' entry. Context: {context}"
    )


# --- acceptance #9: downgrade → drop_index + drop_table ---
def test_downgrade_drops_index_before_table():
    mod = _load_module()
    src = inspect.getsource(mod.downgrade)
    assert "drop_index" in src, "downgrade missing op.drop_index"
    assert "drop_table" in src, "downgrade missing op.drop_table"
    assert "lifestyle_tags" in src, "downgrade missing 'lifestyle_tags' reference"
    # drop_index must appear before drop_table
    assert src.index("drop_index") < src.index("drop_table"), (
        "downgrade must drop_index before drop_table"
    )
