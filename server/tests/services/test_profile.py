import uuid
from unittest.mock import AsyncMock, patch

import pytest

from app.services.profile import bind_session_to_user, save_profile_for_request


# acceptance #1: get_by_session → None → promote 호출 없이 None 반환
async def test_bind_session_to_user_returns_none_when_no_anon_profile():
    conn = AsyncMock()
    session_id = uuid.uuid4()
    user_id = uuid.uuid4()

    with patch("app.services.profile.ProfileRepository") as MockProfileRepo:
        mock_repo = AsyncMock()
        mock_repo.get_by_session.return_value = None
        MockProfileRepo.return_value = mock_repo

        result = await bind_session_to_user(conn, session_id, user_id)

    assert result is None
    mock_repo.promote_anon_to_user.assert_not_called()


# acceptance #2: get_by_session → 값 → promote_anon_to_user(session_id, user_id) 1회, 반환값 패스스루
async def test_bind_session_to_user_calls_promote_and_returns_result():
    conn = AsyncMock()
    session_id = uuid.uuid4()
    user_id = uuid.uuid4()
    anon_profile_id = uuid.uuid4()
    promoted_id = uuid.uuid4()

    with patch("app.services.profile.ProfileRepository") as MockProfileRepo:
        mock_repo = AsyncMock()
        mock_repo.get_by_session.return_value = anon_profile_id
        mock_repo.promote_anon_to_user.return_value = promoted_id
        MockProfileRepo.return_value = mock_repo

        result = await bind_session_to_user(conn, session_id, user_id)

    assert result == promoted_id
    mock_repo.promote_anon_to_user.assert_called_once_with(session_id, user_id)


# acceptance #3: 익명 profile 존재해도 delete_by_user 호출 없음
async def test_bind_session_to_user_does_not_call_delete_by_user():
    conn = AsyncMock()
    session_id = uuid.uuid4()
    user_id = uuid.uuid4()
    anon_profile_id = uuid.uuid4()

    with patch("app.services.profile.ProfileRepository") as MockProfileRepo:
        mock_repo = AsyncMock()
        mock_repo.get_by_session.return_value = anon_profile_id
        mock_repo.promote_anon_to_user.return_value = uuid.uuid4()
        MockProfileRepo.return_value = mock_repo

        await bind_session_to_user(conn, session_id, user_id)

    mock_repo.delete_by_user.assert_not_called()


# acceptance #4: get_user_id → user_id → create_for_user(user_id, payload) 1회 호출
async def test_save_profile_for_request_calls_create_for_user_when_logged_in():
    conn = AsyncMock()
    session_id = uuid.uuid4()
    user_id = uuid.uuid4()
    payload = {"name": "test"}
    profile_id = uuid.uuid4()

    with (
        patch("app.services.profile.SessionRepository") as MockSessionRepo,
        patch("app.services.profile.ProfileRepository") as MockProfileRepo,
    ):
        mock_session_repo = AsyncMock()
        mock_session_repo.get_user_id.return_value = user_id
        MockSessionRepo.return_value = mock_session_repo

        mock_profile_repo = AsyncMock()
        mock_profile_repo.create_for_user.return_value = profile_id
        MockProfileRepo.return_value = mock_profile_repo

        result = await save_profile_for_request(conn, session_id, payload)

    assert result == profile_id
    mock_profile_repo.create_for_user.assert_called_once_with(user_id, payload)


# acceptance #5: get_user_id → None → create(session_id=..., payload=...) 호출, create_for_user 호출 없음
async def test_save_profile_for_request_calls_create_when_anonymous():
    conn = AsyncMock()
    session_id = uuid.uuid4()
    payload = {"name": "anon"}
    profile_id = uuid.uuid4()

    with (
        patch("app.services.profile.SessionRepository") as MockSessionRepo,
        patch("app.services.profile.ProfileRepository") as MockProfileRepo,
    ):
        mock_session_repo = AsyncMock()
        mock_session_repo.get_user_id.return_value = None
        MockSessionRepo.return_value = mock_session_repo

        mock_profile_repo = AsyncMock()
        mock_profile_repo.create.return_value = profile_id
        MockProfileRepo.return_value = mock_profile_repo

        result = await save_profile_for_request(conn, session_id, payload)

    assert result == profile_id
    mock_profile_repo.create.assert_called_once_with(session_id=session_id, payload=payload)
    mock_profile_repo.create_for_user.assert_not_called()
