from app.services.agents.base import make_subagent
from app.services.agents.prompt_loader import build_agent_prompt


def build_risk_agent():
    return make_subagent(name="risk", prompt=build_agent_prompt("risk"), tools=None)
