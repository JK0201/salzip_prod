import uuid
from unittest.mock import AsyncMock, patch

import pytest
from sqlalchemy.exc import IntegrityError


# ── helpers ──────────────────────────────────────────────────────────────────


def _collect_dep_calls(dependant) -> set:
    """Flatten all dependency callable refs in a FastAPI Dependant tree."""
    calls = set()
    for dep in dependant.dependencies:
        calls.add(dep.call)
        calls.update(_collect_dep_calls(dep))
    return calls


# ── acceptance #1: POST /favorites/{listing_id} — status_code 201, UserDep ───


def test_post_favorite_status_code_is_201():
    from fastapi.routing import APIRoute

    from app.api.v1.favorites import router

    route = next(
        r
        for r in router.routes
        if isinstance(r, APIRoute)
        and "POST" in r.methods
        and r.path == "/favorites/{listing_id}"
    )
    assert route.status_code == 201


def test_post_favorite_has_user_dep():
    from fastapi.routing import APIRoute

    from app.api.v1.favorites import router
    from app.core.auth import require_user

    route = next(
        r
        for r in router.routes
        if isinstance(r, APIRoute)
        and "POST" in r.methods
        and r.path == "/favorites/{listing_id}"
    )
    dep_calls = _collect_dep_calls(route.dependant)
    assert require_user in dep_calls, (
        f"POST /favorites/{{listing_id}} must depend on require_user (UserDep). "
        f"found deps: {dep_calls}"
    )


# ── acceptance #2: DELETE /favorites/{listing_id} — status_code 204, UserDep ─


def test_delete_favorite_status_code_is_204():
    from fastapi.routing import APIRoute

    from app.api.v1.favorites import router

    route = next(
        r
        for r in router.routes
        if isinstance(r, APIRoute)
        and "DELETE" in r.methods
        and r.path == "/favorites/{listing_id}"
    )
    assert route.status_code == 204


def test_delete_favorite_has_user_dep():
    from fastapi.routing import APIRoute

    from app.api.v1.favorites import router
    from app.core.auth import require_user

    route = next(
        r
        for r in router.routes
        if isinstance(r, APIRoute)
        and "DELETE" in r.methods
        and r.path == "/favorites/{listing_id}"
    )
    dep_calls = _collect_dep_calls(route.dependant)
    assert require_user in dep_calls, (
        f"DELETE /favorites/{{listing_id}} must depend on require_user (UserDep). "
        f"found deps: {dep_calls}"
    )


# ── acceptance #3: GET /favorites — FavoritesResponse, UserDep ───────────────


def test_get_favorites_response_model_is_favorites_response():
    from fastapi.routing import APIRoute

    from app.api.v1.favorites import router
    from app.schemas.favorites import FavoritesResponse

    route = next(
        r
        for r in router.routes
        if isinstance(r, APIRoute) and "GET" in r.methods and r.path == "/favorites"
    )
    assert route.response_model is FavoritesResponse, (
        f"GET /favorites response_model must be FavoritesResponse, got: {route.response_model}"
    )


def test_get_favorites_has_user_dep():
    from fastapi.routing import APIRoute

    from app.api.v1.favorites import router
    from app.core.auth import require_user

    route = next(
        r
        for r in router.routes
        if isinstance(r, APIRoute) and "GET" in r.methods and r.path == "/favorites"
    )
    dep_calls = _collect_dep_calls(route.dependant)
    assert require_user in dep_calls, (
        f"GET /favorites must depend on require_user (UserDep). found deps: {dep_calls}"
    )


# ── acceptance #4: POST → service raises IntegrityError → 404 ────────────────


async def test_post_favorite_integrity_error_returns_404(client):
    from app.core.auth import CurrentUser, require_user
    from app.core.deps import get_db_conn
    from app.main import app

    fake_user = CurrentUser(session_id=uuid.uuid4(), user_id=uuid.uuid4())
    fake_conn = AsyncMock()
    listing_id = uuid.uuid4()

    app.dependency_overrides[require_user] = lambda: fake_user
    app.dependency_overrides[get_db_conn] = lambda: fake_conn

    try:
        with patch(
            "app.services.favorites.add_favorite",
            new=AsyncMock(side_effect=IntegrityError("fk violation", None, None)),
        ):
            resp = await client.post(f"/api/v1/favorites/{listing_id}")
    finally:
        app.dependency_overrides.pop(require_user, None)
        app.dependency_overrides.pop(get_db_conn, None)

    assert resp.status_code == 404, (
        f"IntegrityError from service must yield 404, got {resp.status_code}: {resp.text}"
    )


# ── acceptance #5: favorites router included in v1 router ────────────────────


def test_favorites_router_included_in_v1_router():
    from fastapi.routing import APIRoute

    from app.api.v1 import router as v1_router_module

    paths = {
        r.path
        for r in v1_router_module.router.routes
        if isinstance(r, APIRoute)
    }
    favorites_paths = {p for p in paths if "favorites" in p}
    assert len(favorites_paths) >= 3, (
        f"Expected at least 3 favorites routes in v1 router, found: {favorites_paths}"
    )
    assert "/favorites" in favorites_paths, (
        f"GET /favorites not in v1 router paths: {favorites_paths}"
    )
    assert "/favorites/{listing_id}" in favorites_paths, (
        f"/favorites/{{listing_id}} not in v1 router paths: {favorites_paths}"
    )


def test_favorites_paths_exposed_in_app():
    from fastapi.routing import APIRoute

    from app.main import app

    paths = {r.path for r in app.routes if isinstance(r, APIRoute)}
    app_favorites = {p for p in paths if "favorites" in p}
    assert any(p.startswith("/api/v1/favorites") for p in app_favorites), (
        f"/api/v1/favorites* not in app routes. favorites paths: {app_favorites}"
    )


# ── acceptance #6: existing v1 routes unchanged (regression) ─────────────────


def test_existing_v1_recommend_routes_intact():
    from fastapi.routing import APIRoute

    from app.api.v1 import router as v1_router_module

    paths = {
        r.path
        for r in v1_router_module.router.routes
        if isinstance(r, APIRoute)
    }
    assert "/recommend" in paths, (
        f"/recommend route missing from v1 router. paths: {sorted(paths)}"
    )
    assert "/recommend/latest" in paths, (
        f"/recommend/latest route missing from v1 router. paths: {sorted(paths)}"
    )


def test_existing_v1_auth_router_intact():
    from app.api.v1 import router as v1_router_module

    # auth_module router is included with prefix="/auth", so its routes
    # appear with "/auth/..." paths in the v1 router
    included_routers = [
        r for r in v1_router_module.router.routes
        if hasattr(r, "routes")  # sub-routers appear as Mount or APIRouter entries
    ]
    # fall back: check app-level paths include /api/v1/auth/*
    from fastapi.routing import APIRoute
    from app.main import app

    app_paths = {r.path for r in app.routes if isinstance(r, APIRoute)}
    auth_paths = {p for p in app_paths if "/api/v1/auth" in p}
    assert len(auth_paths) >= 1, (
        f"Auth routes missing from app after favorites include. auth paths: {auth_paths}"
    )
