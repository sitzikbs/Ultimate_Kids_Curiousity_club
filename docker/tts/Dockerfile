FROM pytorch/pytorch:2.5.1-cuda12.4-cudnn9-runtime

RUN apt-get update && apt-get install -y --no-install-recommends \
    curl ffmpeg git && \
    rm -rf /var/lib/apt/lists/*

RUN pip install --no-cache-dir \
    fastapi \
    uvicorn[standard] \
    python-multipart

# Install VibeVoice from the community fork (PyPI package is a placeholder)
RUN pip install --no-cache-dir \
    git+https://github.com/vibevoice-community/VibeVoice.git

COPY docker/tts/server.py /app/server.py
WORKDIR /app

ENV VIBEVOICE_MODEL=microsoft/VibeVoice-1.5B
ENV VIBEVOICE_CACHE_DIR=/app/models
ENV HF_HOME=/app/models

EXPOSE 8100
HEALTHCHECK --interval=30s --timeout=10s --retries=5 --start-period=300s \
    CMD curl -sf http://localhost:8100/health || exit 1

CMD ["uvicorn", "server:app", "--host", "0.0.0.0", "--port", "8100"]
