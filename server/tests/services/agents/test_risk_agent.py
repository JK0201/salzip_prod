from unittest.mock import MagicMock, patch

import pytest


# acceptance #1
def test_risk_agent_has_no_prompt_constant():
    import importlib
    import app.services.agents.risk_agent as risk_module

    importlib.reload(risk_module)
    assert not hasattr(risk_module, "_PROMPT"), (
        "_PROMPT 상수가 risk_agent.py에 여전히 존재함 — 제거 필요"
    )


# acceptance #2
def test_build_risk_agent_calls_make_subagent_with_name_risk():
    fake_agent = MagicMock(name="fake_risk_agent")
    with patch("app.services.agents.risk_agent.make_subagent", return_value=fake_agent) as mock_fn, \
         patch("app.services.agents.risk_agent.build_agent_prompt", return_value="PROMPT"):
        from app.services.agents.risk_agent import build_risk_agent

        build_risk_agent()

        mock_fn.assert_called_once()
        _, kwargs = mock_fn.call_args
        assert kwargs.get("name") == "risk", (
            f"make_subagent에 name='risk' 미전달, 실제: {kwargs.get('name')!r}"
        )


# acceptance #3
def test_build_risk_agent_passes_build_agent_prompt_result():
    fake_agent = MagicMock()
    with patch("app.services.agents.risk_agent.make_subagent", return_value=fake_agent) as mock_ms, \
         patch("app.services.agents.risk_agent.build_agent_prompt", return_value="COMBINED_PROMPT") as mock_bap:
        from app.services.agents.risk_agent import build_risk_agent

        build_risk_agent()

        mock_bap.assert_called_once_with("risk")
        _, kwargs = mock_ms.call_args
        assert kwargs.get("prompt") == "COMBINED_PROMPT", (
            f"make_subagent에 build_agent_prompt('risk') 결과 미전달, 실제: {kwargs.get('prompt')!r}"
        )


# acceptance #4 (회귀)
def test_build_risk_agent_passes_tools_none():
    fake_agent = MagicMock()
    with patch("app.services.agents.risk_agent.make_subagent", return_value=fake_agent) as mock_fn, \
         patch("app.services.agents.risk_agent.build_agent_prompt", return_value="PROMPT"):
        from app.services.agents.risk_agent import build_risk_agent

        build_risk_agent()

        _, kwargs = mock_fn.call_args
        assert kwargs.get("tools") is None, (
            f"tools=None 미전달, 실제: {kwargs.get('tools')!r}"
        )


def test_build_risk_agent_returns_make_subagent_result():
    fake_agent = MagicMock()
    with patch("app.services.agents.risk_agent.make_subagent", return_value=fake_agent), \
         patch("app.services.agents.risk_agent.build_agent_prompt", return_value="PROMPT"):
        from app.services.agents.risk_agent import build_risk_agent

        result = build_risk_agent()

        assert result is fake_agent


# acceptance #5 (회귀)
def test_import_orchestrator_no_import_error():
    import importlib

    try:
        importlib.import_module("app.services.agents.orchestrator")
    except ImportError as e:
        pytest.fail(f"orchestrator import 시 ImportError 발생: {e}")
