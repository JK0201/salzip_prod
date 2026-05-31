import uuid

from fastapi import APIRouter
from sqlalchemy.exc import IntegrityError

from app.core.auth import UserDep
from app.core.deps import ConnDep
from app.core.exceptions import NotFoundError
from app.schemas.favorites import FavoritesResponse
from app.services import favorites as favorites_service

router = APIRouter(tags=["favorites"])


@router.post("/favorites/{listing_id}", status_code=201)
async def add_favorite(listing_id: uuid.UUID, user: UserDep, conn: ConnDep) -> dict:
    try:
        await favorites_service.add_favorite(conn, user.user_id, listing_id)
    except IntegrityError:
        raise NotFoundError("listing not found") from None
    return {"ok": True}


@router.delete("/favorites/{listing_id}", status_code=204)
async def remove_favorite(listing_id: uuid.UUID, user: UserDep, conn: ConnDep) -> None:
    await favorites_service.remove_favorite(conn, user.user_id, listing_id)


@router.get("/favorites", response_model=FavoritesResponse)
async def list_favorites(user: UserDep, conn: ConnDep) -> FavoritesResponse:
    return await favorites_service.list_favorites(conn, user.user_id)


@router.get("/favorites/count")
async def count_favorites(user: UserDep, conn: ConnDep) -> dict:
    result = await favorites_service.list_favorites(conn, user.user_id)
    return {"count": len(result.items)}
