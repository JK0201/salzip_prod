import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import ARRAY

from app.db.tables.lifestyle_tags import lifestyle_tags_table


def test_import_succeeds():
    assert lifestyle_tags_table is not None


def test_is_sqlalchemy_table_with_correct_name():
    assert isinstance(lifestyle_tags_table, sa.Table)
    assert lifestyle_tags_table.name == "lifestyle_tags"


def test_columns_exact_set():
    assert set(lifestyle_tags_table.columns.keys()) == {
        "id",
        "name",
        "sort_order",
        "categories",
        "is_inverse",
        "created_at",
    }


def test_id_primary_key_and_uuid_type():
    col = lifestyle_tags_table.c.id
    assert col.primary_key is True
    assert isinstance(col.type, sa.UUID)


def test_name_unique_and_not_nullable():
    col = lifestyle_tags_table.c.name
    assert col.unique is True
    assert col.nullable is False


def test_categories_array_of_text():
    col = lifestyle_tags_table.c.categories
    assert isinstance(col.type, ARRAY)
    assert isinstance(col.type.item_type, sa.Text)
    assert col.nullable is False


def test_is_inverse_boolean_with_false_server_default():
    col = lifestyle_tags_table.c.is_inverse
    assert isinstance(col.type, sa.Boolean)
    assert col.server_default is not None
    assert str(col.server_default.arg) == "false"
    assert col.nullable is False


def test_init_export_and_job_categories_not_broken():
    from app.db.tables import job_categories_table, lifestyle_tags_table as lt

    assert isinstance(lt, sa.Table)
    assert isinstance(job_categories_table, sa.Table)
