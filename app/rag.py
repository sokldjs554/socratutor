"""문법 노트 RAG: content/grammar/*.md → ChromaDB 인덱스 구축·검색.

인덱스 구축: python -m app.rag
"""

from pathlib import Path

import chromadb

CONTENT_DIR = Path(__file__).resolve().parent.parent / "content" / "grammar"
CHROMA_DIR = ".chroma"


def _collection():
    client = chromadb.PersistentClient(path=CHROMA_DIR)
    return client.get_or_create_collection("grammar_notes")


def build_index() -> int:
    """content/grammar/의 마크다운을 통째로 임베딩한다.

    노트 하나가 길어지면 검색 품질이 떨어지므로, 노트는 주제당 1파일로 짧게 유지한다.
    (파일이 길어지면 청크 분할 도입 — 트러블슈팅 후보)
    """
    col = _collection()
    docs, ids = [], []
    for path in sorted(CONTENT_DIR.glob("*.md")):
        docs.append(path.read_text(encoding="utf-8"))
        ids.append(path.stem)
    if docs:
        col.upsert(ids=ids, documents=docs)
    return len(docs)


def search(query: str, k: int = 3) -> str:
    col = _collection()
    if col.count() == 0:
        return (
            "지식 베이스가 비어 있습니다."
            " `python -m app.rag`로 인덱스를 먼저 구축해야 합니다."
        )
    res = col.query(query_texts=[query], n_results=min(k, col.count()))
    return "\n\n---\n\n".join(res["documents"][0])


if __name__ == "__main__":
    print(f"인덱스 구축 완료: 문서 {build_index()}개")
