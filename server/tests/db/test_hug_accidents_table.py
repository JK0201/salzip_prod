import sqlalchemy as sa

from app.db.tables.hug_accidents import hug_accidents_table


def test_import_hug_accidents_table():
    assert hug_accidents_table is not None


def test_year_not_nullable():
    assert hug_accidents_table.c.year.nullable is False


def test_accident_count_nullable():
    assert hug_accidents_table.c.accident_count.nullable is True


def test_source_server_default_contains_expected_value():
    col = hug_accidents_table.c.source
    sd = col.server_default
    assert sd is not None
    sd_text = str(sd.arg) if hasattr(sd, "arg") else str(sd)
    assert "data.go.kr 15002597" in sd_text


def test_unique_constraint_natural_key():
    uc = next(
        (
            c
            for c in hug_accidents_table.constraints
            if isinstance(c, sa.UniqueConstraint) and c.name == "uq_hug_accidents_natural"
        ),
        None,
    )
    assert uc is not None, "UniqueConstraint 'uq_hug_accidents_natural' 없음"
    uc_cols = [col.name for col in uc.columns]
    assert uc_cols == ["year", "guarantee_type"]


def test_index_year_type_exists():
    index_names = {idx.name for idx in hug_accidents_table.indexes}
    assert "ix_hug_accidents_year_type" in index_names
