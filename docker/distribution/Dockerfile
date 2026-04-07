FROM python:3.12-slim
RUN pip install --no-cache-dir fastapi uvicorn[standard] feedgen boto3 mutagen pydantic pydantic-settings
COPY server.py /app/server.py
WORKDIR /app
EXPOSE 8200
CMD ["uvicorn", "server:app", "--host", "0.0.0.0", "--port", "8200"]
