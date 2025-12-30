"""Factory for creating LLM provider instances."""

from pathlib import Path

from services.llm.anthropic_provider import AnthropicProvider
from services.llm.base import BaseLLMProvider
from services.llm.gemini_provider import GeminiProvider
from services.llm.mock_provider import MockLLMProvider
from services.llm.openai_provider import OpenAIProvider


class LLMProviderFactory:
    """Factory for creating LLM provider instances."""

    @staticmethod
    def create_provider(
        provider_type: str,
        api_key: str | None = None,
        model: str | None = None,
        fixtures_dir: Path | None = None,
    ) -> BaseLLMProvider:
        """Create an LLM provider instance.

        Args:
            provider_type: Type of provider ('mock', 'openai', 'anthropic', 'gemini')
            api_key: API key for the provider (required for real providers)
            model: Model name to use (optional, uses provider defaults)
            fixtures_dir: Directory for mock fixtures (only for mock provider)

        Returns:
            LLM provider instance

        Raises:
            ValueError: If provider_type is invalid or required credentials are missing
        """
        provider: BaseLLMProvider

        if provider_type == "mock":
            provider = MockLLMProvider(fixtures_dir=fixtures_dir)

        elif provider_type == "openai":
            if not api_key:
                raise ValueError("API key is required for OpenAI provider")
            if model:
                provider = OpenAIProvider(api_key=api_key, model=model)
            else:
                provider = OpenAIProvider(api_key=api_key)

        elif provider_type == "anthropic":
            if not api_key:
                raise ValueError("API key is required for Anthropic provider")
            if model:
                provider = AnthropicProvider(api_key=api_key, model=model)
            else:
                provider = AnthropicProvider(api_key=api_key)

        elif provider_type == "gemini":
            if not api_key:
                raise ValueError("API key is required for Gemini provider")
            if model:
                provider = GeminiProvider(api_key=api_key, model=model)
            else:
                provider = GeminiProvider(api_key=api_key)

        else:
            raise ValueError(
                f"Invalid provider type: {provider_type}. "
                f"Must be one of: mock, openai, anthropic, gemini"
            )

        return provider
