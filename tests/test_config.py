"""Tests for the configuration system."""

from pathlib import Path

import pytest

from src.config import Settings, get_settings, reset_settings


@pytest.fixture(autouse=True)
def reset_singleton():
    """Reset the singleton before each test to ensure clean state."""
    reset_settings()
    yield
    reset_settings()


class TestSettings:
    """Tests for the Settings class."""

    def test_default_values(self, monkeypatch):
        """Test that default values are applied correctly."""
        # Clear any environment variables that might interfere
        for key in [
            "USE_MOCK_SERVICES",
            "OPENAI_API_KEY",
            "ANTHROPIC_API_KEY",
            "ELEVENLABS_API_KEY",
        ]:
            monkeypatch.delenv(key, raising=False)

        settings = Settings()

        # Mock mode defaults
        assert settings.USE_MOCK_SERVICES is True

        # API keys default to None
        assert settings.OPENAI_API_KEY is None
        assert settings.ANTHROPIC_API_KEY is None
        assert settings.ELEVENLABS_API_KEY is None

        # Provider defaults
        assert settings.LLM_PROVIDER == "openai"
        assert settings.TTS_PROVIDER == "elevenlabs"
        assert settings.IMAGE_PROVIDER == "flux"

        # Storage paths
        assert settings.DATA_DIR == Path("data")
        assert settings.SHOWS_DIR == Path("data/shows")
        assert settings.EPISODES_DIR == Path("data/episodes")
        assert settings.ASSETS_DIR == Path("data/assets")
        assert settings.AUDIO_OUTPUT_DIR == Path("data/audio")

    def test_mock_mode_no_api_keys_required(self, monkeypatch):
        """Test that API keys are not required in mock mode."""
        monkeypatch.setenv("USE_MOCK_SERVICES", "true")
        # Clear API key environment variables
        for key in ["OPENAI_API_KEY", "ANTHROPIC_API_KEY", "ELEVENLABS_API_KEY"]:
            monkeypatch.delenv(key, raising=False)

        # Should not raise an error
        settings = Settings()
        assert settings.USE_MOCK_SERVICES is True
        assert settings.OPENAI_API_KEY is None

    def test_real_mode_requires_api_keys(self, monkeypatch):
        """Test that API keys are required when not using mocks."""
        monkeypatch.setenv("USE_MOCK_SERVICES", "false")
        # Clear API key environment variables
        for key in ["OPENAI_API_KEY", "ANTHROPIC_API_KEY", "ELEVENLABS_API_KEY"]:
            monkeypatch.delenv(key, raising=False)

        # Should raise validation error for missing API keys
        with pytest.raises(ValueError, match="is required when USE_MOCK_SERVICES"):
            Settings()

    def test_real_mode_with_api_keys(self, monkeypatch):
        """Test that settings work correctly with API keys provided."""
        monkeypatch.setenv("USE_MOCK_SERVICES", "false")
        monkeypatch.setenv("OPENAI_API_KEY", "sk-test-key")
        monkeypatch.setenv("ANTHROPIC_API_KEY", "sk-ant-test-key")
        monkeypatch.setenv("ELEVENLABS_API_KEY", "test-key")

        settings = Settings()
        assert settings.USE_MOCK_SERVICES is False
        assert settings.OPENAI_API_KEY == "sk-test-key"
        assert settings.ANTHROPIC_API_KEY == "sk-ant-test-key"
        assert settings.ELEVENLABS_API_KEY == "test-key"

    def test_environment_variable_override(self, monkeypatch):
        """Test that environment variables override defaults."""
        monkeypatch.setenv("USE_MOCK_SERVICES", "true")
        monkeypatch.setenv("LLM_PROVIDER", "anthropic")
        monkeypatch.setenv("TTS_PROVIDER", "openai")
        monkeypatch.setenv("IMAGE_PROVIDER", "dalle")
        monkeypatch.setenv("DATA_DIR", "custom_data")

        settings = Settings()
        assert settings.LLM_PROVIDER == "anthropic"
        assert settings.TTS_PROVIDER == "openai"
        assert settings.IMAGE_PROVIDER == "dalle"
        assert settings.DATA_DIR == Path("custom_data")

    def test_path_types(self, monkeypatch):
        """Test that storage paths are Path objects."""
        monkeypatch.setenv("USE_MOCK_SERVICES", "true")

        settings = Settings()
        assert isinstance(settings.DATA_DIR, Path)
        assert isinstance(settings.SHOWS_DIR, Path)
        assert isinstance(settings.EPISODES_DIR, Path)
        assert isinstance(settings.ASSETS_DIR, Path)
        assert isinstance(settings.AUDIO_OUTPUT_DIR, Path)

    def test_custom_paths(self, monkeypatch):
        """Test custom storage paths from environment."""
        monkeypatch.setenv("USE_MOCK_SERVICES", "true")
        monkeypatch.setenv("DATA_DIR", "/custom/data")
        monkeypatch.setenv("SHOWS_DIR", "/custom/shows")
        monkeypatch.setenv("EPISODES_DIR", "/custom/episodes")

        settings = Settings()
        assert settings.DATA_DIR == Path("/custom/data")
        assert settings.SHOWS_DIR == Path("/custom/shows")
        assert settings.EPISODES_DIR == Path("/custom/episodes")


class TestGetSettings:
    """Tests for the get_settings singleton."""

    def test_singleton_behavior(self, monkeypatch):
        """Test that get_settings returns the same instance."""
        monkeypatch.setenv("USE_MOCK_SERVICES", "true")

        settings1 = get_settings()
        settings2 = get_settings()

        # Should be the exact same object
        assert settings1 is settings2

    def test_singleton_preserves_state(self, monkeypatch):
        """Test that singleton preserves settings values."""
        # Clear the singleton before testing
        import src.config

        src.config._settings = None

        monkeypatch.setenv("USE_MOCK_SERVICES", "true")
        monkeypatch.setenv("LLM_PROVIDER", "anthropic")

        settings1 = get_settings()
        assert settings1.LLM_PROVIDER == "anthropic"

        settings2 = get_settings()
        assert settings2.LLM_PROVIDER == "anthropic"
        assert settings1 is settings2


class TestSettingsValidation:
    """Tests for settings validation logic."""

    def test_boolean_string_parsing(self, monkeypatch):
        """Test that boolean strings are parsed correctly."""
        # Test "true"
        monkeypatch.setenv("USE_MOCK_SERVICES", "true")
        settings = Settings()
        assert settings.USE_MOCK_SERVICES is True

        # Reset singleton and test "false"
        reset_settings()

        # Test "false"
        monkeypatch.setenv("USE_MOCK_SERVICES", "false")
        monkeypatch.setenv("OPENAI_API_KEY", "test-key")
        monkeypatch.setenv("ANTHROPIC_API_KEY", "test-key")
        monkeypatch.setenv("ELEVENLABS_API_KEY", "test-key")

        settings = Settings()
        assert settings.USE_MOCK_SERVICES is False

    def test_case_sensitivity(self, monkeypatch):
        """Test that environment variables are case-sensitive."""
        monkeypatch.setenv("USE_MOCK_SERVICES", "true")
        monkeypatch.setenv("llm_provider", "anthropic")  # lowercase

        settings = Settings()
        # Should use default, not the lowercase version
        assert settings.LLM_PROVIDER == "openai"

        # Reset and test with correct case
        reset_settings()

        monkeypatch.setenv("LLM_PROVIDER", "anthropic")
        settings = Settings()
        assert settings.LLM_PROVIDER == "anthropic"
