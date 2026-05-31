import datetime
import uuid

import sqlalchemy as sa
from sqlalchemy.ext.asyncio import AsyncConnection

from app.db.tables.sessions import sessions_table


class SessionRepository:
    def __init__(self, conn: AsyncConnection) -> None:
        self._conn = conn

    async def create(self, token_hash: str, expires_at: datetime.datetime) -> uuid.UUID:
        stmt = (
            sa.insert(sessions_table)
            .values(token_hash=token_hash, expires_at=expires_at)
            .returning(sessions_table.c.id)
        )
        result = await self._conn.execute(stmt)
        return result.scalar_one()

    async def get_active(self, token_hash: str, now: datetime.datetime) -> uuid.UUID | None:
        stmt = sa.select(sessions_table.c.id).where(
            sessions_table.c.token_hash == token_hash,
            sessions_table.c.expires_at > now,
        )
        result = await self._conn.execute(stmt)
        return result.scalar_one_or_none()

    async def set_user_id(self, session_id: uuid.UUID, user_id: uuid.UUID) -> None:
        stmt = (
            sa.update(sessions_table)
            .where(sessions_table.c.id == session_id)
            .values(user_id=user_id)
        )
        await self._conn.execute(stmt)

    async def clear_user_id(self, session_id: uuid.UUID) -> None:
        stmt = (
            sa.update(sessions_table)
            .where(sessions_table.c.id == session_id)
            .values(user_id=None)
        )
        await self._conn.execute(stmt)

    async def get_user_id(self, session_id: uuid.UUID) -> uuid.UUID | None:
        stmt = sa.select(sessions_table.c.user_id).where(
            sessions_table.c.id == session_id,
        )
        result = await self._conn.execute(stmt)
        return result.scalar_one_or_none()

    async def get_expires_at(self, session_id: uuid.UUID) -> datetime.datetime:
        stmt = sa.select(sessions_table.c.expires_at).where(
            sessions_table.c.id == session_id,
        )
        result = await self._conn.execute(stmt)
        return result.scalar_one()

    async def extend_expires_at(
        self, session_id: uuid.UUID, new_expires_at: datetime.datetime
    ) -> None:
        stmt = (
            sa.update(sessions_table)
            .where(sessions_table.c.id == session_id)
            .values(expires_at=new_expires_at)
        )
        await self._conn.execute(stmt)
