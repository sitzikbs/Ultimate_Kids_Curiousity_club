"""Google Gemini LLM provider implementation."""

from collections.abc import AsyncGenerator
from typing import Any

from tenacity import (
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential,
)

from services.llm.base import BaseLLMProvider


class GeminiProvider(BaseLLMProvider):
    """Google Gemini LLM provider with retry logic."""

    def __init__(self, api_key: str, model: str = "gemini-1.5-pro") -> None:
        """Initialize Gemini provider.

        Args:
            api_key: Google API key
            model: Model to use for generation
        """
        try:
            import google.generativeai as genai
        except ImportError as e:
            raise ImportError(
                "google-generativeai package not installed. "
                "Install with: pip install google-generativeai>=0.3.0"
            ) from e

        genai.configure(api_key=api_key)
        self.model_name = model
        self.model = genai.GenerativeModel(model)

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
            **kwargs: Additional Gemini parameters

        Returns:
            Generated text response

        Raises:
            Exception: If generation fails after retries
        """
        generation_config = {
            "max_output_tokens": max_tokens,
            "temperature": temperature,
        }
        generation_config.update(kwargs)

        response = await self.model.generate_content_async(
            prompt, generation_config=generation_config
        )

        if response.text:
            return response.text
        raise ValueError("Gemini returned empty response")

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
            **kwargs: Additional Gemini parameters

        Yields:
            Text chunks as they are generated
        """
        generation_config = {
            "max_output_tokens": max_tokens,
            "temperature": temperature,
        }
        generation_config.update(kwargs)

        response = await self.model.generate_content_async(
            prompt, generation_config=generation_config, stream=True
        )

        async for chunk in response:
            if chunk.text:
                yield chunk.text

    def count_tokens(self, text: str) -> int:
        """Count tokens in text.

        Args:
            text: Text to count tokens for

        Returns:
            Number of tokens in the text

        Note:
            Google uses their own tokenization.
            For estimation, we use ~4 characters per token.
        """
        # Rough estimation: 1 token ≈ 4 characters
        # Gemini provides token counting via count_tokens() method but requires sync
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
            - Gemini 1.5 Pro: $0.00125/1K input, $0.005/1K output (prompts <= 128K)
            - Gemini 1.5 Flash: $0.000075/1K input, $0.0003/1K output (prompts <= 128K)
            - Gemini 1.0 Pro: $0.0005/1K input, $0.0015/1K output
        """
        # Determine pricing based on model
        if "1.5-pro" in self.model_name.lower():
            input_cost = input_tokens * 0.00125 / 1000
            output_cost = output_tokens * 0.005 / 1000
        elif "1.5-flash" in self.model_name.lower():
            input_cost = input_tokens * 0.000075 / 1000
            output_cost = output_tokens * 0.0003 / 1000
        else:  # Gemini 1.0 Pro (default)
            input_cost = input_tokens * 0.0005 / 1000
            output_cost = output_tokens * 0.0015 / 1000

        return input_cost + output_cost
