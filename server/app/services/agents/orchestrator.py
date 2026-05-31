import asyncio
import json
from collections.abc import AsyncGenerator

from app.services.agents.locale_agent import build_locale_agent
from app.services.agents.risk_agent import build_risk_agent
from app.services.agents.sise_agent import build_sise_agent
from app.services.agents.sse import format_sse
from app.services.agents.support_agent import build_support_agent
from app.services.agents.synth_agent import build_synth_agent

# Router 패턴: context["type"]별 전문 에이전트 팀.
# v1은 "research" 팀(4개 병렬) → synthesize(종합) 흐름.
RESEARCH_TEAM: dict = {
    "risk": build_risk_agent,
    "sise": build_sise_agent,
    "locale": build_locale_agent,
    "support": build_support_agent,
}
TEAMS: dict[str, dict] = {
    "research": RESEARCH_TEAM,
}
# 하위호환(기존 테스트가 AGENTS 참조)
AGENTS = RESEARCH_TEAM

_SENTINEL = object()


async def _stream_agent(name, build_fn, user_msg, queue, collected):
    """단일 subagent 실행 → 토큰 SSE + 전문(full text) collected에 적재."""
    await queue.put(format_sse("agent_start", {"agent": name}))
    parts: list[str] = []
    try:
        agent = build_fn()
        stream = await agent.astream_events(
            {"messages": [{"role": "user", "content": user_msg}]}, version="v3"
        )
        async for message in stream.messages:
            async for delta in message.text:
                if delta:
                    parts.append(str(delta))
                    await queue.put(
                        format_sse("token", {"agent": name, "delta": str(delta)})
                    )
    except Exception as exc:  # noqa: BLE001
        await queue.put(format_sse("agent_error", {"agent": name, "error": str(exc)}))
    finally:
        collected[name] = "".join(parts)
        await queue.put(format_sse("agent_done", {"agent": name}))


async def analyze_stream(context: dict) -> AsyncGenerator[str, None]:
    queue: asyncio.Queue = asyncio.Queue()
    user_msg = json.dumps(context, ensure_ascii=False, default=str)

    # ── 라우팅: context.type → 팀 선택 (규칙기반) ──
    route = context.get("type", "research")
    team = TEAMS.get(route, RESEARCH_TEAM)
    yield format_sse("route", {"type": route, "agents": list(team.keys())})
    yield format_sse("scores", {
        "risk": context.get("risk"),
        "sise": context.get("sise"),
        "locale": context.get("locale"),
        "support": context.get("support"),
    })

    collected: dict[str, str] = {}

    async def gather_then_synth():
        # 1) 팀 전문 에이전트 병렬 실행
        await asyncio.gather(
            *(_stream_agent(n, f, user_msg, queue, collected) for n, f in team.items())
        )
        # 2) synthesize: 4개 결과를 종합 에이전트가 통합 스트리밍
        synth_input = json.dumps(
            {"listing": context, "analyses": collected}, ensure_ascii=False, default=str
        )
        await _stream_agent(
            "synth", build_synth_agent, synth_input, queue, collected
        )
        await queue.put(_SENTINEL)

    asyncio.create_task(gather_then_synth())

    while True:
        item = await queue.get()
        if item is _SENTINEL:
            break
        yield item

    yield format_sse("done", {})
