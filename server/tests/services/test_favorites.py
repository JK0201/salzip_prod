import datetime
import uuid
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.services.favorites import add_favorite, list_favorites, remove_favorite

USER_ID = uuid.uuid4()
LISTING_ID = uuid.uuid4()


@pytest.fixture
def mock_conn():
    return MagicMock()


def _make_row(listing_id: uuid.UUID, flood_risk, **kwargs) -> dict:
    return {
        "listing_id": listing_id,
        "kind": "원룸",
        "estimated_kind": None,
        "building_name": None,
        "deposit": 5000,
        "monthly_rent": 50,
        "area_m2": 20.0,
        "floor": 3,
        "flood_risk": flood_risk,
        "build_year": 2010,
        "umd_name": "역삼동",
        "lat": 37.5,
        "lng": 127.0,
        "created_at": datetime.datetime(2024, 1, 1, tzinfo=datetime.timezone.utc),
        **kwargs,
    }


async def test_add_favorite_calls_repo_add_once(mock_conn):
    with patch("app.services.favorites.FavoriteRepository") as MockRepo:
        mock_repo = MockRepo.return_value
        mock_repo.add = AsyncMock()

        await add_favorite(mock_conn, USER_ID, LISTING_ID)

        MockRepo.assert_called_once_with(mock_conn)
        mock_repo.add.assert_called_once_with(USER_ID, LISTING_ID)


async def test_remove_favorite_calls_repo_remove_once(mock_conn):
    with patch("app.services.favorites.FavoriteRepository") as MockRepo:
        mock_repo = MockRepo.return_value
        mock_repo.remove = AsyncMock()

        await remove_favorite(mock_conn, USER_ID, LISTING_ID)

        MockRepo.assert_called_once_with(mock_conn)
        mock_repo.remove.assert_called_once_with(USER_ID, LISTING_ID)


async def test_list_favorites_flood_risk_true_maps_to_danger(mock_conn):
    lid = uuid.uuid4()
    row = _make_row(lid, flood_risk=True)

    with patch("app.services.favorites.FavoriteRepository") as MockRepo:
        mock_repo = MockRepo.return_value
        mock_repo.list_with_listings = AsyncMock(return_value=[row])

        result = await list_favorites(mock_conn, USER_ID)

    assert result.items[0].risk_level == "danger"


async def test_list_favorites_flood_risk_false_maps_to_safe(mock_conn):
    lid = uuid.uuid4()
    row = _make_row(lid, flood_risk=False)

    with patch("app.services.favorites.FavoriteRepository") as MockRepo:
        mock_repo = MockRepo.return_value
        mock_repo.list_with_listings = AsyncMock(return_value=[row])

        result = await list_favorites(mock_conn, USER_ID)

    assert result.items[0].risk_level == "safe"


async def test_list_favorites_flood_risk_none_maps_to_safe(mock_conn):
    lid = uuid.uuid4()
    row = _make_row(lid, flood_risk=None)

    with patch("app.services.favorites.FavoriteRepository") as MockRepo:
        mock_repo = MockRepo.return_value
        mock_repo.list_with_listings = AsyncMock(return_value=[row])

        result = await list_favorites(mock_conn, USER_ID)

    assert result.items[0].risk_level == "safe"


async def test_list_favorites_ids_match_items_listing_ids_in_order(mock_conn):
    lid1 = uuid.uuid4()
    lid2 = uuid.uuid4()
    rows = [_make_row(lid1, flood_risk=False), _make_row(lid2, flood_risk=True)]

    with patch("app.services.favorites.FavoriteRepository") as MockRepo:
        mock_repo = MockRepo.return_value
        mock_repo.list_with_listings = AsyncMock(return_value=rows)

        result = await list_favorites(mock_conn, USER_ID)

    assert result.ids == [item.listing_id for item in result.items]
    assert result.ids == [lid1, lid2]
