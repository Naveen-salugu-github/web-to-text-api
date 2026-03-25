# FastAPI + Playwright (Chromium) for Railway / any Linux host
FROM python:3.12-slim-bookworm

WORKDIR /app

COPY webpage-ai-parser/requirements.txt webpage-ai-parser/requirements.txt
RUN pip install --no-cache-dir -r webpage-ai-parser/requirements.txt

# System libs + Chromium for Playwright (needed for /parse-page scraping)
RUN playwright install --with-deps chromium

COPY . .

ENV PYTHONUNBUFFERED=1

# Railway sets PORT; default 8000 for local docker run
CMD ["sh", "-c", "uvicorn main:app --host 0.0.0.0 --port ${PORT:-8000}"]
