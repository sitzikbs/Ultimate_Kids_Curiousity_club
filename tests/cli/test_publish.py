"""Tests for publish CLI commands."""

from unittest.mock import MagicMock, patch

from typer.testing import CliRunner

from cli.main import app

runner = CliRunner()


class TestPublishCli:
    """Tests for the publish CLI commands."""

    def test_publish_help(self) -> None:
        """Test that publish --help works."""
        result = runner.invoke(app, ["publish", "--help"])
        assert result.exit_code == 0
        assert "publishing" in result.output.lower()

    def test_publish_episode_missing_audio(self, tmp_path) -> None:
        """Test publish episode with non-existent audio file."""
        result = runner.invoke(
            app,
            [
                "publish",
                "episode",
                "ep_001",
                "--show",
                "test_show",
                "--audio",
                str(tmp_path / "nonexistent.mp3"),
            ],
        )
        assert result.exit_code == 1

    @patch("cli.publish.httpx")
    def test_publish_episode_success(self, mock_httpx: MagicMock, tmp_path) -> None:
        """Test successful episode publication."""
        audio_file = tmp_path / "test.mp3"
        audio_file.write_bytes(b"fake audio")

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "state": "PUBLISHED",
            "audio_url": "https://cdn.example.com/test.mp3",
        }
        mock_httpx.post.return_value = mock_response

        result = runner.invoke(
            app,
            [
                "publish",
                "episode",
                "ep_001",
                "--show",
                "test_show",
                "--audio",
                str(audio_file),
            ],
        )
        assert result.exit_code == 0
        assert "Published" in result.output

    @patch("cli.publish.httpx")
    def test_unpublish_episode(self, mock_httpx: MagicMock) -> None:
        """Test unpublish command."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_httpx.post.return_value = mock_response

        result = runner.invoke(
            app,
            [
                "publish",
                "unpublish",
                "ep_001",
                "--show",
                "test_show",
            ],
        )
        assert result.exit_code == 0

    @patch("cli.publish.httpx")
    def test_feed_validate(self, mock_httpx: MagicMock) -> None:
        """Test feed validation command."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"valid": True, "errors": []}
        mock_httpx.post.return_value = mock_response

        result = runner.invoke(
            app,
            ["publish", "feed", "test_show", "--validate"],
        )
        assert result.exit_code == 0

    def test_status_command(self) -> None:
        """Test status command output."""
        result = runner.invoke(app, ["publish", "status", "test_show"])
        assert result.exit_code == 0
        assert "test_show" in result.output
