import uuid
from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock, call, patch

import pytest
from sqlalchemy.exc import IntegrityError

from app.core.exceptions import ConflictError, UnauthorizedError
from app.services.auth import login_user, logout_user, register_user


# acceptance #1: 함수 존재 검증은 import 자체로 커버됨


# acceptance #2 + #3: normalize_email 호출 & 성공 경로 순서
async def test_register_user_calls_normalize_email_and_succeeds():
    conn = AsyncMock()
    session_id = uuid.uuid4()
    user_id = uuid.uuid4()
    expires_at = datetime(2026, 6, 1, tzinfo=timezone.utc)

    with (
        patch("app.services.auth.normalize_email", return_value="user@example.com") as mock_norm,
        patch("app.services.auth.hash_password", return_value="hashed") as mock_hash,
        patch("app.services.auth.UserRepository") as MockUserRepo,
        patch("app.services.auth.SessionRepository") as MockSessionRepo,
        patch("app.services.auth.profile_service") as mock_profile,
    ):
        mock_user_repo = AsyncMock()
        mock_user_repo.create.return_value = user_id
        MockUserRepo.return_value = mock_user_repo

        mock_session_repo = AsyncMock()
        mock_session_repo.get_expires_at.return_value = expires_at
        MockSessionRepo.return_value = mock_session_repo

        mock_profile.bind_session_to_user = AsyncMock()

        result = await register_user(conn, session_id, "User@Example.COM", "pw123", "Alice")

    mock_norm.assert_called_once_with("User@Example.COM")
    mock_hash.assert_called_once_with("pw123")
    assert result == (user_id, expires_at)


# acceptance #3: 호출 순서 검증 (create → set_user_id → bind_session_to_user)
async def test_register_user_success_call_order():
    conn = AsyncMock()
    session_id = uuid.uuid4()
    user_id = uuid.uuid4()
    call_order: list[str] = []

    with (
        patch("app.services.auth.normalize_email", return_value="user@example.com"),
        patch("app.services.auth.hash_password", return_value="hashed"),
        patch("app.services.auth.UserRepository") as MockUserRepo,
        patch("app.services.auth.SessionRepository") as MockSessionRepo,
        patch("app.services.auth.profile_service") as mock_profile,
    ):
        mock_user_repo = AsyncMock()

        async def fake_create(*a, **kw):
            call_order.append("create")
            return user_id

        mock_user_repo.create.side_effect = fake_create
        MockUserRepo.return_value = mock_user_repo

        mock_session_repo = AsyncMock()

        async def fake_set_user_id(*a, **kw):
            call_order.append("set_user_id")

        mock_session_repo.set_user_id.side_effect = fake_set_user_id
        mock_session_repo.get_expires_at.return_value = datetime(2026, 6, 1, tzinfo=timezone.utc)
        MockSessionRepo.return_value = mock_session_repo

        async def fake_bind(*a, **kw):
            call_order.append("bind_session_to_user")

        mock_profile.bind_session_to_user = AsyncMock(side_effect=fake_bind)

        await register_user(conn, session_id, "u@example.com", "pw", "Alice")

    assert call_order == ["create", "set_user_id", "bind_session_to_user"]


# acceptance #4: UserRepository.create IntegrityError → ConflictError
async def test_register_user_raises_conflict_on_integrity_error():
    conn = AsyncMock()
    session_id = uuid.uuid4()

    with (
        patch("app.services.auth.normalize_email", return_value="dup@example.com"),
        patch("app.services.auth.hash_password", return_value="hashed"),
        patch("app.services.auth.UserRepository") as MockUserRepo,
        patch("app.services.auth.SessionRepository"),
        patch("app.services.auth.profile_service"),
    ):
        mock_user_repo = AsyncMock()
        mock_user_repo.create.side_effect = IntegrityError("dup", {}, Exception())
        MockUserRepo.return_value = mock_user_repo

        with pytest.raises(ConflictError, match="email already registered"):
            await register_user(conn, session_id, "dup@example.com", "pw", "Alice")


# acceptance #5: get_by_email None → UnauthorizedError
async def test_login_user_raises_unauthorized_when_user_not_found():
    conn = AsyncMock()
    session_id = uuid.uuid4()

    with (
        patch("app.services.auth.normalize_email", return_value="no@example.com"),
        patch("app.services.auth.UserRepository") as MockUserRepo,
        patch("app.services.auth.SessionRepository"),
        patch("app.services.auth.profile_service"),
    ):
        mock_user_repo = AsyncMock()
        mock_user_repo.get_by_email.return_value = None
        MockUserRepo.return_value = mock_user_repo

        with pytest.raises(UnauthorizedError, match="invalid email or password"):
            await login_user(conn, session_id, "no@example.com", "pw")


# acceptance #6: verify_password False → UnauthorizedError
async def test_login_user_raises_unauthorized_when_password_wrong():
    conn = AsyncMock()
    session_id = uuid.uuid4()
    fake_user = MagicMock()
    fake_user.id = uuid.uuid4()
    fake_user.password_hash = "stored_hash"

    with (
        patch("app.services.auth.normalize_email", return_value="u@example.com"),
        patch("app.services.auth.verify_password", return_value=False),
        patch("app.services.auth.UserRepository") as MockUserRepo,
        patch("app.services.auth.SessionRepository"),
        patch("app.services.auth.profile_service"),
    ):
        mock_user_repo = AsyncMock()
        mock_user_repo.get_by_email.return_value = fake_user
        MockUserRepo.return_value = mock_user_repo

        with pytest.raises(UnauthorizedError, match="invalid email or password"):
            await login_user(conn, session_id, "u@example.com", "wrongpw")


# acceptance #7: login_user 성공 시 set_user_id, bind_session_to_user, extend_expires_at 모두 호출
async def test_login_user_success_calls_all_required_methods():
    conn = AsyncMock()
    session_id = uuid.uuid4()
    user_id = uuid.uuid4()
    fake_user = MagicMock()
    fake_user.id = user_id
    fake_user.password_hash = "stored_hash"
    expires_at = datetime(2026, 6, 1, tzinfo=timezone.utc)

    with (
        patch("app.services.auth.normalize_email", return_value="u@example.com"),
        patch("app.services.auth.verify_password", return_value=True),
        patch("app.services.auth.UserRepository") as MockUserRepo,
        patch("app.services.auth.SessionRepository") as MockSessionRepo,
        patch("app.services.auth.profile_service") as mock_profile,
    ):
        mock_user_repo = AsyncMock()
        mock_user_repo.get_by_email.return_value = fake_user
        MockUserRepo.return_value = mock_user_repo

        mock_session_repo = AsyncMock()
        mock_session_repo.get_expires_at.return_value = expires_at
        MockSessionRepo.return_value = mock_session_repo

        mock_profile.bind_session_to_user = AsyncMock()

        result = await login_user(conn, session_id, "u@example.com", "pw")

    mock_session_repo.set_user_id.assert_called_once_with(session_id, user_id)
    mock_profile.bind_session_to_user.assert_called_once()
    mock_session_repo.extend_expires_at.assert_called_once()
    assert result == (fake_user, expires_at)


# acceptance #8: logout_user → clear_user_id(session_id) 호출
async def test_logout_user_calls_clear_user_id():
    conn = AsyncMock()
    session_id = uuid.uuid4()

    with patch("app.services.auth.SessionRepository") as MockSessionRepo:
        mock_session_repo = AsyncMock()
        MockSessionRepo.return_value = mock_session_repo

        result = await logout_user(conn, session_id)

    mock_session_repo.clear_user_id.assert_called_once_with(session_id)
    assert result is None
