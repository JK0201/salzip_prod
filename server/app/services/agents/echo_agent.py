from app.services.agents.base import make_subagent


def build_echo_agent():
    return make_subagent(
        name="echo",
        prompt="입력 매물에 대해 한두 문장으로 분석 시작을 알리는 짧은 응답만 생성하세요.",
        tools=None,
    )
