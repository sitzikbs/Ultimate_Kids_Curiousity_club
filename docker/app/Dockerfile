FROM python:3.12-slim

RUN apt-get update && apt-get install -y --no-install-recommends curl ffmpeg && \
    rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Install dependencies first for layer caching
COPY pyproject.toml .
RUN pip install --no-cache-dir .

# Copy source code
COPY src/ ./src/

ENV PYTHONPATH=/app/src
EXPOSE 8000

HEALTHCHECK --interval=15s --timeout=5s --retries=3 \
    CMD curl -sf http://localhost:8000/api/health || exit 1

CMD ["uvicorn", "api.main:app", "--host", "0.0.0.0", "--port", "8000"]
