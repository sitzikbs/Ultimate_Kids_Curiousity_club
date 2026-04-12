FROM python:3.12-slim

RUN apt-get update && apt-get install -y --no-install-recommends \
    curl ffmpeg && \
    rm -rf /var/lib/apt/lists/*

WORKDIR /app
COPY pyproject.toml .
COPY src/ ./src/
COPY data/ ./data/
COPY website/ ./website/

RUN pip install --no-cache-dir .

# src/ is the package root per pyproject.toml [tool.setuptools.packages.find]
ENV PYTHONPATH=/app/src

EXPOSE 8000

HEALTHCHECK --interval=15s --timeout=5s --retries=3 \
    CMD curl -sf http://localhost:8000/api/health || exit 1

CMD ["uvicorn", "api.main:app", "--host", "0.0.0.0", "--port", "8000"]
