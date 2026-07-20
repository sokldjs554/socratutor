FROM python:3.12-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8000

# 컨테이너 시작 시 RAG 인덱스를 구축한 뒤 API 서버 기동
CMD ["sh", "-c", "python -m app.rag && uvicorn app.main:app --host 0.0.0.0 --port 8000"]
