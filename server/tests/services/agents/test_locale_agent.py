import importlib
from unittest.mock import MagicMock, patch


def test_build_locale_agent_exists():
    from app.services.agents.locale_agent import build_locale_agent

    assert callable(build_locale_agent)


def test_build_locale_agent_calls_make_subagent_once():
    fake_agent = MagicMock()
    with patch(
        "app.services.agents.locale_agent.make_subagent", return_value=fake_agent
    ) as mock_make:
        from app.services.agents.locale_agent import build_locale_agent

        build_locale_agent()

        mock_make.assert_called_once()


def test_build_locale_agent_passes_name_locale():
    fake_agent = MagicMock()
    with patch(
        "app.services.agents.locale_agent.make_subagent", return_value=fake_agent
    ) as mock_make:
        from app.services.agents.locale_agent import build_locale_agent

        build_locale_agent()

        call_kwargs = mock_make.call_args
        name_val = call_kwargs.kwargs.get("name") or (
            call_kwargs.args[0] if call_kwargs.args else None
        )
        assert name_val == "locale"


def test_build_locale_agent_passes_tools_none():
    fake_agent = MagicMock()
    with patch(
        "app.services.agents.locale_agent.make_subagent", return_value=fake_agent
    ) as mock_make:
        from app.services.agents.locale_agent import build_locale_agent

        build_locale_agent()

        call_kwargs = mock_make.call_args
        tools_val = call_kwargs.kwargs.get("tools", ...)
        assert tools_val is None


# --- T-140 acceptance ---


def test_locale_agent_has_no_prompt_constant():
    """acceptance #1: _PROMPT 상수 제거 확인."""
    import app.services.agents.locale_agent as locale_mod

    importlib.reload(locale_mod)
    assert not hasattr(locale_mod, "_PROMPT")


def test_build_locale_agent_uses_build_agent_prompt():
    """acceptance #3: prompt=build_agent_prompt('locale') 결합 프롬프트 사용."""
    fake_agent = MagicMock()
    fake_prompt = "shared\n\nlocale"
    with (
        patch(
            "app.services.agents.locale_agent.make_subagent", return_value=fake_agent
        ) as mock_make,
        patch(
            "app.services.agents.locale_agent.build_agent_prompt",
            return_value=fake_prompt,
        ) as mock_build,
    ):
        from app.services.agents.locale_agent import build_locale_agent

        build_locale_agent()

        mock_build.assert_called_once_with("locale")
        call_kwargs = mock_make.call_args
        prompt_val = call_kwargs.kwargs.get("prompt") or (
            call_kwargs.args[1] if len(call_kwargs.args) > 1 else None
        )
        assert prompt_val == fake_prompt


def test_orchestrator_import_no_error():
    """acceptance #5: orchestrator import 시 ImportError 없음(회귀)."""
    import app.services.agents.orchestrator  # noqa: F401
