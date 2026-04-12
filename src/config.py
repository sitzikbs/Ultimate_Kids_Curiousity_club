"""Configuration management for Ultimate Kids Curiosity Club.

This module provides centralized settings management with environment-based
configuration, including mock mode toggle, API keys, and provider preferences.
"""

from pathlib import Path

from pydantic import model_validator
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
    GEMINI_API_KEY: str | None = None
    ELEVENLABS_API_KEY: str | None = None

    # Gemma / ollama settings
    GEMMA_BASE_URL: str = "http://llm:11434/v1"
    GEMMA_MODEL: str = "gemma4:26b-a4b"

    # Provider selection
    LLM_PROVIDER: str = "openai"  # openai, anthropic, gemini, gemma, mock
    TTS_PROVIDER: str = "elevenlabs"  # elevenlabs, google, openai, vibevoice, mock
    IMAGE_PROVIDER: str = "flux"  # flux, dalle, mock

    # VibeVoice local TTS settings
    VIBEVOICE_BASE_URL: str = "http://tts:8100"
    VIBEVOICE_MODEL: str = "vibevoice-1.5b"

    # Storage paths (resolve relative to project root)
    DATA_DIR: Path = Path(__file__).resolve().parent.parent / "data"
    SHOWS_DIR: Path = Path(__file__).resolve().parent.parent / "data" / "shows"
    EPISODES_DIR: Path = Path(__file__).resolve().parent.parent / "data" / "episodes"
    ASSETS_DIR: Path = Path(__file__).resolve().parent.parent / "data" / "assets"
    AUDIO_OUTPUT_DIR: Path = Path(__file__).resolve().parent.parent / "data" / "audio"

    model_config = SettingsConfigDict(
        env_file=Path(__file__).resolve().parent.parent / ".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore",
    )

    @model_validator(mode="after")
    def validate_api_keys(self) -> "Settings":
        """Validate that API keys are provided for the selected provider.

        Only requires keys for providers that are actually selected —
        e.g. if LLM_PROVIDER=openai, only OPENAI_API_KEY is required.
        Mock providers never need keys.
        """
        if self.USE_MOCK_SERVICES:
            return self

        provider_map = {
            "OPENAI_API_KEY": ("LLM_PROVIDER", "openai"),
            "ANTHROPIC_API_KEY": ("LLM_PROVIDER", "anthropic"),
            "GEMINI_API_KEY": ("LLM_PROVIDER", "gemini"),
            "ELEVENLABS_API_KEY": ("TTS_PROVIDER", "elevenlabs"),
        }

        for key_field, (setting_key, provider_value) in provider_map.items():
            selected = getattr(self, setting_key)
            key_value = getattr(self, key_field)
            if selected == provider_value and key_value is None:
                raise ValueError(
                    f"{key_field} is required when {setting_key}={provider_value}"
                )

        return self


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


def reset_settings() -> None:
    """Reset the singleton Settings instance.

    This is primarily used for testing to ensure each test has a clean state.
    Should not be used in production code.
    """
    global _settings
    _settings = None
