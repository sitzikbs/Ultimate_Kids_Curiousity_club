"""Tests for publication service."""

from pathlib import Path
from unittest.mock import MagicMock

import pytest

from models.publication import PublicationMetadata, PublicationState
from services.distribution.publication_service import PublicationService


@pytest.fixture
def mock_r2() -> MagicMock:
    """Create a mock R2 storage client."""
    mock = MagicMock()
    mock.upload_episode.return_value = (
        "https://cdn.example.com/episodes/test_show/ep_001.mp3"
    )
    return mock


@pytest.fixture
def mock_feed_gen() -> MagicMock:
    """Create a mock feed generator."""
    mock = MagicMock()
    mock.generate_feed.return_value = "<?xml version='1.0'?><rss></rss>"
    return mock


@pytest.fixture
def pub_service(
    mock_r2: MagicMock, mock_feed_gen: MagicMock, tmp_path: Path
) -> PublicationService:
    """Create a PublicationService with mocked dependencies."""
    return PublicationService(
        r2_client=mock_r2,
        feed_generator=mock_feed_gen,
        data_dir=tmp_path / "data",
        feeds_dir=tmp_path / "feeds",
    )


class TestPublicationService:
    """Tests for PublicationService."""

    def test_publish_episode_workflow(
        self,
        pub_service: PublicationService,
        mock_r2: MagicMock,
        tmp_path: Path,
    ) -> None:
        """Test the full publish workflow."""
        audio_file = tmp_path / "test.mp3"
        audio_file.write_bytes(b"x" * 1000)

        result = pub_service.publish_episode(
            show_id="test_show",
            episode_id="ep_001",
            audio_path=audio_file,
            title="Test Episode",
            description="A test",
            duration_seconds=120.0,
            episode_number=1,
        )

        assert result.state == PublicationState.PUBLISHED
        assert result.audio_url is not None
        assert result.file_size_bytes == 1000
        assert result.duration_seconds == 120.0
        assert result.published_at is not None
        mock_r2.upload_episode.assert_called_once()

    def test_unpublish_marks_as_unlisted(
        self, pub_service: PublicationService, tmp_path: Path
    ) -> None:
        """Test that unpublish marks episode as UNLISTED."""
        # First, create a published state
        audio_file = tmp_path / "test.mp3"
        audio_file.write_bytes(b"x" * 500)
        pub_service.publish_episode(
            show_id="test_show",
            episode_id="ep_001",
            audio_path=audio_file,
            title="Test",
            description="",
            duration_seconds=60.0,
            episode_number=1,
        )

        result = pub_service.unpublish_episode("test_show", "ep_001")

        assert result.state == PublicationState.UNLISTED

    def test_publish_stores_episode_metadata(
        self,
        pub_service: PublicationService,
        tmp_path: Path,
    ) -> None:
        """Test that publish stores title, description, episode_number."""
        audio_file = tmp_path / "test.mp3"
        audio_file.write_bytes(b"x" * 1000)

        pub_service.publish_episode(
            show_id="test_show",
            episode_id="ep_meta",
            audio_path=audio_file,
            title="My Title",
            description="My Description",
            duration_seconds=90.0,
            episode_number=5,
        )

        loaded = pub_service._load_publication_state("test_show", "ep_meta")
        assert loaded.title == "My Title"
        assert loaded.description == "My Description"
        assert loaded.episode_number == 5

    def test_state_persistence_save_and_load(
        self, pub_service: PublicationService
    ) -> None:
        """Test that publication state can be saved and loaded."""
        metadata = PublicationMetadata(
            state=PublicationState.PUBLISHED,
            audio_url="https://cdn.example.com/test.mp3",
            file_size_bytes=5000,
            duration_seconds=300.0,
            title="Test Title",
            description="Test Description",
            episode_number=3,
        )
        metadata.mark_published()

        pub_service._save_publication_state("test_show", "ep_001", metadata)
        loaded = pub_service._load_publication_state("test_show", "ep_001")

        assert loaded.state == PublicationState.PUBLISHED
        assert loaded.audio_url == "https://cdn.example.com/test.mp3"
        assert loaded.file_size_bytes == 5000
        assert loaded.duration_seconds == 300.0
        assert loaded.title == "Test Title"
        assert loaded.description == "Test Description"
        assert loaded.episode_number == 3

    def test_load_nonexistent_state_returns_unpublished(
        self, pub_service: PublicationService
    ) -> None:
        """Test that loading nonexistent state returns UNPUBLISHED."""
        result = pub_service._load_publication_state("nonexistent", "ep_999")
        assert result.state == PublicationState.UNPUBLISHED

    def test_regenerate_feed_collects_published_episodes(
        self,
        pub_service: PublicationService,
        mock_feed_gen: MagicMock,
        tmp_path: Path,
    ) -> None:
        """Test that regenerate_feed collects only published episodes."""
        # Create two published and one unpublished episode
        for ep_id in ["ep_001", "ep_002"]:
            audio_file = tmp_path / f"{ep_id}.mp3"
            audio_file.write_bytes(b"x" * 500)
            pub_service.publish_episode(
                show_id="test_show",
                episode_id=ep_id,
                audio_path=audio_file,
                title=f"Episode {ep_id}",
                description="",
                duration_seconds=60.0,
                episode_number=1,
            )

        # Unpublish one
        pub_service.unpublish_episode("test_show", "ep_002")

        # Regenerate feed
        pub_service.regenerate_feed("test_show")

        # Check that feed_gen was called with only the published episode
        call_args = mock_feed_gen.generate_feed.call_args
        episodes = call_args[1]["episodes"]
        assert len(episodes) == 1
        assert episodes[0]["id"] == "ep_001"

    def test_unpublished_episodes_excluded_from_feed(
        self,
        pub_service: PublicationService,
        mock_feed_gen: MagicMock,
    ) -> None:
        """Test that unpublished episodes are excluded from the feed."""
        # Save an UNPUBLISHED state
        metadata = PublicationMetadata(state=PublicationState.UNPUBLISHED)
        pub_service._save_publication_state("test_show", "ep_draft", metadata)

        pub_service.regenerate_feed("test_show")

        call_args = mock_feed_gen.generate_feed.call_args
        episodes = call_args[1]["episodes"]
        assert len(episodes) == 0

    def test_get_publication_status(self, pub_service: PublicationService) -> None:
        """Test getting publication status."""
        metadata = PublicationMetadata(
            state=PublicationState.UPLOADED,
            audio_url="https://cdn.example.com/test.mp3",
        )
        pub_service._save_publication_state("test_show", "ep_001", metadata)

        result = pub_service.get_publication_status("test_show", "ep_001")
        assert result.state == PublicationState.UPLOADED
        assert result.audio_url == "https://cdn.example.com/test.mp3"
