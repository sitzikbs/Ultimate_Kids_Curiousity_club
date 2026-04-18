"""Anthropic LLM provider implementation."""

from collections.abc import AsyncGenerator
from typing import Any

from tenacity import (
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential,
)

from services.llm.base import BaseLLMProvider

DEFAULT_MODEL = "claude-haiku-4-5-20251001"


def _build_system_param(system: str | None) -> list[dict[str, Any]] | None:
    """Wrap a system prompt for ephemeral prompt caching."""
    if not system:
        return None
    return [
        {
            "type": "text",
            "text": system,
            "cache_control": {"type": "ephemeral"},
        }
    ]


class AnthropicProvider(BaseLLMProvider):
    """Anthropic Claude LLM provider with retry logic."""

    def __init__(self, api_key: str, model: str = DEFAULT_MODEL) -> None:
        """Initialize Anthropic provider.

        Args:
            api_key: Anthropic API key
            model: Model to use for generation (defaults to Claude Haiku 4.5)
        """
        try:
            from anthropic import AsyncAnthropic
        except ImportError as e:
            raise ImportError(
                "anthropic package not installed. "
                "Install with: pip install anthropic>=0.18.0"
            ) from e

        self.client = AsyncAnthropic(api_key=api_key)
        self.model = model

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        retry=retry_if_exception_type(Exception),
    )
    async def generate(
        self,
        prompt: str,
        max_tokens: int = 2000,
        temperature: float = 0.7,
        system: str | None = None,
        **kwargs: Any,
    ) -> str:
        """Generate text from prompt with retry logic.

        Args:
            prompt: The user prompt for the LLM
            max_tokens: Maximum number of tokens to generate
            temperature: Sampling temperature
            system: Optional system prompt. When provided, it is sent with
                ephemeral ``cache_control`` so repeated calls with the same
                system prompt (e.g. show/protagonist/world) can hit the
                prompt cache.
            **kwargs: Additional Anthropic parameters

        Returns:
            Generated text response

        Raises:
            Exception: If generation fails after retries
        """
        create_kwargs: dict[str, Any] = {
            "model": self.model,
            "max_tokens": max_tokens,
            "temperature": temperature,
            "messages": [{"role": "user", "content": prompt}],
            **kwargs,
        }
        system_param = _build_system_param(system)
        if system_param is not None:
            create_kwargs["system"] = system_param

        response = await self.client.messages.create(**create_kwargs)

        # Extract text from response
        if response.content and len(response.content) > 0:
            return response.content[0].text
        raise ValueError("Anthropic returned empty response")

    async def generate_stream(
        self,
        prompt: str,
        max_tokens: int = 2000,
        temperature: float = 0.7,
        system: str | None = None,
        **kwargs: Any,
    ) -> AsyncGenerator[str, None]:
        """Generate text with streaming support.

        Args:
            prompt: The user prompt for the LLM
            max_tokens: Maximum number of tokens to generate
            temperature: Sampling temperature
            system: Optional system prompt (see ``generate``)
            **kwargs: Additional Anthropic parameters

        Yields:
            Text chunks as they are generated
        """
        stream_kwargs: dict[str, Any] = {
            "model": self.model,
            "max_tokens": max_tokens,
            "temperature": temperature,
            "messages": [{"role": "user", "content": prompt}],
            **kwargs,
        }
        system_param = _build_system_param(system)
        if system_param is not None:
            stream_kwargs["system"] = system_param

        async with self.client.messages.stream(**stream_kwargs) as stream:
            async for text in stream.text_stream:
                yield text

    def count_tokens(self, text: str) -> int:
        """Count tokens in text.

        Args:
            text: Text to count tokens for

        Returns:
            Number of tokens in the text

        Note:
            Anthropic uses their own tokenization.
            For estimation, we use ~4 characters per token.
        """
        # Rough estimation: 1 token ≈ 4 characters
        # Anthropic provides token counting via their API but requires a call
        return len(text) // 4

    def get_cost(self, input_tokens: int, output_tokens: int) -> float:
        """Calculate cost for token usage.

        Args:
            input_tokens: Number of input tokens
            output_tokens: Number of output tokens

        Returns:
            Cost in USD

        Note:
            Pricing tiers (per 1M tokens, approximate — confirm against
            https://anthropic.com/pricing):
            - Opus 4.x:   $15 input / $75 output
            - Sonnet 4.x: $3 input  / $15 output
            - Haiku 4.5:  $1 input  / $5 output
            - Haiku 3.5:  $0.80 input / $4 output
            - Claude 3 Haiku: $0.25 input / $1.25 output
        """
        model_lower = self.model.lower()
        if "opus" in model_lower:
            input_cost = input_tokens * 15.0 / 1_000_000
            output_cost = output_tokens * 75.0 / 1_000_000
        elif "haiku-4" in model_lower:
            input_cost = input_tokens * 1.0 / 1_000_000
            output_cost = output_tokens * 5.0 / 1_000_000
        elif "haiku-3-5" in model_lower or "haiku-3.5" in model_lower:
            input_cost = input_tokens * 0.80 / 1_000_000
            output_cost = output_tokens * 4.0 / 1_000_000
        elif "haiku" in model_lower:
            input_cost = input_tokens * 0.25 / 1_000_000
            output_cost = output_tokens * 1.25 / 1_000_000
        else:  # Sonnet (default for unknown Claude models)
            input_cost = input_tokens * 3.0 / 1_000_000
            output_cost = output_tokens * 15.0 / 1_000_000

        return input_cost + output_cost
