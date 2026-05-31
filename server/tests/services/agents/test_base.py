import inspect
from unittest.mock import patch

from app.services.agents import base


def test_make_subagent_signature():
    sig = inspect.signature(base.make_subagent)
    params = list(sig.parameters.keys())
    assert params == ["name", "prompt", "tools"]
    assert sig.parameters["tools"].default is None


@patch("app.services.agents.base.get_model")
@patch("app.services.agents.base.create_agent")
def test_make_subagent_uses_create_agent(mock_create, mock_model):
    base.make_subagent("safety", "분석하라", tools=None)
    mock_create.assert_called_once()
    kwargs = mock_create.call_args.kwargs
    assert kwargs["name"] == "safety"
    assert kwargs["system_prompt"] == "분석하라"
    assert kwargs["tools"] == []


@patch("app.services.agents.base.ChatOpenAI")
def test_get_model_returns_chat_openai(mock_chat):
    base.get_model()
    mock_chat.assert_called_once()
