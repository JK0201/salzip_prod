import typing
import uuid

import sqlalchemy as sa
from sqlalchemy.ext.asyncio import AsyncConnection

from app.db.tables.users import users_table


class UserRow(typing.NamedTuple):
    id: uuid.UUID
    email: str
    password_hash: str
    name: str


class UserRepository:
    def __init__(self, conn: AsyncConnection) -> None:
        self._conn = conn

    async def create(self, email: str, password_hash: str, name: str = "") -> uuid.UUID:
        stmt = (
            sa.insert(users_table)
            .values(email=email.lower(), password_hash=password_hash, name=name)
            .returning(users_table.c.id)
        )
        result = await self._conn.execute(stmt)
        return result.scalar_one()

    async def get_by_email(self, email: str) -> UserRow | None:
        stmt = sa.select(
            users_table.c.id,
            users_table.c.email,
            users_table.c.password_hash,
            users_table.c.name,
        ).where(users_table.c.email == email.lower())
        result = await self._conn.execute(stmt)
        row = result.fetchone()
        if row is None:
            return None
        return UserRow(id=row.id, email=row.email, password_hash=row.password_hash, name=row.name)
