import uuid
from typing import NamedTuple

import sqlalchemy as sa
from sqlalchemy.ext.asyncio import AsyncConnection

from app.db.tables.profiles import profiles_table
from app.db.tables.support_programs import support_programs_table
from app.schemas.policy_eligible import (
    EligiblePolicy,
    PoliciesEligibleResponse,
    UserCriteria,
)

_LARGE = 10**12


class EligibilityCriteria(NamedTuple):
    age: int
    annual_income_wan: int
    home_ownerless: bool
    deposit_max_wan: int
    monthly_rent_max_wan: int


def _parse_int(value: object, default: int) -> int:
    if value is None:
        return default
    try:
        return int(float(value))
    except (ValueError, TypeError):
        return default


def parse_eligibility_criteria(payload: dict) -> EligibilityCriteria:
    return EligibilityCriteria(
        age=_parse_int(payload.get("age"), 0),
        annual_income_wan=_parse_int(payload.get("annual_income_wan"), _LARGE),
        home_ownerless=payload.get("home_ownerless") is True,
        deposit_max_wan=_parse_int(payload.get("deposit_max_wan"), _LARGE),
        monthly_rent_max_wan=_parse_int(payload.get("monthly_rent_max_wan"), _LARGE),
    )


def is_eligible(criteria: EligibilityCriteria, program: dict) -> bool:
    # 0 또는 None = "제한 없음"(LLM이 추출 못 하면 0이 박힘) → 필터 무시
    age_min = program.get("age_min")
    age_max = program.get("age_max")
    if age_min and criteria.age < age_min:
        return False
    if age_max and criteria.age > age_max:
        return False

    if program.get("is_homeless_required") and not criteria.home_ownerless:
        return False

    income_max = program.get("income_max_annual")
    if income_max and criteria.annual_income_wan > income_max:
        return False

    rent_limit = program.get("rent_limit")
    if rent_limit and criteria.monthly_rent_max_wan > rent_limit:
        return False

    deposit_limit = program.get("deposit_limit")
    return not deposit_limit or criteria.deposit_max_wan <= deposit_limit


def sort_eligible_programs(programs: list[dict]) -> list[dict]:
    def _key(p: dict) -> tuple:
        monthly = p.get("monthly_amount_wan")
        loan = p.get("loan_limit")
        return (
            1 if monthly is None else 0,
            -monthly if monthly is not None else 0,
            1 if loan is None else 0,
            -loan if loan is not None else 0,
            p.get("name", ""),
        )

    return sorted(programs, key=_key)


_DISPLAY_COLS = [
    support_programs_table.c.id,
    support_programs_table.c.name,
    support_programs_table.c.card_key,
    support_programs_table.c.support_type,
    support_programs_table.c.monthly_amount_wan,
    support_programs_table.c.loan_limit,
    support_programs_table.c.duration_months,
    support_programs_table.c.agency_name,
    support_programs_table.c.apply_url,
    support_programs_table.c.age_min,
    support_programs_table.c.age_max,
    support_programs_table.c.is_homeless_required,
    support_programs_table.c.income_max_annual,
    support_programs_table.c.rent_limit,
    support_programs_table.c.deposit_limit,
]


async def eligible_policies(
    user_id: uuid.UUID, conn: AsyncConnection
) -> PoliciesEligibleResponse:
    profile_q = (
        sa.select(profiles_table.c.payload)
        .where(profiles_table.c.user_id == user_id)
        .order_by(profiles_table.c.created_at.desc())
        .limit(1)
    )
    profile_row = (await conn.execute(profile_q)).fetchone()
    if profile_row is None:
        return PoliciesEligibleResponse(policies=[])

    criteria = parse_eligibility_criteria(profile_row.payload)

    programs_q = sa.select(*_DISPLAY_COLS)
    rows: list[dict] = list((await conn.execute(programs_q)).mappings().all())

    eligible = [r for r in rows if is_eligible(criteria, r)]
    sorted_programs = sort_eligible_programs(eligible)
    policies = [EligiblePolicy.model_validate(dict(p)) for p in sorted_programs]
    return PoliciesEligibleResponse(
        policies=policies,
        criteria=UserCriteria(
            age=criteria.age,
            annual_income_wan=criteria.annual_income_wan,
            home_ownerless=criteria.home_ownerless,
            deposit_max_wan=criteria.deposit_max_wan,
            monthly_rent_max_wan=criteria.monthly_rent_max_wan,
        ),
    )
