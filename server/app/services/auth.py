import uuid
from datetime import UTC, datetime, timedelta

from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncConnection

from app.core.config import settings
from app.core.exceptions import ConflictError, UnauthorizedError
from app.core.security import hash_password, verify_password
from app.repositories.session import SessionRepository
from app.repositories.users import UserRepository, UserRow
from app.services import profile as profile_service
from app.utils.normalize import normalize_email


async def register_user(
    conn: AsyncConnection,
    session_id: uuid.UUID,
    email: str,
    password: str,
    name: str,
) -> tuple[uuid.UUID, datetime]:
    email_norm = normalize_email(email)
    password_hash = hash_password(password)
    try:
        user_id = await UserRepository(conn).create(email_norm, password_hash, name)
        await SessionRepository(conn).set_user_id(session_id, user_id)
    except IntegrityError:
        raise ConflictError("email already registered") from None
    await profile_service.bind_session_to_user(conn, session_id, user_id)
    expires_at = await SessionRepository(conn).get_expires_at(session_id)
    return (user_id, expires_at)


async def login_user(
    conn: AsyncConnection,
    session_id: uuid.UUID,
    email: str,
    password: str,
) -> tuple[UserRow, datetime]:
    email_norm = normalize_email(email)
    user = await UserRepository(conn).get_by_email(email_norm)
    if user is None or not verify_password(password, user.password_hash):
        raise UnauthorizedError("invalid email or password")
    await SessionRepository(conn).set_user_id(session_id, user.id)
    await profile_service.bind_session_to_user(conn, session_id, user.id)
    new_expires_at = datetime.now(UTC) + timedelta(days=settings.SESSION_TTL_DAYS)
    await SessionRepository(conn).extend_expires_at(session_id, new_expires_at)
    expires_at = await SessionRepository(conn).get_expires_at(session_id)
    return (user, expires_at)


async def logout_user(conn: AsyncConnection, session_id: uuid.UUID) -> None:
    await SessionRepository(conn).clear_user_id(session_id)
