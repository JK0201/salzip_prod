import sqlalchemy as sa

from app.db.tables.commute_cache import commute_cache_table


def test_import_commute_cache_table():
    assert commute_cache_table is not None


def test_origin_lat_numeric_not_nullable():
    col = commute_cache_table.c.origin_lat
    assert isinstance(col.type, sa.Numeric)
    assert col.type.precision == 9
    assert col.type.scale == 4
    assert col.nullable is False


def test_origin_lng_numeric_not_nullable():
    col = commute_cache_table.c.origin_lng
    assert isinstance(col.type, sa.Numeric)
    assert col.type.precision == 9
    assert col.type.scale == 4
    assert col.nullable is False


def test_area_id_foreign_key_cascade_not_nullable():
    col = commute_cache_table.c.area_id
    assert col.nullable is False
    fk = next(iter(col.foreign_keys))
    assert fk.column.table.name == "areas"
    assert fk.column.name == "id"
    assert fk.ondelete.upper() == "CASCADE"


def test_total_time_min_not_nullable():
    assert commute_cache_table.c.total_time_min.nullable is False


def test_payment_won_nullable():
    assert commute_cache_table.c.payment_won.nullable is True


def test_unique_constraint_natural_key():
    uc = next(
        (
            c
            for c in commute_cache_table.constraints
            if isinstance(c, sa.UniqueConstraint) and c.name == "uq_commute_cache_natural"
        ),
        None,
    )
    assert uc is not None, "UniqueConstraint 'uq_commute_cache_natural' 없음"
    uc_cols = [col.name for col in uc.columns]
    assert uc_cols == ["origin_lat", "origin_lng", "area_id"]


def test_index_fetched_at_exists():
    index_names = {idx.name for idx in commute_cache_table.indexes}
    assert "ix_commute_cache_fetched_at" in index_names


def test_transfers_column_exists():
    assert "transfers" in commute_cache_table.c


def test_transfers_column_is_integer_and_nullable():
    col = commute_cache_table.c.transfers
    assert isinstance(col.type, sa.Integer)
    assert col.nullable is True


def test_total_walk_m_column_exists():
    assert "total_walk_m" in commute_cache_table.c


def test_total_walk_m_column_is_integer_and_nullable():
    col = commute_cache_table.c.total_walk_m
    assert isinstance(col.type, sa.Integer)
    assert col.nullable is True
