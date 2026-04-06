"""Placeholder TTS service for Docker Compose infrastructure."""

from fastapi import FastAPI

app = FastAPI(title="TTS Service", version="0.1.0")


@app.get("/health")
async def health() -> dict[str, str]:
    """Health check endpoint."""
    return {"status": "ok", "service": "tts", "model": "vibevoice-1.5b"}
