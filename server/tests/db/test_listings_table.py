import sqlalchemy as sa
import pytest

from app.db.tables.listings import listings_table


def test_import_listings_table():
    assert listings_table is not None


def test_region_id_fk_references_regions_cascade():
    col = listings_table.c.region_id
    assert col.nullable is False
    fks = list(col.foreign_keys)
    assert len(fks) == 1
    fk = fks[0]
    assert fk.column.table.name == "regions"
    assert fk.column.name == "id"
    assert fk.ondelete.upper() == "CASCADE"


def test_area_id_fk_references_areas_set_null_nullable():
    col = listings_table.c.area_id
    assert col.nullable is True
    fks = list(col.foreign_keys)
    assert len(fks) == 1
    fk = fks[0]
    assert fk.column.table.name == "areas"
    assert fk.column.name == "id"
    assert fk.ondelete.upper() == "SET NULL"


def test_dedup_hash_char64_not_null_unique():
    col = listings_table.c.dedup_hash
    assert isinstance(col.type, sa.CHAR)
    assert col.type.length == 64
    assert col.nullable is False
    assert col.unique is True


def test_source_payload_type_is_jsonb():
    col = listings_table.c.source_payload
    assert type(col.type).__name__ == "JSONB"


def test_monthly_rent_not_null_server_default_zero():
    col = listings_table.c.monthly_rent
    assert col.nullable is False
    assert col.server_default is not None
    assert "0" in str(col.server_default.arg)


def test_deal_date_type_is_date():
    col = listings_table.c.deal_date
    assert isinstance(col.type, sa.Date)


def test_all_five_indexes_exist():
    index_names = {idx.name for idx in listings_table.indexes}
    expected = {
        "ix_listings_region_deal_type",
        "ix_listings_area_deal_type",
        "ix_listings_kind_dtype_date",
        "ix_listings_building_area",
        "ix_listings_deal_date",
    }
    assert expected <= index_names


def test_area_m2_numeric_8_2():
    col = listings_table.c.area_m2
    assert isinstance(col.type, sa.Numeric)
    assert col.type.precision == 8
    assert col.type.scale == 2


# T-068: RTMS raw 6컬럼

def test_house_type_raw_text_nullable():
    col = listings_table.c.house_type_raw
    assert isinstance(col.type, sa.Text)
    assert col.nullable is True


def test_pre_deposit_integer_nullable():
    col = listings_table.c.pre_deposit
    assert isinstance(col.type, sa.Integer)
    assert col.nullable is True


def test_pre_monthly_rent_integer_nullable():
    col = listings_table.c.pre_monthly_rent
    assert isinstance(col.type, sa.Integer)
    assert col.nullable is True


def test_contract_type_text_nullable():
    col = listings_table.c.contract_type
    assert isinstance(col.type, sa.Text)
    assert col.nullable is True


def test_use_rr_right_boolean_nullable():
    col = listings_table.c.use_rr_right
    assert isinstance(col.type, sa.Boolean)
    assert col.nullable is True


def test_apt_seq_text_nullable():
    col = listings_table.c.apt_seq
    assert isinstance(col.type, sa.Text)
    assert col.nullable is True


def test_existing_columns_not_removed():
    existing = {"estimated_kind", "dedup_hash", "source_payload", "deal_amount", "area_m2"}
    col_names = set(listings_table.c.keys())
    assert existing <= col_names
