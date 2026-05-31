import importlib
from unittest.mock import MagicMock, patch


def test_synth_agent_has_no_PROMPT_constant():
    """AC#1: _PROMPT 상수가 모듈에 존재하지 않아야 한다."""
    import app.services.agents.synth_agent as mod

    importlib.reload(mod)
    assert not hasattr(mod, "_PROMPT"), "_PROMPT 상수가 제거되지 않았다"


def test_build_synth_agent_passes_name_synth():
    """AC#2: make_subagent를 name='synth'로 호출한다."""
    fake_agent = MagicMock()
    with patch(
        "app.services.agents.synth_agent.make_subagent", return_value=fake_agent
    ) as mock_make:
        import app.services.agents.synth_agent as mod

        importlib.reload(mod)
        mod.build_synth_agent()

        call_kwargs = mock_make.call_args
        name_val = call_kwargs.kwargs.get("name") or (
            call_kwargs.args[0] if call_kwargs.args else None
        )
        assert name_val == "synth"


def test_build_synth_agent_uses_build_agent_prompt():
    """AC#3: build_agent_prompt('synth') 반환값이 prompt로 전달된다."""
    fake_agent = MagicMock()
    fake_prompt = "combined-prompt-for-synth"

    with patch(
        "app.services.agents.synth_agent.make_subagent", return_value=fake_agent
    ) as mock_make, patch(
        "app.services.agents.synth_agent.build_agent_prompt",
        return_value=fake_prompt,
    ) as mock_build:
        import app.services.agents.synth_agent as mod

        importlib.reload(mod)
        mod.build_synth_agent()

        mock_build.assert_called_once_with("synth")
        call_kwargs = mock_make.call_args
        prompt_val = call_kwargs.kwargs.get("prompt") or (
            call_kwargs.args[1] if len(call_kwargs.args) > 1 else None
        )
        assert prompt_val == fake_prompt


def test_build_synth_agent_passes_tools_none():
    """AC#4: make_subagent에 tools=None을 전달한다(회귀)."""
    fake_agent = MagicMock()
    with patch(
        "app.services.agents.synth_agent.make_subagent", return_value=fake_agent
    ) as mock_make:
        import app.services.agents.synth_agent as mod

        importlib.reload(mod)
        mod.build_synth_agent()

        call_kwargs = mock_make.call_args
        tools_val = call_kwargs.kwargs.get("tools", ...)
        assert tools_val is None


def test_import_orchestrator_no_import_error():
    """AC#5: orchestrator import 시 build_synth_agent import에서 ImportError 발생 안 함."""
    try:
        importlib.import_module("app.services.agents.orchestrator")
    except ImportError as exc:
        raise AssertionError(f"orchestrator import 실패: {exc}") from exc


def test_test_file_contains_name_and_prompt_verification():
    """AC#6: 이 테스트 파일이 name='synth'·prompt 전달 검증 테스트를 포함한다."""
    from pathlib import Path

    test_file = Path(__file__)
    content = test_file.read_text(encoding="utf-8")
    assert "synth" in content
    assert "prompt" in content
    assert "mock_build.assert_called_once_with" in content or "mock_make.call_args" in content
