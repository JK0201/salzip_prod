import uuid

from pydantic import BaseModel, ConfigDict


class EligiblePolicy(BaseModel):
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
    # 자격 기준 (FE 체크리스트용)
    age_min: int | None = None
    age_max: int | None = None
    is_homeless_required: bool | None = None
    income_max_annual: int | None = None
    rent_limit: int | None = None
    deposit_limit: int | None = None


class UserCriteria(BaseModel):
    age: int
    annual_income_wan: int
    home_ownerless: bool
    deposit_max_wan: int
    monthly_rent_max_wan: int


class PoliciesEligibleResponse(BaseModel):
    policies: list[EligiblePolicy]
    criteria: UserCriteria | None = None
