FROM python:3.12-slim

RUN apt-get update && apt-get install -y --no-install-recommends curl && \
    rm -rf /var/lib/apt/lists/*

RUN pip install --no-cache-dir \
    fastapi \
    uvicorn[standard] \
    feedgen \
    boto3 \
    mutagen \
    pydantic \
    pydantic-settings

# Copy distribution service code
COPY server.py /app/server.py

# Also need the src modules for imports
# In production this would be a proper package install

WORKDIR /app
EXPOSE 8200

HEALTHCHECK --interval=15s --timeout=5s --retries=3 \
    CMD curl -sf http://localhost:8200/health || exit 1

CMD ["uvicorn", "server:app", "--host", "0.0.0.0", "--port", "8200"]
