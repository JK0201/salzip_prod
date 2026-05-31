import inspect
import typing
import uuid
from unittest.mock import AsyncMock, MagicMock

import pytest

from app.services.policies import (
    EligibilityCriteria,
    eligible_policies,
    is_eligible,
    parse_eligibility_criteria,
    sort_eligible_programs,
)
from app.schemas.policy_eligible import EligiblePolicy, PoliciesEligibleResponse


class TestEligibilityCriteriaStructure:
    def test_is_namedtuple(self):
        assert issubclass(EligibilityCriteria, tuple)
        assert hasattr(EligibilityCriteria, "_fields")

    def test_fields_exist(self):
        fields = EligibilityCriteria._fields
        assert "age" in fields
        assert "annual_income_wan" in fields
        assert "home_ownerless" in fields
        assert "deposit_max_wan" in fields
        assert "monthly_rent_max_wan" in fields

    def test_field_types_via_annotations(self):
        hints = typing.get_type_hints(EligibilityCriteria)
        assert hints["age"] is int
        assert hints["annual_income_wan"] is int
        assert hints["deposit_max_wan"] is int
        assert hints["monthly_rent_max_wan"] is int
        assert hints["home_ownerless"] is bool


class TestParseEligibilityCriteriaHappyPath:
    def test_full_payload_mapped_correctly(self):
        payload = {
            "age": 27,
            "annual_income_wan": 4500,
            "home_ownerless": True,
            "deposit_max_wan": 3000,
            "monthly_rent_max_wan": 60,
        }
        result = parse_eligibility_criteria(payload)
        assert result.age == 27
        assert result.annual_income_wan == 4500
        assert result.home_ownerless is True
        assert result.deposit_max_wan == 3000
        assert result.monthly_rent_max_wan == 60

    def test_returns_eligibility_criteria_type(self):
        payload = {
            "age": 30,
            "annual_income_wan": 5000,
            "home_ownerless": False,
            "deposit_max_wan": 10000,
            "monthly_rent_max_wan": 100,
        }
        result = parse_eligibility_criteria(payload)
        assert isinstance(result, EligibilityCriteria)


class TestParseEligibilityCriteriaMissingKeys:
    def test_missing_age_defaults_to_zero(self):
        payload = {
            "annual_income_wan": 4500,
            "home_ownerless": True,
            "deposit_max_wan": 3000,
            "monthly_rent_max_wan": 60,
        }
        result = parse_eligibility_criteria(payload)
        assert result.age == 0

    def test_missing_annual_income_wan_defaults_to_large(self):
        payload = {"age": 27, "home_ownerless": True, "deposit_max_wan": 3000, "monthly_rent_max_wan": 60}
        result = parse_eligibility_criteria(payload)
        assert result.annual_income_wan == 10**12

    def test_missing_deposit_max_wan_defaults_to_large(self):
        payload = {"age": 27, "annual_income_wan": 4500, "home_ownerless": True, "monthly_rent_max_wan": 60}
        result = parse_eligibility_criteria(payload)
        assert result.deposit_max_wan == 10**12

    def test_missing_monthly_rent_max_wan_defaults_to_large(self):
        payload = {"age": 27, "annual_income_wan": 4500, "home_ownerless": True, "deposit_max_wan": 3000}
        result = parse_eligibility_criteria(payload)
        assert result.monthly_rent_max_wan == 10**12

    def test_missing_home_ownerless_defaults_to_false(self):
        payload = {"age": 27, "annual_income_wan": 4500, "deposit_max_wan": 3000, "monthly_rent_max_wan": 60}
        result = parse_eligibility_criteria(payload)
        assert result.home_ownerless is False

    def test_home_ownerless_false_value_stays_false(self):
        payload = {
            "age": 27,
            "annual_income_wan": 4500,
            "home_ownerless": False,
            "deposit_max_wan": 3000,
            "monthly_rent_max_wan": 60,
        }
        result = parse_eligibility_criteria(payload)
        assert result.home_ownerless is False

    def test_empty_payload_all_defaults(self):
        result = parse_eligibility_criteria({})
        assert result.age == 0
        assert result.annual_income_wan == 10**12
        assert result.deposit_max_wan == 10**12
        assert result.monthly_rent_max_wan == 10**12
        assert result.home_ownerless is False


class TestParseEligibilityCriteriaTypeCoercion:
    def test_age_string_numeric_parsed_as_int(self):
        payload = {"age": "27", "annual_income_wan": 4500, "deposit_max_wan": 3000, "monthly_rent_max_wan": 60}
        result = parse_eligibility_criteria(payload)
        assert result.age == 27
        assert isinstance(result.age, int)

    def test_age_float_string_parsed_as_int(self):
        payload = {"age": "27.9", "annual_income_wan": 4500, "deposit_max_wan": 3000, "monthly_rent_max_wan": 60}
        result = parse_eligibility_criteria(payload)
        assert result.age == 27
        assert isinstance(result.age, int)

    def test_age_float_value_parsed_as_int(self):
        payload = {"age": 27.9, "annual_income_wan": 4500, "deposit_max_wan": 3000, "monthly_rent_max_wan": 60}
        result = parse_eligibility_criteria(payload)
        assert result.age == 27
        assert isinstance(result.age, int)

    def test_age_unparsable_defaults_to_zero(self):
        payload = {"age": "불가능", "annual_income_wan": 4500, "deposit_max_wan": 3000, "monthly_rent_max_wan": 60}
        result = parse_eligibility_criteria(payload)
        assert result.age == 0

    def test_age_none_defaults_to_zero(self):
        payload = {"age": None, "annual_income_wan": 4500, "deposit_max_wan": 3000, "monthly_rent_max_wan": 60}
        result = parse_eligibility_criteria(payload)
        assert result.age == 0

    def test_home_ownerless_bool_true_is_true(self):
        payload = {"age": 27, "annual_income_wan": 4500, "home_ownerless": True, "deposit_max_wan": 3000, "monthly_rent_max_wan": 60}
        result = parse_eligibility_criteria(payload)
        assert result.home_ownerless is True

    def test_home_ownerless_string_true_is_false(self):
        payload = {"age": 27, "annual_income_wan": 4500, "home_ownerless": "True", "deposit_max_wan": 3000, "monthly_rent_max_wan": 60}
        result = parse_eligibility_criteria(payload)
        assert result.home_ownerless is False

    def test_home_ownerless_int_one_is_false(self):
        payload = {"age": 27, "annual_income_wan": 4500, "home_ownerless": 1, "deposit_max_wan": 3000, "monthly_rent_max_wan": 60}
        result = parse_eligibility_criteria(payload)
        assert result.home_ownerless is False


# ── T-088 fixtures ────────────────────────────────────────────────────────────

def _criteria(
    age=30,
    annual_income_wan=3000,
    home_ownerless=False,
    deposit_max_wan=5000,
    monthly_rent_max_wan=50,
) -> EligibilityCriteria:
    return EligibilityCriteria(
        age=age,
        annual_income_wan=annual_income_wan,
        home_ownerless=home_ownerless,
        deposit_max_wan=deposit_max_wan,
        monthly_rent_max_wan=monthly_rent_max_wan,
    )


def _program(
    age_min=None,
    age_max=None,
    is_homeless_required=False,
    income_max_annual=None,
    rent_limit=None,
    deposit_limit=None,
) -> dict:
    return {
        "age_min": age_min,
        "age_max": age_max,
        "is_homeless_required": is_homeless_required,
        "income_max_annual": income_max_annual,
        "rent_limit": rent_limit,
        "deposit_limit": deposit_limit,
    }


# ── is_eligible ───────────────────────────────────────────────────────────────

class TestIsEligibleAllNull:
    def test_all_null_limits_any_criteria_returns_true(self):
        program = _program()
        criteria = _criteria(age=99, annual_income_wan=10**9, home_ownerless=False, deposit_max_wan=10**9, monthly_rent_max_wan=10**9)
        assert is_eligible(criteria, program) is True

    def test_all_null_limits_zero_age_returns_true(self):
        program = _program()
        criteria = _criteria(age=0)
        assert is_eligible(criteria, program) is True


class TestIsEligibleAge:
    def test_age_below_min_returns_false(self):
        program = _program(age_min=20, age_max=34)
        criteria = _criteria(age=19)
        assert is_eligible(criteria, program) is False

    def test_age_above_max_returns_false(self):
        program = _program(age_min=20, age_max=34)
        criteria = _criteria(age=35)
        assert is_eligible(criteria, program) is False

    def test_age_at_min_boundary_returns_true(self):
        program = _program(age_min=20, age_max=34)
        criteria = _criteria(age=20)
        assert is_eligible(criteria, program) is True

    def test_age_at_max_boundary_returns_true(self):
        program = _program(age_min=20, age_max=34)
        criteria = _criteria(age=34)
        assert is_eligible(criteria, program) is True

    def test_age_within_range_returns_true(self):
        program = _program(age_min=20, age_max=34)
        criteria = _criteria(age=27)
        assert is_eligible(criteria, program) is True

    def test_age_null_limits_pass_any_age(self):
        program = _program(age_min=None, age_max=None)
        assert is_eligible(_criteria(age=0), program) is True
        assert is_eligible(_criteria(age=100), program) is True


class TestIsEligibleHomeless:
    def test_homeless_required_ownerless_false_returns_false(self):
        program = _program(is_homeless_required=True)
        criteria = _criteria(home_ownerless=False)
        assert is_eligible(criteria, program) is False

    def test_homeless_required_ownerless_true_returns_true(self):
        program = _program(is_homeless_required=True)
        criteria = _criteria(home_ownerless=True)
        assert is_eligible(criteria, program) is True

    def test_homeless_not_required_falsy_ownerless_still_passes(self):
        program = _program(is_homeless_required=False)
        criteria = _criteria(home_ownerless=False)
        assert is_eligible(criteria, program) is True

    def test_homeless_required_none_falsy_ownerless_passes(self):
        program = _program(is_homeless_required=None)
        criteria = _criteria(home_ownerless=False)
        assert is_eligible(criteria, program) is True


class TestIsEligibleIncome:
    def test_income_exceeds_max_returns_false(self):
        program = _program(income_max_annual=5000)
        criteria = _criteria(annual_income_wan=5001)
        assert is_eligible(criteria, program) is False

    def test_income_equal_to_max_returns_true(self):
        program = _program(income_max_annual=5000)
        criteria = _criteria(annual_income_wan=5000)
        assert is_eligible(criteria, program) is True

    def test_income_below_max_returns_true(self):
        program = _program(income_max_annual=5000)
        criteria = _criteria(annual_income_wan=4999)
        assert is_eligible(criteria, program) is True

    def test_income_null_limit_always_passes(self):
        program = _program(income_max_annual=None)
        assert is_eligible(_criteria(annual_income_wan=10**12), program) is True


class TestIsEligibleRentAndDeposit:
    def test_rent_exceeds_limit_returns_false(self):
        program = _program(rent_limit=50)
        criteria = _criteria(monthly_rent_max_wan=51)
        assert is_eligible(criteria, program) is False

    def test_rent_equal_to_limit_returns_true(self):
        program = _program(rent_limit=50)
        criteria = _criteria(monthly_rent_max_wan=50)
        assert is_eligible(criteria, program) is True

    def test_deposit_exceeds_limit_returns_false(self):
        program = _program(deposit_limit=5000)
        criteria = _criteria(deposit_max_wan=5001)
        assert is_eligible(criteria, program) is False

    def test_deposit_equal_to_limit_returns_true(self):
        program = _program(deposit_limit=5000)
        criteria = _criteria(deposit_max_wan=5000)
        assert is_eligible(criteria, program) is True

    def test_rent_null_limit_always_passes(self):
        program = _program(rent_limit=None)
        assert is_eligible(_criteria(monthly_rent_max_wan=10**12), program) is True

    def test_deposit_null_limit_always_passes(self):
        program = _program(deposit_limit=None)
        assert is_eligible(_criteria(deposit_max_wan=10**12), program) is True


# ── sort_eligible_programs ────────────────────────────────────────────────────

class TestSortEligibleProgramsMonthly:
    def test_monthly_desc_basic(self):
        programs = [
            {"name": "A", "monthly_amount_wan": 30, "loan_limit": None},
            {"name": "B", "monthly_amount_wan": 50, "loan_limit": None},
            {"name": "C", "monthly_amount_wan": 10, "loan_limit": None},
        ]
        result = sort_eligible_programs(programs)
        assert [p["name"] for p in result] == ["B", "A", "C"]

    def test_monthly_none_after_valued(self):
        programs = [
            {"name": "A", "monthly_amount_wan": None, "loan_limit": None},
            {"name": "B", "monthly_amount_wan": 50, "loan_limit": None},
            {"name": "C", "monthly_amount_wan": None, "loan_limit": None},
        ]
        result = sort_eligible_programs(programs)
        assert result[0]["name"] == "B"
        assert result[0]["monthly_amount_wan"] == 50

    def test_all_monthly_none_order_by_next_key(self):
        programs = [
            {"name": "Z", "monthly_amount_wan": None, "loan_limit": 200},
            {"name": "A", "monthly_amount_wan": None, "loan_limit": 500},
        ]
        result = sort_eligible_programs(programs)
        assert result[0]["name"] == "A"

    def test_returns_new_list_not_mutate(self):
        programs = [
            {"name": "A", "monthly_amount_wan": 10, "loan_limit": None},
            {"name": "B", "monthly_amount_wan": 50, "loan_limit": None},
        ]
        original_order = [p["name"] for p in programs]
        sort_eligible_programs(programs)
        assert [p["name"] for p in programs] == original_order


class TestSortEligibleProgramsLoanLimit:
    def test_monthly_tie_loan_limit_desc(self):
        programs = [
            {"name": "A", "monthly_amount_wan": 100, "loan_limit": 1000},
            {"name": "B", "monthly_amount_wan": 100, "loan_limit": 3000},
            {"name": "C", "monthly_amount_wan": 100, "loan_limit": 2000},
        ]
        result = sort_eligible_programs(programs)
        assert [p["name"] for p in result] == ["B", "C", "A"]

    def test_loan_limit_none_after_valued_when_monthly_tied(self):
        programs = [
            {"name": "A", "monthly_amount_wan": 100, "loan_limit": None},
            {"name": "B", "monthly_amount_wan": 100, "loan_limit": 3000},
        ]
        result = sort_eligible_programs(programs)
        assert result[0]["name"] == "B"
        assert result[1]["name"] == "A"

    def test_both_monthly_none_loan_desc(self):
        programs = [
            {"name": "A", "monthly_amount_wan": None, "loan_limit": 1000},
            {"name": "B", "monthly_amount_wan": None, "loan_limit": 5000},
        ]
        result = sort_eligible_programs(programs)
        assert result[0]["name"] == "B"

    def test_monthly_and_loan_tied_name_asc(self):
        programs = [
            {"name": "Zebra", "monthly_amount_wan": 100, "loan_limit": 1000},
            {"name": "Apple", "monthly_amount_wan": 100, "loan_limit": 1000},
            {"name": "Mango", "monthly_amount_wan": 100, "loan_limit": 1000},
        ]
        result = sort_eligible_programs(programs)
        assert [p["name"] for p in result] == ["Apple", "Mango", "Zebra"]

    def test_both_none_name_asc_tiebreak(self):
        programs = [
            {"name": "Z", "monthly_amount_wan": None, "loan_limit": None},
            {"name": "A", "monthly_amount_wan": None, "loan_limit": None},
        ]
        result = sort_eligible_programs(programs)
        assert result[0]["name"] == "A"
        assert result[1]["name"] == "Z"


# ── T-089: eligible_policies 서비스 ───────────────────────────────────────────

_PAYLOAD = {
    "age": 27,
    "annual_income_wan": 3000,
    "home_ownerless": False,
    "deposit_max_wan": 5000,
    "monthly_rent_max_wan": 50,
}

_PROG_BASE: dict = {
    "id": uuid.UUID("00000000-0000-0000-0000-000000000001"),
    "name": "테스트정책A",
    "card_key": "test-a",
    "support_type": "rent",
    "monthly_amount_wan": 30,
    "loan_limit": None,
    "duration_months": 12,
    "agency_name": "국토교통부",
    "apply_url": "https://example.com",
    # 매칭 전용 컬럼
    "age_min": None,
    "age_max": None,
    "is_homeless_required": False,
    "income_max_annual": None,
    "rent_limit": None,
    "deposit_limit": None,
}


def _conn_no_profile() -> AsyncMock:
    conn = AsyncMock()
    result = MagicMock()
    result.fetchone.return_value = None
    conn.execute.return_value = result
    return conn


def _conn_with_programs(payload: dict, programs: list[dict]) -> AsyncMock:
    conn = AsyncMock()

    profile_result = MagicMock()
    profile_row = MagicMock()
    profile_row.payload = payload
    profile_result.fetchone.return_value = profile_row

    programs_result = MagicMock()
    programs_result.mappings.return_value.all.return_value = programs

    conn.execute.side_effect = [profile_result, programs_result]
    return conn


class TestEligiblePoliciesSignature:
    def test_is_async_function(self):
        assert inspect.iscoroutinefunction(eligible_policies)


class TestEligiblePoliciesNoProfile:
    async def test_no_profile_returns_empty_response(self):
        result = await eligible_policies(uuid.uuid4(), _conn_no_profile())
        assert result == PoliciesEligibleResponse(policies=[])

    async def test_no_profile_no_exception(self):
        # 예외 미발생 보장
        await eligible_policies(uuid.uuid4(), _conn_no_profile())


class TestEligiblePoliciesTwoSelects:
    async def test_profile_exists_executes_twice(self):
        conn = _conn_with_programs(_PAYLOAD, [])
        await eligible_policies(uuid.uuid4(), conn)
        assert conn.execute.call_count == 2


class TestEligiblePoliciesFiltering:
    async def test_ineligible_row_excluded(self):
        ineligible = {**_PROG_BASE, "id": uuid.uuid4(), "name": "미자격정책", "age_min": 30, "age_max": 34}
        eligible = {**_PROG_BASE, "id": uuid.uuid4(), "name": "자격정책"}
        conn = _conn_with_programs(_PAYLOAD, [ineligible, eligible])
        result = await eligible_policies(uuid.uuid4(), conn)
        names = [p.name for p in result.policies]
        assert "미자격정책" not in names
        assert "자격정책" in names

    async def test_all_ineligible_returns_empty_list(self):
        ineligible = {**_PROG_BASE, "age_min": 30, "age_max": 34}  # criteria.age=27 < 30
        conn = _conn_with_programs(_PAYLOAD, [ineligible])
        result = await eligible_policies(uuid.uuid4(), conn)
        assert result.policies == []

    async def test_all_eligible_all_returned(self):
        prog1 = {**_PROG_BASE, "id": uuid.uuid4(), "name": "P1"}
        prog2 = {**_PROG_BASE, "id": uuid.uuid4(), "name": "P2"}
        conn = _conn_with_programs(_PAYLOAD, [prog1, prog2])
        result = await eligible_policies(uuid.uuid4(), conn)
        assert len(result.policies) == 2


class TestEligiblePoliciesOutputShape:
    async def test_each_item_is_eligible_policy_instance(self):
        conn = _conn_with_programs(_PAYLOAD, [{**_PROG_BASE}])
        result = await eligible_policies(uuid.uuid4(), conn)
        assert len(result.policies) == 1
        assert isinstance(result.policies[0], EligiblePolicy)

    async def test_display_fields_populated(self):
        conn = _conn_with_programs(_PAYLOAD, [{**_PROG_BASE}])
        result = await eligible_policies(uuid.uuid4(), conn)
        item = result.policies[0]
        assert item.id == _PROG_BASE["id"]
        assert item.name == "테스트정책A"
        assert item.card_key == "test-a"
        assert item.support_type == "rent"
        assert item.monthly_amount_wan == 30
        assert item.duration_months == 12
        assert item.agency_name == "국토교통부"
        assert item.apply_url == "https://example.com"

    async def test_matching_columns_not_in_model_dump(self):
        conn = _conn_with_programs(_PAYLOAD, [{**_PROG_BASE}])
        result = await eligible_policies(uuid.uuid4(), conn)
        dumped = result.policies[0].model_dump()
        for col in ("age_min", "age_max", "is_homeless_required", "income_max_annual", "rent_limit", "deposit_limit"):
            assert col not in dumped, f"{col} should not be exposed in EligiblePolicy"

    async def test_exactly_nine_display_fields(self):
        conn = _conn_with_programs(_PAYLOAD, [{**_PROG_BASE}])
        result = await eligible_policies(uuid.uuid4(), conn)
        dumped = result.policies[0].model_dump()
        assert set(dumped.keys()) == {
            "id", "name", "card_key", "support_type",
            "monthly_amount_wan", "loan_limit", "duration_months",
            "agency_name", "apply_url",
        }


class TestEligiblePoliciesSortOrder:
    async def test_sorted_monthly_amount_desc(self):
        prog_a = {**_PROG_BASE, "id": uuid.uuid4(), "name": "A", "monthly_amount_wan": 30, "loan_limit": None}
        prog_b = {**_PROG_BASE, "id": uuid.uuid4(), "name": "B", "monthly_amount_wan": 50, "loan_limit": None}
        prog_c = {**_PROG_BASE, "id": uuid.uuid4(), "name": "C", "monthly_amount_wan": 10, "loan_limit": None}
        conn = _conn_with_programs(_PAYLOAD, [prog_a, prog_b, prog_c])
        result = await eligible_policies(uuid.uuid4(), conn)
        assert [p.name for p in result.policies] == ["B", "A", "C"]

    async def test_monthly_tie_sorted_loan_limit_desc(self):
        prog_x = {**_PROG_BASE, "id": uuid.uuid4(), "name": "X", "monthly_amount_wan": 100, "loan_limit": 1000}
        prog_y = {**_PROG_BASE, "id": uuid.uuid4(), "name": "Y", "monthly_amount_wan": 100, "loan_limit": 3000}
        conn = _conn_with_programs(_PAYLOAD, [prog_x, prog_y])
        result = await eligible_policies(uuid.uuid4(), conn)
        assert [p.name for p in result.policies] == ["Y", "X"]

    async def test_monthly_none_after_valued(self):
        prog_has_monthly = {**_PROG_BASE, "id": uuid.uuid4(), "name": "M", "monthly_amount_wan": 50, "loan_limit": None}
        prog_no_monthly = {**_PROG_BASE, "id": uuid.uuid4(), "name": "N", "monthly_amount_wan": None, "loan_limit": None}
        conn = _conn_with_programs(_PAYLOAD, [prog_no_monthly, prog_has_monthly])
        result = await eligible_policies(uuid.uuid4(), conn)
        assert result.policies[0].name == "M"
