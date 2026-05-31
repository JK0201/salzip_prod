import inspect
import uuid
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.schemas.policy_eligible import EligiblePolicy, PoliciesEligibleResponse

FAKE_SESSION_ID = uuid.uuid4()
FAKE_USER_ID = uuid.uuid4()


def make_policy(**kwargs) -> EligiblePolicy:
    defaults = {
        "id": uuid.uuid4(),
        "name": "청년버팀목전세대출",
        "support_type": "전세대출",
        "monthly_amount_wan": 30,
        "loan_limit": 10000,
        "agency_name": "주택도시보증공사",
    }
    defaults.update(kwargs)
    return EligiblePolicy(**defaults)


def _patched_repo(user_id):
    """SessionRepository(conn).get_user_id → user_id 반환하는 patch용 mock."""
    mock_instance = MagicMock()
    mock_instance.get_user_id = AsyncMock(return_value=user_id)
    mock_cls = MagicMock(return_value=mock_instance)
    return mock_cls


# acceptance #1: async coroutine, 시그니처 (session_id, conn)
def test_get_support_input_is_async_coroutine():
    from app.services.agents.support_data import get_support_input

    assert inspect.iscoroutinefunction(get_support_input)
    params = list(inspect.signature(get_support_input).parameters.keys())
    assert params == ["session_id", "conn"]


# acceptance #2: get_user_id → None 이면 None 반환
async def test_returns_none_when_user_id_is_none():
    from app.services.agents.support_data import get_support_input

    conn = MagicMock()
    with patch(
        "app.services.agents.support_data.SessionRepository",
        _patched_repo(None),
    ):
        result = await get_support_input(FAKE_SESSION_ID, conn)

    assert result is None


# acceptance #3: user_id 있으면 policies.eligible_policies(user_id, conn) 호출
async def test_calls_eligible_policies_with_user_id_and_conn():
    from app.services.agents.support_data import get_support_input

    conn = MagicMock()
    eligible_response = PoliciesEligibleResponse(policies=[make_policy()])

    with patch(
        "app.services.agents.support_data.SessionRepository",
        _patched_repo(FAKE_USER_ID),
    ), patch(
        "app.services.agents.support_data.policies.eligible_policies",
        new_callable=AsyncMock,
        return_value=eligible_response,
    ) as mock_eligible:
        await get_support_input(FAKE_SESSION_ID, conn)

    mock_eligible.assert_called_once_with(FAKE_USER_ID, conn)


# acceptance #4: 반환 dict에 count(int)와 programs(list) 키 존재
async def test_returned_dict_has_count_int_and_programs_list():
    from app.services.agents.support_data import get_support_input

    conn = MagicMock()
    policy = make_policy()
    eligible_response = PoliciesEligibleResponse(policies=[policy])

    with patch(
        "app.services.agents.support_data.SessionRepository",
        _patched_repo(FAKE_USER_ID),
    ), patch(
        "app.services.agents.support_data.policies.eligible_policies",
        new_callable=AsyncMock,
        return_value=eligible_response,
    ):
        result = await get_support_input(FAKE_SESSION_ID, conn)

    assert result is not None
    assert isinstance(result["count"], int)
    assert isinstance(result["programs"], list)
    assert result["count"] == 1
    assert len(result["programs"]) == 1


# acceptance #5: programs 각 항목에 name과 support_type 키 존재
async def test_programs_items_have_name_and_support_type():
    from app.services.agents.support_data import get_support_input

    conn = MagicMock()
    policy = make_policy(name="청년버팀목전세대출", support_type="전세대출")
    eligible_response = PoliciesEligibleResponse(policies=[policy])

    with patch(
        "app.services.agents.support_data.SessionRepository",
        _patched_repo(FAKE_USER_ID),
    ), patch(
        "app.services.agents.support_data.policies.eligible_policies",
        new_callable=AsyncMock,
        return_value=eligible_response,
    ):
        result = await get_support_input(FAKE_SESSION_ID, conn)

    item = result["programs"][0]
    assert "name" in item
    assert "support_type" in item
    assert item["name"] == "청년버팀목전세대출"
    assert item["support_type"] == "전세대출"


# acceptance #6: 자격 프로그램 0개여도 None 아니라 count=0, programs=[]
async def test_zero_programs_returns_empty_dict_not_none():
    from app.services.agents.support_data import get_support_input

    conn = MagicMock()
    eligible_response = PoliciesEligibleResponse(policies=[])

    with patch(
        "app.services.agents.support_data.SessionRepository",
        _patched_repo(FAKE_USER_ID),
    ), patch(
        "app.services.agents.support_data.policies.eligible_policies",
        new_callable=AsyncMock,
        return_value=eligible_response,
    ):
        result = await get_support_input(FAKE_SESSION_ID, conn)

    assert result is not None
    assert result["count"] == 0
    assert result["programs"] == []


# acceptance #7: 반환 dict에 max_monthly와 max_loan 키 존재 + 값 검증
async def test_returned_dict_has_max_monthly_and_max_loan():
    from app.services.agents.support_data import get_support_input

    conn = MagicMock()
    p1 = make_policy(monthly_amount_wan=50, loan_limit=20000)
    p2 = make_policy(monthly_amount_wan=30, loan_limit=8000)
    eligible_response = PoliciesEligibleResponse(policies=[p1, p2])

    with patch(
        "app.services.agents.support_data.SessionRepository",
        _patched_repo(FAKE_USER_ID),
    ), patch(
        "app.services.agents.support_data.policies.eligible_policies",
        new_callable=AsyncMock,
        return_value=eligible_response,
    ):
        result = await get_support_input(FAKE_SESSION_ID, conn)

    assert "max_monthly" in result
    assert "max_loan" in result
    assert result["max_monthly"] == 50
    assert result["max_loan"] == 20000


# max_monthly/max_loan: 전부 None이면 None
async def test_max_monthly_and_max_loan_none_when_all_none():
    from app.services.agents.support_data import get_support_input

    conn = MagicMock()
    policy = make_policy(monthly_amount_wan=None, loan_limit=None)
    eligible_response = PoliciesEligibleResponse(policies=[policy])

    with patch(
        "app.services.agents.support_data.SessionRepository",
        _patched_repo(FAKE_USER_ID),
    ), patch(
        "app.services.agents.support_data.policies.eligible_policies",
        new_callable=AsyncMock,
        return_value=eligible_response,
    ):
        result = await get_support_input(FAKE_SESSION_ID, conn)

    assert result["max_monthly"] is None
    assert result["max_loan"] is None
