if "make_subagent" not in globals():
    from app.services.agents.base import make_subagent
if "build_agent_prompt" not in globals():
    from app.services.agents.prompt_loader import build_agent_prompt


def build_sise_agent():
    return make_subagent(name="sise", prompt=build_agent_prompt("sise"), tools=None)
