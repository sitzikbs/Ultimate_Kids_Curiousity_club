"""Gemma 4 local LLM provider via ollama's OpenAI-compatible API."""

import json
import logging
from collections.abc import AsyncGenerator
from typing import Any

from openai import APIConnectionError, APITimeoutError
from tenacity import (
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential,
)

from services.llm.base import BaseLLMProvider

logger = logging.getLogger(__name__)


class GemmaProvider(BaseLLMProvider):
    """Gemma 4 LLM provider using ollama's OpenAI-compatible endpoint.

    Uses the ``openai`` SDK pointed at a local ollama server to run
    Gemma 4 models entirely on-device with no external API calls.
    """

    def __init__(
        self,
        base_url: str = "http://llm:11434/v1",
        model: str = "gemma4:26b-a4b",
    ) -> None:
        """Initialize Gemma provider.

        Args:
            base_url: Base URL for the ollama OpenAI-compatible endpoint.
            model: Gemma model tag to use for generation.
        """
        try:
            from openai import AsyncOpenAI
        except ImportError as e:
            raise ImportError(
                "openai package not installed. Install with: uv add openai>=1.0.0"
            ) from e

        self.client = AsyncOpenAI(
            base_url=base_url,
            api_key="ollama",  # ollama doesn't need a real key
        )
        self.model = model
        self._base_url = base_url
        logger.info(
            "GemmaProvider initialised: model=%s, base_url=%s",
            model,
            base_url,
        )

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
            prompt: The input prompt for the LLM.
            max_tokens: Maximum number of tokens to generate.
            temperature: Sampling temperature.
            **kwargs: Additional parameters forwarded to the OpenAI SDK.

        Returns:
            Generated text response.

        Raises:
            Exception: If generation fails after retries.
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
            raise ValueError("Gemma returned empty response")
        return content

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=30),
        retry=retry_if_exception_type((APIConnectionError, APITimeoutError)),
    )
    async def generate_structured(
        self,
        prompt: str,
        max_tokens: int = 2000,
        temperature: float = 0.7,
        **kwargs: Any,
    ) -> dict[str, Any]:
        """Generate structured JSON output using ollama's JSON mode.

        Note: This method is specific to GemmaProvider and not part of
        BaseLLMProvider. Callers should check for this capability or
        use the service layer for structured output parsing.

        Uses ``response_format={"type": "json_object"}`` to instruct
        the model to return valid JSON.

        Args:
            prompt: The input prompt (should ask for JSON output).
            max_tokens: Maximum number of tokens to generate.
            temperature: Sampling temperature.
            **kwargs: Additional parameters forwarded to the OpenAI SDK.

        Returns:
            Parsed JSON dictionary.

        Raises:
            ValueError: If the response is empty or not valid JSON.
        """
        response = await self.client.chat.completions.create(
            model=self.model,
            messages=[{"role": "user", "content": prompt}],
            max_tokens=max_tokens,
            temperature=temperature,
            response_format={"type": "json_object"},
            **kwargs,
        )
        content = response.choices[0].message.content
        if content is None:
            raise ValueError("Gemma returned empty response")

        try:
            return json.loads(content)
        except json.JSONDecodeError as e:
            raise ValueError(
                f"Gemma response is not valid JSON: {content[:200]}"
            ) from e

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        retry=retry_if_exception_type((APIConnectionError, APITimeoutError)),
    )
    async def generate_stream(
        self,
        prompt: str,
        max_tokens: int = 2000,
        temperature: float = 0.7,
        **kwargs: Any,
    ) -> AsyncGenerator[str, None]:
        """Generate text with streaming support.

        Args:
            prompt: The input prompt for the LLM.
            max_tokens: Maximum number of tokens to generate.
            temperature: Sampling temperature.
            **kwargs: Additional parameters forwarded to the OpenAI SDK.

        Yields:
            Text chunks as they are generated.
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
        """Count tokens in text using rough estimation.

        Gemma does not have a public tokenizer in tiktoken, so we fall
        back to a character-based approximation.

        Args:
            text: Text to count tokens for.

        Returns:
            Estimated number of tokens in the text.
        """
        # Rough estimation: 1 token ~ 4 characters for English text
        return len(text) // 4

    def get_cost(self, input_tokens: int, output_tokens: int) -> float:
        """Calculate cost for token usage.

        Gemma runs locally via ollama, so there is no per-token API cost.

        Args:
            input_tokens: Number of input tokens.
            output_tokens: Number of output tokens.

        Returns:
            Cost in USD (always 0.0 for local inference).
        """
        return 0.0
