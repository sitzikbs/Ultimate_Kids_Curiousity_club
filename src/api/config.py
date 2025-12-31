"""API server configuration settings."""

from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class APISettings(BaseSettings):
    """API server configuration settings."""

    # Server configuration
    HOST: str = Field(default="0.0.0.0", description="API server host")
    PORT: int = Field(default=8000, description="API server port")
    RELOAD: bool = Field(default=True, description="Enable auto-reload for development")

    # CORS configuration
    CORS_ORIGINS: list[str] = Field(
        default=["http://localhost:3000", "http://localhost:8000", "*"],
        description="Allowed CORS origins",
    )
    CORS_CREDENTIALS: bool = Field(
        default=True, description="Allow credentials in CORS"
    )
    CORS_METHODS: list[str] = Field(default=["*"], description="Allowed HTTP methods")
    CORS_HEADERS: list[str] = Field(default=["*"], description="Allowed HTTP headers")

    # Static files configuration
    WEBSITE_DIR: Path = Field(
        default=Path("website"), description="Website static files directory"
    )

    # WebSocket configuration
    WS_HEARTBEAT_INTERVAL: int = Field(
        default=30, description="WebSocket heartbeat interval in seconds"
    )

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        env_prefix="API_",
        case_sensitive=True,
    )


# Singleton instance
_api_settings: APISettings | None = None


def get_api_settings() -> APISettings:
    """Get the singleton APISettings instance.

    Returns:
        The singleton APISettings instance
    """
    global _api_settings
    if _api_settings is None:
        _api_settings = APISettings()
    return _api_settings


def reset_api_settings() -> None:
    """Reset the singleton APISettings instance for testing."""
    global _api_settings
    _api_settings = None
