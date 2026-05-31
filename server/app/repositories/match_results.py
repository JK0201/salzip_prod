import uuid
from typing import Any

import sqlalchemy as sa
from sqlalchemy.ext.asyncio import AsyncConnection

from app.db.tables.match_results import match_results_table
from app.db.tables.profiles import profiles_table


class MatchResultRepository:
    def __init__(self, conn: AsyncConnection) -> None:
        self._conn = conn

    async def create(self, profile_id: uuid.UUID, payload: dict[str, Any]) -> uuid.UUID:
        stmt = (
            sa.insert(match_results_table)
            .values(profile_id=profile_id, payload=payload)
            .returning(match_results_table.c.id)
        )
        result = await self._conn.execute(stmt)
        return result.scalar_one()

    async def list_by_user(self, user_id: uuid.UUID) -> list[dict[str, Any]]:
        m = match_results_table
        p = profiles_table
        stmt = (
            sa.select(m.c.payload)
            .join(p, p.c.id == m.c.profile_id)
            .where(p.c.user_id == user_id)
            .order_by(m.c.created_at.desc())
        )
        result = await self._conn.execute(stmt)
        rows = result.mappings().all()
        return [row["payload"] for row in rows]
