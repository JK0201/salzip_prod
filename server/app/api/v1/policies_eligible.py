from fastapi import APIRouter

from app.core.auth import UserDep
from app.core.deps import ConnDep
from app.schemas.policy_eligible import PoliciesEligibleResponse
from app.services import policies as policies_service

router = APIRouter(tags=["policies"])


@router.get("/policies/eligible")
async def eligible_policies_endpoint(
    user: UserDep,
    conn: ConnDep,
) -> PoliciesEligibleResponse:
    return await policies_service.eligible_policies(user.user_id, conn)
