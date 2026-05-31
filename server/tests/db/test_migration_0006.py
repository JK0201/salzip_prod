import importlib.util
import os
import subprocess
from pathlib import Path

import psycopg
import pytest

MIGRATION_FILE = Path("alembic/versions/0006_recommend_data.py")
TEST_DB_DSN = "postgresql://postgres:postgres@localhost:5432/test"
TEST_ENV = {
    **os.environ,
    "DATABASE_URL": "postgresql+asyncpg://postgres:postgres@localhost:5432/test",
}

EXPECTED_TABLES = [
    "regions",
    "areas",
    "listings",
    "support_programs",
    "area_metrics",
    "area_trends",
    "hug_accidents",
    "commute_cache",
    "favorites",
]
EXPECTED_INDEXES = [
    "ix_listings_building_area",
    "ix_areas_lat_lng",
    "ix_commute_cache_fetched_at",
]
EXPECTED_UNIQUE_CONSTRAINTS = [
    "uq_area_trends_natural",
    "uq_hug_accidents_natural",
    "uq_commute_cache_natural",
]


def _load_module():
    spec = importlib.util.spec_from_file_location("migration_0006", MIGRATION_FILE)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


# --- acceptance #1 ---
def test_migration_file_exists():
    assert MIGRATION_FILE.exists(), f"{MIGRATION_FILE} not found"


# --- acceptance #2 ---
def test_revision_and_down_revision():
    mod = _load_module()
    assert mod.revision == "0006_recommend_data"
    assert mod.down_revision == "0005_users_name"


# --- acceptance #3 ---
def test_upgrade_and_downgrade_callable():
    mod = _load_module()
    assert callable(mod.upgrade)
    assert callable(mod.downgrade)


# --- DB integration fixture (acceptance #4–7) ---

@pytest.fixture(scope="module")
def db_upgraded():
    result = subprocess.run(
        ["uv", "run", "alembic", "upgrade", "head"],
        capture_output=True,
        env=TEST_ENV,
    )
    yield result
    subprocess.run(
        ["uv", "run", "alembic", "downgrade", "base"],
        capture_output=True,
        env=TEST_ENV,
    )


# --- acceptance #4 ---
def test_upgrade_exit_code_zero(db_upgraded):
    assert db_upgraded.returncode == 0, db_upgraded.stderr.decode()


# --- acceptance #5 ---
def test_nine_tables_exist_after_upgrade(db_upgraded):
    with psycopg.connect(TEST_DB_DSN) as conn:
        rows = conn.execute(
            "SELECT table_name FROM information_schema.tables"
            " WHERE table_schema='public' AND table_name = ANY(%s)",
            (EXPECTED_TABLES,),
        ).fetchall()
    found = {r[0] for r in rows}
    assert found == set(EXPECTED_TABLES), f"Missing tables: {set(EXPECTED_TABLES) - found}"


# --- acceptance #6 ---
def test_three_indexes_exist_after_upgrade(db_upgraded):
    with psycopg.connect(TEST_DB_DSN) as conn:
        rows = conn.execute(
            "SELECT indexname FROM pg_indexes"
            " WHERE schemaname='public' AND indexname = ANY(%s)",
            (EXPECTED_INDEXES,),
        ).fetchall()
    found = {r[0] for r in rows}
    assert found == set(EXPECTED_INDEXES), f"Missing indexes: {set(EXPECTED_INDEXES) - found}"


# --- acceptance #7 ---
def test_three_unique_constraints_exist_after_upgrade(db_upgraded):
    with psycopg.connect(TEST_DB_DSN) as conn:
        rows = conn.execute(
            "SELECT conname FROM pg_constraint"
            " WHERE contype='u' AND conname = ANY(%s)",
            (EXPECTED_UNIQUE_CONSTRAINTS,),
        ).fetchall()
    found = {r[0] for r in rows}
    assert found == set(EXPECTED_UNIQUE_CONSTRAINTS), (
        f"Missing constraints: {set(EXPECTED_UNIQUE_CONSTRAINTS) - found}"
    )


# --- acceptance #8 ---
def test_downgrade_removes_nine_tables():
    # Ensure upgraded before testing downgrade
    subprocess.run(
        ["uv", "run", "alembic", "upgrade", "head"],
        capture_output=True,
        env=TEST_ENV,
    )
    result = subprocess.run(
        ["uv", "run", "alembic", "downgrade", "0005_users_name"],
        capture_output=True,
        env=TEST_ENV,
    )
    assert result.returncode == 0, result.stderr.decode()

    with psycopg.connect(TEST_DB_DSN) as conn:
        rows = conn.execute(
            "SELECT table_name FROM information_schema.tables"
            " WHERE table_schema='public' AND table_name = ANY(%s)",
            (EXPECTED_TABLES,),
        ).fetchall()
    found = {r[0] for r in rows}
    assert found == set(), f"Tables still present after downgrade: {found}"
