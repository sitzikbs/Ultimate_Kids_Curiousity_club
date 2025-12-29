"""Anthropic LLM provider implementation."""

from typing import Any, AsyncGenerator

from tenacity import (
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential,
)

from services.llm.base import BaseLLMProvider


class AnthropicProvider(BaseLLMProvider):
    """Anthropic Claude LLM provider with retry logic."""

    def __init__(self, api_key: str, model: str = "claude-3-sonnet-20240229") -> None:
        """Initialize Anthropic provider.

        Args:
            api_key: Anthropic API key
            model: Model to use for generation
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
        **kwargs: Any,
    ) -> str:
        """Generate text from prompt with retry logic.

        Args:
            prompt: The input prompt for the LLM
            max_tokens: Maximum number of tokens to generate
            temperature: Sampling temperature
            **kwargs: Additional Anthropic parameters

        Returns:
            Generated text response

        Raises:
            Exception: If generation fails after retries
        """
        response = await self.client.messages.create(
            model=self.model,
            max_tokens=max_tokens,
            temperature=temperature,
            messages=[{"role": "user", "content": prompt}],
            **kwargs,
        )

        # Extract text from response
        if response.content and len(response.content) > 0:
            return response.content[0].text
        raise ValueError("Anthropic returned empty response")

    async def generate_stream(
        self,
        prompt: str,
        max_tokens: int = 2000,
        temperature: float = 0.7,
        **kwargs: Any,
    ) -> AsyncGenerator[str, None]:
        """Generate text with streaming support.

        Args:
            prompt: The input prompt for the LLM
            max_tokens: Maximum number of tokens to generate
            temperature: Sampling temperature
            **kwargs: Additional Anthropic parameters

        Yields:
            Text chunks as they are generated
        """
        async with self.client.messages.stream(
            model=self.model,
            max_tokens=max_tokens,
            temperature=temperature,
            messages=[{"role": "user", "content": prompt}],
            **kwargs,
        ) as stream:
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
            Pricing as of 2024:
            - Claude 3 Opus: $0.015/1K input, $0.075/1K output
            - Claude 3 Sonnet: $0.003/1K input, $0.015/1K output
            - Claude 3 Haiku: $0.00025/1K input, $0.00125/1K output
        """
        # Determine pricing based on model
        if "opus" in self.model.lower():
            input_cost = input_tokens * 0.015 / 1000
            output_cost = output_tokens * 0.075 / 1000
        elif "haiku" in self.model.lower():
            input_cost = input_tokens * 0.00025 / 1000
            output_cost = output_tokens * 0.00125 / 1000
        else:  # Sonnet (default)
            input_cost = input_tokens * 0.003 / 1000
            output_cost = output_tokens * 0.015 / 1000

        return input_cost + output_cost
