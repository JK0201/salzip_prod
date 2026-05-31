if "make_subagent" not in globals():
    from app.services.agents.base import make_subagent
if "build_agent_prompt" not in globals():
    from app.services.agents.prompt_loader import build_agent_prompt


def build_support_agent():
    return make_subagent(name="support", prompt=build_agent_prompt("support"), tools=None)
