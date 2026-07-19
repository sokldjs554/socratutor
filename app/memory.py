"""학습자 오답노트와 요청 로그 저장 (SQLite)."""

import sqlite3

from app.config import DB_PATH, estimate_cost_usd


def _conn():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db() -> None:
    with _conn() as conn:
        conn.executescript(
            """
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            );
            CREATE TABLE IF NOT EXISTS mistakes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL REFERENCES users(id),
                topic TEXT NOT NULL,
                question TEXT NOT NULL,
                wrong_answer TEXT NOT NULL,
                note TEXT NOT NULL,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            );
            CREATE TABLE IF NOT EXISTS request_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                model TEXT NOT NULL,
                input_tokens INTEGER NOT NULL,
                output_tokens INTEGER NOT NULL,
                latency_ms INTEGER NOT NULL,
                est_cost_usd REAL NOT NULL,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            );
            """
        )


def get_or_create_user(user_id: int) -> None:
    with _conn() as conn:
        conn.execute("INSERT OR IGNORE INTO users (id) VALUES (?)", (user_id,))


def record_mistake(
    user_id: int, topic: str, question: str, wrong_answer: str, note: str
) -> None:
    with _conn() as conn:
        conn.execute(
            "INSERT INTO mistakes (user_id, topic, question, wrong_answer, note)"
            " VALUES (?, ?, ?, ?, ?)",
            (user_id, topic, question, wrong_answer, note),
        )


def get_recent_mistakes(user_id: int, limit: int = 10) -> list[dict]:
    with _conn() as conn:
        rows = conn.execute(
            "SELECT topic, question, wrong_answer, note, created_at FROM mistakes"
            " WHERE user_id = ? ORDER BY id DESC LIMIT ?",
            (user_id, limit),
        ).fetchall()
    return [dict(r) for r in rows]


def format_recent_mistakes(user_id: int, limit: int = 5) -> str:
    """에이전트 툴이 컨텍스트로 쓰기 좋은 문자열 형태로 오답노트를 요약한다."""
    mistakes = get_recent_mistakes(user_id, limit)
    if not mistakes:
        return "아직 기록된 오답이 없습니다."
    lines = [
        f"- [{m['topic']}] {m['question']} → 오답: {m['wrong_answer']} ({m['note']})"
        for m in mistakes
    ]
    return "최근 오답노트:\n" + "\n".join(lines)


def log_request(
    user_id: int, model: str, input_tokens: int, output_tokens: int, latency_ms: int
) -> None:
    with _conn() as conn:
        conn.execute(
            "INSERT INTO request_logs"
            " (user_id, model, input_tokens, output_tokens, latency_ms, est_cost_usd)"
            " VALUES (?, ?, ?, ?, ?, ?)",
            (
                user_id,
                model,
                input_tokens,
                output_tokens,
                latency_ms,
                estimate_cost_usd(model, input_tokens, output_tokens),
            ),
        )


def get_stats() -> dict:
    with _conn() as conn:
        row = conn.execute(
            "SELECT COUNT(*) AS requests,"
            " COALESCE(SUM(input_tokens), 0) AS input_tokens,"
            " COALESCE(SUM(output_tokens), 0) AS output_tokens,"
            " COALESCE(AVG(latency_ms), 0) AS avg_latency_ms,"
            " COALESCE(SUM(est_cost_usd), 0) AS total_cost_usd"
            " FROM request_logs"
        ).fetchone()
    return dict(row)
