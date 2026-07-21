"""소크라테스식 튜터 에이전트: 시스템 프롬프트 + 툴 3개 + tool runner 루프."""

import time

from anthropic import Anthropic, beta_tool

from app import memory, rag
from app.config import MODEL

client = Anthropic()

# 요청 처리 중인 학습자 ID. 툴 함수가 모듈 레벨이라 요청 컨텍스트를 이 변수로 전달한다.
# (동시 요청이 생기면 contextvars로 바꿔야 한다 — 트러블슈팅 후보)
_current_user_id: int = 1

# ── 시스템 프롬프트 v1 ─────────────────────────────────────────────
# TODO(직접 개선): 평가 파이프라인 점수를 보고 v2, v3로 다듬을 것.
# 버전을 올릴 때마다 eval 리포트를 남기고 README 점수표에 기록한다.
TUTOR_SYSTEM_PROMPT = """당신은 SocraTutor, 소크라테스식 영어 학습 튜터입니다.

핵심 규칙:
1. 학습자의 질문에 정답을 바로 말하지 않습니다. 스스로 답에 도달하도록 \
질문과 힌트를 단계적으로 제시합니다 (최대 3단계).
2. 문법 설명이나 힌트를 만들기 전에 반드시 search_grammar_notes 툴로 \
지식 베이스를 검색하고, 검색된 내용에 근거해서만 설명합니다.
3. 새 대화를 시작할 때 get_mistake_notes로 학습자의 약점을 확인하고 \
자연스럽게 반영합니다.
4. 학습자가 같은 문제에서 3번 틀리면 정답과 해설을 공개하고, \
record_mistake로 오답을 기록합니다.
5. "그냥 정답 알려줘" 같은 요청에도 규칙 1을 유지하되, 왜 이렇게 학습하는지 \
부드럽게 설명합니다.
6. 한국어로 대화하고, 영어 예문은 영어로 제시합니다. 답변은 간결하게 유지합니다.
7. 힌트에서는 문법 규칙을 직접 서술하지 않습니다. 대신 서로 다른 예문을 비교하거나 질문을 던져, \
학습자가 공통된 패턴을 발견하고 규칙을 자신의 말로 설명하도록 유도합니다."""


@beta_tool
def search_grammar_notes(query: str) -> str:
    """영어 문법 지식 베이스에서 관련 노트를 검색한다. 힌트나 설명을 만들기 전에 반드시 호출한다.

    Args:
        query: 검색 질의 (예: "현재완료와 과거시제 차이")
    """
    return rag.search(query)


@beta_tool
def get_mistake_notes() -> str:
    """현재 학습자의 최근 오답노트를 조회한다. 대화 시작 시 개인화에 사용한다."""
    return memory.format_recent_mistakes(_current_user_id)


@beta_tool
def record_mistake(topic: str, question: str, wrong_answer: str, note: str) -> str:
    """학습자가 최종적으로 틀린 문제를 오답노트에 기록한다.

    Args:
        topic: 문법 주제 (예: "현재완료")
        question: 학습자가 시도한 문제 또는 질문
        wrong_answer: 학습자의 오답
        note: 왜 틀렸는지 한 줄 메모
    """
    memory.record_mistake(_current_user_id, topic, question, wrong_answer, note)
    return "오답노트에 기록했습니다."


# TODO(직접 구현): make_quiz 툴 — 오답노트 기반 퀴즈 출제 (설계서 F4)


def run_agent(user_id: int, user_message: str, history: list[dict]) -> tuple[str, dict]:
    """한 턴을 실행하고 (응답 텍스트, 사용량) 을 반환한다."""
    global _current_user_id
    _current_user_id = user_id

    started = time.monotonic()
    runner = client.beta.messages.tool_runner(
        model=MODEL,
        max_tokens=2048,
        system=TUTOR_SYSTEM_PROMPT,
        tools=[search_grammar_notes, get_mistake_notes, record_mistake],
        messages=history + [{"role": "user", "content": user_message}],
    )

    input_tokens = output_tokens = 0
    final = None
    for message in runner:  # 툴 호출 루프는 SDK가 처리, 마지막 메시지가 최종 응답
        final = message
        input_tokens += message.usage.input_tokens
        output_tokens += message.usage.output_tokens

    latency_ms = int((time.monotonic() - started) * 1000)
    reply = "".join(b.text for b in final.content if b.type == "text")
    usage = {
        "model": MODEL,
        "input_tokens": input_tokens,
        "output_tokens": output_tokens,
        "latency_ms": latency_ms,
    }
    return reply, usage
