import uuid

import pydantic
import pytest

from app.schemas.policy_preview import (
    PolicyPreviewItem,
    PolicyPreviewResponse,
    PolicyPreviewSummary,
)

# acceptance #1: 3개 클래스 존재 및 BaseModel 상속


def test_policy_preview_item_is_basemodel():
    assert issubclass(PolicyPreviewItem, pydantic.BaseModel)


def test_policy_preview_summary_is_basemodel():
    assert issubclass(PolicyPreviewSummary, pydantic.BaseModel)


def test_policy_preview_response_is_basemodel():
    assert issubclass(PolicyPreviewResponse, pydantic.BaseModel)


# acceptance #2: PolicyPreviewItem 9 필드

EXPECTED_ITEM_FIELDS = {
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


def test_policy_preview_item_field_keys():
    assert set(PolicyPreviewItem.model_fields.keys()) == EXPECTED_ITEM_FIELDS


# acceptance #3: 7 옵셔널 필드가 None 허용

OPTIONAL_ITEM_FIELDS = [
    "card_key",
    "support_type",
    "monthly_amount_wan",
    "loan_limit",
    "duration_months",
    "agency_name",
    "apply_url",
]


@pytest.mark.parametrize("field_name", OPTIONAL_ITEM_FIELDS)
def test_policy_preview_item_optional_field_accepts_none(field_name):
    required = {
        "id": uuid.uuid4(),
        "name": "청년 정책",
        field_name: None,
    }
    instance = PolicyPreviewItem.model_validate(required)
    assert getattr(instance, field_name) is None


def test_policy_preview_item_id_and_name_are_required():
    with pytest.raises(pydantic.ValidationError):
        PolicyPreviewItem()


# acceptance #4: PolicyPreviewSummary 3 필드

def test_policy_preview_summary_field_keys():
    assert set(PolicyPreviewSummary.model_fields.keys()) == {
        "total_matched",
        "max_monthly_support_wan",
        "max_loan_limit_wan",
    }


def test_policy_preview_summary_total_matched_is_int():
    assert PolicyPreviewSummary.model_fields["total_matched"].annotation is int


def test_policy_preview_summary_optional_fields_accept_none():
    s = PolicyPreviewSummary(
        total_matched=5,
        max_monthly_support_wan=None,
        max_loan_limit_wan=None,
    )
    assert s.max_monthly_support_wan is None
    assert s.max_loan_limit_wan is None


# acceptance #5: PolicyPreviewResponse 2 필드

def test_policy_preview_response_field_keys():
    assert set(PolicyPreviewResponse.model_fields.keys()) == {"by_card", "summary"}


# acceptance #6: PolicyPreviewResponse 인스턴스화 성공

def test_policy_preview_response_instantiation():
    summary = PolicyPreviewSummary(
        total_matched=0,
        max_monthly_support_wan=None,
        max_loan_limit_wan=None,
    )
    response = PolicyPreviewResponse(by_card={"monthly": []}, summary=summary)
    assert response.by_card == {"monthly": []}
    assert response.summary.total_matched == 0
    assert response.summary.max_monthly_support_wan is None
    assert response.summary.max_loan_limit_wan is None


def test_policy_preview_response_by_card_contains_items():
    item = PolicyPreviewItem(
        id=uuid.UUID("550e8400-e29b-41d4-a716-446655440000"),
        name="청년 주거 지원",
        card_key="housing",
        support_type="보조금",
        monthly_amount_wan=30,
        loan_limit=None,
        duration_months=12,
        agency_name="서울시",
        apply_url="https://example.com",
    )
    summary = PolicyPreviewSummary(
        total_matched=1,
        max_monthly_support_wan=30,
        max_loan_limit_wan=None,
    )
    response = PolicyPreviewResponse(by_card={"housing": [item]}, summary=summary)
    assert len(response.by_card["housing"]) == 1
    assert response.by_card["housing"][0].name == "청년 주거 지원"
