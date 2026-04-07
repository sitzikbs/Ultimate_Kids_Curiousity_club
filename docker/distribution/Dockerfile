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

WORKDIR /app

# Copy distribution server
COPY docker/distribution/server.py /app/server.py

# Copy src modules needed by the server
COPY src/services/distribution/ /app/services/distribution/
COPY src/models/publication.py /app/models/publication.py

# Create __init__.py files for package imports
RUN touch /app/services/__init__.py /app/models/__init__.py

EXPOSE 8200

HEALTHCHECK --interval=15s --timeout=5s --retries=3 \
    CMD curl -sf http://localhost:8200/health || exit 1

CMD ["uvicorn", "server:app", "--host", "0.0.0.0", "--port", "8200"]
