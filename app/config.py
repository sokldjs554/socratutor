import os

from dotenv import load_dotenv

load_dotenv()

MODEL = os.getenv("SOCRATUTOR_MODEL", "claude-opus-4-8")
JUDGE_MODEL = os.getenv("SOCRATUTOR_JUDGE_MODEL", MODEL)
DB_PATH = os.getenv("SOCRATUTOR_DB", "socratutor.sqlite3")

# 1M 토큰당 (입력, 출력) 달러 단가 — 요청별 추정 비용 계산에 사용
PRICES = {
    "claude-opus-4-8": (5.0, 25.0),
    "claude-haiku-4-5": (1.0, 5.0),
}


def estimate_cost_usd(model: str, input_tokens: int, output_tokens: int) -> float:
    price_in, price_out = PRICES.get(model, (0.0, 0.0))
    return input_tokens * price_in / 1e6 + output_tokens * price_out / 1e6
