"""Tests for RSS feed generator."""

import pytest

from services.distribution.rss_generator import PodcastFeedGenerator


@pytest.fixture
def generator() -> PodcastFeedGenerator:
    """Create a PodcastFeedGenerator instance."""
    return PodcastFeedGenerator(
        site_url="https://kidscuriosityclub.com",
        cdn_url="https://cdn.kidscuriosityclub.com",
    )


@pytest.fixture
def sample_episodes() -> list[dict]:
    """Create sample episode data for testing."""
    return [
        {
            "id": "ep_001",
            "title": "The Lever Adventure",
            "description": "Learn about levers!",
            "audio_url": "https://cdn.kidscuriosityclub.com/episodes/test_show/ep_001.mp3",
            "file_size_bytes": 6820000,
            "duration_seconds": 512,
            "publish_date": "2025-12-24T10:00:00Z",
            "episode_number": 1,
        },
        {
            "id": "ep_002",
            "title": "The Light Bulb Revolution",
            "description": "Learn about light bulbs!",
            "audio_url": "https://cdn.kidscuriosityclub.com/episodes/test_show/ep_002.mp3",
            "file_size_bytes": 7250000,
            "duration_seconds": 545,
            "publish_date": "2025-12-31T10:00:00Z",
            "episode_number": 2,
        },
    ]


class TestPodcastFeedGenerator:
    """Tests for PodcastFeedGenerator."""

    def test_generate_feed_with_episodes(
        self, generator: PodcastFeedGenerator, sample_episodes: list[dict]
    ) -> None:
        """Test feed generation with sample episodes."""
        xml = generator.generate_feed(
            show_id="test_show",
            show_title="Test Show",
            show_description="A test show",
            author="Test Author",
            artwork_url="https://example.com/art.jpg",
            episodes=sample_episodes,
        )

        assert "<?xml" in xml
        assert "<rss" in xml
        assert "Test Show" in xml
        assert "A test show" in xml
        assert "The Lever Adventure" in xml
        assert "The Light Bulb Revolution" in xml

    def test_itunes_tags_present(
        self, generator: PodcastFeedGenerator, sample_episodes: list[dict]
    ) -> None:
        """Test that iTunes tags are present in the feed."""
        xml = generator.generate_feed(
            show_id="test_show",
            show_title="Test Show",
            show_description="A test show",
            author="Test Author",
            artwork_url="https://example.com/art.jpg",
            episodes=sample_episodes,
        )

        assert "xmlns:itunes" in xml
        assert "<itunes:author>" in xml
        assert "<itunes:image" in xml
        assert "<itunes:category" in xml

    def test_itunes_explicit_always_no(
        self, generator: PodcastFeedGenerator, sample_episodes: list[dict]
    ) -> None:
        """Test that itunes:explicit is always set to no (not explicit)."""
        xml = generator.generate_feed(
            show_id="test_show",
            show_title="Test Show",
            show_description="A test show",
            author="Test Author",
            artwork_url="https://example.com/art.jpg",
            episodes=sample_episodes,
        )

        assert "<itunes:explicit>no</itunes:explicit>" in xml

    def test_episodes_sorted_newest_first(
        self, generator: PodcastFeedGenerator
    ) -> None:
        """Test that episodes are sorted newest-first in the feed."""
        episodes = [
            {
                "id": "ep_old",
                "title": "Old Episode",
                "description": "",
                "audio_url": "https://cdn.example.com/old.mp3",
                "file_size_bytes": 1000,
                "duration_seconds": 60,
                "publish_date": "2025-01-01T00:00:00Z",
                "episode_number": 1,
            },
            {
                "id": "ep_new",
                "title": "New Episode",
                "description": "",
                "audio_url": "https://cdn.example.com/new.mp3",
                "file_size_bytes": 2000,
                "duration_seconds": 120,
                "publish_date": "2025-12-31T00:00:00Z",
                "episode_number": 2,
            },
        ]

        xml = generator.generate_feed(
            show_id="test",
            show_title="Test",
            show_description="Test",
            author="Test",
            artwork_url="https://example.com/art.jpg",
            episodes=episodes,
        )

        # New episode should appear before old episode
        new_pos = xml.index("New Episode")
        old_pos = xml.index("Old Episode")
        assert new_pos < old_pos

    def test_validation_catches_missing_elements(
        self, generator: PodcastFeedGenerator
    ) -> None:
        """Test that validation detects missing elements."""
        result = generator.validate_feed("<html>not a feed</html>")
        assert result["valid"] is False
        assert len(result["errors"]) > 0
        assert "Missing XML declaration" in result["errors"]
        assert "Missing <rss> root element" in result["errors"]

    def test_validation_passes_for_valid_feed(
        self, generator: PodcastFeedGenerator, sample_episodes: list[dict]
    ) -> None:
        """Test that validation passes for a well-formed feed."""
        xml = generator.generate_feed(
            show_id="test_show",
            show_title="Test Show",
            show_description="A test show",
            author="Test Author",
            artwork_url="https://example.com/art.jpg",
            episodes=sample_episodes,
        )

        result = generator.validate_feed(xml)
        assert result["valid"] is True
        assert result["errors"] == []

    def test_empty_episode_list_produces_valid_feed(
        self, generator: PodcastFeedGenerator
    ) -> None:
        """Test that an empty episode list still produces a valid feed."""
        xml = generator.generate_feed(
            show_id="test_show",
            show_title="Test Show",
            show_description="An empty show",
            author="Test Author",
            artwork_url="https://example.com/art.jpg",
            episodes=[],
        )

        result = generator.validate_feed(xml)
        assert result["valid"] is True
        assert "<?xml" in xml
        assert "<rss" in xml
        assert "Test Show" in xml

    def test_enclosure_present_for_episodes(
        self, generator: PodcastFeedGenerator, sample_episodes: list[dict]
    ) -> None:
        """Test that enclosure elements are present for episodes."""
        xml = generator.generate_feed(
            show_id="test_show",
            show_title="Test Show",
            show_description="A test show",
            author="Test Author",
            artwork_url="https://example.com/art.jpg",
            episodes=sample_episodes,
        )

        assert "<enclosure" in xml
        assert 'type="audio/mpeg"' in xml
