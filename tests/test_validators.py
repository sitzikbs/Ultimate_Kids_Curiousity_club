"""Tests for validation utilities."""

from pathlib import Path

import pytest

from src.utils.validators import (
    VocabularyLevel,
    validate_age,
    validate_duration,
    validate_episode_id,
    validate_image_path,
    validate_show_id,
    validate_url,
)


class TestVocabularyLevel:
    """Tests for VocabularyLevel enum."""

    def test_vocabulary_levels(self):
        """Test vocabulary level enum values."""
        assert VocabularyLevel.SIMPLE == "SIMPLE"
        assert VocabularyLevel.INTERMEDIATE == "INTERMEDIATE"
        assert VocabularyLevel.ADVANCED == "ADVANCED"


class TestValidateDuration:
    """Tests for duration validation."""

    def test_valid_durations(self):
        """Test valid duration values."""
        assert validate_duration(5) == 5
        assert validate_duration(10) == 10
        assert validate_duration(20) == 20

    def test_invalid_durations(self):
        """Test invalid duration values."""
        with pytest.raises(ValueError, match="5 and 20"):
            validate_duration(4)

        with pytest.raises(ValueError, match="5 and 20"):
            validate_duration(21)

        with pytest.raises(ValueError, match="5 and 20"):
            validate_duration(0)


class TestValidateAge:
    """Tests for age validation."""

    def test_valid_ages(self):
        """Test valid age values."""
        assert validate_age(5) == 5
        assert validate_age(8) == 8
        assert validate_age(12) == 12

    def test_invalid_ages(self):
        """Test invalid age values."""
        with pytest.raises(ValueError, match="5 and 12"):
            validate_age(4)

        with pytest.raises(ValueError, match="5 and 12"):
            validate_age(13)


class TestValidateShowId:
    """Tests for show ID validation."""

    def test_valid_show_ids(self):
        """Test valid show ID formats."""
        assert validate_show_id("olivers_workshop") == "olivers_workshop"
        assert validate_show_id("test_show") == "test_show"
        assert validate_show_id("show123") == "show123"

    def test_invalid_show_ids(self):
        """Test invalid show ID formats."""
        with pytest.raises(ValueError, match="empty"):
            validate_show_id("")

        with pytest.raises(ValueError, match="lowercase"):
            validate_show_id("InvalidShow")

        with pytest.raises(ValueError, match="letters, numbers, and underscores"):
            validate_show_id("invalid-show")

        with pytest.raises(ValueError, match="letters, numbers, and underscores"):
            validate_show_id("invalid@show")


class TestValidateEpisodeId:
    """Tests for episode ID validation."""

    def test_valid_episode_ids(self):
        """Test valid episode ID formats."""
        assert validate_episode_id("ep_001") == "ep_001"
        assert validate_episode_id("test-episode") == "test-episode"
        assert validate_episode_id("ep_001_magnets") == "ep_001_magnets"

    def test_invalid_episode_ids(self):
        """Test invalid episode ID formats."""
        with pytest.raises(ValueError, match="empty"):
            validate_episode_id("")

        with pytest.raises(ValueError, match="Episode ID"):
            validate_episode_id("invalid@episode")


class TestValidateImagePath:
    """Tests for image path validation."""

    def test_valid_image_extensions(self, tmp_path):
        """Test valid image extensions."""
        # Test with non-existent paths (allowed for future assets)
        assert validate_image_path("path/to/image.png") == Path("path/to/image.png")
        assert validate_image_path("path/to/image.jpg") == Path("path/to/image.jpg")
        assert validate_image_path("path/to/image.jpeg") == Path("path/to/image.jpeg")
        assert validate_image_path("path/to/image.webp") == Path("path/to/image.webp")

    def test_invalid_image_extensions(self):
        """Test invalid image extensions."""
        with pytest.raises(ValueError, match="Invalid image extension"):
            validate_image_path("path/to/image.txt")

        with pytest.raises(ValueError, match="Invalid image extension"):
            validate_image_path("path/to/image.pdf")

    def test_none_image_path(self):
        """Test None image path is allowed."""
        assert validate_image_path(None) is None


class TestValidateUrl:
    """Tests for URL validation."""

    def test_valid_urls(self):
        """Test valid URL formats."""
        assert validate_url("http://example.com") == "http://example.com"
        assert validate_url("https://example.com") == "https://example.com"
        assert (
            validate_url("https://example.com/path/to/image.png")
            == "https://example.com/path/to/image.png"
        )

    def test_invalid_urls(self):
        """Test invalid URL formats."""
        with pytest.raises(ValueError, match="http"):
            validate_url("ftp://example.com")

        with pytest.raises(ValueError, match="http"):
            validate_url("example.com")

    def test_none_url(self):
        """Test None URL is allowed."""
        assert validate_url(None) is None
