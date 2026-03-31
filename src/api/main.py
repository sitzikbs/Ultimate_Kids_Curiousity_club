"""FastAPI application for Ultimate Kids Curiosity Club dashboard."""

from datetime import UTC, datetime
from pathlib import Path

from fastapi import FastAPI, WebSocket
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from api.config import get_api_settings
from api.models import HealthResponse
from api.routes import episodes, shows, uploads
from api.websocket import websocket_endpoint

# Get API settings
settings = get_api_settings()

# Create FastAPI application
app = FastAPI(
    title="Ultimate Kids Curiosity Club API",
    description="REST API and WebSocket server for the dashboard backend",
    version="0.1.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=settings.CORS_CREDENTIALS,
    allow_methods=settings.CORS_METHODS,
    allow_headers=settings.CORS_HEADERS,
)

# Include routers
app.include_router(shows.router)
app.include_router(episodes.router)
app.include_router(uploads.router)


@app.get("/health", response_model=HealthResponse, tags=["health"])
async def health_check() -> HealthResponse:
    """Health check endpoint.

    Returns:
        Service status and timestamp
    """
    return HealthResponse(status="healthy", timestamp=datetime.now(UTC))


@app.websocket("/ws")
async def websocket_route(websocket: WebSocket) -> None:
    """WebSocket endpoint for real-time updates.

    Args:
        websocket: WebSocket connection
    """
    await websocket_endpoint(websocket)


# Mount data directory for serving show images
from config import get_settings as _get_app_settings

_app_settings = _get_app_settings()
data_path = Path(_app_settings.DATA_DIR)
if data_path.exists():
    app.mount("/data", StaticFiles(directory=str(data_path)), name="data")

# Mount static files (website directory) — must be last (catch-all)
website_path = Path(settings.WEBSITE_DIR)
if website_path.exists():
    app.mount("/", StaticFiles(directory=str(website_path), html=True), name="static")


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "api.main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.RELOAD,
    )
