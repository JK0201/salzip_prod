import uuid

from sqlalchemy.ext.asyncio import AsyncConnection

from app.repositories.profiles import ProfileRepository
from app.repositories.session import SessionRepository


async def bind_session_to_user(
    conn: AsyncConnection,
    session_id: uuid.UUID,
    user_id: uuid.UUID,
) -> uuid.UUID | None:
    repo = ProfileRepository(conn)
    existing = await repo.get_by_session(session_id)
    if existing is None:
        return None
    return await repo.promote_anon_to_user(session_id, user_id)


async def save_profile_for_request(
    conn: AsyncConnection,
    session_id: uuid.UUID,
    payload: dict,
) -> uuid.UUID:
    user_id = await SessionRepository(conn).get_user_id(session_id)
    profile_repo = ProfileRepository(conn)
    if user_id is not None:
        return await profile_repo.create_for_user(user_id, payload)
    return await profile_repo.create(session_id=session_id, payload=payload)
