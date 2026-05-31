import sqlalchemy as sa
import pytest

from app.db.tables.areas import areas_table


def test_import_areas_table():
    assert areas_table is not None


def test_region_id_fk_references_regions_cascade():
    col = areas_table.c.region_id
    assert col.nullable is False
    fks = list(col.foreign_keys)
    assert len(fks) == 1
    fk = fks[0]
    assert fk.column.table.name == "regions"
    assert fk.column.name == "id"
    assert fk.ondelete.upper() == "CASCADE"


def test_emd_cd_char8_not_null_unique():
    col = areas_table.c.emd_cd
    assert isinstance(col.type, sa.CHAR)
    assert col.type.length == 8
    assert col.nullable is False
    assert col.unique is True


def test_lat_nullable_numeric_9_6():
    col = areas_table.c.lat
    assert col.nullable is True
    assert isinstance(col.type, sa.Numeric)
    assert col.type.precision == 9
    assert col.type.scale == 6


def test_lng_nullable_numeric_9_6():
    col = areas_table.c.lng
    assert col.nullable is True
    assert isinstance(col.type, sa.Numeric)
    assert col.type.precision == 9
    assert col.type.scale == 6


def test_indexes_region_id_and_lat_lng_exist():
    index_names = {idx.name for idx in areas_table.indexes}
    assert "ix_areas_region_id" in index_names
    assert "ix_areas_lat_lng" in index_names


def test_updated_at_not_null_server_default_now():
    col = areas_table.c.updated_at
    assert col.nullable is False
    assert col.server_default is not None
    assert "now()" in col.server_default.arg.text
