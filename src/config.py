"""Configuration management for Ultimate Kids Curiosity Club.

This module provides centralized settings management with environment-based
configuration, including mock mode toggle, API keys, and provider preferences.
"""

from pathlib import Path

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings with environment-based configuration.

    Settings are loaded from environment variables and .env files.
    API keys are only required when USE_MOCK_SERVICES is False.
    """

    # Mock toggle for development
    USE_MOCK_SERVICES: bool = True

    # API Keys (optional when using mocks)
    OPENAI_API_KEY: str | None = None
    ANTHROPIC_API_KEY: str | None = None
    ELEVENLABS_API_KEY: str | None = None

    # Provider selection
    LLM_PROVIDER: str = "openai"  # openai, anthropic, mock
    TTS_PROVIDER: str = "elevenlabs"  # elevenlabs, google, openai, mock
    IMAGE_PROVIDER: str = "flux"  # flux, dalle, mock

    # Storage paths
    DATA_DIR: Path = Path("data")
    SHOWS_DIR: Path = Path("data/shows")
    EPISODES_DIR: Path = Path("data/episodes")
    ASSETS_DIR: Path = Path("data/assets")
    AUDIO_OUTPUT_DIR: Path = Path("data/audio")

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
    )

    @field_validator(
        "OPENAI_API_KEY",
        "ANTHROPIC_API_KEY",
        "ELEVENLABS_API_KEY",
        mode="after",
    )
    @classmethod
    def validate_api_keys(cls, v: str | None, info) -> str | None:
        """Validate that API keys are provided when not using mocks.

        Args:
            v: The API key value
            info: Validation context with other field values

        Returns:
            The API key value if valid

        Raises:
            ValueError: If API key is required but not provided
        """
        # Get USE_MOCK_SERVICES from the validation data
        use_mock = info.data.get("USE_MOCK_SERVICES", True)

        # Only require API keys when not using mocks
        if not use_mock and v is None:
            field_name = info.field_name
            raise ValueError(
                f"{field_name} is required when USE_MOCK_SERVICES is False"
            )

        return v


# Singleton instance
_settings: Settings | None = None


def get_settings() -> Settings:
    """Get the singleton Settings instance.

    Creates the settings instance on first call and returns the same
    instance on subsequent calls.

    Returns:
        The singleton Settings instance
    """
    global _settings
    if _settings is None:
        _settings = Settings()
    return _settings
