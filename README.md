# 🏛️ SocraTutor

> 정답을 바로 알려주지 않고 소크라테스식 질문으로 유도하는 영어 학습 AI 튜터 에이전트

학습자가 영어 문법을 질문하면 정답 대신 **단계적 질문과 힌트**로 스스로 답에 도달하게 돕습니다.
문법 지식 베이스를 검색(RAG)해 근거 있는 힌트를 만들고, 학습자의 오답을 기억해 개인화하며,
튜터의 응답 품질을 **LLM-as-judge 자동 평가 파이프라인**으로 검증합니다.

## 🛠️ Tech Stack

| 영역 | 기술 |
|------|------|
| Agent / LLM | Claude API (tool use), Python SDK |
| Backend | FastAPI |
| RAG | ChromaDB |
| Memory / Log | SQLite (학습자 오답노트, 토큰·지연·비용 로그) |
| UI | Streamlit |
| Test / CI | pytest, LLM-as-judge 평가 스크립트, GitHub Actions |

## 📋 주요 기능

- **소크라테스식 튜터 챗** — 정답 즉시 공개 금지, 최대 3단계 질문·힌트로 유도
- **RAG 지식 검색** — 문법 노트를 ChromaDB에서 검색해 근거 있는 힌트 생성
- **학습자 메모리** — 오답·약점을 기록하고 다음 대화에 컨텍스트로 주입
- **퀴즈 출제·채점** — 약점 기반 문제 출제, 결과를 오답노트에 반영
- **자동 평가 파이프라인** — 시나리오 30개 × 기준 3개(행동 준수/정확성/교육적 품질)를 LLM-as-judge로 채점, 프롬프트 버전별 점수 추적
- **운영 로그** — 요청별 토큰·지연시간·추정 비용 기록 + `/stats` 요약

## 📐 설계 문서

상세 설계는 [docs/PROJECT_DESIGN.md](docs/PROJECT_DESIGN.md) 참고
(아키텍처, 에이전트·툴 설계, 데이터 모델, API 명세, 평가 파이프라인, 4주 일정)

## 🗓️ 진행 상황

- [x] 프로젝트 기획 및 설계
- [x] 뼈대 구축: FastAPI + 에이전트 루프 + RAG/메모리/평가 스크립트 틀, 테스트·CI
- [ ] 문법 노트 15~20개 작성 및 RAG 인덱스 구축
- [ ] 시스템 프롬프트 실사용 검증 및 개선 (v1 → v2)
- [ ] 퀴즈 툴(make_quiz) 구현
- [ ] 평가 시나리오 12개+ 작성, 프롬프트 버전별 점수 기록
- [ ] 데모 영상, 트러블슈팅 정리

## 📈 평가 점수 변화 (프롬프트 버전별)

> 평가 파이프라인 구축 후 기록 예정

| 버전 | 행동 준수 | 사실 정확성 | 교육적 품질 |
|------|-----------|-------------|-------------|
| v1 | - | - | - |

## 🚀 실행 방법

```bash
# 1. 의존성 설치 & 환경 변수
pip install -r requirements.txt
cp .env.example .env   # ANTHROPIC_API_KEY 입력

# 2. RAG 인덱스 구축 (content/grammar/ 노트 임베딩)
python -m app.rag

# 3. API 서버
uvicorn app.main:app --reload

# 4. 채팅 UI (별도 터미널)
streamlit run ui/streamlit_app.py

# 5. 평가 파이프라인
python -m eval.run --prompt-version v1

# 테스트 / 린트
pytest && ruff check .
```

## 🧗 트러블슈팅 기록

> 개발하며 막힌 문제와 해결 과정을 기록합니다
