import importlib
from unittest.mock import MagicMock, patch


def test_build_support_agent_exists():
    from app.services.agents.support_agent import build_support_agent

    assert callable(build_support_agent)


def test_build_support_agent_calls_make_subagent_once():
    fake_agent = MagicMock()
    with patch(
        "app.services.agents.support_agent.make_subagent", return_value=fake_agent
    ) as mock_make:
        from app.services.agents.support_agent import build_support_agent

        build_support_agent()

        mock_make.assert_called_once()


def test_build_support_agent_passes_name_support():
    fake_agent = MagicMock()
    with patch(
        "app.services.agents.support_agent.make_subagent", return_value=fake_agent
    ) as mock_make:
        from app.services.agents.support_agent import build_support_agent

        build_support_agent()

        call_kwargs = mock_make.call_args
        name_val = call_kwargs.kwargs.get("name") or (
            call_kwargs.args[0] if call_kwargs.args else None
        )
        assert name_val == "support"


def test_build_support_agent_passes_tools_none():
    fake_agent = MagicMock()
    with patch(
        "app.services.agents.support_agent.make_subagent", return_value=fake_agent
    ) as mock_make:
        from app.services.agents.support_agent import build_support_agent

        build_support_agent()

        call_kwargs = mock_make.call_args
        tools_val = call_kwargs.kwargs.get("tools", ...)
        assert tools_val is None


def test_build_support_agent_prompt_is_nonempty_str():
    fake_agent = MagicMock()
    with patch(
        "app.services.agents.support_agent.make_subagent", return_value=fake_agent
    ) as mock_make:
        from app.services.agents.support_agent import build_support_agent

        build_support_agent()

        call_kwargs = mock_make.call_args
        prompt_val = call_kwargs.kwargs.get("prompt") or (
            call_kwargs.args[1] if len(call_kwargs.args) > 1 else None
        )
        assert isinstance(prompt_val, str)
        assert len(prompt_val) > 0


# --- T-141 새 acceptance 테스트 ---


def test_support_agent_has_no_PROMPT_constant():
    """AC#1: _PROMPT 상수가 모듈에 존재하지 않아야 한다."""
    import app.services.agents.support_agent as mod

    importlib.reload(mod)
    assert not hasattr(mod, "_PROMPT"), "_PROMPT 상수가 제거되지 않았다"


def test_build_support_agent_uses_build_agent_prompt():
    """AC#3: build_agent_prompt('support') 반환값이 prompt로 전달된다."""
    fake_agent = MagicMock()
    fake_prompt = "combined-prompt-for-support"

    with patch(
        "app.services.agents.support_agent.make_subagent", return_value=fake_agent
    ) as mock_make, patch(
        "app.services.agents.support_agent.build_agent_prompt",
        return_value=fake_prompt,
    ) as mock_build:
        import app.services.agents.support_agent as mod

        importlib.reload(mod)
        mod.build_support_agent()

        mock_build.assert_called_once_with("support")
        call_kwargs = mock_make.call_args
        prompt_val = call_kwargs.kwargs.get("prompt") or (
            call_kwargs.args[1] if len(call_kwargs.args) > 1 else None
        )
        assert prompt_val == fake_prompt


def test_import_orchestrator_no_import_error():
    """AC#5: support_agent 로더 전환 후 orchestrator import가 깨지지 않아야 한다."""
    try:
        importlib.import_module("app.services.agents.orchestrator")
    except ImportError as exc:
        raise AssertionError(f"orchestrator import 실패: {exc}") from exc
