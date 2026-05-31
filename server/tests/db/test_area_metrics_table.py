import pytest
import sqlalchemy as sa

from app.db.tables.area_metrics import area_metrics_table

COUNT_COLUMNS = [
    "mart_count",
    "cafe_count",
    "food_count",
    "hospital_count",
    "pharmacy_count",
    "culture_count",
    "subway_count",
    "park_count",
]


def test_import_area_metrics_table():
    assert area_metrics_table is not None


def test_primary_key_is_area_id_only():
    pk_cols = list(area_metrics_table.primary_key.columns.keys())
    assert pk_cols == ["area_id"]


def test_area_id_foreign_key_references_areas_id_with_cascade():
    fks = list(area_metrics_table.c.area_id.foreign_keys)
    assert len(fks) == 1
    fk = fks[0]
    assert fk.column.table.name == "areas"
    assert fk.column.name == "id"
    assert fk.ondelete.upper() == "CASCADE"


@pytest.mark.parametrize("col_name", COUNT_COLUMNS)
def test_count_column_not_nullable(col_name):
    col = area_metrics_table.c[col_name]
    assert col.nullable is False


@pytest.mark.parametrize("col_name", COUNT_COLUMNS)
def test_count_column_server_default_is_zero(col_name):
    col = area_metrics_table.c[col_name]
    sd = col.server_default
    assert sd is not None
    assert "0" in str(sd.arg)


def test_updated_at_not_nullable():
    assert area_metrics_table.c.updated_at.nullable is False


# T-075: 집계 컬럼 5개 추가 검증

NEW_AGGREGATE_COLUMNS = [
    "avg_jeonse_ratio",
    "flood_ratio",
    "avg_build_year",
    "listing_count",
    "flood_risk_count",
]


@pytest.mark.parametrize("col_name", NEW_AGGREGATE_COLUMNS)
def test_new_aggregate_columns_exist(col_name):
    assert col_name in area_metrics_table.c


def test_avg_jeonse_ratio_type_numeric_5_2():
    col_type = area_metrics_table.c.avg_jeonse_ratio.type
    assert isinstance(col_type, sa.Numeric)
    assert col_type.precision == 5
    assert col_type.scale == 2


def test_flood_ratio_type_numeric_5_4():
    col_type = area_metrics_table.c.flood_ratio.type
    assert isinstance(col_type, sa.Numeric)
    assert col_type.precision == 5
    assert col_type.scale == 4


@pytest.mark.parametrize("col_name", ["avg_build_year", "listing_count", "flood_risk_count"])
def test_integer_aggregate_columns_type(col_name):
    col_type = area_metrics_table.c[col_name].type
    assert isinstance(col_type, sa.Integer)


@pytest.mark.parametrize("col_name", NEW_AGGREGATE_COLUMNS)
def test_new_aggregate_columns_nullable(col_name):
    assert area_metrics_table.c[col_name].nullable is True
