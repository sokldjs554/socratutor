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
| UI | FastAPI 내장 웹 채팅 페이지 (HTML/JS) |
| Deploy | Docker, docker-compose |
| Test / CI | pytest, LLM-as-judge 평가 스크립트, GitHub Actions |

## 📋 주요 기능

- **소크라테스식 튜터 챗** — 정답 즉시 공개 금지, 최대 3단계 질문·힌트로 유도
- **RAG 지식 검색** — 문법 노트를 ChromaDB에서 검색해 근거 있는 힌트 생성
- **학습자 메모리** — 오답·약점을 기록하고 다음 대화에 컨텍스트로 주입
- **퀴즈 출제·채점** (구현 예정) — 약점 기반 문제 출제, 결과를 오답노트에 반영
- **자동 평가 파이프라인** — 시나리오 15개 × 기준 3개(행동 준수/정확성/교육적 품질)를 LLM-as-judge로 채점, 프롬프트 버전별 점수 추적
- **운영 로그** — 요청별 토큰·지연시간·추정 비용 기록 + `/stats` 요약

## 📐 설계 문서

상세 설계는 [docs/PROJECT_DESIGN.md](docs/PROJECT_DESIGN.md) 참고
(아키텍처, 에이전트·툴 설계, 데이터 모델, API 명세, 평가 파이프라인, 4주 일정)

## 🗓️ 진행 상황

- [x] 프로젝트 기획 및 설계
- [x] 뼈대 구축: FastAPI + 에이전트 루프 + RAG/메모리/평가 스크립트 틀, 테스트·CI
- [x] 문법 노트 18개 작성 (⚠️ 내용 검토 후 확정) 및 RAG 인덱스 구축
- [x] 시스템 프롬프트 개선 사이클 (v1 → v1-rev → v2 → v3)
- [ ] 퀴즈 툴(make_quiz) 구현
- [x] 평가 시나리오 15개 작성, 프롬프트 버전별 점수 기록
- [ ] (선택) AWS EC2에 Docker로 데모 배포 — 또는 데모 영상으로 대체
- [ ] 데모 영상, 트러블슈팅 정리

## 📈 평가 점수 변화 (프롬프트 버전별)

시나리오 15개 × 기준 3개(1~5점)를 LLM-as-judge로 채점. 버전 간 비교를 위해 변수는 한 번에 하나씩 바꿨다.

| 버전 | 행동 준수 | 사실 정확성 | 교육적 품질 | 변경 내용 |
|------|-----------|-------------|-------------|-----------|
| v1 | 4.93 | 4.67 | 4.53 | 최초 베이스라인 |
| v1-rev | 5.00 | 4.93 | 4.87 | 평가 설계 보완: jailbreak 시나리오에 구체적 문제 추가 (프롬프트 동일 — 새 기준점) |
| v2 | 5.00 | 4.87 | 4.67 | 힌트에서 규칙 직접 서술 금지 규칙 추가 → **점수 하락**. 리포트 분석 결과, 튜터가 예문을 직접 지어내다 비문을 생성한 것이 원인 |
| v3 | 5.00 | 4.93 | 4.80 | 비교 예문은 노트 예문 우선 사용, 새 예문은 짧고 단순하게, 내부 동작 언급 금지 → **회복** |

> 배운 것: 직관적으로 "개선"이라 생각한 수정도 측정해보면 부작용이 있을 수 있다.
> 점수만 보지 않고 채점 코멘트에서 구체적 결함(비문 예문 생성)을 찾아 원인을 고쳤다.

## 🚀 실행 방법

```bash
# 1. 의존성 설치 & 환경 변수
pip install -r requirements.txt
cp .env.example .env   # ANTHROPIC_API_KEY 입력

# 2. RAG 인덱스 구축 (content/grammar/ 노트 임베딩)
python -m app.rag

# 3. API 서버
uvicorn app.main:app --reload

# 4. 채팅 UI — 브라우저에서 http://localhost:8000 접속

# 5. 평가 파이프라인
python -m eval.run --prompt-version v1

# 테스트 / 린트
pytest && ruff check .
```

### Docker로 실행

```bash
cp .env.example .env   # ANTHROPIC_API_KEY 입력
docker compose up --build
# → http://localhost:8000 (컨테이너 시작 시 RAG 인덱스 자동 구축)
```

## 🧗 트러블슈팅 기록

- **Python 3.13 + Intel Mac에서 의존성 설치 실패** — `onnxruntime`(chromadb 의존성)이 해당 환경용 배포판을 제공하지 않아 `ResolutionImpossible` 발생 → Python 3.12로 가상환경 재생성해 해결. 실행 환경은 Python 3.11~3.12 권장
- **YAML 파싱 에러** — 시나리오 메시지에 문장을 추가할 때 닫는 따옴표 바깥에 이어 붙여 `ParserError` 발생 → 에러 메시지의 줄 번호로 위치를 찾아 문장 전체를 따옴표 한 쌍 안으로 수정. 문장 값은 항상 전체를 따옴표로 감싸는 습관
- **프롬프트 개선이 점수를 낮춘 사건** — v2에서 "규칙 직접 서술 금지"를 추가하자 정확성·품질 점수가 하락. 리포트 코멘트를 비교 분석해 원인 발견: 튜터가 비교용 예문을 직접 지어내다 비문을 생성함 → v3에서 "노트 예문 우선 사용" 조건을 붙여 회복. 대조 측정(v1-rev)이 없었다면 원인 분리가 불가능했음
- **로컬은 통과, CI는 실패** — 유닛 테스트가 로컬에선 통과하는데 GitHub Actions에서만 `No module named 'app'`으로 실패. 원인: 로컬은 `python -m pytest`(현재 폴더가 sys.path에 포함), CI는 `pytest` 직접 실행(미포함)이라는 실행 방식 차이 → `pytest.ini`에 `pythonpath = .` 설정으로 두 방식 모두 동작하게 수정
- **구형 macOS(Intel)에서 Streamlit 설치 실패** — Streamlit 의존성인 `pyarrow`가 이 플랫폼용 wheel이 없어 소스 빌드를 시도하다 실패(Arrow C++ 미설치) → UI를 FastAPI가 직접 서빙하는 HTML/JS 채팅 페이지로 교체. 의존성이 가벼워져 어떤 환경에서도 동작
