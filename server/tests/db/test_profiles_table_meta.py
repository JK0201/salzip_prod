import sqlalchemy as sa


# --- acceptance #1 ---
def test_profiles_table_no_unique_user_id_index():
    from app.db.tables.profiles import profiles_table

    index_names = {idx.name for idx in profiles_table.indexes}
    assert "ix_profiles_user_id_unique" not in index_names, (
        f"ix_profiles_user_id_unique 인덱스가 profiles_table에 여전히 존재함. "
        f"인덱스 목록: {index_names}"
    )


def test_profiles_table_columns_intact():
    from app.db.tables.profiles import profiles_table

    col_names = {c.name for c in profiles_table.columns}
    assert {"id", "session_id", "user_id", "payload", "created_at"} <= col_names, (
        f"profiles_table 컬럼 누락. 발견: {col_names}"
    )
