import importlib
from unittest.mock import MagicMock, call, patch


def test_build_sise_agent_calls_make_subagent_with_name_sise():
    fake_agent = MagicMock()
    with patch(
        "app.services.agents.sise_agent.make_subagent", return_value=fake_agent
    ) as mock_make:
        from app.services.agents.sise_agent import build_sise_agent

        build_sise_agent()

        mock_make.assert_called_once()
        call_kwargs = mock_make.call_args
        assert call_kwargs.kwargs.get("name") == "sise" or call_kwargs.args[0] == "sise"


def test_build_sise_agent_returns_make_subagent_return_value():
    fake_agent = MagicMock()
    with patch(
        "app.services.agents.sise_agent.make_subagent", return_value=fake_agent
    ):
        import app.services.agents.sise_agent as mod
        importlib.reload(mod)

        result = mod.build_sise_agent()
        assert result is fake_agent


def test_build_sise_agent_passes_non_empty_prompt():
    with patch(
        "app.services.agents.sise_agent.make_subagent"
    ) as mock_make:
        import app.services.agents.sise_agent as mod
        importlib.reload(mod)

        mod.build_sise_agent()

        call_kwargs = mock_make.call_args
        prompt = call_kwargs.kwargs.get("prompt") or (
            call_kwargs.args[1] if len(call_kwargs.args) > 1 else None
        )
        assert prompt is not None
        assert isinstance(prompt, str)
        assert len(prompt.strip()) > 0


# --- T-139 acceptance 추가 테스트 ---


def test_sise_agent_has_no_prompt_constant():
    """acceptance #1: _PROMPT 상수가 모듈에 존재하지 않는다."""
    import app.services.agents.sise_agent as mod
    importlib.reload(mod)

    assert not hasattr(mod, "_PROMPT"), "_PROMPT 상수가 제거되지 않았음"


def test_build_sise_agent_prompt_comes_from_build_agent_prompt():
    """acceptance #3: prompt=build_agent_prompt('sise') 결합 프롬프트를 전달한다."""
    fake_prompt = "shared\n\nsise-domain-content"
    fake_agent = MagicMock()

    with patch(
        "app.services.agents.sise_agent.build_agent_prompt", return_value=fake_prompt
    ) as mock_bap, patch(
        "app.services.agents.sise_agent.make_subagent", return_value=fake_agent
    ) as mock_make:
        import app.services.agents.sise_agent as mod
        importlib.reload(mod)

        mod.build_sise_agent()

        mock_bap.assert_called_once_with("sise")

        call_kwargs = mock_make.call_args
        prompt_arg = call_kwargs.kwargs.get("prompt") or (
            call_kwargs.args[1] if len(call_kwargs.args) > 1 else None
        )
        assert prompt_arg == fake_prompt, (
            f"make_subagent에 전달된 prompt가 build_agent_prompt 반환값이 아님: {prompt_arg!r}"
        )


def test_build_sise_agent_passes_tools_none():
    """acceptance #4: make_subagent에 tools=None을 전달한다(회귀)."""
    fake_agent = MagicMock()

    with patch(
        "app.services.agents.sise_agent.make_subagent", return_value=fake_agent
    ) as mock_make:
        import app.services.agents.sise_agent as mod
        importlib.reload(mod)

        mod.build_sise_agent()

        call_kwargs = mock_make.call_args
        tools_arg = call_kwargs.kwargs.get("tools")
        # positional 3번째 인자일 수도 있음
        if "tools" not in call_kwargs.kwargs and len(call_kwargs.args) > 2:
            tools_arg = call_kwargs.args[2]

        assert tools_arg is None, f"tools 인자가 None이 아님: {tools_arg!r}"


def test_orchestrator_import_no_error():
    """acceptance #5: import orchestrator 시 ImportError 없다(회귀)."""
    import app.services.agents.orchestrator  # noqa: F401
