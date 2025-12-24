"""Tests for configuration settings."""

import pytest

from src.config import Settings, get_settings, reset_settings


class TestSettings:
    """Tests for Settings class."""

    def test_default_settings(self):
        """Test default settings values."""
        settings = Settings()
        assert settings.USE_MOCK_SERVICES is True
        assert settings.LLM_PROVIDER == "openai"
        assert settings.TTS_PROVIDER == "elevenlabs"
        assert settings.IMAGE_PROVIDER == "flux"

    def test_provider_validation(self):
        """Test provider validation."""
        # Valid providers
        Settings(LLM_PROVIDER="openai")
        Settings(LLM_PROVIDER="anthropic")
        Settings(LLM_PROVIDER="mock")

        # Invalid providers
        with pytest.raises(ValueError, match="LLM provider"):
            Settings(LLM_PROVIDER="invalid")

    def test_tts_provider_validation(self):
        """Test TTS provider validation."""
        # Valid providers
        Settings(TTS_PROVIDER="elevenlabs")
        Settings(TTS_PROVIDER="google")
        Settings(TTS_PROVIDER="openai")
        Settings(TTS_PROVIDER="mock")

        # Invalid providers
        with pytest.raises(ValueError, match="TTS provider"):
            Settings(TTS_PROVIDER="invalid")

    def test_image_provider_validation(self):
        """Test image provider validation."""
        # Valid providers
        Settings(IMAGE_PROVIDER="flux")
        Settings(IMAGE_PROVIDER="dalle")
        Settings(IMAGE_PROVIDER="mock")

        # Invalid providers
        with pytest.raises(ValueError, match="Image provider"):
            Settings(IMAGE_PROVIDER="invalid")

    def test_mock_mode_no_api_keys_required(self):
        """Test that API keys are not required in mock mode."""
        settings = Settings(USE_MOCK_SERVICES=True)
        # Should not raise
        settings.validate_api_keys()

    def test_real_mode_requires_api_keys(self):
        """Test that API keys are required when not using mocks."""
        settings = Settings(
            USE_MOCK_SERVICES=False,
            LLM_PROVIDER="openai",
        )

        # Should raise because OPENAI_API_KEY is not set
        with pytest.raises(ValueError, match="OPENAI_API_KEY"):
            settings.validate_api_keys()

    def test_real_mode_with_api_keys(self):
        """Test real mode with API keys provided."""
        settings = Settings(
            USE_MOCK_SERVICES=False,
            LLM_PROVIDER="openai",
            TTS_PROVIDER="elevenlabs",
            IMAGE_PROVIDER="flux",
            OPENAI_API_KEY="test_key",
            ELEVENLABS_API_KEY="test_key",
            FLUX_API_KEY="test_key",
        )

        # Should not raise
        settings.validate_api_keys()

    def test_paths_are_created(self, tmp_path):
        """Test that storage paths are created."""
        data_dir = tmp_path / "test_data"
        settings = Settings(
            DATA_DIR=data_dir,
            SHOWS_DIR=data_dir / "shows",
            EPISODES_DIR=data_dir / "episodes",
            ASSETS_DIR=data_dir / "assets",
        )

        assert settings.DATA_DIR.exists()
        assert settings.SHOWS_DIR.exists()
        assert settings.EPISODES_DIR.exists()
        assert settings.ASSETS_DIR.exists()


class TestGetSettings:
    """Tests for get_settings singleton."""

    def teardown_method(self):
        """Reset settings after each test."""
        reset_settings()

    def test_get_settings_singleton(self):
        """Test that get_settings returns same instance."""
        settings1 = get_settings()
        settings2 = get_settings()
        assert settings1 is settings2

    def test_reset_settings(self):
        """Test resetting settings."""
        settings1 = get_settings()
        reset_settings()
        settings2 = get_settings()
        assert settings1 is not settings2
