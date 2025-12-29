"""OpenAI LLM provider implementation."""

from collections.abc import AsyncGenerator
from typing import Any

from tenacity import (
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential,
)

from services.llm.base import BaseLLMProvider


class OpenAIProvider(BaseLLMProvider):
    """OpenAI LLM provider with retry logic."""

    def __init__(self, api_key: str, model: str = "gpt-4-turbo-preview") -> None:
        """Initialize OpenAI provider.

        Args:
            api_key: OpenAI API key
            model: Model to use for generation
        """
        try:
            from openai import AsyncOpenAI
        except ImportError as e:
            raise ImportError(
                "openai package not installed. Install with: pip install openai>=1.0.0"
            ) from e

        self.client = AsyncOpenAI(api_key=api_key)
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
            **kwargs: Additional OpenAI parameters

        Returns:
            Generated text response

        Raises:
            Exception: If generation fails after retries
        """
        response = await self.client.chat.completions.create(
            model=self.model,
            messages=[{"role": "user", "content": prompt}],
            max_tokens=max_tokens,
            temperature=temperature,
            **kwargs,
        )
        content = response.choices[0].message.content
        if content is None:
            raise ValueError("OpenAI returned empty response")
        return content

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
            **kwargs: Additional OpenAI parameters

        Yields:
            Text chunks as they are generated
        """
        stream = await self.client.chat.completions.create(
            model=self.model,
            messages=[{"role": "user", "content": prompt}],
            max_tokens=max_tokens,
            temperature=temperature,
            stream=True,
            **kwargs,
        )
        async for chunk in stream:
            if chunk.choices[0].delta.content:
                yield chunk.choices[0].delta.content

    def count_tokens(self, text: str) -> int:
        """Count tokens in text using tiktoken.

        Args:
            text: Text to count tokens for

        Returns:
            Number of tokens in the text
        """
        try:
            import tiktoken
        except ImportError:
            # Fallback: rough estimation (1 token ≈ 4 characters)
            return len(text) // 4

        try:
            encoding = tiktoken.encoding_for_model(self.model)
        except KeyError:
            # If model not found, use default encoding
            encoding = tiktoken.get_encoding("cl100k_base")

        return len(encoding.encode(text))

    def get_cost(self, input_tokens: int, output_tokens: int) -> float:
        """Calculate cost for token usage.

        Args:
            input_tokens: Number of input tokens
            output_tokens: Number of output tokens

        Returns:
            Cost in USD

        Note:
            Pricing as of 2024:
            - GPT-4 Turbo: $0.01/1K input, $0.03/1K output
            - GPT-3.5 Turbo: $0.0005/1K input, $0.0015/1K output
        """
        # GPT-4 Turbo pricing (default)
        if "gpt-4" in self.model.lower():
            input_cost = input_tokens * 0.01 / 1000
            output_cost = output_tokens * 0.03 / 1000
        else:  # GPT-3.5 Turbo pricing
            input_cost = input_tokens * 0.0005 / 1000
            output_cost = output_tokens * 0.0015 / 1000

        return input_cost + output_cost
