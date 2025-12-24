"""Custom exception hierarchy and error handling utilities."""

from datetime import datetime
from functools import wraps
from time import sleep
from typing import Any


class PodcastError(Exception):
    """Base exception class for all podcast-related errors."""

    def __init__(
        self,
        message: str,
        *,
        stage: str | None = None,
        episode_id: str | None = None,
        show_id: str | None = None,
        **kwargs: Any,
    ):
        """Initialize error with context tracking.
        
        Args:
            message: Error message
            stage: Pipeline stage where error occurred
            episode_id: Episode ID if applicable
            show_id: Show ID if applicable
            **kwargs: Additional context
        """
        super().__init__(message)
        self.message = message
        self.stage = stage
        self.episode_id = episode_id
        self.show_id = show_id
        self.timestamp = datetime.now()
        self.context = kwargs

    def __str__(self) -> str:
        """String representation with context."""
        parts = [self.message]
        if self.show_id:
            parts.append(f"Show: {self.show_id}")
        if self.episode_id:
            parts.append(f"Episode: {self.episode_id}")
        if self.stage:
            parts.append(f"Stage: {self.stage}")
        return " | ".join(parts)


class ShowNotFoundError(PodcastError):
    """Raised when a show blueprint cannot be found."""

    pass


class CharacterNotFoundError(PodcastError):
    """Raised when a character cannot be found."""

    pass


class ValidationError(PodcastError):
    """Raised when data validation fails."""

    pass


class APIError(PodcastError):
    """Raised when an external API call fails."""

    def __init__(
        self,
        message: str,
        *,
        provider: str | None = None,
        status_code: int | None = None,
        **kwargs: Any,
    ):
        """Initialize API error with provider context.
        
        Args:
            message: Error message
            provider: API provider name (e.g., "openai", "elevenlabs")
            status_code: HTTP status code if applicable
            **kwargs: Additional context
        """
        super().__init__(message, **kwargs)
        self.provider = provider
        self.status_code = status_code


class AudioProcessingError(PodcastError):
    """Raised when audio processing fails."""

    pass


class ApprovalRequiredError(PodcastError):
    """Raised when human approval is required to continue."""

    pass


class EpisodeNotFoundError(PodcastError):
    """Raised when an episode cannot be found."""

    pass


class StorageError(PodcastError):
    """Raised when file I/O operations fail."""

    pass


def retry_on_failure(
    max_retries: int = 3,
    delay: float = 1.0,
    backoff: float = 2.0,
    exceptions: tuple[type[Exception], ...] = (Exception,),
):
    """Decorator to retry a function on transient failures.
    
    Args:
        max_retries: Maximum number of retry attempts
        delay: Initial delay between retries in seconds
        backoff: Multiplier for delay after each retry
        exceptions: Tuple of exception types to catch and retry
        
    Returns:
        Decorated function
    """

    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            current_delay = delay
            last_exception = None

            for attempt in range(max_retries):
                try:
                    return func(*args, **kwargs)
                except exceptions as e:
                    last_exception = e
                    if attempt < max_retries - 1:
                        sleep(current_delay)
                        current_delay *= backoff
                    continue

            # All retries exhausted
            raise last_exception

        return wrapper

    return decorator
