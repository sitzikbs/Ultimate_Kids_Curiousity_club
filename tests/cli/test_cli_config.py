"""Tests for config CLI commands (Task 7.7.4)."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

from typer.testing import CliRunner

from cli.main import app

# ---------------------------------------------------------------------------
# config show
# ---------------------------------------------------------------------------


class TestConfigShow:
    """Tests for the 'config show' command."""

    def test_show_displays_settings(self, cli_runner: CliRunner):
        """config show prints current settings table."""
        mock_settings = MagicMock()
        mock_settings.USE_MOCK_SERVICES = True
        mock_settings.LLM_PROVIDER = "openai"
        mock_settings.TTS_PROVIDER = "elevenlabs"
        mock_settings.IMAGE_PROVIDER = "flux"
        mock_settings.OPENAI_API_KEY = "sk-abcdefgh12345678"
        mock_settings.ANTHROPIC_API_KEY = ""
        mock_settings.GEMINI_API_KEY = None
        mock_settings.ELEVENLABS_API_KEY = "el-key-short"
        mock_settings.DATA_DIR = "/tmp/data"
        mock_settings.SHOWS_DIR = "/tmp/shows"
        mock_settings.EPISODES_DIR = "/tmp/episodes"
        mock_settings.ASSETS_DIR = "/tmp/assets"
        mock_settings.AUDIO_OUTPUT_DIR = "/tmp/audio"

        with patch("cli.config.get_settings", return_value=mock_settings):
            result = cli_runner.invoke(app, ["config", "show"])

        assert result.exit_code == 0
        assert "USE_MOCK_SERVICES" in result.stdout
        assert "LLM_PROVIDER" in result.stdout
        assert "openai" in result.stdout

    def test_show_masks_api_keys(self, cli_runner: CliRunner):
        """Long API keys are masked; short keys show <set>."""
        mock_settings = MagicMock()
        mock_settings.USE_MOCK_SERVICES = False
        mock_settings.LLM_PROVIDER = "openai"
        mock_settings.TTS_PROVIDER = "mock"
        mock_settings.IMAGE_PROVIDER = "mock"
        mock_settings.OPENAI_API_KEY = "sk-1234567890abcdef"
        mock_settings.ANTHROPIC_API_KEY = "short"
        mock_settings.GEMINI_API_KEY = None
        mock_settings.ELEVENLABS_API_KEY = None
        mock_settings.DATA_DIR = "/tmp/data"
        mock_settings.SHOWS_DIR = "/tmp/shows"
        mock_settings.EPISODES_DIR = "/tmp/episodes"
        mock_settings.ASSETS_DIR = "/tmp/assets"
        mock_settings.AUDIO_OUTPUT_DIR = "/tmp/audio"

        with patch("cli.config.get_settings", return_value=mock_settings):
            result = cli_runner.invoke(app, ["config", "show"])

        assert result.exit_code == 0
        # Full key should NOT appear
        assert "sk-1234567890abcdef" not in result.stdout
        # Masked form: first 4 + ellipsis + last 4
        assert "sk-1" in result.stdout
        assert "cdef" in result.stdout
        # Short key should show as <set>
        assert "<set>" in result.stdout
        # Unset key should show not set
        assert "not set" in result.stdout


# ---------------------------------------------------------------------------
# config validate
# ---------------------------------------------------------------------------


class TestConfigValidate:
    """Tests for the 'config validate' command."""

    def test_validate_mock_mode_ok(self, cli_runner: CliRunner):
        """Mock mode passes validation."""
        mock_settings = MagicMock()
        mock_settings.USE_MOCK_SERVICES = True
        mock_settings.LLM_PROVIDER = "mock"
        mock_settings.TTS_PROVIDER = "mock"
        mock_settings.DATA_DIR = MagicMock()
        mock_settings.DATA_DIR.exists.return_value = True
        mock_settings.SHOWS_DIR = MagicMock()
        mock_settings.SHOWS_DIR.exists.return_value = True

        with patch("cli.config.get_settings", return_value=mock_settings):
            result = cli_runner.invoke(app, ["config", "validate"])

        assert result.exit_code == 0
        assert "valid" in result.stdout.lower()

    def test_validate_live_missing_key(self, cli_runner: CliRunner):
        """Live mode without API key → exit code 1."""
        mock_settings = MagicMock()
        mock_settings.USE_MOCK_SERVICES = False
        mock_settings.LLM_PROVIDER = "openai"
        mock_settings.OPENAI_API_KEY = ""
        mock_settings.TTS_PROVIDER = "mock"
        mock_settings.ELEVENLABS_API_KEY = None
        mock_settings.DATA_DIR = MagicMock()
        mock_settings.DATA_DIR.exists.return_value = True
        mock_settings.SHOWS_DIR = MagicMock()
        mock_settings.SHOWS_DIR.exists.return_value = True

        with patch("cli.config.get_settings", return_value=mock_settings):
            result = cli_runner.invoke(app, ["config", "validate"])

        assert result.exit_code == 1
        assert "OPENAI_API_KEY" in result.stdout

    def test_validate_missing_directory(self, cli_runner: CliRunner):
        """Non-existent DATA_DIR → exit code 1."""
        mock_settings = MagicMock()
        mock_settings.USE_MOCK_SERVICES = True
        mock_settings.LLM_PROVIDER = "mock"
        mock_settings.TTS_PROVIDER = "mock"
        mock_settings.DATA_DIR = MagicMock()
        mock_settings.DATA_DIR.exists.return_value = False
        mock_settings.DATA_DIR.__str__ = lambda s: "/tmp/missing"
        mock_settings.SHOWS_DIR = MagicMock()
        mock_settings.SHOWS_DIR.exists.return_value = True

        with patch("cli.config.get_settings", return_value=mock_settings):
            result = cli_runner.invoke(app, ["config", "validate"])

        assert result.exit_code == 1
        assert "does not exist" in result.stdout


# ---------------------------------------------------------------------------
# config providers
# ---------------------------------------------------------------------------


class TestConfigProviders:
    """Tests for the 'config providers' command."""

    def test_providers_lists_options(self, cli_runner: CliRunner):
        """providers command prints available provider options."""
        mock_settings = MagicMock()
        mock_settings.LLM_PROVIDER = "openai"
        mock_settings.TTS_PROVIDER = "elevenlabs"
        mock_settings.IMAGE_PROVIDER = "flux"

        with patch("cli.config.get_settings", return_value=mock_settings):
            result = cli_runner.invoke(app, ["config", "providers"])

        assert result.exit_code == 0
        assert "LLM Providers" in result.stdout
        assert "TTS Providers" in result.stdout
        assert "openai" in result.stdout
        assert "elevenlabs" in result.stdout
