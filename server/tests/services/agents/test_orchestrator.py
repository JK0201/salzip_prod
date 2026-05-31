import json
from unittest.mock import MagicMock

import pytest

from app.services.agents.locale_agent import build_locale_agent
from app.services.agents.orchestrator import AGENTS, analyze_stream
from app.services.agents.risk_agent import build_risk_agent
from app.services.agents.sise_agent import build_sise_agent
from app.services.agents.support_agent import build_support_agent


# ── helpers ───────────────────────────────────────────────────────────────────

async def _collect(context: dict) -> list[str]:
    return [chunk async for chunk in analyze_stream(context)]


def _stub_agent():
    """astream_events가 토큰 없이 즉시 끝나는 최소 mock 에이전트.

    실제 API 형태: astream_events는 코루틴 → stream 객체 반환,
    stream.messages는 async 이터러블(메시지 없음).
    """
    async def _messages():
        if False:
            yield

    async def astream_events(input, **kwargs):
        stream = MagicMock()
        stream.messages = _messages()
        return stream

    agent = MagicMock()
    agent.astream_events = astream_events
    return agent


# ── acceptance #1: AGENTS에 "risk" 키 존재 ────────────────────────────────────

def test_agents_contains_risk_key():
    assert "risk" in AGENTS, f"AGENTS에 'risk' 키가 없음. 현재 키: {list(AGENTS.keys())}"


# ── acceptance #2: AGENTS에 "echo" 키 부재 ────────────────────────────────────

def test_agents_does_not_contain_echo_key():
    assert "echo" not in AGENTS, "'echo' 키가 AGENTS에 여전히 존재함 — 제거되어야 함"


# ── acceptance #3: AGENTS["risk"]가 build_risk_agent ─────────────────────────

def test_agents_risk_value_is_build_risk_agent():
    assert AGENTS["risk"] is build_risk_agent, (
        f"AGENTS['risk']가 build_risk_agent가 아님. 실제: {AGENTS.get('risk')!r}"
    )


# ── T-117 acceptance #1: AGENTS에 "risk"와 "sise" 키 모두 포함 ───────────────

def test_agents_contains_both_risk_and_sise_keys():
    missing = [k for k in ("risk", "sise") if k not in AGENTS]
    assert not missing, f"AGENTS에 누락된 키: {missing}. 현재 키: {list(AGENTS.keys())}"


# ── T-117 acceptance #1(부분): AGENTS에 "sise" 키 존재 ───────────────────────

def test_agents_contains_sise_key():
    assert "sise" in AGENTS, f"AGENTS에 'sise' 키가 없음. 현재 키: {list(AGENTS.keys())}"


# ── T-117 acceptance #2: AGENTS["sise"]가 build_sise_agent ───────────────────

def test_agents_sise_value_is_build_sise_agent():
    assert AGENTS["sise"] is build_sise_agent, (
        f"AGENTS['sise']가 build_sise_agent가 아님. 실제: {AGENTS.get('sise')!r}"
    )


# ── T-117 acceptance #3: 기존 "risk" 키 회귀 ─────────────────────────────────

def test_agents_risk_regression_after_sise_added():
    assert "risk" in AGENTS, "'risk' 키가 sise 추가 후 사라짐"
    assert AGENTS["risk"] is build_risk_agent, (
        f"AGENTS['risk']가 build_risk_agent가 아님. 실제: {AGENTS.get('risk')!r}"
    )


# ── acceptance #4: analyze_stream이 AsyncGenerator 반환 (회귀) ───────────────

async def test_analyze_stream_returns_async_generator(monkeypatch):
    monkeypatch.setattr(
        "app.services.agents.orchestrator.AGENTS",
        {"risk": _stub_agent},
    )

    gen = analyze_stream({"input": "test"})
    assert hasattr(gen, "__aiter__"), "analyze_stream 반환값에 __aiter__ 없음"
    assert hasattr(gen, "__anext__"), "analyze_stream 반환값에 __anext__ 없음"

    # 소비 — 예외 없이 완료되어야 함
    async for _ in gen:
        pass


# ── acceptance #5: stub monkeypatch 상태에서 마지막 chunk에 "event: done" 포함 (회귀) ──

# ── T-121 acceptance #1: AGENTS에 "locale" 키 존재 ──────────────────────────

def test_agents_contains_locale_key():
    assert "locale" in AGENTS, f"AGENTS에 'locale' 키가 없음. 현재 키: {list(AGENTS.keys())}"


# ── T-121 acceptance #2: AGENTS["locale"]가 build_locale_agent ───────────────

def test_agents_locale_value_is_build_locale_agent():
    assert AGENTS["locale"] is build_locale_agent, (
        f"AGENTS['locale']가 build_locale_agent가 아님. 실제: {AGENTS.get('locale')!r}"
    )


# ── acceptance #5: stub monkeypatch 상태에서 마지막 chunk에 "event: done" 포함 (회귀) ──

async def test_analyze_stream_last_chunk_contains_done_event(monkeypatch):
    monkeypatch.setattr(
        "app.services.agents.orchestrator.AGENTS",
        {"risk": _stub_agent},
    )

    chunks = await _collect({"input": "test"})

    assert len(chunks) > 0, "analyze_stream이 아무것도 yield하지 않음"
    assert "event: done" in chunks[-1], (
        f"마지막 chunk에 'event: done' 없음. 실제: {chunks[-1]!r}"
    )


# ── T-125 acceptance #1: AGENTS에 "support" 키 존재 ─────────────────────────

def test_agents_contains_support_key():
    assert "support" in AGENTS, f"AGENTS에 'support' 키가 없음. 현재 키: {list(AGENTS.keys())}"


# ── T-125 acceptance #2: AGENTS["support"]가 build_support_agent ────────────

def test_agents_support_value_is_build_support_agent():
    assert AGENTS["support"] is build_support_agent, (
        f"AGENTS['support']가 build_support_agent가 아님. 실제: {AGENTS.get('support')!r}"
    )


# ── T-125 acceptance #3: AGENTS에 4개 키 모두 포함 ──────────────────────────

def test_agents_contains_all_four_keys():
    required = {"risk", "sise", "locale", "support"}
    missing = required - set(AGENTS.keys())
    assert not missing, f"AGENTS에 누락된 키: {missing}. 현재 키: {list(AGENTS.keys())}"


# ── T-125 acceptance #4: 회귀 — risk 키 유지 ────────────────────────────────

def test_agents_risk_regression_after_support_added():
    assert "risk" in AGENTS, "'risk' 키가 support 추가 후 사라짐"
    assert AGENTS["risk"] is build_risk_agent, (
        f"AGENTS['risk']가 build_risk_agent가 아님. 실제: {AGENTS.get('risk')!r}"
    )


# ── T-125 acceptance #5: 회귀 — sise/locale 키 유지 ─────────────────────────

def test_agents_sise_and_locale_regression_after_support_added():
    assert AGENTS.get("sise") is build_sise_agent, (
        f"AGENTS['sise']가 build_sise_agent가 아님. 실제: {AGENTS.get('sise')!r}"
    )
    assert AGENTS.get("locale") is build_locale_agent, (
        f"AGENTS['locale']가 build_locale_agent가 아님. 실제: {AGENTS.get('locale')!r}"
    )


# ── T-133 helpers ─────────────────────────────────────────────────────────────

def _parse_sse_event(chunk: str) -> tuple[str | None, dict]:
    event_name = None
    data_str = None
    for line in chunk.splitlines():
        if line.startswith("event:"):
            event_name = line.split(":", 1)[1].strip()
        elif line.startswith("data:"):
            data_str = line.split(":", 1)[1].strip()
    return event_name, json.loads(data_str) if data_str else {}


_STUB_TEAM = {
    "risk": _stub_agent,
    "sise": _stub_agent,
    "locale": _stub_agent,
    "support": _stub_agent,
}


# ── T-133 acceptance #1: 첫 번째 이벤트가 event: route (회귀) ────────────────

async def test_t133_first_event_is_route(monkeypatch):
    monkeypatch.setattr("app.services.agents.orchestrator.TEAMS", {"research": _STUB_TEAM})
    chunks = await _collect({"type": "research", "risk": "low"})
    assert len(chunks) >= 1, f"이벤트가 없음. chunks={chunks!r}"
    event, _ = _parse_sse_event(chunks[0])
    assert event == "route", f"첫 번째 이벤트가 'route'가 아님. 실제: {event!r}"


# ── T-133 acceptance #2: 두 번째 이벤트가 event: scores ──────────────────────

async def test_t133_second_event_is_scores(monkeypatch):
    monkeypatch.setattr("app.services.agents.orchestrator.TEAMS", {"research": _STUB_TEAM})
    chunks = await _collect({"type": "research", "risk": "low"})
    assert len(chunks) >= 2, f"이벤트가 2개 미만. chunks={chunks!r}"
    event, _ = _parse_sse_event(chunks[1])
    assert event == "scores", f"두 번째 이벤트가 'scores'가 아님. 실제: {event!r}"


# ── T-133 acceptance #3: scores 페이로드에 risk/sise/locale/support 4개 키 ───

async def test_t133_scores_payload_has_all_four_keys(monkeypatch):
    monkeypatch.setattr("app.services.agents.orchestrator.TEAMS", {"research": _STUB_TEAM})
    context = {"type": "research", "risk": "medium", "sise": 1.5, "locale": "ko", "support": True}
    chunks = await _collect(context)
    _, payload = _parse_sse_event(chunks[1])
    for key in ("risk", "sise", "locale", "support"):
        assert key in payload, f"scores 페이로드에 '{key}' 키 없음. 페이로드: {payload!r}"


# ── T-133 acceptance #4: scores 페이로드 값 = context 동일 키 값 ──────────────

async def test_t133_scores_payload_values_match_context(monkeypatch):
    monkeypatch.setattr("app.services.agents.orchestrator.TEAMS", {"research": _STUB_TEAM})
    context = {"type": "research", "risk": "high", "sise": 2.3, "locale": "en", "support": False}
    chunks = await _collect(context)
    _, payload = _parse_sse_event(chunks[1])
    assert payload["risk"] == context["risk"], f"risk 불일치: {payload['risk']!r} != {context['risk']!r}"
    assert payload["sise"] == context["sise"], f"sise 불일치: {payload['sise']!r} != {context['sise']!r}"
    assert payload["locale"] == context["locale"], f"locale 불일치: {payload['locale']!r} != {context['locale']!r}"
    assert payload["support"] == context["support"], f"support 불일치: {payload['support']!r} != {context['support']!r}"


# ── T-133 acceptance #5: context에 sise 없으면 scores.sise = null ─────────────

async def test_t133_scores_sise_is_none_when_missing_from_context(monkeypatch):
    monkeypatch.setattr("app.services.agents.orchestrator.TEAMS", {"research": _STUB_TEAM})
    context = {"type": "research", "risk": "low", "locale": "ko", "support": True}  # sise 키 없음
    chunks = await _collect(context)
    _, payload = _parse_sse_event(chunks[1])
    assert payload["sise"] is None, f"sise가 None이어야 하는데 실제: {payload['sise']!r}"


# ── T-133 acceptance #6: route 페이로드에 type/agents 키 존재 (회귀) ──────────

async def test_t133_route_payload_has_type_and_agents(monkeypatch):
    monkeypatch.setattr("app.services.agents.orchestrator.TEAMS", {"research": _STUB_TEAM})
    chunks = await _collect({"type": "research", "risk": "low"})
    _, payload = _parse_sse_event(chunks[0])
    assert "type" in payload, f"route 페이로드에 'type' 키 없음. 페이로드: {payload!r}"
    assert "agents" in payload, f"route 페이로드에 'agents' 키 없음. 페이로드: {payload!r}"


# ── T-133 acceptance #7: scores 이후 agent_start/agent_done/done 순서 회귀 ───

async def test_t133_event_order_after_scores(monkeypatch):
    monkeypatch.setattr("app.services.agents.orchestrator.TEAMS", {"research": _STUB_TEAM})
    chunks = await _collect({"type": "research", "risk": "low", "locale": "ko"})
    events_after_scores = [_parse_sse_event(c)[0] for c in chunks[2:]]
    assert "agent_start" in events_after_scores, f"agent_start 없음. 이벤트: {events_after_scores}"
    assert "agent_done" in events_after_scores, f"agent_done 없음. 이벤트: {events_after_scores}"
    assert events_after_scores[-1] == "done", f"마지막 이벤트가 'done'이 아님. 실제: {events_after_scores[-1]!r}"
    first_start = events_after_scores.index("agent_start")
    first_done_idx = events_after_scores.index("agent_done")
    assert first_start < first_done_idx, "agent_start가 agent_done보다 늦게 등장"
