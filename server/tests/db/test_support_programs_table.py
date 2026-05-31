import sqlalchemy as sa
import pytest

from app.db.tables.support_programs import support_programs_table


def test_import_support_programs_table():
    assert support_programs_table is not None


def test_plcy_no_not_null_unique():
    col = support_programs_table.c.plcy_no
    assert col.nullable is False
    assert col.unique is True


def test_housing_types_type_is_array():
    col = support_programs_table.c.housing_types
    assert type(col.type).__name__ == "ARRAY"


def test_raw_type_is_jsonb():
    col = support_programs_table.c.raw
    assert type(col.type).__name__ == "JSONB"


def test_rules_extracted_type_is_jsonb():
    col = support_programs_table.c.rules_extracted
    assert type(col.type).__name__ == "JSONB"


def test_three_indexes_exist():
    index_names = {idx.name for idx in support_programs_table.indexes}
    expected = {
        "ix_support_programs_category_m",
        "ix_support_programs_age",
        "ix_support_programs_card_key",
    }
    assert expected <= index_names


def test_card_key_nullable():
    col = support_programs_table.c.card_key
    assert col.nullable is True


def test_start_date_type_is_date_and_nullable():
    col = support_programs_table.c.start_date
    assert isinstance(col.type, sa.Date)
    assert col.nullable is True


# T-066: LLM 추출 6개 컬럼 존재
def test_llm_extracted_6_columns_exist():
    new_cols = [
        "monthly_amount_wan",
        "duration_months",
        "asset_limit_wan",
        "support_type",
        "is_homeless_required",
        "separate_from_parents",
    ]
    col_names = set(support_programs_table.c.keys())
    for col in new_cols:
        assert col in col_names, f"컬럼 누락: {col}"


# T-066: raw 메타 + 추가 코드 14개 컬럼 존재
def test_raw_meta_and_code_14_columns_exist():
    new_cols = [
        "agency_name",
        "operating_agency",
        "recruit_count",
        "recruit_unlimited",
        "submission_documents",
        "screening_method",
        "participation_exclusion",
        "reference_urls",
        "keyword_name",
        "view_count",
        "major_code",
        "job_code",
        "school_code",
        "business_code",
    ]
    col_names = set(support_programs_table.c.keys())
    for col in new_cols:
        assert col in col_names, f"컬럼 누락: {col}"


# T-066: reference_urls 타입이 ARRAY
def test_reference_urls_type_is_array():
    col = support_programs_table.c.reference_urls
    assert type(col.type).__name__ == "ARRAY"


# T-066: Boolean 컬럼 타입 검증
def test_boolean_columns_are_sa_boolean():
    bool_cols = ["is_homeless_required", "separate_from_parents", "recruit_unlimited"]
    for col_name in bool_cols:
        col = support_programs_table.c[col_name]
        assert isinstance(col.type, sa.Boolean), f"{col_name} 타입 오류: {type(col.type)}"


# T-066: Integer 컬럼 타입 검증
def test_integer_columns_are_sa_integer():
    int_cols = [
        "monthly_amount_wan",
        "duration_months",
        "asset_limit_wan",
        "recruit_count",
        "view_count",
    ]
    for col_name in int_cols:
        col = support_programs_table.c[col_name]
        assert isinstance(col.type, sa.Integer), f"{col_name} 타입 오류: {type(col.type)}"


# T-066: 신규 20개 컬럼 전부 nullable=True
def test_all_20_new_columns_are_nullable():
    new_cols = [
        "monthly_amount_wan",
        "duration_months",
        "asset_limit_wan",
        "support_type",
        "is_homeless_required",
        "separate_from_parents",
        "agency_name",
        "operating_agency",
        "recruit_count",
        "recruit_unlimited",
        "submission_documents",
        "screening_method",
        "participation_exclusion",
        "reference_urls",
        "keyword_name",
        "view_count",
        "major_code",
        "job_code",
        "school_code",
        "business_code",
    ]
    for col_name in new_cols:
        col = support_programs_table.c[col_name]
        assert col.nullable is True, f"{col_name} nullable=False"


# T-066: 기존 컬럼 회귀
def test_existing_columns_regression():
    existing_cols = [
        "card_key",
        "loan_limit",
        "deposit_limit",
        "rent_limit",
        "income_max_annual",
        "income_median_pct",
        "housing_types",
        "rules_extracted",
    ]
    col_names = set(support_programs_table.c.keys())
    for col in existing_cols:
        assert col in col_names, f"기존 컬럼 유실: {col}"
