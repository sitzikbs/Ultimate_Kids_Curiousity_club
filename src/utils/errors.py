"""Custom exception hierarchy and error handling utilities.

This module provides a structured exception hierarchy for the podcast generation
system, including context tracking, retry decorators, and structured error logging.
"""

import logging
from collections.abc import Callable
from datetime import UTC, datetime
from functools import wraps
from typing import Any, TypeVar

logger = logging.getLogger(__name__)

F = TypeVar("F", bound=Callable[..., Any])


class PodcastError(Exception):
    """Base exception for all podcast generation errors.

    Captures context information including stage, IDs, and timestamp for debugging.
    """

    def __init__(self, message: str, **context: Any) -> None:
        """Initialize error with message and context.

        Args:
            message: Error description
            **context: Additional context (stage, episode_id, show_id, etc.)
        """
        super().__init__(message)
        self.message = message
        self.context = context
        self.timestamp = datetime.now(UTC)

        # Log error with structured data
        logger.error(
            f"{self.__class__.__name__}: {message}",
            extra={
                "error_class": self.__class__.__name__,
                "timestamp": self.timestamp.isoformat(),
                **context,
            },
        )

    def __str__(self) -> str:
        """String representation with context."""
        context_str = ", ".join(f"{k}={v}" for k, v in self.context.items())
        if context_str:
            return f"{self.message} ({context_str})"
        return self.message


class ShowNotFoundError(PodcastError):
    """Show ID does not exist in the system."""

    pass


class CharacterNotFoundError(PodcastError):
    """Character ID not found in show blueprint."""

    pass


class ValidationError(PodcastError):
    """Data validation failed."""

    pass


class APIError(PodcastError):
    """External API call failed."""

    pass


class AudioProcessingError(PodcastError):
    """Audio synthesis or mixing failed."""

    pass


class ApprovalRequiredError(PodcastError):
    """Content requires human approval before proceeding."""

    pass


class StorageError(PodcastError):
    """File storage operation failed."""

    pass


def retry_on_failure(
    max_attempts: int = 3,
    delay: float = 1.0,
    exceptions: tuple[type[Exception], ...] = (APIError,),
) -> Callable[[F], F]:
    """Retry function on transient failures with exponential backoff.

    Args:
        max_attempts: Maximum number of retry attempts (default: 3)
        delay: Base delay in seconds between retries (default: 1.0)
        exceptions: Tuple of exception types to catch and retry (default: APIError)

    Returns:
        Decorated function with retry logic

    Example:
        @retry_on_failure(max_attempts=3, delay=1.0, exceptions=(APIError,))
        def call_external_api():
            # API call that might fail
            pass
    """

    def decorator(func: F) -> F:
        @wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            import time  # Import here as it's only needed for retry logic

            last_exception: Exception | None = None

            for attempt in range(max_attempts):
                try:
                    return func(*args, **kwargs)
                except exceptions as e:
                    last_exception = e
                    if attempt < max_attempts - 1:
                        # Exponential backoff: delay * (2 ** attempt)
                        wait_time = delay * (2**attempt)
                        logger.warning(
                            f"Attempt {attempt + 1}/{max_attempts} failed for "
                            f"{func.__name__}: {e}. Retrying in {wait_time}s..."
                        )
                        time.sleep(wait_time)
                    else:
                        logger.error(
                            f"All {max_attempts} attempts failed for {func.__name__}"
                        )

            # Re-raise the last exception if all attempts failed
            if last_exception:
                raise last_exception

            # This should never happen, but added for type safety
            raise RuntimeError(
                f"Unexpected state in retry_on_failure for {func.__name__}"
            )

        return wrapper  # type: ignore

    return decorator
