import pytest

from app.services.agents.prompt_loader import build_agent_prompt, load_prompt_text


def test_load_prompt_text_shared_returns_nonempty_stripped_string():
    result = load_prompt_text("_shared")
    assert isinstance(result, str)
    assert len(result) > 0
    assert result == result.strip()


def test_load_prompt_text_risk_contains_domain_phrase():
    result = load_prompt_text("risk")
    assert "4축" in result or "깡통전세" in result


def test_build_agent_prompt_risk_contains_shared_as_substring():
    shared = load_prompt_text("_shared")
    combined = build_agent_prompt("risk")
    assert shared in combined


def test_build_agent_prompt_risk_contains_risk_as_substring():
    risk = load_prompt_text("risk")
    combined = build_agent_prompt("risk")
    assert risk in combined


def test_build_agent_prompt_risk_shared_appears_before_domain():
    shared = load_prompt_text("_shared")
    risk = load_prompt_text("risk")
    combined = build_agent_prompt("risk")
    shared_idx = combined.index(shared)
    risk_idx = combined.index(risk)
    assert shared_idx < risk_idx


def test_load_prompt_text_unknown_raises_file_not_found_error():
    with pytest.raises(FileNotFoundError):
        load_prompt_text("unknown")
