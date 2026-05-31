from app.services.agents.base import make_subagent
from app.services.agents.prompt_loader import build_agent_prompt


def build_locale_agent():
    return make_subagent(name="locale", prompt=build_agent_prompt("locale"), tools=None)
