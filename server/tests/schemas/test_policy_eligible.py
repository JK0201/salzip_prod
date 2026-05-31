import uuid

import pytest

from app.schemas.policy_eligible import EligiblePolicy, PoliciesEligibleResponse


# acceptance #1: EligiblePolicy 존재, 9개 필드 보유
def test_eligible_policy_has_required_fields():
    fields = EligiblePolicy.model_fields
    expected = {
        "id",
        "name",
        "card_key",
        "support_type",
        "monthly_amount_wan",
        "loan_limit",
        "duration_months",
        "agency_name",
        "apply_url",
    }
    assert expected == set(fields.keys())


# acceptance #2: id는 uuid.UUID, name은 str (필수)
def test_eligible_policy_required_fields_types():
    policy = EligiblePolicy(id=uuid.UUID("12345678-1234-5678-1234-567812345678"), name="청년 지원금")
    assert isinstance(policy.id, uuid.UUID)
    assert isinstance(policy.name, str)


def test_eligible_policy_missing_name_raises():
    with pytest.raises(Exception):
        EligiblePolicy(id=uuid.UUID("12345678-1234-5678-1234-567812345678"))


def test_eligible_policy_missing_id_raises():
    with pytest.raises(Exception):
        EligiblePolicy(name="청년 지원금")


# acceptance #3: 7개 Optional 필드 기본값 None
def test_eligible_policy_optional_fields_default_none():
    policy = EligiblePolicy(id=uuid.UUID("12345678-1234-5678-1234-567812345678"), name="청년 지원금")
    assert policy.card_key is None
    assert policy.support_type is None
    assert policy.monthly_amount_wan is None
    assert policy.loan_limit is None
    assert policy.duration_months is None
    assert policy.agency_name is None
    assert policy.apply_url is None


# acceptance #4: from_attributes=True — ORM 객체(row)에서 model_validate 가능
def test_eligible_policy_from_attributes():
    class FakeRow:
        id = uuid.UUID("12345678-1234-5678-1234-567812345678")
        name = "청년 지원금"
        card_key = "kb"
        support_type = "현금"
        monthly_amount_wan = 50
        loan_limit = None
        duration_months = 12
        agency_name = "서울시"
        apply_url = "https://example.com"

    policy = EligiblePolicy.model_validate(FakeRow(), from_attributes=True)
    assert policy.id == FakeRow.id
    assert policy.name == FakeRow.name
    assert policy.card_key == "kb"
    assert policy.duration_months == 12


# acceptance #5: PoliciesEligibleResponse 존재, policies: list[EligiblePolicy]
def test_policies_eligible_response_has_policies_field():
    fields = PoliciesEligibleResponse.model_fields
    assert "policies" in fields


def test_policies_eligible_response_policies_type():
    policy = EligiblePolicy(id=uuid.UUID("12345678-1234-5678-1234-567812345678"), name="청년 지원금")
    resp = PoliciesEligibleResponse(policies=[policy])
    assert isinstance(resp.policies, list)
    assert isinstance(resp.policies[0], EligiblePolicy)


# acceptance #6: PoliciesEligibleResponse(policies=[]) 빈 리스트 유효
def test_policies_eligible_response_empty_list_valid():
    resp = PoliciesEligibleResponse(policies=[])
    assert resp.policies == []
