"""Unit tests for error handling utilities."""

import time
from datetime import datetime

import pytest

from utils.errors import (
    APIError,
    ApprovalRequiredError,
    AudioProcessingError,
    CharacterNotFoundError,
    PodcastError,
    ShowNotFoundError,
    StorageError,
    ValidationError,
    retry_on_failure,
)


class TestPodcastError:
    """Tests for base PodcastError class."""

    def test_base_error_creation(self):
        """Test creating base PodcastError with message only."""
        error = PodcastError("Test error")
        assert str(error) == "Test error"
        assert error.message == "Test error"
        assert isinstance(error.timestamp, datetime)
        assert error.context == {}

    def test_error_with_context(self):
        """Test error with context tracking."""
        error = PodcastError(
            "Test error",
            stage="IDEATION",
            episode_id="ep001",
            show_id="test_show",
        )
        assert error.context["stage"] == "IDEATION"
        assert error.context["episode_id"] == "ep001"
        assert error.context["show_id"] == "test_show"
        assert "stage=IDEATION" in str(error)
        assert "episode_id=ep001" in str(error)

    def test_error_timestamp(self):
        """Test that error timestamp is captured."""
        from datetime import UTC

        before = datetime.now(UTC)
        error = PodcastError("Test error")
        after = datetime.now(UTC)

        # Timestamp should be between before and after
        assert before <= error.timestamp <= after


class TestDomainSpecificErrors:
    """Tests for domain-specific exception classes."""

    def test_show_not_found_error(self):
        """Test ShowNotFoundError raises correctly."""
        with pytest.raises(ShowNotFoundError) as exc_info:
            raise ShowNotFoundError("Show not found", show_id="missing_show")

        assert "Show not found" in str(exc_info.value)
        assert exc_info.value.context["show_id"] == "missing_show"

    def test_character_not_found_error(self):
        """Test CharacterNotFoundError raises correctly."""
        with pytest.raises(CharacterNotFoundError) as exc_info:
            raise CharacterNotFoundError(
                "Character not found",
                character_name="Unknown",
                show_id="test_show",
            )

        assert "Character not found" in str(exc_info.value)
        assert exc_info.value.context["character_name"] == "Unknown"

    def test_validation_error(self):
        """Test ValidationError raises correctly."""
        with pytest.raises(ValidationError) as exc_info:
            raise ValidationError("Invalid data", field="title", value="")

        assert "Invalid data" in str(exc_info.value)
        assert exc_info.value.context["field"] == "title"

    def test_api_error(self):
        """Test APIError raises correctly."""
        with pytest.raises(APIError) as exc_info:
            raise APIError(
                "API call failed",
                provider="openai",
                status_code=500,
            )

        assert "API call failed" in str(exc_info.value)
        assert exc_info.value.context["provider"] == "openai"
        assert exc_info.value.context["status_code"] == 500

    def test_audio_processing_error(self):
        """Test AudioProcessingError raises correctly."""
        with pytest.raises(AudioProcessingError) as exc_info:
            raise AudioProcessingError(
                "Audio generation failed",
                stage="synthesis",
                segment_id="seg_001",
            )

        assert "Audio generation failed" in str(exc_info.value)
        assert exc_info.value.context["stage"] == "synthesis"

    def test_approval_required_error(self):
        """Test ApprovalRequiredError raises correctly."""
        with pytest.raises(ApprovalRequiredError) as exc_info:
            raise ApprovalRequiredError(
                "Content needs approval",
                episode_id="ep001",
                reason="sensitive_topic",
            )

        assert "Content needs approval" in str(exc_info.value)
        assert exc_info.value.context["reason"] == "sensitive_topic"

    def test_storage_error(self):
        """Test StorageError raises correctly."""
        with pytest.raises(StorageError) as exc_info:
            raise StorageError(
                "Failed to save file",
                path="/tmp/test.json",
                operation="save",
            )

        assert "Failed to save file" in str(exc_info.value)
        assert exc_info.value.context["path"] == "/tmp/test.json"


class TestRetryDecorator:
    """Tests for retry_on_failure decorator."""

    def test_retry_succeeds_on_first_attempt(self):
        """Test that function succeeds without retry if no error."""
        call_count = 0

        @retry_on_failure(max_attempts=3, delay=0.1, exceptions=(APIError,))
        def successful_function():
            nonlocal call_count
            call_count += 1
            return "success"

        result = successful_function()
        assert result == "success"
        assert call_count == 1

    def test_retry_succeeds_after_failures(self):
        """Test that function retries and eventually succeeds."""
        call_count = 0

        @retry_on_failure(max_attempts=3, delay=0.1, exceptions=(APIError,))
        def eventually_successful():
            nonlocal call_count
            call_count += 1
            if call_count < 3:
                raise APIError("Temporary failure", attempt=call_count)
            return "success"

        result = eventually_successful()
        assert result == "success"
        assert call_count == 3

    def test_retry_exhausts_all_attempts(self):
        """Test that function raises after all retry attempts fail."""
        call_count = 0

        @retry_on_failure(max_attempts=3, delay=0.1, exceptions=(APIError,))
        def always_fails():
            nonlocal call_count
            call_count += 1
            raise APIError("Persistent failure", attempt=call_count)

        with pytest.raises(APIError) as exc_info:
            always_fails()

        assert call_count == 3
        assert "Persistent failure" in str(exc_info.value)

    def test_retry_exponential_backoff(self):
        """Test that retry uses exponential backoff."""
        call_times: list[float] = []

        @retry_on_failure(max_attempts=3, delay=0.1, exceptions=(APIError,))
        def timing_function():
            call_times.append(time.time())
            if len(call_times) < 3:
                raise APIError("Retry test")
            return "success"

        result = timing_function()
        assert result == "success"
        assert len(call_times) == 3

        # Check delays: ~0.1s after first failure, ~0.2s after second
        delay1 = call_times[1] - call_times[0]
        delay2 = call_times[2] - call_times[1]

        # Allow some tolerance for timing
        assert 0.08 < delay1 < 0.15  # ~0.1s
        assert 0.18 < delay2 < 0.25  # ~0.2s

    def test_retry_only_catches_specified_exceptions(self):
        """Test that retry only catches specified exception types."""

        @retry_on_failure(max_attempts=3, delay=0.1, exceptions=(APIError,))
        def raises_wrong_exception():
            raise ValidationError("Wrong exception type")

        # Should raise immediately without retry
        with pytest.raises(ValidationError):
            raises_wrong_exception()

    def test_retry_with_multiple_exception_types(self):
        """Test retry with multiple exception types."""
        call_count = 0

        @retry_on_failure(
            max_attempts=3,
            delay=0.1,
            exceptions=(APIError, StorageError),
        )
        def mixed_failures():
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                raise APIError("API failed")
            elif call_count == 2:
                raise StorageError("Storage failed")
            return "success"

        result = mixed_failures()
        assert result == "success"
        assert call_count == 3

    def test_retry_preserves_function_metadata(self):
        """Test that decorator preserves function name and docstring."""

        @retry_on_failure(max_attempts=3, delay=0.1, exceptions=(APIError,))
        def documented_function():
            """This is a documented function."""
            return "result"

        assert documented_function.__name__ == "documented_function"
        assert documented_function.__doc__ == "This is a documented function."

    def test_retry_with_function_arguments(self):
        """Test that retry works with functions that take arguments."""
        call_count = 0

        @retry_on_failure(max_attempts=3, delay=0.1, exceptions=(APIError,))
        def function_with_args(x: int, y: str = "default") -> str:
            nonlocal call_count
            call_count += 1
            if call_count < 2:
                raise APIError("Temporary failure")
            return f"{x}-{y}"

        result = function_with_args(42, y="test")
        assert result == "42-test"
        assert call_count == 2
