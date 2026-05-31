from pathlib import Path

_PROMPTS_DIR = Path(__file__).parent / "prompts"


def load_prompt_text(name: str) -> str:
    return (_PROMPTS_DIR / f"{name}.md").read_text(encoding="utf-8").strip()


def build_agent_prompt(domain: str) -> str:
    return load_prompt_text("_shared") + "\n\n" + load_prompt_text(domain)
