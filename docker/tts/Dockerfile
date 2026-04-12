FROM pytorch/pytorch:2.5.1-cuda12.4-cudnn9-runtime

RUN apt-get update && apt-get install -y --no-install-recommends \
    curl ffmpeg && \
    rm -rf /var/lib/apt/lists/*

RUN pip install --no-cache-dir \
    fastapi \
    uvicorn[standard] \
    python-multipart \
    vibevoice

COPY server.py /app/server.py
WORKDIR /app

ENV VIBEVOICE_MODEL=microsoft/VibeVoice-1.5B
ENV VIBEVOICE_CACHE_DIR=/app/models

EXPOSE 8100
HEALTHCHECK --interval=30s --timeout=10s --retries=5 --start-period=120s \
    CMD curl -sf http://localhost:8100/health || exit 1

CMD ["uvicorn", "server:app", "--host", "0.0.0.0", "--port", "8100"]
