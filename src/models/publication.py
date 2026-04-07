"""Publication state models for podcast distribution."""

from datetime import UTC, datetime
from enum import Enum

from pydantic import BaseModel, Field


class PublicationState(str, Enum):
    """Episode publication state."""

    UNPUBLISHED = "UNPUBLISHED"
    UPLOADING = "UPLOADING"
    UPLOADED = "UPLOADED"
    PUBLISHED = "PUBLISHED"
    UNLISTED = "UNLISTED"


class PublicationMetadata(BaseModel):
    """Track publication state for an episode."""

    state: PublicationState = PublicationState.UNPUBLISHED
    audio_url: str | None = None
    published_at: datetime | None = None
    file_size_bytes: int | None = None
    duration_seconds: float | None = None
    title: str = ""
    description: str = ""
    episode_number: int = 1
    platform_urls: dict[str, str] = Field(default_factory=dict)

    def mark_uploaded(self, audio_url: str, file_size: int, duration: float) -> None:
        """Mark episode as uploaded with audio metadata.

        Args:
            audio_url: CDN URL for the uploaded audio.
            file_size: File size in bytes.
            duration: Duration in seconds.
        """
        self.state = PublicationState.UPLOADED
        self.audio_url = audio_url
        self.file_size_bytes = file_size
        self.duration_seconds = duration

    def mark_published(self) -> None:
        """Mark episode as published in the RSS feed."""
        self.state = PublicationState.PUBLISHED
        self.published_at = datetime.now(UTC)

    def mark_unlisted(self) -> None:
        """Mark episode as unlisted (removed from RSS feed)."""
        self.state = PublicationState.UNLISTED
