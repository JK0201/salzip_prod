import uuid

import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.ext.asyncio import AsyncConnection

from app.db.tables.favorites import favorites_table
from app.db.tables.listings import listings_table


class FavoriteRepository:
    def __init__(self, conn: AsyncConnection) -> None:
        self._conn = conn

    async def add(self, user_id: uuid.UUID, listing_id: uuid.UUID) -> None:
        stmt = (
            pg_insert(favorites_table)
            .values(user_id=user_id, listing_id=listing_id)
            .on_conflict_do_nothing(index_elements=["user_id", "listing_id"])
        )
        await self._conn.execute(stmt)

    async def remove(self, user_id: uuid.UUID, listing_id: uuid.UUID) -> None:
        stmt = sa.delete(favorites_table).where(
            favorites_table.c.user_id == user_id,
            favorites_table.c.listing_id == listing_id,
        )
        await self._conn.execute(stmt)

    async def list_with_listings(self, user_id: uuid.UUID) -> list:
        stmt = (
            sa.select(
                listings_table.c.id.label("listing_id"),
                listings_table.c.kind,
                listings_table.c.estimated_kind,
                listings_table.c.building_name,
                listings_table.c.deposit,
                listings_table.c.monthly_rent,
                listings_table.c.area_m2,
                listings_table.c.floor,
                listings_table.c.flood_risk,
                listings_table.c.build_year,
                listings_table.c.umd_name,
                listings_table.c.lat,
                listings_table.c.lng,
                favorites_table.c.created_at,
            )
            .select_from(
                favorites_table.join(
                    listings_table,
                    favorites_table.c.listing_id == listings_table.c.id,
                )
            )
            .where(favorites_table.c.user_id == user_id)
            .order_by(favorites_table.c.created_at.desc())
        )
        result = await self._conn.execute(stmt)
        return result.mappings().all()
