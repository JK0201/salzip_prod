import uuid

from sqlalchemy.ext.asyncio import AsyncConnection

from app.repositories.favorites import FavoriteRepository
from app.schemas.favorites import FavoriteItem, FavoritesResponse


async def add_favorite(conn: AsyncConnection, user_id: uuid.UUID, listing_id: uuid.UUID) -> None:
    await FavoriteRepository(conn).add(user_id, listing_id)


async def remove_favorite(conn: AsyncConnection, user_id: uuid.UUID, listing_id: uuid.UUID) -> None:
    await FavoriteRepository(conn).remove(user_id, listing_id)


async def list_favorites(conn: AsyncConnection, user_id: uuid.UUID) -> FavoritesResponse:
    rows = await FavoriteRepository(conn).list_with_listings(user_id)
    items = [
        FavoriteItem(
            **row,
            risk_level="danger" if row["flood_risk"] else "safe",
        )
        for row in rows
    ]
    ids = [item.listing_id for item in items]
    return FavoritesResponse(items=items, ids=ids)
