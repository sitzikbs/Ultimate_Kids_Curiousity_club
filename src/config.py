"""Centralized configuration with environment-based settings."""

from pathlib import Path

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings with environment configuration."""

    model_config = SettingsConfigDict(
        env_file=".env", env_file_encoding="utf-8", extra="ignore"
    )

    # Mock toggle
    USE_MOCK_SERVICES: bool = True

    # API Keys (required only when USE_MOCK_SERVICES=False)
    OPENAI_API_KEY: str | None = None
    ANTHROPIC_API_KEY: str | None = None
    ELEVENLABS_API_KEY: str | None = None
    GOOGLE_TTS_API_KEY: str | None = None
    FLUX_API_KEY: str | None = None

    # Provider selection
    LLM_PROVIDER: str = "openai"  # openai, anthropic, mock
    TTS_PROVIDER: str = "elevenlabs"  # elevenlabs, google, openai, mock
    IMAGE_PROVIDER: str = "flux"  # flux, dalle, mock

    # Storage paths
    DATA_DIR: Path = Field(default=Path("data"))
    SHOWS_DIR: Path = Field(default=Path("data/shows"))
    EPISODES_DIR: Path = Field(default=Path("data/episodes"))
    ASSETS_DIR: Path = Field(default=Path("data/assets"))

    @field_validator("DATA_DIR", "SHOWS_DIR", "EPISODES_DIR", "ASSETS_DIR")
    @classmethod
    def ensure_path_exists(cls, v: Path) -> Path:
        """Ensure directory paths exist.

        Args:
            v: Path to validate

        Returns:
            Validated path
        """
        v.mkdir(parents=True, exist_ok=True)
        return v

    @field_validator("LLM_PROVIDER")
    @classmethod
    def validate_llm_provider(cls, v: str) -> str:
        """Validate LLM provider is supported.

        Args:
            v: Provider name

        Returns:
            Validated provider name

        Raises:
            ValueError: If provider is not supported
        """
        valid_providers = ["openai", "anthropic", "mock"]
        if v not in valid_providers:
            raise ValueError(f"LLM provider must be one of {valid_providers}")
        return v

    @field_validator("TTS_PROVIDER")
    @classmethod
    def validate_tts_provider(cls, v: str) -> str:
        """Validate TTS provider is supported.

        Args:
            v: Provider name

        Returns:
            Validated provider name

        Raises:
            ValueError: If provider is not supported
        """
        valid_providers = ["elevenlabs", "google", "openai", "mock"]
        if v not in valid_providers:
            raise ValueError(f"TTS provider must be one of {valid_providers}")
        return v

    @field_validator("IMAGE_PROVIDER")
    @classmethod
    def validate_image_provider(cls, v: str) -> str:
        """Validate image provider is supported.

        Args:
            v: Provider name

        Returns:
            Validated provider name

        Raises:
            ValueError: If provider is not supported
        """
        valid_providers = ["flux", "dalle", "mock"]
        if v not in valid_providers:
            raise ValueError(f"Image provider must be one of {valid_providers}")
        return v

    def validate_api_keys(self) -> None:
        """Validate required API keys are present when not using mocks.

        Raises:
            ValueError: If required API keys are missing
        """
        if self.USE_MOCK_SERVICES:
            return

        errors = []

        # Check LLM provider API key
        if self.LLM_PROVIDER == "openai" and not self.OPENAI_API_KEY:
            errors.append("OPENAI_API_KEY is required when LLM_PROVIDER is 'openai'")
        elif self.LLM_PROVIDER == "anthropic" and not self.ANTHROPIC_API_KEY:
            errors.append(
                "ANTHROPIC_API_KEY is required when LLM_PROVIDER is 'anthropic'"
            )

        # Check TTS provider API key
        if self.TTS_PROVIDER == "elevenlabs" and not self.ELEVENLABS_API_KEY:
            errors.append(
                "ELEVENLABS_API_KEY is required when TTS_PROVIDER is 'elevenlabs'"
            )
        elif self.TTS_PROVIDER == "google" and not self.GOOGLE_TTS_API_KEY:
            errors.append(
                "GOOGLE_TTS_API_KEY is required when TTS_PROVIDER is 'google'"
            )
        elif self.TTS_PROVIDER == "openai" and not self.OPENAI_API_KEY:
            errors.append("OPENAI_API_KEY is required when TTS_PROVIDER is 'openai'")

        # Check image provider API key
        if self.IMAGE_PROVIDER == "flux" and not self.FLUX_API_KEY:
            errors.append("FLUX_API_KEY is required when IMAGE_PROVIDER is 'flux'")
        elif self.IMAGE_PROVIDER == "dalle" and not self.OPENAI_API_KEY:
            errors.append("OPENAI_API_KEY is required when IMAGE_PROVIDER is 'dalle'")

        if errors:
            raise ValueError("Missing required API keys:\n  " + "\n  ".join(errors))


# Singleton instance
_settings: Settings | None = None


def get_settings() -> Settings:
    """Get the singleton settings instance.

    Returns:
        Settings instance
    """
    global _settings
    if _settings is None:
        _settings = Settings()
    return _settings


def reset_settings() -> None:
    """Reset the singleton settings instance (useful for testing)."""
    global _settings
    _settings = None
