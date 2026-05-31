import sqlalchemy as sa
from fastapi import APIRouter, Query

from app.core.deps import ConnDep
from app.db.tables.support_programs import support_programs_table
from app.schemas.policy_preview import (
    PolicyPreviewItem,
    PolicyPreviewResponse,
    PolicyPreviewSummary,
)

router = APIRouter(tags=["policies"])


@router.get("/policies/preview")
async def preview_policies(
    conn: ConnDep,
    deposit_max_wan: int = Query(...),
    monthly_rent_max_wan: int = Query(...),
) -> PolicyPreviewResponse:
    t = support_programs_table
    stmt = (
        sa.select(
            t.c.id,
            t.c.name,
            t.c.card_key,
            t.c.support_type,
            t.c.monthly_amount_wan,
            t.c.loan_limit,
            t.c.duration_months,
            t.c.agency_name,
            t.c.apply_url,
        )
        .where(t.c.rent_limit >= monthly_rent_max_wan)
        .where(t.c.deposit_limit >= deposit_max_wan)
        .order_by(
            t.c.monthly_amount_wan.desc().nullslast(),
            t.c.loan_limit.desc().nullslast(),
            t.c.name.asc(),
        )
    )
    result = await conn.execute(stmt)
    rows = list(result)

    by_card: dict[str, list[PolicyPreviewItem]] = {}
    for row in rows:
        key = row.card_key if row.card_key is not None else "other"
        by_card.setdefault(key, []).append(
            PolicyPreviewItem.model_validate(row, from_attributes=True)
        )

    monthly_vals = [r.monthly_amount_wan for r in rows if r.monthly_amount_wan is not None]
    loan_vals = [r.loan_limit for r in rows if r.loan_limit is not None]

    summary = PolicyPreviewSummary(
        total_matched=len(rows),
        max_monthly_support_wan=max(monthly_vals) if monthly_vals else None,
        max_loan_limit_wan=max(loan_vals) if loan_vals else None,
    )

    return PolicyPreviewResponse(by_card=by_card, summary=summary)
