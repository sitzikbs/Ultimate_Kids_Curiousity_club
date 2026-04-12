"""End-to-end integration tests for the containerized pipeline.

These tests verify that all services work together correctly.
They require the Docker services to be running and are skipped in CI.
"""

import json
from pathlib import Path
from unittest.mock import MagicMock

import pytest

from models.episode import Episode, PipelineStage
from models.publication import PublicationMetadata, PublicationState


def _create_show_config(tmp_path: Path, show_id: str) -> None:
    """Create a minimal website shows.json so feed generation works.

    The PublicationService._load_show_config looks for
    data_dir.parent / "website" / "data" / "shows.json".
    When data_dir = tmp_path / "data", parent is tmp_path.
    """
    website_dir = tmp_path / "website" / "data"
    website_dir.mkdir(parents=True, exist_ok=True)
    shows_data = {
        "shows": [
            {
                "id": show_id,
                "title": f"Test Show: {show_id}",
                "description": "A test podcast show for integration testing.",
                "artwork_url": "https://example.com/artwork.png",
            }
        ]
    }
    (website_dir / "shows.json").write_text(json.dumps(shows_data), encoding="utf-8")


@pytest.fixture
def sample_episode() -> Episode:
    """Create a sample completed episode."""
    return Episode(
        episode_id="test_ep_001",
        show_id="olivers_workshop",
        topic="How do magnets work?",
        title="The Magnet Mystery",
        current_stage=PipelineStage.COMPLETE,
        audio_path="/data/episodes/olivers_workshop/test_ep_001/final_audio.mp3",
    )


class TestPipelineIntegration:
    """Test pipeline stages work together."""

    def test_episode_creation(self, sample_episode: Episode) -> None:
        """Test that an episode can be created with all required fields."""
        assert sample_episode.episode_id == "test_ep_001"
        assert sample_episode.show_id == "olivers_workshop"
        assert sample_episode.current_stage == PipelineStage.COMPLETE

    def test_publication_state_transitions(self) -> None:
        """Test publication state machine transitions."""
        meta = PublicationMetadata()
        assert meta.state == PublicationState.UNPUBLISHED

        meta.state = PublicationState.UPLOADING
        assert meta.state == PublicationState.UPLOADING

        meta.mark_uploaded(
            audio_url="https://cdn.example.com/ep001.mp3",
            file_size=8388608,
            duration=512.0,
        )
        assert meta.state == PublicationState.UPLOADED
        assert meta.audio_url == "https://cdn.example.com/ep001.mp3"
        assert meta.file_size_bytes == 8388608

        meta.mark_published()
        assert meta.state == PublicationState.PUBLISHED
        assert meta.published_at is not None

        meta.mark_unlisted()
        assert meta.state == PublicationState.UNLISTED

    def test_full_publication_flow(
        self, sample_episode: Episode, tmp_path: Path
    ) -> None:
        """Test full publish flow with mocked R2."""
        from services.distribution.publication_service import (
            PublicationService,
        )
        from services.distribution.rss_generator import PodcastFeedGenerator

        # Create mock R2 client
        mock_r2 = MagicMock()
        mock_r2.upload_episode.return_value = (
            "https://cdn.example.com/episodes/olivers_workshop/test_ep_001.mp3"
        )

        feed_gen = PodcastFeedGenerator()
        feeds_dir = tmp_path / "feeds"
        data_dir = tmp_path / "data"

        # Create show config so feed generation has required metadata
        _create_show_config(tmp_path, "olivers_workshop")

        service = PublicationService(
            r2_client=mock_r2,
            feed_generator=feed_gen,
            data_dir=data_dir,
            feeds_dir=feeds_dir,
        )

        # Create a fake audio file
        audio_file = tmp_path / "test_audio.mp3"
        audio_file.write_bytes(b"\xff\xfb\x90\x00" * 1000)

        # Publish
        metadata = service.publish_episode(
            show_id="olivers_workshop",
            episode_id="test_ep_001",
            audio_path=audio_file,
            title="The Magnet Mystery",
            description="Learn about magnets!",
            duration_seconds=512.0,
            episode_number=1,
        )

        assert metadata.state == PublicationState.PUBLISHED
        assert metadata.audio_url is not None
        mock_r2.upload_episode.assert_called_once()

        # Verify RSS feed was generated
        feed_path = feeds_dir / "olivers_workshop.xml"
        assert feed_path.exists()
        feed_content = feed_path.read_text()
        assert "<?xml" in feed_content
        assert "rss" in feed_content

    def test_unpublish_removes_from_feed(self, tmp_path: Path) -> None:
        """Test that unpublishing removes episode from RSS feed."""
        from services.distribution.publication_service import (
            PublicationService,
        )
        from services.distribution.rss_generator import PodcastFeedGenerator

        mock_r2 = MagicMock()
        mock_r2.upload_episode.return_value = "https://cdn.example.com/ep001.mp3"

        # Create show config so feed generation has required metadata
        _create_show_config(tmp_path, "test_show")

        service = PublicationService(
            r2_client=mock_r2,
            feed_generator=PodcastFeedGenerator(),
            data_dir=tmp_path / "data",
            feeds_dir=tmp_path / "feeds",
        )

        # Publish first
        audio_file = tmp_path / "audio.mp3"
        audio_file.write_bytes(b"\xff\xfb\x90\x00" * 100)
        service.publish_episode(
            show_id="test_show",
            episode_id="ep001",
            audio_path=audio_file,
            title="Test Episode",
            description="Test",
            duration_seconds=60.0,
            episode_number=1,
        )

        # Unpublish
        metadata = service.unpublish_episode("test_show", "ep001")
        assert metadata.state == PublicationState.UNLISTED

        # Verify episode not in regenerated feed
        feed_path = tmp_path / "feeds" / "test_show.xml"
        if feed_path.exists():
            feed_content = feed_path.read_text()
            assert "Test Episode" not in feed_content


class TestServiceHealth:
    """Test service health check patterns."""

    def test_app_health_endpoint(self):
        """Verify /api/health returns expected format."""
        import importlib
        import sys
        from pathlib import Path

        from fastapi.testclient import TestClient

        # The tests/api/ package shadows src/api/ when tests/ is on sys.path.
        # Temporarily remove tests/ so we can import the real api.main module.
        src_dir = str(Path(__file__).resolve().parents[2] / "src")
        tests_dir = str(Path(__file__).resolve().parents[2] / "tests")
        old_path = sys.path[:]
        try:
            sys.path = [p for p in sys.path if p != tests_dir]
            if src_dir not in sys.path:
                sys.path.insert(0, src_dir)
            # Clear cached api package from tests/api if present
            for key in list(sys.modules):
                if key == "api" or key.startswith("api."):
                    del sys.modules[key]
            app_module = importlib.import_module("api.main")
            app = app_module.app
        finally:
            sys.path = old_path

        client = TestClient(app)
        response = client.get("/api/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ok"
        assert data["service"] == "app"


@pytest.mark.real_api
class TestLiveServices:
    """Tests that require running Docker services.

    Run with: pytest -m real_api tests/integration/
    Requires: docker compose up (or make up-dev)
    """

    def test_distribution_health(self) -> None:
        """Test distribution service health endpoint."""
        import httpx

        response = httpx.get("http://localhost:8200/health", timeout=5.0)
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ok"
        assert data["service"] == "distribution"

    def test_app_health(self) -> None:
        """Test app service health endpoint."""
        import httpx

        response = httpx.get("http://localhost:8000/api/health", timeout=5.0)
        assert response.status_code == 200

    def test_rss_feed_endpoint(self) -> None:
        """Test RSS feed generation via distribution service."""
        import httpx

        response = httpx.post(
            "http://localhost:8200/feeds/olivers_workshop/regenerate",
            timeout=10.0,
        )
        assert response.status_code == 200
        data = response.json()
        assert data["regenerated"] is True
