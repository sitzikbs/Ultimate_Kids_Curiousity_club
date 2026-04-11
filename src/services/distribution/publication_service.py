"""Publication orchestrator for podcast distribution."""

import json
import logging
from pathlib import Path

from models.publication import PublicationMetadata, PublicationState
from services.distribution.r2_storage import R2StorageClient
from services.distribution.rss_generator import PodcastFeedGenerator

logger = logging.getLogger(__name__)


class PublicationService:
    """Orchestrates episode publication across storage and RSS.

    Manages the full lifecycle of publishing an episode: uploading
    audio to R2, tracking publication state, and regenerating RSS feeds.
    """

    def __init__(
        self,
        r2_client: R2StorageClient,
        feed_generator: PodcastFeedGenerator,
        data_dir: Path,
        feeds_dir: Path,
    ) -> None:
        """Initialize publication service.

        Args:
            r2_client: Cloudflare R2 storage client.
            feed_generator: RSS feed generator.
            data_dir: Root data directory for state persistence.
            feeds_dir: Directory to write RSS feed files.
        """
        self.r2 = r2_client
        self.feed_gen = feed_generator
        self.data_dir = data_dir
        self.feeds_dir = feeds_dir
        self.feeds_dir.mkdir(parents=True, exist_ok=True)

    def publish_episode(
        self,
        show_id: str,
        episode_id: str,
        audio_path: Path,
        title: str,
        description: str,
        duration_seconds: float,
        episode_number: int,
    ) -> PublicationMetadata:
        """Full publication workflow: upload to R2, update RSS.

        Args:
            show_id: Show identifier.
            episode_id: Episode identifier.
            audio_path: Path to the audio file.
            title: Episode title.
            description: Episode description.
            duration_seconds: Audio duration in seconds.
            episode_number: Episode number in the show.

        Returns:
            Publication metadata with final state.
        """
        metadata = PublicationMetadata()

        # Store episode metadata for feed regeneration
        metadata.title = title
        metadata.description = description
        metadata.episode_number = episode_number

        # Step 1: Upload audio to R2
        metadata.state = PublicationState.UPLOADING
        file_size = audio_path.stat().st_size
        audio_url = self.r2.upload_episode(show_id, episode_id, audio_path)
        metadata.mark_uploaded(audio_url, file_size, duration_seconds)

        # Step 2: Save publication state
        self._save_publication_state(show_id, episode_id, metadata)

        # Step 3: Regenerate RSS feed
        self.regenerate_feed(show_id)

        # Step 4: Mark as published
        metadata.mark_published()
        self._save_publication_state(show_id, episode_id, metadata)

        logger.info("Published episode %s/%s: %s", show_id, episode_id, audio_url)
        return metadata

    def unpublish_episode(self, show_id: str, episode_id: str) -> PublicationMetadata:
        """Remove episode from RSS feed (keep audio in R2).

        Args:
            show_id: Show identifier.
            episode_id: Episode identifier.

        Returns:
            Updated publication metadata.
        """
        metadata = self._load_publication_state(show_id, episode_id)
        metadata.mark_unlisted()
        self._save_publication_state(show_id, episode_id, metadata)
        self.regenerate_feed(show_id)
        logger.info("Unpublished episode %s/%s", show_id, episode_id)
        return metadata

    def regenerate_feed(self, show_id: str) -> str:
        """Regenerate RSS feed for a show from current publication state.

        Args:
            show_id: Show identifier.

        Returns:
            Generated RSS XML string.
        """
        # Load show metadata
        show_config = self._load_show_config(show_id)

        # Collect published episodes
        published_episodes = self._get_published_episodes(show_id)

        # Generate feed
        feed_xml = self.feed_gen.generate_feed(
            show_id=show_id,
            show_title=show_config.get("title", show_id),
            show_description=show_config.get("description", ""),
            author="Kids Curiosity Club",
            artwork_url=show_config.get("artwork_url", ""),
            episodes=published_episodes,
        )

        # Write feed file
        feed_path = self.feeds_dir / f"{show_id}.xml"
        feed_path.write_text(feed_xml, encoding="utf-8")
        logger.info("Regenerated RSS feed: %s", feed_path)
        return feed_xml

    def get_publication_status(
        self, show_id: str, episode_id: str
    ) -> PublicationMetadata:
        """Get publication state for an episode.

        Args:
            show_id: Show identifier.
            episode_id: Episode identifier.

        Returns:
            Current publication metadata.
        """
        return self._load_publication_state(show_id, episode_id)

    def _save_publication_state(
        self,
        show_id: str,
        episode_id: str,
        metadata: PublicationMetadata,
    ) -> None:
        """Save publication state to disk.

        Args:
            show_id: Show identifier.
            episode_id: Episode identifier.
            metadata: Publication metadata to persist.
        """
        state_dir = self.data_dir / "publication_state" / show_id
        state_dir.mkdir(parents=True, exist_ok=True)
        state_file = state_dir / f"{episode_id}.json"
        state_file.write_text(metadata.model_dump_json(indent=2), encoding="utf-8")

    def _load_publication_state(
        self, show_id: str, episode_id: str
    ) -> PublicationMetadata:
        """Load publication state from disk.

        Args:
            show_id: Show identifier.
            episode_id: Episode identifier.

        Returns:
            Publication metadata (default UNPUBLISHED if not found).
        """
        state_file = (
            self.data_dir / "publication_state" / show_id / f"{episode_id}.json"
        )
        if state_file.exists():
            return PublicationMetadata.model_validate_json(state_file.read_text())
        return PublicationMetadata()

    def _load_show_config(self, show_id: str) -> dict:
        """Load show config from website JSON data.

        Args:
            show_id: Show identifier.

        Returns:
            Show config dict with title and description.
        """
        website_shows = self.data_dir.parent / "website" / "data" / "shows.json"
        if website_shows.exists():
            shows = json.loads(website_shows.read_text())
            for show in shows.get("shows", []):
                if show.get("id") == show_id:
                    return show
        return {"title": show_id, "description": ""}

    def _get_published_episodes(self, show_id: str) -> list[dict]:
        """Get all published episodes for RSS feed.

        Args:
            show_id: Show identifier.

        Returns:
            List of episode dicts suitable for feed generation.
        """
        state_dir = self.data_dir / "publication_state" / show_id
        if not state_dir.exists():
            return []

        episodes: list[dict] = []
        for state_file in sorted(state_dir.glob("*.json")):
            meta = PublicationMetadata.model_validate_json(state_file.read_text())
            if meta.state == PublicationState.PUBLISHED:
                episode_id = state_file.stem
                episodes.append(
                    {
                        "id": episode_id,
                        "title": meta.title or episode_id,
                        "description": meta.description,
                        "audio_url": meta.audio_url,
                        "file_size_bytes": meta.file_size_bytes,
                        "duration_seconds": meta.duration_seconds,
                        "publish_date": (
                            meta.published_at.isoformat() if meta.published_at else ""
                        ),
                        "episode_number": meta.episode_number,
                    }
                )
        return episodes
