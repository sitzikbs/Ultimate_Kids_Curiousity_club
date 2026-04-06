"""Placeholder distribution service for Docker Compose infrastructure."""

from fastapi import FastAPI

app = FastAPI(title="Distribution Service", version="0.1.0")


@app.get("/health")
async def health() -> dict[str, str]:
    """Health check endpoint."""
    return {"status": "ok", "service": "distribution"}
