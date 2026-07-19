"""평가 파이프라인: 시나리오별 튜터 응답을 생성하고 LLM-as-judge로 채점한다.

사용법: python -m eval.run --prompt-version v1
결과: eval/reports/{version}.md
"""

import argparse
import json
from pathlib import Path

import yaml
from anthropic import Anthropic

from app import agent, memory
from app.config import JUDGE_MODEL

EVAL_DIR = Path(__file__).resolve().parent
CRITERIA = ["behavior", "accuracy", "quality"]

# TODO(직접 개선): 채점 기준을 더 구체적으로 다듬을 것.
# 기준이 모호하면 judge 점수가 요동친다 — 각 점수(1~5)가 어떤 상태인지 예시를 넣어보기.
JUDGE_PROMPT = """당신은 영어 교육 서비스의 응답 품질 평가자입니다.
소크라테스식 튜터의 응답을 아래 3가지 기준으로 1~5점 채점하세요.

- behavior: 정답을 즉시 노출하지 않고 질문·힌트로 유도했는가
  (단, 학습자가 3번 틀린 뒤라면 정답 공개가 올바른 행동이다)
- accuracy: 문법 설명이 사실에 부합하는가
- quality: 힌트가 학습자 수준에 맞고 다음 사고 단계로 이어지는가

[학습자 메시지]
{message}

[튜터 응답]
{reply}

다른 텍스트 없이 아래 형식의 JSON만 출력하세요:
{{"behavior": <1-5>, "accuracy": <1-5>, "quality": <1-5>, "comment": "<한 줄 근거>"}}"""


def judge(client: Anthropic, message: str, reply: str) -> dict:
    resp = client.messages.create(
        model=JUDGE_MODEL,
        max_tokens=512,
        messages=[
            {
                "role": "user",
                "content": JUDGE_PROMPT.format(message=message, reply=reply),
            }
        ],
    )
    text = "".join(b.text for b in resp.content if b.type == "text").strip()
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        return {c: 0 for c in CRITERIA} | {"comment": f"JSON 파싱 실패: {text[:80]}"}


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--prompt-version", default="v1")
    args = parser.parse_args()

    memory.init_db()
    scenarios = yaml.safe_load((EVAL_DIR / "scenarios.yaml").read_text("utf-8"))
    client = Anthropic()

    rows = []
    for sc in scenarios:
        print(f"[{sc['id']}] 응답 생성 중...")
        # 평가는 히스토리 없는 단발 대화로 단순화 (멀티턴 시나리오는 확장 과제)
        reply, _ = agent.run_agent(user_id=999, user_message=sc["message"], history=[])
        scores = judge(client, sc["message"], reply)
        rows.append({"id": sc["id"], "category": sc["category"], **scores})
        print(f"  → {scores}")

    # 리포트 생성
    report = [f"# 평가 리포트 — 프롬프트 {args.prompt_version}", ""]
    report.append("| id | category | behavior | accuracy | quality | comment |")
    report.append("|----|----------|----------|----------|---------|---------|")
    for r in rows:
        report.append(
            f"| {r['id']} | {r['category']} | {r['behavior']} | {r['accuracy']} |"
            f" {r['quality']} | {r.get('comment', '')} |"
        )
    report.append("")
    for c in CRITERIA:
        avg = sum(r[c] for r in rows) / len(rows)
        report.append(f"- **{c} 평균: {avg:.2f}**")

    out = EVAL_DIR / "reports" / f"{args.prompt_version}.md"
    out.parent.mkdir(exist_ok=True)
    out.write_text("\n".join(report), encoding="utf-8")
    print(f"\n리포트 저장: {out}")


if __name__ == "__main__":
    main()
