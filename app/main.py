"""SocraTutor API 서버.

실행: uvicorn app.main:app --reload
"""

from fastapi import FastAPI
from pydantic import BaseModel

from app import agent, memory

app = FastAPI(title="SocraTutor")
memory.init_db()

# 유저별 대화 히스토리 (메모리 보관 — 서버 재시작 시 사라진다.
# 텍스트만 보관하고 툴 호출 블록은 버리는 단순화. DB 보관은 확장 과제)
_histories: dict[int, list[dict]] = {}


class ChatRequest(BaseModel):
    user_id: int = 1
    message: str


@app.post("/chat")
def chat(req: ChatRequest):
    memory.get_or_create_user(req.user_id)
    history = _histories.setdefault(req.user_id, [])

    reply, usage = agent.run_agent(req.user_id, req.message, history)

    history.append({"role": "user", "content": req.message})
    history.append({"role": "assistant", "content": reply})
    memory.log_request(
        req.user_id,
        usage["model"],
        usage["input_tokens"],
        usage["output_tokens"],
        usage["latency_ms"],
    )
    return {"reply": reply, "usage": usage}


@app.get("/users/{user_id}/memory")
def user_memory(user_id: int):
    return {"mistakes": memory.get_recent_mistakes(user_id, limit=20)}


@app.get("/stats")
def stats():
    return memory.get_stats()


@app.get("/health")
def health():
    return {"ok": True}
