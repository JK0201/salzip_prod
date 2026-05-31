from unittest.mock import MagicMock, patch


def test_build_echo_agent_callable_no_args():
    from app.services.agents.echo_agent import build_echo_agent

    with patch("app.services.agents.echo_agent.make_subagent") as mock_make:
        mock_make.return_value = MagicMock()
        result = build_echo_agent()
        assert result is not None


def test_build_echo_agent_calls_make_subagent_with_name_echo():
    from app.services.agents.echo_agent import build_echo_agent

    with patch("app.services.agents.echo_agent.make_subagent") as mock_make:
        mock_make.return_value = MagicMock()
        build_echo_agent()
        mock_make.assert_called_once()
        _, kwargs = mock_make.call_args
        assert kwargs.get("name") == "echo" or mock_make.call_args.args[0] == "echo"


def test_build_echo_agent_passes_nonempty_prompt():
    from app.services.agents.echo_agent import build_echo_agent

    with patch("app.services.agents.echo_agent.make_subagent") as mock_make:
        mock_make.return_value = MagicMock()
        build_echo_agent()
        mock_make.assert_called_once()
        call_kwargs = mock_make.call_args.kwargs
        call_args = mock_make.call_args.args
        prompt = call_kwargs.get("prompt") or (call_args[1] if len(call_args) > 1 else None)
        assert isinstance(prompt, str) and len(prompt) > 0
