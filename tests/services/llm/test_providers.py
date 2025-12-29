"""Tests for LLM provider implementations."""

import pytest

from services.llm.base import BaseLLMProvider
from services.llm.factory import LLMProviderFactory
from services.llm.mock_provider import MockLLMProvider


class TestMockLLMProvider:
    """Tests for MockLLMProvider."""

    @pytest.mark.asyncio
    async def test_generate_concept(self):
        """Test generating a story concept."""
        provider = MockLLMProvider()

        prompt = "Generate a story concept about airplanes for Oliver."
        result = await provider.generate(prompt, max_tokens=1000, temperature=0.7)

        assert result
        assert len(result) > 50
        assert "Oliver" in result or "story" in result.lower()

    @pytest.mark.asyncio
    async def test_generate_outline(self):
        """Test generating a story outline."""
        provider = MockLLMProvider()

        prompt = "Generate story beats and outline for the concept."
        result = await provider.generate(prompt, max_tokens=2000, temperature=0.7)

        assert result
        assert "beat" in result.lower() or "story_beats" in result

    @pytest.mark.asyncio
    async def test_generate_script(self):
        """Test generating a script."""
        provider = MockLLMProvider()

        prompt = "Generate script with dialogue for the segment."
        result = await provider.generate(prompt, max_tokens=2000, temperature=0.7)

        assert result
        assert "speaker" in result.lower() or "narrator" in result.lower()

    @pytest.mark.asyncio
    async def test_generate_stream(self):
        """Test streaming generation."""
        provider = MockLLMProvider()

        prompt = "Generate a story concept."
        chunks = []
        async for chunk in provider.generate_stream(prompt):
            chunks.append(chunk)

        assert len(chunks) > 0
        full_text = "".join(chunks)
        assert len(full_text) > 50

    def test_count_tokens(self):
        """Test token counting."""
        provider = MockLLMProvider()

        text = "This is a test sentence with approximately twenty characters."
        tokens = provider.count_tokens(text)

        assert tokens > 0
        # Rough estimate: 1 token ≈ 4 characters
        assert tokens == len(text) // 4

    def test_get_cost(self):
        """Test cost calculation (should be $0 for mock)."""
        provider = MockLLMProvider()

        cost = provider.get_cost(input_tokens=1000, output_tokens=500)
        assert cost == 0.0


class TestLLMProviderFactory:
    """Tests for LLMProviderFactory."""

    def test_create_mock_provider(self):
        """Test creating a mock provider."""
        provider = LLMProviderFactory.create_provider("mock")

        assert isinstance(provider, BaseLLMProvider)
        assert isinstance(provider, MockLLMProvider)

    def test_create_openai_provider_without_key(self):
        """Test that OpenAI provider requires API key."""
        with pytest.raises(ValueError, match="API key is required"):
            LLMProviderFactory.create_provider("openai")

    def test_create_openai_provider_with_key(self):
        """Test creating OpenAI provider with API key."""
        try:
            provider = LLMProviderFactory.create_provider(
                "openai", api_key="test-key-123"
            )
            assert isinstance(provider, BaseLLMProvider)
            assert provider.model == "gpt-4-turbo-preview"
        except ImportError as e:
            # Skip test if openai package not installed
            pytest.skip(f"OpenAI package not installed: {e}")

    def test_create_openai_provider_custom_model(self):
        """Test creating OpenAI provider with custom model."""
        try:
            provider = LLMProviderFactory.create_provider(
                "openai", api_key="test-key-123", model="gpt-3.5-turbo"
            )
            assert isinstance(provider, BaseLLMProvider)
            assert provider.model == "gpt-3.5-turbo"
        except ImportError as e:
            # Skip test if openai package not installed
            pytest.skip(f"OpenAI package not installed: {e}")

    def test_create_anthropic_provider_without_key(self):
        """Test that Anthropic provider requires API key."""
        with pytest.raises(ValueError, match="API key is required"):
            LLMProviderFactory.create_provider("anthropic")

    def test_create_anthropic_provider_with_key(self):
        """Test creating Anthropic provider with API key."""
        try:
            provider = LLMProviderFactory.create_provider(
                "anthropic", api_key="test-key-123"
            )
            assert isinstance(provider, BaseLLMProvider)
            assert provider.model == "claude-3-sonnet-20240229"
        except ImportError as e:
            # Skip test if anthropic package not installed
            pytest.skip(f"Anthropic package not installed: {e}")

    def test_invalid_provider_type(self):
        """Test that invalid provider type raises error."""
        with pytest.raises(ValueError, match="Invalid provider type"):
            LLMProviderFactory.create_provider("invalid")


@pytest.mark.skipif(
    True, reason="Requires OpenAI API key - run manually with real credentials"
)
class TestOpenAIProviderIntegration:
    """Integration tests for OpenAI provider (requires API key)."""

    @pytest.mark.asyncio
    async def test_openai_generate(self):
        """Test OpenAI generation."""
        import os

        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            pytest.skip("OPENAI_API_KEY not set")

        provider = LLMProviderFactory.create_provider("openai", api_key=api_key)

        result = await provider.generate(
            "Write a one-sentence story about a cat.", max_tokens=50
        )

        assert result
        assert len(result) > 0

    def test_openai_token_counting(self):
        """Test OpenAI token counting with tiktoken."""
        import os

        api_key = os.getenv("OPENAI_API_KEY", "fake-key")
        provider = LLMProviderFactory.create_provider("openai", api_key=api_key)

        text = "Hello world! This is a test."
        tokens = provider.count_tokens(text)

        assert tokens > 0
        assert tokens < len(text)  # Tokens should be less than characters


@pytest.mark.skipif(
    True, reason="Requires Anthropic API key - run manually with real credentials"
)
class TestAnthropicProviderIntegration:
    """Integration tests for Anthropic provider (requires API key)."""

    @pytest.mark.asyncio
    async def test_anthropic_generate(self):
        """Test Anthropic generation."""
        import os

        api_key = os.getenv("ANTHROPIC_API_KEY")
        if not api_key:
            pytest.skip("ANTHROPIC_API_KEY not set")

        provider = LLMProviderFactory.create_provider("anthropic", api_key=api_key)

        result = await provider.generate(
            "Write a one-sentence story about a dog.", max_tokens=50
        )

        assert result
        assert len(result) > 0
