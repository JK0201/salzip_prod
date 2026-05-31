import inspect
import uuid
from unittest.mock import AsyncMock, MagicMock

import pytest
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from app.repositories.favorites import FavoriteRepository

USER_ID = uuid.uuid4()
LISTING_ID = uuid.uuid4()


def _make_conn(return_rows=None):
    conn = AsyncMock()
    result = MagicMock()
    result.mappings.return_value.all.return_value = return_rows or []
    conn.execute.return_value = result
    return conn


def _compile(stmt) -> str:
    return str(stmt.compile(dialect=postgresql.dialect()))


# ── acceptance #1: add/remove/list_with_listings 존재 + async ──────────────

def test_has_add_remove_list_methods():
    assert hasattr(FavoriteRepository, "add")
    assert hasattr(FavoriteRepository, "remove")
    assert hasattr(FavoriteRepository, "list_with_listings")


def test_all_methods_are_async_coroutines():
    assert inspect.iscoroutinefunction(FavoriteRepository.add)
    assert inspect.iscoroutinefunction(FavoriteRepository.remove)
    assert inspect.iscoroutinefunction(FavoriteRepository.list_with_listings)


# ── acceptance #2: 시그니처 검증 ────────────────────────────────────────────

def test_add_signature():
    params = list(inspect.signature(FavoriteRepository.add).parameters.keys())
    assert params == ["self", "user_id", "listing_id"]


def test_remove_signature():
    params = list(inspect.signature(FavoriteRepository.remove).parameters.keys())
    assert params == ["self", "user_id", "listing_id"]


def test_list_with_listings_signature():
    params = list(inspect.signature(FavoriteRepository.list_with_listings).parameters.keys())
    assert params == ["self", "user_id"]


# ── acceptance #3: add → postgresql INSERT ON CONFLICT DO NOTHING ──────────

async def test_add_uses_pg_insert_on_conflict_do_nothing():
    from sqlalchemy.dialects.postgresql import Insert as PgInsert

    conn = _make_conn()
    repo = FavoriteRepository(conn)
    await repo.add(USER_ID, LISTING_ID)

    conn.execute.assert_called_once()
    stmt = conn.execute.call_args[0][0]
    assert isinstance(stmt, PgInsert), "add()는 postgresql Insert를 사용해야 한다"
    compiled = _compile(stmt)
    assert "ON CONFLICT" in compiled.upper()
    assert "DO NOTHING" in compiled.upper()


async def test_add_targets_favorites_table():
    conn = _make_conn()
    repo = FavoriteRepository(conn)
    await repo.add(USER_ID, LISTING_ID)

    stmt = conn.execute.call_args[0][0]
    compiled = _compile(stmt)
    assert "favorites" in compiled.lower()


# ── acceptance #4: remove → DELETE favorites WHERE user_id AND listing_id ──

async def test_remove_executes_delete_on_favorites():
    conn = _make_conn()
    repo = FavoriteRepository(conn)
    await repo.remove(USER_ID, LISTING_ID)

    conn.execute.assert_called_once()
    stmt = conn.execute.call_args[0][0]
    compiled = _compile(stmt).upper()
    assert "DELETE" in compiled
    assert "FAVORITES" in compiled


async def test_remove_where_includes_user_id_and_listing_id_columns():
    conn = _make_conn()
    repo = FavoriteRepository(conn)
    await repo.remove(USER_ID, LISTING_ID)

    stmt = conn.execute.call_args[0][0]
    compiled = _compile(stmt)
    assert "user_id" in compiled
    assert "listing_id" in compiled


# ── acceptance #5: list_with_listings → JOIN + user_id 필터 + created_at DESC

async def test_list_with_listings_sql_joins_favorites_and_listings():
    conn = _make_conn()
    repo = FavoriteRepository(conn)
    await repo.list_with_listings(USER_ID)

    conn.execute.assert_called_once()
    stmt = conn.execute.call_args[0][0]
    compiled = _compile(stmt).upper()
    assert "JOIN" in compiled
    assert "LISTINGS" in compiled
    assert "FAVORITES" in compiled


async def test_list_with_listings_filters_by_user_id():
    conn = _make_conn()
    repo = FavoriteRepository(conn)
    await repo.list_with_listings(USER_ID)

    stmt = conn.execute.call_args[0][0]
    compiled = _compile(stmt)
    assert "user_id" in compiled


async def test_list_with_listings_orders_by_created_at_desc():
    conn = _make_conn()
    repo = FavoriteRepository(conn)
    await repo.list_with_listings(USER_ID)

    stmt = conn.execute.call_args[0][0]
    compiled = _compile(stmt).upper()
    assert "ORDER BY" in compiled
    assert "DESC" in compiled
    assert "CREATED_AT" in compiled


async def test_list_with_listings_returns_mappings_all():
    rows = [{"listing_id": LISTING_ID, "building_name": "테스트 빌딩"}]
    conn = _make_conn(return_rows=rows)
    repo = FavoriteRepository(conn)
    result = await repo.list_with_listings(USER_ID)

    assert result == rows
