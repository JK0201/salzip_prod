import sqlalchemy as sa

from app.db.tables.area_trends import area_trends_table


def test_import_area_trends_table():
    assert area_trends_table is not None


def test_region_id_nullable_and_fk_cascade():
    col = area_trends_table.c.region_id
    assert col.nullable is True
    fks = list(col.foreign_keys)
    assert len(fks) == 1
    fk = fks[0]
    assert fk.column.table.name == "regions"
    assert fk.column.name == "id"
    assert fk.ondelete.upper() == "CASCADE"


def test_value_numeric_14_4_and_nullable():
    col = area_trends_table.c.value
    assert col.nullable is True
    t = col.type
    assert isinstance(t, sa.Numeric)
    assert t.precision == 14
    assert t.scale == 4


def test_statbl_id_not_nullable():
    assert area_trends_table.c.statbl_id.nullable is False


def test_unique_constraint_natural_key():
    uc = next(
        (
            c
            for c in area_trends_table.constraints
            if isinstance(c, sa.UniqueConstraint) and c.name == "uq_area_trends_natural"
        ),
        None,
    )
    assert uc is not None, "UniqueConstraint 'uq_area_trends_natural' 없음"
    uc_cols = [col.name for col in uc.columns]
    assert uc_cols == ["region_label", "metric", "period", "statbl_id"]


def test_indexes_exist():
    index_names = {idx.name for idx in area_trends_table.indexes}
    assert "ix_area_trends_region_metric_period" in index_names
    assert "ix_area_trends_label_metric_period" in index_names
