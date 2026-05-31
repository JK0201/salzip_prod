import sqlalchemy as sa

from app.db.tables.favorites import favorites_table


def test_import_favorites_table():
    assert favorites_table is not None


def test_primary_key_composite_user_id_listing_id():
    pk_cols = favorites_table.primary_key.columns.keys()
    assert list(pk_cols) == ["user_id", "listing_id"]


def test_user_id_foreign_key_users_cascade():
    col = favorites_table.c.user_id
    assert col.nullable is False
    fk = next(iter(col.foreign_keys))
    assert fk.column.table.name == "users"
    assert fk.column.name == "id"
    assert fk.ondelete.upper() == "CASCADE"


def test_listing_id_foreign_key_listings_cascade():
    col = favorites_table.c.listing_id
    assert col.nullable is False
    fk = next(iter(col.foreign_keys))
    assert fk.column.table.name == "listings"
    assert fk.column.name == "id"
    assert fk.ondelete.upper() == "CASCADE"


def test_index_ix_favorites_user_id_exists():
    index_names = {idx.name for idx in favorites_table.indexes}
    assert "ix_favorites_user_id" in index_names


def test_created_at_not_nullable():
    assert favorites_table.c.created_at.nullable is False
