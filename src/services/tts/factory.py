"""Factory for creating TTS provider instances with retry logic."""

import time
from functools import wraps
from pathlib import Path
from typing import Any, Callable

from services.tts.base import BaseTTSProvider
from services.tts.elevenlabs_provider import ElevenLabsProvider
from services.tts.google_provider import GoogleTTSProvider
from services.tts.mock_provider import MockTTSProvider
from services.tts.openai_provider import OpenAITTSProvider


def retry_on_failure(
    max_retries: int = 3, delay_seconds: float = 1.0, backoff_factor: float = 2.0
) -> Callable:
    """Decorator to retry function on transient failures.

    Args:
        max_retries: Maximum number of retry attempts
        delay_seconds: Initial delay between retries in seconds
        backoff_factor: Multiplier for delay after each retry

    Returns:
        Decorated function with retry logic
    """

    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            delay = delay_seconds
            last_exception = None

            for attempt in range(max_retries + 1):
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    last_exception = e
                    if attempt < max_retries:
                        # Check if it's a transient error
                        error_msg = str(e).lower()
                        if any(
                            keyword in error_msg
                            for keyword in [
                                "timeout",
                                "connection",
                                "rate limit",
                                "503",
                                "502",
                                "429",
                            ]
                        ):
                            time.sleep(delay)
                            delay *= backoff_factor
                            continue
                    raise

            # If we get here, all retries failed
            if last_exception:
                raise last_exception
            raise RuntimeError("Retry logic failed without exception")

        return wrapper

    return decorator


class RetryableTTSProvider(BaseTTSProvider):
    """Wrapper that adds retry logic to any TTS provider."""

    def __init__(
        self,
        provider: BaseTTSProvider,
        max_retries: int = 3,
        delay_seconds: float = 1.0,
    ) -> None:
        """Initialize retryable TTS provider.

        Args:
            provider: The underlying TTS provider
            max_retries: Maximum number of retry attempts
            delay_seconds: Initial delay between retries
        """
        self.provider = provider
        self.max_retries = max_retries
        self.delay_seconds = delay_seconds

    @retry_on_failure(max_retries=3, delay_seconds=1.0, backoff_factor=2.0)
    def synthesize(
        self,
        text: str,
        voice_id: str,
        output_path: Path,
        **kwargs: Any,
    ) -> dict[str, Any]:
        """Synthesize with retry logic."""
        return self.provider.synthesize(text, voice_id, output_path, **kwargs)

    def list_voices(self) -> list[dict[str, Any]]:
        """List voices (no retry needed for listing)."""
        return self.provider.list_voices()

    def get_cost(self, characters: int) -> float:
        """Calculate cost (no retry needed for calculation)."""
        return self.provider.get_cost(characters)


class TTSProviderFactory:
    """Factory for creating TTS provider instances."""

    @staticmethod
    def create_provider(
        provider_type: str,
        api_key: str | None = None,
        credentials_path: str | None = None,
        fast_mode: bool = False,
        add_noise: bool = False,
        enable_retry: bool = True,
    ) -> BaseTTSProvider:
        """Create a TTS provider instance.

        Args:
            provider_type: Type of provider ('mock', 'elevenlabs', 'google', 'openai')
            api_key: API key for the provider (required for real providers)
            credentials_path: Path to credentials file (for Google Cloud)
            fast_mode: Enable fast mode for mock provider
            add_noise: Add noise to mock audio
            enable_retry: Enable retry logic for transient failures

        Returns:
            TTS provider instance

        Raises:
            ValueError: If provider_type is invalid or required credentials are missing
        """
        provider: BaseTTSProvider

        if provider_type == "mock":
            provider = MockTTSProvider(fast_mode=fast_mode, add_noise=add_noise)
        elif provider_type == "elevenlabs":
            if not api_key:
                raise ValueError("API key is required for ElevenLabs provider")
            provider = ElevenLabsProvider(api_key=api_key)
        elif provider_type == "google":
            provider = GoogleTTSProvider(credentials_path=credentials_path)
        elif provider_type == "openai":
            if not api_key:
                raise ValueError("API key is required for OpenAI provider")
            provider = OpenAITTSProvider(api_key=api_key)
        else:
            raise ValueError(
                f"Invalid provider type: {provider_type}. "
                f"Must be one of: mock, elevenlabs, google, openai"
            )

        # Wrap with retry logic if enabled and not mock
        if enable_retry and provider_type != "mock":
            provider = RetryableTTSProvider(provider)

        return provider
