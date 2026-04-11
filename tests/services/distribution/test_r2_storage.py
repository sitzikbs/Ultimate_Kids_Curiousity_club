"""Tests for R2 storage client."""

from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
from botocore.exceptions import ClientError

from services.distribution.r2_storage import R2StorageClient


@pytest.fixture
def mock_s3():
    """Create a mock S3 client."""
    with patch("services.distribution.r2_storage.boto3") as mock_boto3:
        mock_client = MagicMock()
        mock_boto3.client.return_value = mock_client
        yield mock_client


@pytest.fixture
def r2_client(mock_s3) -> R2StorageClient:
    """Create an R2StorageClient with a mocked S3 client."""
    client = R2StorageClient(
        account_id="test-account",
        access_key_id="test-key",
        secret_access_key="test-secret",
        bucket_name="test-bucket",
        cdn_base_url="https://cdn.example.com",
    )
    return client


class TestR2StorageClient:
    """Tests for R2StorageClient."""

    def test_upload_returns_correct_cdn_url(
        self, r2_client: R2StorageClient, tmp_path: Path
    ) -> None:
        """Test that upload returns the expected CDN URL."""
        audio_file = tmp_path / "test.mp3"
        audio_file.write_bytes(b"fake audio data")

        url = r2_client.upload_episode("my_show", "ep_001", audio_file)

        assert url == "https://cdn.example.com/episodes/my_show/ep_001.mp3"
        r2_client.s3.upload_file.assert_called_once()

    def test_upload_passes_correct_args(
        self, r2_client: R2StorageClient, tmp_path: Path
    ) -> None:
        """Test that upload passes correct arguments to S3."""
        audio_file = tmp_path / "test.mp3"
        audio_file.write_bytes(b"fake audio data")

        r2_client.upload_episode("my_show", "ep_001", audio_file)

        call_args = r2_client.s3.upload_file.call_args
        assert call_args[0][0] == str(audio_file)
        assert call_args[0][1] == "test-bucket"
        assert call_args[0][2] == "episodes/my_show/ep_001.mp3"
        assert call_args[1]["ExtraArgs"]["ContentType"] == "audio/mpeg"

    def test_delete_episode(self, r2_client: R2StorageClient) -> None:
        """Test deleting an episode from R2."""
        r2_client.delete_episode("my_show", "ep_001")

        r2_client.s3.delete_object.assert_called_once_with(
            Bucket="test-bucket",
            Key="episodes/my_show/ep_001.mp3",
        )

    def test_episode_exists_returns_true(self, r2_client: R2StorageClient) -> None:
        """Test episode_exists returns True when object exists."""
        r2_client.s3.head_object.return_value = {}

        assert r2_client.episode_exists("my_show", "ep_001") is True

    def test_episode_exists_returns_false(self, r2_client: R2StorageClient) -> None:
        """Test episode_exists returns False when object does not exist."""
        r2_client.s3.head_object.side_effect = ClientError(
            {"Error": {"Code": "404", "Message": "Not Found"}},
            "HeadObject",
        )

        assert r2_client.episode_exists("my_show", "ep_001") is False

    def test_episode_exists_reraises_non_404(self, r2_client: R2StorageClient) -> None:
        """Test episode_exists re-raises non-404 ClientErrors."""
        r2_client.s3.head_object.side_effect = ClientError(
            {"Error": {"Code": "403", "Message": "Forbidden"}},
            "HeadObject",
        )

        with pytest.raises(ClientError):
            r2_client.episode_exists("my_show", "ep_001")

    def test_get_episode_url(self, r2_client: R2StorageClient) -> None:
        """Test URL construction."""
        url = r2_client.get_episode_url("my_show", "ep_001")
        assert url == "https://cdn.example.com/episodes/my_show/ep_001.mp3"
