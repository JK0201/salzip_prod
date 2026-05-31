import sqlalchemy as sa

from app.db.tables.job_categories import job_categories_table


def test_import_succeeds():
    assert job_categories_table is not None


def test_is_sqlalchemy_table():
    assert isinstance(job_categories_table, sa.Table)


def test_columns_exact_set():
    assert set(job_categories_table.columns.keys()) == {"id", "name", "sort_order", "created_at"}


def test_id_primary_key_uuid_server_default():
    col = job_categories_table.c.id
    assert col.primary_key is True
    assert isinstance(col.type, sa.UUID)
    assert col.server_default is not None


def test_name_unique_not_nullable():
    col = job_categories_table.c.name
    assert col.unique is True
    assert col.nullable is False


def test_sort_order_integer_not_nullable():
    col = job_categories_table.c.sort_order
    assert isinstance(col.type, sa.Integer)
    assert col.nullable is False


def test_metadata_contains_job_categories():
    import app.db.tables  # noqa: F401
    from app.db.tables import metadata

    assert "job_categories" in metadata.tables
