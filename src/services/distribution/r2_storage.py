"""Cloudflare R2 storage client for episode audio files."""

import logging
from pathlib import Path

import boto3
from botocore.exceptions import ClientError

logger = logging.getLogger(__name__)


class R2StorageClient:
    """S3-compatible client for Cloudflare R2.

    Handles uploading, deleting, and checking episode audio files
    in a Cloudflare R2 bucket via the S3-compatible API.
    """

    def __init__(
        self,
        account_id: str,
        access_key_id: str,
        secret_access_key: str,
        bucket_name: str,
        cdn_base_url: str = "https://cdn.kidscuriosityclub.com",
    ) -> None:
        """Initialize R2 storage client.

        Args:
            account_id: Cloudflare account ID.
            access_key_id: R2 access key ID.
            secret_access_key: R2 secret access key.
            bucket_name: R2 bucket name.
            cdn_base_url: Base URL for CDN-served files.
        """
        self.bucket_name = bucket_name
        self.cdn_base_url = cdn_base_url.rstrip("/")
        self._account_id = account_id
        self._access_key_id = access_key_id
        self._secret_access_key = secret_access_key
        self._s3 = None

    @property
    def s3(self):
        """Lazy-init boto3 client (fails only when R2 is actually needed)."""
        if self._s3 is None:
            if not self._account_id:
                raise ValueError(
                    "R2_ACCOUNT_ID not configured — cannot access R2 storage"
                )
            self._s3 = boto3.client(
                "s3",
                endpoint_url=f"https://{self._account_id}.r2.cloudflarestorage.com",
                aws_access_key_id=self._access_key_id,
                aws_secret_access_key=self._secret_access_key,
            )
        return self._s3

    def upload_episode(self, show_id: str, episode_id: str, audio_path: Path) -> str:
        """Upload episode audio and return CDN URL.

        Args:
            show_id: Show identifier.
            episode_id: Episode identifier.
            audio_path: Path to the audio file to upload.

        Returns:
            CDN URL for the uploaded file.
        """
        key = f"episodes/{show_id}/{episode_id}.mp3"
        file_size = audio_path.stat().st_size

        logger.info("Uploading %s (%d bytes) to R2: %s", audio_path, file_size, key)
        self.s3.upload_file(
            str(audio_path),
            self.bucket_name,
            key,
            ExtraArgs={
                "ContentType": "audio/mpeg",
                "CacheControl": "public, max-age=31536000",
            },
        )
        url = f"{self.cdn_base_url}/{key}"
        logger.info("Upload complete: %s", url)
        return url

    def delete_episode(self, show_id: str, episode_id: str) -> None:
        """Delete episode audio from R2.

        Args:
            show_id: Show identifier.
            episode_id: Episode identifier.
        """
        key = f"episodes/{show_id}/{episode_id}.mp3"
        self.s3.delete_object(Bucket=self.bucket_name, Key=key)
        logger.info("Deleted from R2: %s", key)

    def episode_exists(self, show_id: str, episode_id: str) -> bool:
        """Check if episode audio exists in R2.

        Args:
            show_id: Show identifier.
            episode_id: Episode identifier.

        Returns:
            True if the episode audio exists in R2.
        """
        key = f"episodes/{show_id}/{episode_id}.mp3"
        try:
            self.s3.head_object(Bucket=self.bucket_name, Key=key)
            return True
        except ClientError as e:
            if e.response["Error"]["Code"] == "404":
                return False
            raise

    def get_episode_url(self, show_id: str, episode_id: str) -> str:
        """Get CDN URL for an episode.

        Args:
            show_id: Show identifier.
            episode_id: Episode identifier.

        Returns:
            CDN URL for the episode audio.
        """
        return f"{self.cdn_base_url}/episodes/{show_id}/{episode_id}.mp3"
