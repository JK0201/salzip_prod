from app.repositories.session import SessionRepository
from app.services import policies


async def get_support_input(session_id, conn) -> dict | None:
    user_id = await SessionRepository(conn).get_user_id(session_id)
    if user_id is None:
        return None

    response = await policies.eligible_policies(user_id, conn)
    programs = response.policies

    items = [
        {
            "name": p.name,
            "support_type": p.support_type,
            "monthly_amount_wan": p.monthly_amount_wan,
            "loan_limit": p.loan_limit,
            "agency_name": p.agency_name,
        }
        for p in programs
    ]

    monthly_vals = [p.monthly_amount_wan for p in programs if p.monthly_amount_wan is not None]
    loan_vals = [p.loan_limit for p in programs if p.loan_limit is not None]

    return {
        "count": len(items),
        "programs": items,
        "max_monthly": max(monthly_vals) if monthly_vals else None,
        "max_loan": max(loan_vals) if loan_vals else None,
    }
