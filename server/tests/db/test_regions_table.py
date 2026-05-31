"""T-031: regions sa.Table 정의 검증."""
import sqlalchemy as sa


# ── Acceptance 1: import 성공 ─────────────────────────────────────────────────

def test_regions_table_importable():
    from app.db.tables.regions import regions_table  # ImportError → RED

    assert isinstance(regions_table, sa.Table)


# ── Acceptance 2: 테이블명 ────────────────────────────────────────────────────

def test_regions_table_name():
    from app.db.tables.regions import regions_table

    assert regions_table.name == "regions"


# ── Acceptance 3: lawd_cd — CHAR(5), nullable=False, unique=True ─────────────

def test_lawd_cd_type_is_char5():
    from app.db.tables.regions import regions_table

    col = regions_table.c.lawd_cd
    assert isinstance(col.type, sa.CHAR), f"타입: {col.type}"
    assert col.type.length == 5, f"length: {col.type.length}"


def test_lawd_cd_not_nullable():
    from app.db.tables.regions import regions_table

    assert regions_table.c.lawd_cd.nullable is False


def test_lawd_cd_unique():
    from app.db.tables.regions import regions_table

    assert regions_table.c.lawd_cd.unique is True


# ── Acceptance 4: sgg_name — nullable=False ───────────────────────────────────

def test_sgg_name_not_nullable():
    from app.db.tables.regions import regions_table

    assert regions_table.c.sgg_name.nullable is False


# ── Acceptance 5: sido_name server_default — '서울특별시' 포함 ──────────────────

def test_sido_name_server_default_contains_seoul():
    from app.db.tables.regions import regions_table

    col = regions_table.c.sido_name
    assert col.server_default is not None, "sido_name server_default 없음"
    assert "서울특별시" in col.server_default.arg.text, (
        f"server_default: {col.server_default.arg.text!r}"
    )


# ── Acceptance 6: id — primary_key=True, server_default gen_random_uuid() 포함 ──

def test_id_is_primary_key():
    from app.db.tables.regions import regions_table

    assert regions_table.c.id.primary_key is True


def test_id_server_default_contains_gen_random_uuid():
    from app.db.tables.regions import regions_table

    col = regions_table.c.id
    assert col.server_default is not None, "id server_default 없음"
    assert "gen_random_uuid()" in col.server_default.arg.text, (
        f"server_default: {col.server_default.arg.text!r}"
    )


# ── Acceptance 7: created_at — timezone=True, nullable=False ─────────────────

def test_created_at_timezone():
    from app.db.tables.regions import regions_table

    assert regions_table.c.created_at.type.timezone is True


def test_created_at_not_nullable():
    from app.db.tables.regions import regions_table

    assert regions_table.c.created_at.nullable is False


# ── Acceptance 8: app.db.tables import 시 metadata에 'regions' 등록 ────────────

def test_regions_registered_in_metadata():
    import app.db.tables  # noqa: F401
    from app.db.tables import metadata

    assert "regions" in metadata.tables, (
        f"metadata.tables 키: {list(metadata.tables.keys())}"
    )
