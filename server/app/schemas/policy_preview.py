import uuid

from pydantic import BaseModel, ConfigDict


class PolicyPreviewItem(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    name: str
    card_key: str | None = None
    support_type: str | None = None
    monthly_amount_wan: int | None = None
    loan_limit: int | None = None
    duration_months: int | None = None
    agency_name: str | None = None
    apply_url: str | None = None


class PolicyPreviewSummary(BaseModel):
    total_matched: int
    max_monthly_support_wan: int | None = None
    max_loan_limit_wan: int | None = None


class PolicyPreviewResponse(BaseModel):
    by_card: dict[str, list[PolicyPreviewItem]]
    summary: PolicyPreviewSummary
