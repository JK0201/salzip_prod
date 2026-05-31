import uuid
from unittest.mock import AsyncMock, MagicMock, patch

import pytest


def _collect_dep_calls(dependant) -> set:
    calls = set()
    for dep in dependant.dependencies:
        calls.add(dep.call)
        calls.update(_collect_dep_calls(dep))
    return calls


# ── acceptance #1: POST /listings/{listing_id}/analyze 라우트가 v1 router에 등록 ─


def test_analyze_route_registered_in_v1_router():
    from fastapi.routing import APIRoute

    from app.api.v1 import router as v1_router_module

    routes = [r for r in v1_router_module.router.routes if isinstance(r, APIRoute)]
    paths = {r.path for r in routes}
    assert "/listings/{listing_id}/analyze" in paths, (
        f"/listings/{{listing_id}}/analyze not in v1 router. paths: {paths}"
    )
    route = next(r for r in routes if r.path == "/listings/{listing_id}/analyze")
    assert "POST" in route.methods, (
        f"/listings/{{listing_id}}/analyze must be POST, got: {route.methods}"
    )


# ── acceptance #2: post_analyze 핸들러가 SessionDep에 의존한다 ──────────────────


def test_post_analyze_depends_on_session_dep():
    from fastapi.routing import APIRoute

    from app.api.v1.analyze import router
    from app.core.auth import require_session

    route = next(
        r
        for r in router.routes
        if isinstance(r, APIRoute) and r.path == "/listings/{listing_id}/analyze"
    )
    dep_calls = _collect_dep_calls(route.dependant)
    assert require_session in dep_calls, (
        f"post_analyze must depend on require_session (SessionDep). found: {dep_calls}"
    )


# ── acceptance #3: 존재하지 않는 listing_id → 404 (orchestrator mock) ────────────


async def test_post_analyze_returns_404_when_listing_not_found():
    from app.api.v1.analyze import post_analyze
    from app.core.auth import SessionContext
    from app.core.exceptions import NotFoundError

    listing_id = uuid.uuid4()
    session = SessionContext(session_id=uuid.uuid4(), token="test-token")

    result = MagicMock()
    result.first.return_value = None
    result.scalar_one_or_none.return_value = None
    result.fetchone.return_value = None
    mm = MagicMock()
    mm.first.return_value = None
    result.mappings.return_value = mm

    conn = AsyncMock()
    conn.execute = AsyncMock(return_value=result)

    from app.services.agents import orchestrator

    with patch.object(orchestrator, "analyze_stream", new=MagicMock()):
        with pytest.raises(NotFoundError):
            await post_analyze(listing_id=listing_id, session=session, conn=conn)


# ── acceptance #4: listing 존재 시 응답 media_type이 text/event-stream ───────────


async def test_post_analyze_returns_sse_streaming_response_when_listing_exists():
    from starlette.responses import StreamingResponse

    from app.api.v1.analyze import post_analyze
    from app.core.auth import SessionContext
    from app.services.agents import orchestrator

    listing_id = uuid.uuid4()
    session = SessionContext(session_id=uuid.uuid4(), token="test-token")

    row = MagicMock()
    row.id = listing_id
    row.building_name = "테스트빌딩"
    row.kind = "아파트"
    row.deal_type = "전세"
    row.deposit = 30000
    row.monthly_rent = 0
    row.area_m2 = 59.0
    row.floor = 5
    row.road_addr = "서울 강남구 테헤란로 123"

    result = MagicMock()
    result.first.return_value = row
    result.scalar_one_or_none.return_value = row
    result.fetchone.return_value = row
    mm = MagicMock()
    mm.first.return_value = row
    result.mappings.return_value = mm

    conn = AsyncMock()
    conn.execute = AsyncMock(return_value=result)

    async def fake_stream(context):
        yield b"data: test\n\n"

    with patch.object(orchestrator, "analyze_stream", return_value=fake_stream({})):
        response = await post_analyze(listing_id=listing_id, session=session, conn=conn)

    assert isinstance(response, StreamingResponse), (
        f"listing 존재 시 StreamingResponse여야 함. got: {type(response)}"
    )
    assert response.media_type == "text/event-stream", (
        f"media_type must be text/event-stream, got: {response.media_type}"
    )


# ── acceptance #5: 기존 라우터들 v1 router에 그대로 등록 (회귀 가드) ──────────────


def test_existing_routers_still_registered_in_v1_router():
    from fastapi.routing import APIRoute

    from app.api.v1 import router as v1_router_module

    paths = {r.path for r in v1_router_module.router.routes if isinstance(r, APIRoute)}

    # recommend
    assert any("recommend" in p for p in paths), (
        f"recommend 라우터 경로가 v1 router에 없음. paths: {paths}"
    )
    # session
    assert any("session" in p for p in paths), (
        f"session 라우터 경로가 v1 router에 없음. paths: {paths}"
    )
    # favorites
    assert any("favorites" in p for p in paths), (
        f"favorites 라우터 경로가 v1 router에 없음. paths: {paths}"
    )
    # auth
    assert any("auth" in p for p in paths), (
        f"auth 라우터 경로가 v1 router에 없음. paths: {paths}"
    )


# ── T-114 acceptance #1: get_risk_input이 (listing_id, conn)으로 호출된다 ──────────


async def test_get_risk_input_called_with_listing_id_and_conn():
    from unittest.mock import AsyncMock, MagicMock, patch

    from app.api.v1.analyze import post_analyze
    from app.core.auth import SessionContext
    from app.services.agents import orchestrator

    listing_id = uuid.uuid4()
    session = SessionContext(session_id=uuid.uuid4(), token="test-token")

    row = MagicMock()
    row.id = listing_id
    row.building_name = "테스트빌딩"
    row.kind = "아파트"
    row.deal_type = "전세"
    row.deposit = 30000
    row.monthly_rent = 0
    row.area_m2 = 59.0
    row.floor = 5
    row.road_addr = "서울 강남구 테헤란로 123"

    result = MagicMock()
    result.first.return_value = row
    result.scalar_one_or_none.return_value = row
    result.fetchone.return_value = row
    mm = MagicMock()
    mm.first.return_value = row
    result.mappings.return_value = mm

    conn = AsyncMock()
    conn.execute = AsyncMock(return_value=result)

    fake_risk = {"risk_pct": 35.0, "grade": "중", "factors": ["flood"]}

    async def fake_stream(context):
        yield b"data: test\n\n"

    with patch(
        "app.api.v1.analyze.get_risk_input", new=AsyncMock(return_value=fake_risk)
    ) as mock_risk, patch.object(
        orchestrator, "analyze_stream", return_value=fake_stream({})
    ):
        await post_analyze(listing_id=listing_id, session=session, conn=conn)

    mock_risk.assert_called_once()
    called_listing_id = mock_risk.call_args.args[0]
    called_conn = mock_risk.call_args.args[1]
    assert called_listing_id == listing_id, (
        f"get_risk_input 첫 번째 인자가 listing_id여야 함. got: {called_listing_id}"
    )
    assert called_conn is conn, (
        f"get_risk_input 두 번째 인자가 conn이어야 함. got: {called_conn}"
    )


# ── T-114 acceptance #2: risk 결과가 analyze_stream context에 포함된다 ─────────────


async def test_risk_result_included_in_analyze_stream_context():
    from unittest.mock import AsyncMock, MagicMock, patch

    from app.api.v1.analyze import post_analyze
    from app.core.auth import SessionContext
    from app.services.agents import orchestrator

    listing_id = uuid.uuid4()
    session = SessionContext(session_id=uuid.uuid4(), token="test-token")

    row = MagicMock()
    row.id = listing_id
    row.building_name = "테스트빌딩"
    row.kind = "아파트"
    row.deal_type = "전세"
    row.deposit = 50000
    row.monthly_rent = 0
    row.area_m2 = 84.0
    row.floor = 10
    row.road_addr = "서울 서초구 반포대로 10"

    result = MagicMock()
    result.first.return_value = row
    result.scalar_one_or_none.return_value = row
    result.fetchone.return_value = row
    mm = MagicMock()
    mm.first.return_value = row
    result.mappings.return_value = mm

    conn = AsyncMock()
    conn.execute = AsyncMock(return_value=result)

    fake_risk = {"risk_pct": 72.5, "grade": "고", "factors": ["flood", "hug_accident"]}
    captured_contexts = []

    async def fake_stream(context):
        captured_contexts.append(context)
        yield b"data: test\n\n"

    with patch(
        "app.api.v1.analyze.get_risk_input", new=AsyncMock(return_value=fake_risk)
    ), patch.object(
        orchestrator,
        "analyze_stream",
        side_effect=lambda ctx: fake_stream(ctx),
    ):
        await post_analyze(listing_id=listing_id, session=session, conn=conn)

    assert len(captured_contexts) == 1, (
        f"analyze_stream이 정확히 1번 호출돼야 함. 호출 수: {len(captured_contexts)}"
    )
    context = captured_contexts[0]
    assert "risk" in context, (
        f"context에 'risk' 키가 없음. context keys: {list(context.keys())}"
    )
    assert context["risk"] == fake_risk, (
        f"context['risk']가 get_risk_input 반환값과 달라야 함. got: {context['risk']}"
    )


# ── T-114 acceptance #4 회귀: get_risk_input mock 포함 SSE 응답 확인 ──────────────


async def test_post_analyze_returns_sse_with_risk_mocked():
    from unittest.mock import AsyncMock, MagicMock, patch

    from starlette.responses import StreamingResponse

    from app.api.v1.analyze import post_analyze
    from app.core.auth import SessionContext
    from app.services.agents import orchestrator

    listing_id = uuid.uuid4()
    session = SessionContext(session_id=uuid.uuid4(), token="test-token")

    row = MagicMock()
    row.id = listing_id
    row.building_name = "테스트빌딩"
    row.kind = "오피스텔"
    row.deal_type = "전세"
    row.deposit = 20000
    row.monthly_rent = 0
    row.area_m2 = 33.0
    row.floor = 3
    row.road_addr = "서울 마포구 잔다리로 1"

    result = MagicMock()
    result.first.return_value = row
    result.scalar_one_or_none.return_value = row
    result.fetchone.return_value = row
    mm = MagicMock()
    mm.first.return_value = row
    result.mappings.return_value = mm

    conn = AsyncMock()
    conn.execute = AsyncMock(return_value=result)

    fake_risk = {"risk_pct": 20.0, "grade": "저", "factors": []}

    async def fake_stream(context):
        yield b"data: test\n\n"

    with patch(
        "app.api.v1.analyze.get_risk_input", new=AsyncMock(return_value=fake_risk)
    ), patch.object(orchestrator, "analyze_stream", return_value=fake_stream({})):
        response = await post_analyze(listing_id=listing_id, session=session, conn=conn)

    assert isinstance(response, StreamingResponse), (
        f"listing 존재 시 StreamingResponse여야 함. got: {type(response)}"
    )
    assert response.media_type == "text/event-stream", (
        f"media_type must be text/event-stream, got: {response.media_type}"
    )


# ── T-118 acceptance #1: get_sise_input이 (listing_id, conn)으로 호출된다 ──────────


async def test_get_sise_input_called_with_listing_id_and_conn():
    from app.api.v1.analyze import post_analyze
    from app.core.auth import SessionContext
    from app.services.agents import orchestrator

    listing_id = uuid.uuid4()
    session = SessionContext(session_id=uuid.uuid4(), token="test-token")

    row = MagicMock()
    row.id = listing_id
    row.building_name = "테스트빌딩"
    row.kind = "아파트"
    row.deal_type = "전세"
    row.deposit = 30000
    row.monthly_rent = 0
    row.area_m2 = 59.0
    row.floor = 5
    row.road_addr = "서울 강남구 테헤란로 123"

    result = MagicMock()
    result.first.return_value = row
    result.scalar_one_or_none.return_value = row
    result.fetchone.return_value = row
    mm = MagicMock()
    mm.first.return_value = row
    result.mappings.return_value = mm

    conn = AsyncMock()
    conn.execute = AsyncMock(return_value=result)

    fake_sise = {"avg_price": 80000, "count": 12}

    async def fake_stream(context):
        yield b"data: test\n\n"

    with patch(
        "app.api.v1.analyze.get_risk_input", new=AsyncMock(return_value=None)
    ), patch(
        "app.api.v1.analyze.get_sise_input", new=AsyncMock(return_value=fake_sise)
    ) as mock_sise, patch.object(
        orchestrator, "analyze_stream", return_value=fake_stream({})
    ):
        await post_analyze(listing_id=listing_id, session=session, conn=conn)

    mock_sise.assert_called_once()
    called_listing_id = mock_sise.call_args.args[0]
    called_conn = mock_sise.call_args.args[1]
    assert called_listing_id == listing_id, (
        f"get_sise_input 첫 번째 인자가 listing_id여야 함. got: {called_listing_id}"
    )
    assert called_conn is conn, (
        f"get_sise_input 두 번째 인자가 conn이어야 함. got: {called_conn}"
    )


# ── T-118 acceptance #2: sise 반환값 non-None → context["sise"]에 포함 ──────────────


async def test_sise_result_included_in_context_when_not_none():
    from app.api.v1.analyze import post_analyze
    from app.core.auth import SessionContext
    from app.services.agents import orchestrator

    listing_id = uuid.uuid4()
    session = SessionContext(session_id=uuid.uuid4(), token="test-token")

    row = MagicMock()
    row.id = listing_id
    row.building_name = "테스트빌딩"
    row.kind = "아파트"
    row.deal_type = "월세"
    row.deposit = 5000
    row.monthly_rent = 80
    row.area_m2 = 40.0
    row.floor = 2
    row.road_addr = "서울 용산구 이태원로 1"

    result = MagicMock()
    result.first.return_value = row
    result.scalar_one_or_none.return_value = row
    result.fetchone.return_value = row
    mm = MagicMock()
    mm.first.return_value = row
    result.mappings.return_value = mm

    conn = AsyncMock()
    conn.execute = AsyncMock(return_value=result)

    fake_sise = {"avg_price": 55000, "count": 7, "items": []}
    captured_contexts = []

    async def fake_stream(context):
        captured_contexts.append(context)
        yield b"data: test\n\n"

    with patch(
        "app.api.v1.analyze.get_risk_input", new=AsyncMock(return_value=None)
    ), patch(
        "app.api.v1.analyze.get_sise_input", new=AsyncMock(return_value=fake_sise)
    ), patch.object(
        orchestrator, "analyze_stream", side_effect=lambda ctx: fake_stream(ctx)
    ):
        await post_analyze(listing_id=listing_id, session=session, conn=conn)

    assert len(captured_contexts) == 1, (
        f"analyze_stream이 정확히 1번 호출돼야 함. 호출 수: {len(captured_contexts)}"
    )
    context = captured_contexts[0]
    assert "sise" in context, (
        f"context에 'sise' 키가 없음. context keys: {list(context.keys())}"
    )
    assert context["sise"] == fake_sise, (
        f"context['sise']가 get_sise_input 반환값과 달라야 함. got: {context['sise']}"
    )


# ── T-118 acceptance #3: sise None → context에 "sise" 키 없음 ───────────────────────


async def test_sise_not_in_context_when_get_sise_input_returns_none():
    from app.api.v1.analyze import post_analyze
    from app.core.auth import SessionContext
    from app.services.agents import orchestrator

    listing_id = uuid.uuid4()
    session = SessionContext(session_id=uuid.uuid4(), token="test-token")

    row = MagicMock()
    row.id = listing_id
    row.building_name = "테스트빌딩"
    row.kind = "오피스텔"
    row.deal_type = "전세"
    row.deposit = 15000
    row.monthly_rent = 0
    row.area_m2 = 25.0
    row.floor = 7
    row.road_addr = "서울 송파구 올림픽로 99"

    result = MagicMock()
    result.first.return_value = row
    result.scalar_one_or_none.return_value = row
    result.fetchone.return_value = row
    mm = MagicMock()
    mm.first.return_value = row
    result.mappings.return_value = mm

    conn = AsyncMock()
    conn.execute = AsyncMock(return_value=result)

    captured_contexts = []

    async def fake_stream(context):
        captured_contexts.append(context)
        yield b"data: test\n\n"

    with patch(
        "app.api.v1.analyze.get_risk_input", new=AsyncMock(return_value=None)
    ), patch(
        "app.api.v1.analyze.get_sise_input", new=AsyncMock(return_value=None)
    ), patch.object(
        orchestrator, "analyze_stream", side_effect=lambda ctx: fake_stream(ctx)
    ):
        await post_analyze(listing_id=listing_id, session=session, conn=conn)

    assert len(captured_contexts) == 1
    context = captured_contexts[0]
    assert "sise" not in context, (
        f"get_sise_input이 None 반환 시 context에 'sise' 키 없어야 함. context keys: {list(context.keys())}"
    )


# ── T-118 acceptance #4: risk 여전히 context["risk"]에 포함 (회귀) ─────────────────


async def test_risk_still_in_context_when_sise_injected():
    from app.api.v1.analyze import post_analyze
    from app.core.auth import SessionContext
    from app.services.agents import orchestrator

    listing_id = uuid.uuid4()
    session = SessionContext(session_id=uuid.uuid4(), token="test-token")

    row = MagicMock()
    row.id = listing_id
    row.building_name = "테스트빌딩"
    row.kind = "아파트"
    row.deal_type = "전세"
    row.deposit = 50000
    row.monthly_rent = 0
    row.area_m2 = 84.0
    row.floor = 10
    row.road_addr = "서울 서초구 반포대로 10"

    result = MagicMock()
    result.first.return_value = row
    result.scalar_one_or_none.return_value = row
    result.fetchone.return_value = row
    mm = MagicMock()
    mm.first.return_value = row
    result.mappings.return_value = mm

    conn = AsyncMock()
    conn.execute = AsyncMock(return_value=result)

    fake_risk = {"risk_pct": 60.0, "grade": "고", "factors": ["flood"]}
    fake_sise = {"avg_price": 120000, "count": 5}
    captured_contexts = []

    async def fake_stream(context):
        captured_contexts.append(context)
        yield b"data: test\n\n"

    with patch(
        "app.api.v1.analyze.get_risk_input", new=AsyncMock(return_value=fake_risk)
    ), patch(
        "app.api.v1.analyze.get_sise_input", new=AsyncMock(return_value=fake_sise)
    ), patch.object(
        orchestrator, "analyze_stream", side_effect=lambda ctx: fake_stream(ctx)
    ):
        await post_analyze(listing_id=listing_id, session=session, conn=conn)

    assert len(captured_contexts) == 1
    context = captured_contexts[0]
    assert "risk" in context, (
        f"sise 주입 후에도 context에 'risk' 키가 있어야 함. context keys: {list(context.keys())}"
    )
    assert context["risk"] == fake_risk, (
        f"context['risk']가 get_risk_input 반환값과 달라야 함. got: {context['risk']}"
    )


# ── T-118 acceptance #5: StreamingResponse 회귀 (sise mock 포함) ──────────────────


async def test_post_analyze_sse_response_with_sise_mocked():
    from starlette.responses import StreamingResponse

    from app.api.v1.analyze import post_analyze
    from app.core.auth import SessionContext
    from app.services.agents import orchestrator

    listing_id = uuid.uuid4()
    session = SessionContext(session_id=uuid.uuid4(), token="test-token")

    row = MagicMock()
    row.id = listing_id
    row.building_name = "테스트빌딩"
    row.kind = "아파트"
    row.deal_type = "전세"
    row.deposit = 40000
    row.monthly_rent = 0
    row.area_m2 = 59.0
    row.floor = 3
    row.road_addr = "서울 강북구 도봉로 50"

    result = MagicMock()
    result.first.return_value = row
    result.scalar_one_or_none.return_value = row
    result.fetchone.return_value = row
    mm = MagicMock()
    mm.first.return_value = row
    result.mappings.return_value = mm

    conn = AsyncMock()
    conn.execute = AsyncMock(return_value=result)

    async def fake_stream(context):
        yield b"data: test\n\n"

    with patch(
        "app.api.v1.analyze.get_risk_input", new=AsyncMock(return_value=None)
    ), patch(
        "app.api.v1.analyze.get_sise_input", new=AsyncMock(return_value=None)
    ), patch.object(orchestrator, "analyze_stream", return_value=fake_stream({})):
        response = await post_analyze(listing_id=listing_id, session=session, conn=conn)

    assert isinstance(response, StreamingResponse), (
        f"listing 존재 시 StreamingResponse여야 함. got: {type(response)}"
    )
    assert response.media_type == "text/event-stream", (
        f"media_type must be text/event-stream, got: {response.media_type}"
    )


# ── T-122 acceptance #1: get_locale_input이 (listing_id, conn)으로 호출된다 ─────────


async def test_get_locale_input_called_with_listing_id_and_conn():
    from app.api.v1.analyze import post_analyze
    from app.core.auth import SessionContext
    from app.services.agents import orchestrator

    listing_id = uuid.uuid4()
    session = SessionContext(session_id=uuid.uuid4(), token="test-token")

    row = MagicMock()
    row.id = listing_id
    row.building_name = "테스트빌딩"
    row.kind = "아파트"
    row.deal_type = "전세"
    row.deposit = 30000
    row.monthly_rent = 0
    row.area_m2 = 59.0
    row.floor = 5
    row.road_addr = "서울 강남구 테헤란로 123"

    result = MagicMock()
    result.first.return_value = row
    result.scalar_one_or_none.return_value = row
    result.fetchone.return_value = row
    mm = MagicMock()
    mm.first.return_value = row
    result.mappings.return_value = mm

    conn = AsyncMock()
    conn.execute = AsyncMock(return_value=result)

    fake_locale = {"counts": {"cafe": 3}, "subway_access": True, "medical": 2, "convenience": 5, "green": 1, "area_name": "역삼동"}

    async def fake_stream(context):
        yield b"data: test\n\n"

    with patch(
        "app.api.v1.analyze.get_risk_input", new=AsyncMock(return_value=None)
    ), patch(
        "app.api.v1.analyze.get_sise_input", new=AsyncMock(return_value=None)
    ), patch(
        "app.api.v1.analyze.get_locale_input", new=AsyncMock(return_value=fake_locale)
    ) as mock_locale, patch.object(
        orchestrator, "analyze_stream", return_value=fake_stream({})
    ):
        await post_analyze(listing_id=listing_id, session=session, conn=conn)

    mock_locale.assert_called_once()
    called_listing_id = mock_locale.call_args.args[0]
    called_conn = mock_locale.call_args.args[1]
    assert called_listing_id == listing_id, (
        f"get_locale_input 첫 번째 인자가 listing_id여야 함. got: {called_listing_id}"
    )
    assert called_conn is conn, (
        f"get_locale_input 두 번째 인자가 conn이어야 함. got: {called_conn}"
    )


# ── T-122 acceptance #2: locale non-None → context["locale"]에 포함 ───────────────


async def test_locale_result_included_in_context_when_not_none():
    from app.api.v1.analyze import post_analyze
    from app.core.auth import SessionContext
    from app.services.agents import orchestrator

    listing_id = uuid.uuid4()
    session = SessionContext(session_id=uuid.uuid4(), token="test-token")

    row = MagicMock()
    row.id = listing_id
    row.building_name = "테스트빌딩"
    row.kind = "아파트"
    row.deal_type = "전세"
    row.deposit = 50000
    row.monthly_rent = 0
    row.area_m2 = 84.0
    row.floor = 10
    row.road_addr = "서울 서초구 반포대로 10"

    result = MagicMock()
    result.first.return_value = row
    result.scalar_one_or_none.return_value = row
    result.fetchone.return_value = row
    mm = MagicMock()
    mm.first.return_value = row
    result.mappings.return_value = mm

    conn = AsyncMock()
    conn.execute = AsyncMock(return_value=result)

    fake_locale = {
        "counts": {"cafe": 5, "food": 10, "culture": 2, "park": 3, "mart": 1, "subway": 2, "hospital": 4, "pharmacy": 2},
        "subway_access": True,
        "medical": 6,
        "convenience": 16,
        "green": 3,
        "area_name": "반포동",
    }
    captured_contexts = []

    async def fake_stream(context):
        captured_contexts.append(context)
        yield b"data: test\n\n"

    with patch(
        "app.api.v1.analyze.get_risk_input", new=AsyncMock(return_value=None)
    ), patch(
        "app.api.v1.analyze.get_sise_input", new=AsyncMock(return_value=None)
    ), patch(
        "app.api.v1.analyze.get_locale_input", new=AsyncMock(return_value=fake_locale)
    ), patch.object(
        orchestrator, "analyze_stream", side_effect=lambda ctx: fake_stream(ctx)
    ):
        await post_analyze(listing_id=listing_id, session=session, conn=conn)

    assert len(captured_contexts) == 1, (
        f"analyze_stream이 정확히 1번 호출돼야 함. 호출 수: {len(captured_contexts)}"
    )
    context = captured_contexts[0]
    assert "locale" in context, (
        f"context에 'locale' 키가 없음. context keys: {list(context.keys())}"
    )
    assert context["locale"] == fake_locale, (
        f"context['locale']가 get_locale_input 반환값과 달라야 함. got: {context['locale']}"
    )


# ── T-122 acceptance #3: locale None → context에 "locale" 키 없음 ──────────────────


async def test_locale_not_in_context_when_get_locale_input_returns_none():
    from app.api.v1.analyze import post_analyze
    from app.core.auth import SessionContext
    from app.services.agents import orchestrator

    listing_id = uuid.uuid4()
    session = SessionContext(session_id=uuid.uuid4(), token="test-token")

    row = MagicMock()
    row.id = listing_id
    row.building_name = "테스트빌딩"
    row.kind = "오피스텔"
    row.deal_type = "전세"
    row.deposit = 15000
    row.monthly_rent = 0
    row.area_m2 = 25.0
    row.floor = 7
    row.road_addr = "서울 송파구 올림픽로 99"

    result = MagicMock()
    result.first.return_value = row
    result.scalar_one_or_none.return_value = row
    result.fetchone.return_value = row
    mm = MagicMock()
    mm.first.return_value = row
    result.mappings.return_value = mm

    conn = AsyncMock()
    conn.execute = AsyncMock(return_value=result)

    captured_contexts = []

    async def fake_stream(context):
        captured_contexts.append(context)
        yield b"data: test\n\n"

    with patch(
        "app.api.v1.analyze.get_risk_input", new=AsyncMock(return_value=None)
    ), patch(
        "app.api.v1.analyze.get_sise_input", new=AsyncMock(return_value=None)
    ), patch(
        "app.api.v1.analyze.get_locale_input", new=AsyncMock(return_value=None)
    ), patch.object(
        orchestrator, "analyze_stream", side_effect=lambda ctx: fake_stream(ctx)
    ):
        await post_analyze(listing_id=listing_id, session=session, conn=conn)

    assert len(captured_contexts) == 1
    context = captured_contexts[0]
    assert "locale" not in context, (
        f"get_locale_input이 None 반환 시 context에 'locale' 키 없어야 함. context keys: {list(context.keys())}"
    )


# ── T-122 acceptance #4: locale 주입 후 context["risk"] 유지 (회귀) ─────────────────


async def test_risk_still_in_context_when_locale_injected():
    from app.api.v1.analyze import post_analyze
    from app.core.auth import SessionContext
    from app.services.agents import orchestrator

    listing_id = uuid.uuid4()
    session = SessionContext(session_id=uuid.uuid4(), token="test-token")

    row = MagicMock()
    row.id = listing_id
    row.building_name = "테스트빌딩"
    row.kind = "아파트"
    row.deal_type = "전세"
    row.deposit = 50000
    row.monthly_rent = 0
    row.area_m2 = 84.0
    row.floor = 10
    row.road_addr = "서울 서초구 반포대로 10"

    result = MagicMock()
    result.first.return_value = row
    result.scalar_one_or_none.return_value = row
    result.fetchone.return_value = row
    mm = MagicMock()
    mm.first.return_value = row
    result.mappings.return_value = mm

    conn = AsyncMock()
    conn.execute = AsyncMock(return_value=result)

    fake_risk = {"risk_pct": 60.0, "grade": "고", "factors": ["flood"]}
    fake_locale = {"counts": {}, "subway_access": False, "medical": 0, "convenience": 0, "green": 0, "area_name": "반포동"}
    captured_contexts = []

    async def fake_stream(context):
        captured_contexts.append(context)
        yield b"data: test\n\n"

    with patch(
        "app.api.v1.analyze.get_risk_input", new=AsyncMock(return_value=fake_risk)
    ), patch(
        "app.api.v1.analyze.get_sise_input", new=AsyncMock(return_value=None)
    ), patch(
        "app.api.v1.analyze.get_locale_input", new=AsyncMock(return_value=fake_locale)
    ), patch.object(
        orchestrator, "analyze_stream", side_effect=lambda ctx: fake_stream(ctx)
    ):
        await post_analyze(listing_id=listing_id, session=session, conn=conn)

    assert len(captured_contexts) == 1
    context = captured_contexts[0]
    assert "risk" in context, (
        f"locale 주입 후에도 context에 'risk' 키가 있어야 함. context keys: {list(context.keys())}"
    )
    assert context["risk"] == fake_risk, (
        f"context['risk']가 get_risk_input 반환값과 달라야 함. got: {context['risk']}"
    )


# ── T-122 acceptance #5: locale 주입 후 context["sise"] 유지 (회귀) ─────────────────


async def test_sise_still_in_context_when_locale_injected():
    from app.api.v1.analyze import post_analyze
    from app.core.auth import SessionContext
    from app.services.agents import orchestrator

    listing_id = uuid.uuid4()
    session = SessionContext(session_id=uuid.uuid4(), token="test-token")

    row = MagicMock()
    row.id = listing_id
    row.building_name = "테스트빌딩"
    row.kind = "아파트"
    row.deal_type = "전세"
    row.deposit = 40000
    row.monthly_rent = 0
    row.area_m2 = 59.0
    row.floor = 3
    row.road_addr = "서울 강북구 도봉로 50"

    result = MagicMock()
    result.first.return_value = row
    result.scalar_one_or_none.return_value = row
    result.fetchone.return_value = row
    mm = MagicMock()
    mm.first.return_value = row
    result.mappings.return_value = mm

    conn = AsyncMock()
    conn.execute = AsyncMock(return_value=result)

    fake_sise = {"avg_price": 80000, "count": 12}
    fake_locale = {"counts": {}, "subway_access": True, "medical": 3, "convenience": 8, "green": 2, "area_name": "도봉동"}
    captured_contexts = []

    async def fake_stream(context):
        captured_contexts.append(context)
        yield b"data: test\n\n"

    with patch(
        "app.api.v1.analyze.get_risk_input", new=AsyncMock(return_value=None)
    ), patch(
        "app.api.v1.analyze.get_sise_input", new=AsyncMock(return_value=fake_sise)
    ), patch(
        "app.api.v1.analyze.get_locale_input", new=AsyncMock(return_value=fake_locale)
    ), patch.object(
        orchestrator, "analyze_stream", side_effect=lambda ctx: fake_stream(ctx)
    ):
        await post_analyze(listing_id=listing_id, session=session, conn=conn)

    assert len(captured_contexts) == 1
    context = captured_contexts[0]
    assert "sise" in context, (
        f"locale 주입 후에도 context에 'sise' 키가 있어야 함. context keys: {list(context.keys())}"
    )
    assert context["sise"] == fake_sise, (
        f"context['sise']가 get_sise_input 반환값과 달라야 함. got: {context['sise']}"
    )


# ── T-122 acceptance #6: StreamingResponse 회귀 (locale mock 포함) ───────────────────


async def test_post_analyze_sse_response_with_locale_mocked():
    from starlette.responses import StreamingResponse

    from app.api.v1.analyze import post_analyze
    from app.core.auth import SessionContext
    from app.services.agents import orchestrator

    listing_id = uuid.uuid4()
    session = SessionContext(session_id=uuid.uuid4(), token="test-token")

    row = MagicMock()
    row.id = listing_id
    row.building_name = "테스트빌딩"
    row.kind = "아파트"
    row.deal_type = "전세"
    row.deposit = 30000
    row.monthly_rent = 0
    row.area_m2 = 59.0
    row.floor = 5
    row.road_addr = "서울 강남구 테헤란로 123"

    result = MagicMock()
    result.first.return_value = row
    result.scalar_one_or_none.return_value = row
    result.fetchone.return_value = row
    mm = MagicMock()
    mm.first.return_value = row
    result.mappings.return_value = mm

    conn = AsyncMock()
    conn.execute = AsyncMock(return_value=result)

    async def fake_stream(context):
        yield b"data: test\n\n"

    with patch(
        "app.api.v1.analyze.get_risk_input", new=AsyncMock(return_value=None)
    ), patch(
        "app.api.v1.analyze.get_sise_input", new=AsyncMock(return_value=None)
    ), patch(
        "app.api.v1.analyze.get_locale_input", new=AsyncMock(return_value=None)
    ), patch.object(orchestrator, "analyze_stream", return_value=fake_stream({})):
        response = await post_analyze(listing_id=listing_id, session=session, conn=conn)

    assert isinstance(response, StreamingResponse), (
        f"listing 존재 시 StreamingResponse여야 함. got: {type(response)}"
    )
    assert response.media_type == "text/event-stream", (
        f"media_type must be text/event-stream, got: {response.media_type}"
    )


# ── T-126 acceptance #1: get_support_input이 (session.session_id, conn)으로 호출된다 ──


async def test_get_support_input_called_with_session_id_and_conn():
    from app.api.v1.analyze import post_analyze
    from app.core.auth import SessionContext
    from app.services.agents import orchestrator

    listing_id = uuid.uuid4()
    session = SessionContext(session_id=uuid.uuid4(), token="test-token")

    row = MagicMock()
    row.id = listing_id
    row.building_name = "테스트빌딩"
    row.kind = "아파트"
    row.deal_type = "전세"
    row.deposit = 30000
    row.monthly_rent = 0
    row.area_m2 = 59.0
    row.floor = 5
    row.road_addr = "서울 강남구 테헤란로 123"

    result = MagicMock()
    result.first.return_value = row
    result.scalar_one_or_none.return_value = row
    result.fetchone.return_value = row
    mm = MagicMock()
    mm.first.return_value = row
    result.mappings.return_value = mm

    conn = AsyncMock()
    conn.execute = AsyncMock(return_value=result)

    fake_support = {"count": 2, "programs": [], "max_monthly": None, "max_loan": 50000}

    async def fake_stream(context):
        yield b"data: test\n\n"

    with patch(
        "app.api.v1.analyze.get_risk_input", new=AsyncMock(return_value=None)
    ), patch(
        "app.api.v1.analyze.get_sise_input", new=AsyncMock(return_value=None)
    ), patch(
        "app.api.v1.analyze.get_locale_input", new=AsyncMock(return_value=None)
    ), patch(
        "app.api.v1.analyze.get_support_input", new=AsyncMock(return_value=fake_support)
    ) as mock_support, patch.object(
        orchestrator, "analyze_stream", return_value=fake_stream({})
    ):
        await post_analyze(listing_id=listing_id, session=session, conn=conn)

    mock_support.assert_called_once()
    called_session_id = mock_support.call_args.args[0]
    called_conn = mock_support.call_args.args[1]
    assert called_session_id == session.session_id, (
        f"get_support_input 첫 번째 인자가 session.session_id여야 함. got: {called_session_id}"
    )
    assert called_conn is conn, (
        f"get_support_input 두 번째 인자가 conn이어야 함. got: {called_conn}"
    )


# ── T-126 acceptance #2: support non-None → context["support"]에 포함 ───────────────


async def test_support_result_included_in_context_when_not_none():
    from app.api.v1.analyze import post_analyze
    from app.core.auth import SessionContext
    from app.services.agents import orchestrator

    listing_id = uuid.uuid4()
    session = SessionContext(session_id=uuid.uuid4(), token="test-token")

    row = MagicMock()
    row.id = listing_id
    row.building_name = "테스트빌딩"
    row.kind = "아파트"
    row.deal_type = "전세"
    row.deposit = 50000
    row.monthly_rent = 0
    row.area_m2 = 84.0
    row.floor = 10
    row.road_addr = "서울 서초구 반포대로 10"

    result = MagicMock()
    result.first.return_value = row
    result.scalar_one_or_none.return_value = row
    result.fetchone.return_value = row
    mm = MagicMock()
    mm.first.return_value = row
    result.mappings.return_value = mm

    conn = AsyncMock()
    conn.execute = AsyncMock(return_value=result)

    fake_support = {
        "count": 3,
        "programs": [{"name": "청년전세대출", "support_type": "대출", "monthly_amount_wan": None, "loan_limit": 100000, "agency_name": "주택금융공사"}],
        "max_monthly": None,
        "max_loan": 100000,
    }
    captured_contexts = []

    async def fake_stream(context):
        captured_contexts.append(context)
        yield b"data: test\n\n"

    with patch(
        "app.api.v1.analyze.get_risk_input", new=AsyncMock(return_value=None)
    ), patch(
        "app.api.v1.analyze.get_sise_input", new=AsyncMock(return_value=None)
    ), patch(
        "app.api.v1.analyze.get_locale_input", new=AsyncMock(return_value=None)
    ), patch(
        "app.api.v1.analyze.get_support_input", new=AsyncMock(return_value=fake_support)
    ), patch.object(
        orchestrator, "analyze_stream", side_effect=lambda ctx: fake_stream(ctx)
    ):
        await post_analyze(listing_id=listing_id, session=session, conn=conn)

    assert len(captured_contexts) == 1, (
        f"analyze_stream이 정확히 1번 호출돼야 함. 호출 수: {len(captured_contexts)}"
    )
    context = captured_contexts[0]
    assert "support" in context, (
        f"context에 'support' 키가 없음. context keys: {list(context.keys())}"
    )
    assert context["support"] == fake_support, (
        f"context['support']가 get_support_input 반환값과 달라야 함. got: {context['support']}"
    )


# ── T-126 acceptance #3: support None → context에 "support" 키 없음 ─────────────────


async def test_support_not_in_context_when_get_support_input_returns_none():
    from app.api.v1.analyze import post_analyze
    from app.core.auth import SessionContext
    from app.services.agents import orchestrator

    listing_id = uuid.uuid4()
    session = SessionContext(session_id=uuid.uuid4(), token="test-token")

    row = MagicMock()
    row.id = listing_id
    row.building_name = "테스트빌딩"
    row.kind = "오피스텔"
    row.deal_type = "전세"
    row.deposit = 15000
    row.monthly_rent = 0
    row.area_m2 = 25.0
    row.floor = 7
    row.road_addr = "서울 송파구 올림픽로 99"

    result = MagicMock()
    result.first.return_value = row
    result.scalar_one_or_none.return_value = row
    result.fetchone.return_value = row
    mm = MagicMock()
    mm.first.return_value = row
    result.mappings.return_value = mm

    conn = AsyncMock()
    conn.execute = AsyncMock(return_value=result)

    captured_contexts = []

    async def fake_stream(context):
        captured_contexts.append(context)
        yield b"data: test\n\n"

    with patch(
        "app.api.v1.analyze.get_risk_input", new=AsyncMock(return_value=None)
    ), patch(
        "app.api.v1.analyze.get_sise_input", new=AsyncMock(return_value=None)
    ), patch(
        "app.api.v1.analyze.get_locale_input", new=AsyncMock(return_value=None)
    ), patch(
        "app.api.v1.analyze.get_support_input", new=AsyncMock(return_value=None)
    ), patch.object(
        orchestrator, "analyze_stream", side_effect=lambda ctx: fake_stream(ctx)
    ):
        await post_analyze(listing_id=listing_id, session=session, conn=conn)

    assert len(captured_contexts) == 1
    context = captured_contexts[0]
    assert "support" not in context, (
        f"get_support_input이 None 반환 시 context에 'support' 키 없어야 함. context keys: {list(context.keys())}"
    )


# ── T-126 acceptance #4: support 주입 후에도 context["risk"] 유지 (회귀) ──────────────


async def test_risk_still_in_context_when_support_injected():
    from app.api.v1.analyze import post_analyze
    from app.core.auth import SessionContext
    from app.services.agents import orchestrator

    listing_id = uuid.uuid4()
    session = SessionContext(session_id=uuid.uuid4(), token="test-token")

    row = MagicMock()
    row.id = listing_id
    row.building_name = "테스트빌딩"
    row.kind = "아파트"
    row.deal_type = "전세"
    row.deposit = 50000
    row.monthly_rent = 0
    row.area_m2 = 84.0
    row.floor = 10
    row.road_addr = "서울 서초구 반포대로 10"

    result = MagicMock()
    result.first.return_value = row
    result.scalar_one_or_none.return_value = row
    result.fetchone.return_value = row
    mm = MagicMock()
    mm.first.return_value = row
    result.mappings.return_value = mm

    conn = AsyncMock()
    conn.execute = AsyncMock(return_value=result)

    fake_risk = {"risk_pct": 60.0, "grade": "고", "factors": ["flood"]}
    fake_support = {"count": 1, "programs": [], "max_monthly": 30, "max_loan": None}
    captured_contexts = []

    async def fake_stream(context):
        captured_contexts.append(context)
        yield b"data: test\n\n"

    with patch(
        "app.api.v1.analyze.get_risk_input", new=AsyncMock(return_value=fake_risk)
    ), patch(
        "app.api.v1.analyze.get_sise_input", new=AsyncMock(return_value=None)
    ), patch(
        "app.api.v1.analyze.get_locale_input", new=AsyncMock(return_value=None)
    ), patch(
        "app.api.v1.analyze.get_support_input", new=AsyncMock(return_value=fake_support)
    ), patch.object(
        orchestrator, "analyze_stream", side_effect=lambda ctx: fake_stream(ctx)
    ):
        await post_analyze(listing_id=listing_id, session=session, conn=conn)

    assert len(captured_contexts) == 1
    context = captured_contexts[0]
    assert "risk" in context, (
        f"support 주입 후에도 context에 'risk' 키가 있어야 함. context keys: {list(context.keys())}"
    )
    assert context["risk"] == fake_risk, (
        f"context['risk']가 get_risk_input 반환값과 달라야 함. got: {context['risk']}"
    )


# ── T-126 acceptance #5: support 주입 후에도 context["sise"], context["locale"] 유지 ─


async def test_sise_and_locale_still_in_context_when_support_injected():
    from app.api.v1.analyze import post_analyze
    from app.core.auth import SessionContext
    from app.services.agents import orchestrator

    listing_id = uuid.uuid4()
    session = SessionContext(session_id=uuid.uuid4(), token="test-token")

    row = MagicMock()
    row.id = listing_id
    row.building_name = "테스트빌딩"
    row.kind = "아파트"
    row.deal_type = "전세"
    row.deposit = 40000
    row.monthly_rent = 0
    row.area_m2 = 59.0
    row.floor = 3
    row.road_addr = "서울 강북구 도봉로 50"

    result = MagicMock()
    result.first.return_value = row
    result.scalar_one_or_none.return_value = row
    result.fetchone.return_value = row
    mm = MagicMock()
    mm.first.return_value = row
    result.mappings.return_value = mm

    conn = AsyncMock()
    conn.execute = AsyncMock(return_value=result)

    fake_sise = {"avg_price": 80000, "count": 12}
    fake_locale = {"counts": {}, "subway_access": True, "medical": 2, "convenience": 5, "green": 1, "area_name": "도봉동"}
    fake_support = {"count": 0, "programs": [], "max_monthly": None, "max_loan": None}
    captured_contexts = []

    async def fake_stream(context):
        captured_contexts.append(context)
        yield b"data: test\n\n"

    with patch(
        "app.api.v1.analyze.get_risk_input", new=AsyncMock(return_value=None)
    ), patch(
        "app.api.v1.analyze.get_sise_input", new=AsyncMock(return_value=fake_sise)
    ), patch(
        "app.api.v1.analyze.get_locale_input", new=AsyncMock(return_value=fake_locale)
    ), patch(
        "app.api.v1.analyze.get_support_input", new=AsyncMock(return_value=fake_support)
    ), patch.object(
        orchestrator, "analyze_stream", side_effect=lambda ctx: fake_stream(ctx)
    ):
        await post_analyze(listing_id=listing_id, session=session, conn=conn)

    assert len(captured_contexts) == 1
    context = captured_contexts[0]
    assert "sise" in context, (
        f"support 주입 후에도 context에 'sise' 키가 있어야 함. context keys: {list(context.keys())}"
    )
    assert context["sise"] == fake_sise, (
        f"context['sise']가 get_sise_input 반환값과 달라야 함. got: {context['sise']}"
    )
    assert "locale" in context, (
        f"support 주입 후에도 context에 'locale' 키가 있어야 함. context keys: {list(context.keys())}"
    )
    assert context["locale"] == fake_locale, (
        f"context['locale']가 get_locale_input 반환값과 달라야 함. got: {context['locale']}"
    )
