import importlib.util
import inspect
import re
from pathlib import Path

MIGRATION_FILE = Path("alembic/versions/0011_area_places.py")

ALL_COLUMNS = [
    "id",
    "area_id",
    "category",
    "kakao_id",
    "place_name",
    "road_address",
    "jibun_address",
    "lat",
    "lng",
    "distance_m",
    "phone",
    "place_url",
    "category_path",
    "created_at",
]

INDEX_NAMES = [
    "ix_area_places_area_id",
    "ix_area_places_category_area_id",
    "ix_area_places_lat_lng",
]


def _load_module():
    spec = importlib.util.spec_from_file_location("migration_0011", MIGRATION_FILE)
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
    assert mod.revision == "0011_area_places"
    assert mod.down_revision == "0010_listings_enrich"


# --- acceptance #3 ---
def test_upgrade_and_downgrade_callable():
    mod = _load_module()
    assert callable(mod.upgrade)
    assert callable(mod.downgrade)


# --- acceptance #4 ---
def test_upgrade_has_create_table_area_places():
    src = _upgrade_src()
    assert "op.create_table('area_places'" in src or 'op.create_table("area_places"' in src, (
        "upgrade must call op.create_table('area_places'...)"
    )


# --- acceptance #5 ---
def test_upgrade_contains_all_14_column_names():
    src = _upgrade_src()
    missing = [col for col in ALL_COLUMNS if col not in src]
    assert missing == [], f"upgrade missing columns: {missing}"


# --- acceptance #6 ---
def test_upgrade_has_areas_id_foreign_key():
    src = _upgrade_src()
    assert "areas.id" in src, "upgrade must reference 'areas.id' for FK constraint"
    has_fk = "sa.ForeignKeyConstraint" in src or "sa.ForeignKey" in src
    assert has_fk, "upgrade must use sa.ForeignKeyConstraint or sa.ForeignKey for areas.id"


# --- acceptance #7 ---
def test_upgrade_has_unique_constraint_area_id_kakao_id():
    src = _upgrade_src()
    assert "area_id" in src and "kakao_id" in src, (
        "upgrade must contain both 'area_id' and 'kakao_id'"
    )
    has_unique = (
        "UniqueConstraint" in src
        or re.search(r"unique\s*=\s*True", src)
    )
    assert has_unique, "upgrade must have a UniqueConstraint or unique=True on (area_id, kakao_id)"
    # area_id and kakao_id must appear in same constraint block
    uc_match = re.search(r"UniqueConstraint\([^)]*area_id[^)]*kakao_id[^)]*\)", src)
    uc_match_rev = re.search(r"UniqueConstraint\([^)]*kakao_id[^)]*area_id[^)]*\)", src)
    assert uc_match or uc_match_rev, (
        "UniqueConstraint must include both 'area_id' and 'kakao_id' in the same call"
    )


# --- acceptance #8 ---
def test_upgrade_has_three_indexes():
    src = _upgrade_src()
    count = src.count("op.create_index(")
    assert count >= 3, f"upgrade has {count} op.create_index calls, expected >= 3"
    missing = [name for name in INDEX_NAMES if name not in src]
    assert missing == [], f"upgrade missing index names: {missing}"


# --- acceptance #9 ---
def test_downgrade_drops_area_places():
    src = _downgrade_src()
    assert "op.drop_table('area_places')" in src or 'op.drop_table("area_places")' in src, (
        "downgrade must call op.drop_table('area_places')"
    )
