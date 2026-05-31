import uuid
from typing import Any

import sqlalchemy as sa
from sqlalchemy.ext.asyncio import AsyncConnection

from app.db.tables.profiles import profiles_table


class ProfileRepository:
    def __init__(self, conn: AsyncConnection) -> None:
        self._conn = conn

    async def create(self, session_id: uuid.UUID, payload: dict[str, Any]) -> uuid.UUID:
        stmt = (
            sa.insert(profiles_table)
            .values(session_id=session_id, payload=payload)
            .returning(profiles_table.c.id)
        )
        result = await self._conn.execute(stmt)
        return result.scalar_one()

    async def create_for_user(self, user_id: uuid.UUID, payload: dict[str, Any]) -> uuid.UUID:
        stmt = (
            sa.insert(profiles_table)
            .values(user_id=user_id, payload=payload)
            .returning(profiles_table.c.id)
        )
        result = await self._conn.execute(stmt)
        return result.scalar_one()

    async def get_by_user(self, user_id: uuid.UUID) -> uuid.UUID | None:
        stmt = sa.select(profiles_table.c.id).where(profiles_table.c.user_id == user_id)
        result = await self._conn.execute(stmt)
        return result.scalar_one_or_none()

    async def get_by_session(self, session_id: uuid.UUID) -> uuid.UUID | None:
        stmt = sa.select(profiles_table.c.id).where(
            profiles_table.c.session_id == session_id,
            profiles_table.c.user_id.is_(None),
        )
        result = await self._conn.execute(stmt)
        return result.scalar_one_or_none()

    async def promote_anon_to_user(
        self, session_id: uuid.UUID, user_id: uuid.UUID
    ) -> uuid.UUID | None:
        stmt = (
            sa.update(profiles_table)
            .where(
                profiles_table.c.session_id == session_id,
                profiles_table.c.user_id.is_(None),
            )
            .values(user_id=user_id, session_id=None)
            .returning(profiles_table.c.id)
        )
        result = await self._conn.execute(stmt)
        return result.scalar_one_or_none()
