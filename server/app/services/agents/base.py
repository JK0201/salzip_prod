from langchain.agents import create_agent
from langchain_openai import ChatOpenAI

from app.core.config import settings


def get_model():
    api_key = settings.OPENAI_API_KEY.get_secret_value() if settings.OPENAI_API_KEY else None
    # temperature 0.5 — 점수 인용 일관성 + 자연스러운 풍부함 균형
    return ChatOpenAI(model="gpt-4o-mini", temperature=0.5, api_key=api_key)


def make_subagent(name: str, prompt: str, tools: list | None = None):
    return create_agent(
        model=get_model(), tools=tools or [], system_prompt=prompt, name=name
    )
