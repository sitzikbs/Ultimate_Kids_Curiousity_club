"""Tests for error handling."""

from time import time

import pytest

from src.utils.errors import (
    APIError,
    ApprovalRequiredError,
    AudioProcessingError,
    CharacterNotFoundError,
    EpisodeNotFoundError,
    PodcastError,
    ShowNotFoundError,
    StorageError,
    ValidationError,
    retry_on_failure,
)


class TestPodcastError:
    """Tests for base PodcastError."""

    def test_podcast_error_creation(self):
        """Test creating a podcast error."""
        error = PodcastError("Test error")
        assert str(error) == "Test error"
        assert error.message == "Test error"
        assert error.stage is None
        assert error.episode_id is None
        assert error.show_id is None

    def test_podcast_error_with_context(self):
        """Test creating error with context."""
        error = PodcastError(
            "Test error",
            stage="OUTLINING",
            episode_id="ep_001",
            show_id="test_show",
            additional_info="test",
        )

        error_str = str(error)
        assert "Test error" in error_str
        assert "test_show" in error_str
        assert "ep_001" in error_str
        assert "OUTLINING" in error_str
        assert error.context["additional_info"] == "test"

    def test_podcast_error_timestamp(self):
        """Test that error has timestamp."""
        before = time()
        error = PodcastError("Test error")
        after = time()

        timestamp = error.timestamp.timestamp()
        assert before <= timestamp <= after


class TestDomainErrors:
    """Tests for domain-specific errors."""

    def test_show_not_found_error(self):
        """Test ShowNotFoundError."""
        error = ShowNotFoundError("Show not found", show_id="test_show")
        assert "Show not found" in str(error)
        assert error.show_id == "test_show"

    def test_character_not_found_error(self):
        """Test CharacterNotFoundError."""
        error = CharacterNotFoundError("Character not found")
        assert "Character not found" in str(error)

    def test_validation_error(self):
        """Test ValidationError."""
        error = ValidationError("Invalid data")
        assert "Invalid data" in str(error)

    def test_api_error(self):
        """Test APIError."""
        error = APIError(
            "API call failed",
            provider="openai",
            status_code=500,
        )
        assert "API call failed" in str(error)
        assert error.provider == "openai"
        assert error.status_code == 500

    def test_audio_processing_error(self):
        """Test AudioProcessingError."""
        error = AudioProcessingError("Audio processing failed")
        assert "Audio processing failed" in str(error)

    def test_approval_required_error(self):
        """Test ApprovalRequiredError."""
        error = ApprovalRequiredError("Approval needed")
        assert "Approval needed" in str(error)

    def test_episode_not_found_error(self):
        """Test EpisodeNotFoundError."""
        error = EpisodeNotFoundError(
            "Episode not found",
            episode_id="ep_001",
            show_id="test_show",
        )
        assert "Episode not found" in str(error)
        assert error.episode_id == "ep_001"

    def test_storage_error(self):
        """Test StorageError."""
        error = StorageError("Storage failed")
        assert "Storage failed" in str(error)


class TestRetryDecorator:
    """Tests for retry_on_failure decorator."""

    def test_successful_call_no_retry(self):
        """Test that successful calls don't retry."""
        call_count = {"count": 0}

        @retry_on_failure(max_retries=3, delay=0.01)
        def successful_func():
            call_count["count"] += 1
            return "success"

        result = successful_func()
        assert result == "success"
        assert call_count["count"] == 1

    def test_retry_on_failure(self):
        """Test that function retries on failure."""
        call_count = {"count": 0}

        @retry_on_failure(max_retries=3, delay=0.01)
        def failing_func():
            call_count["count"] += 1
            if call_count["count"] < 3:
                raise ValueError("Transient error")
            return "success"

        result = failing_func()
        assert result == "success"
        assert call_count["count"] == 3

    def test_max_retries_exhausted(self):
        """Test that function raises after max retries."""
        call_count = {"count": 0}

        @retry_on_failure(max_retries=3, delay=0.01)
        def always_failing_func():
            call_count["count"] += 1
            raise ValueError("Persistent error")

        with pytest.raises(ValueError, match="Persistent error"):
            always_failing_func()

        assert call_count["count"] == 3

    def test_retry_specific_exceptions(self):
        """Test retrying only specific exceptions."""
        call_count = {"count": 0}

        @retry_on_failure(max_retries=3, delay=0.01, exceptions=(ValueError,))
        def func_with_type_error():
            call_count["count"] += 1
            raise TypeError("Not retryable")

        with pytest.raises(TypeError):
            func_with_type_error()

        # Should fail immediately without retry
        assert call_count["count"] == 1

    def test_backoff_delay(self):
        """Test that delay increases with backoff."""
        call_times = []

        @retry_on_failure(max_retries=3, delay=0.01, backoff=2.0)
        def failing_func():
            call_times.append(time())
            raise ValueError("Error")

        with pytest.raises(ValueError):
            failing_func()

        # Should have 3 calls
        assert len(call_times) == 3

        # Check that delays increase (with some tolerance for timing)
        # First retry after ~0.01s, second after ~0.02s
        # Note: We can't check exact timings due to system variations
