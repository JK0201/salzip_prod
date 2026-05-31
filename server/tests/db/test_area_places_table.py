import sqlalchemy as sa
from sqlalchemy import UniqueConstraint

from app.db.tables.area_places import area_places_table


def test_area_places_table_is_sqlalchemy_table():
    assert isinstance(area_places_table, sa.Table)
    assert area_places_table.name == "area_places"


def test_area_places_table_column_names():
    expected = {
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
    }
    assert set(area_places_table.columns.keys()) == expected


def test_area_id_nullable_false_and_fk_to_areas():
    col = area_places_table.c.area_id
    assert col.nullable is False
    fk_targets = {fk.target_fullname for fk in col.foreign_keys}
    assert "areas.id" in fk_targets


def test_lat_lng_numeric_precision_scale():
    for col_name in ("lat", "lng"):
        col = area_places_table.c[col_name]
        assert isinstance(col.type, sa.Numeric), f"{col_name} 타입이 Numeric 아님"
        assert col.type.precision == 9, f"{col_name} precision != 9"
        assert col.type.scale == 6, f"{col_name} scale != 6"


def test_created_at_server_default_contains_now():
    col = area_places_table.c.created_at
    assert col.server_default is not None
    clause_text = str(col.server_default.arg)
    assert "now()" in clause_text


def test_unique_constraint_area_id_kakao_id():
    uc_col_sets = []
    for constraint in area_places_table.constraints:
        if isinstance(constraint, UniqueConstraint):
            uc_col_sets.append({c.name for c in constraint.columns})
    assert {"area_id", "kakao_id"} in uc_col_sets


def test_import_area_places_from_tables_package():
    from app.db.tables import area_places  # noqa: F401
