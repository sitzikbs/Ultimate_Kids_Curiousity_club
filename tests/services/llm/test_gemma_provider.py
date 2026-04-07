"""Tests for the Gemma 4 local LLM provider."""

from unittest.mock import AsyncMock, MagicMock

import pytest
from tenacity import RetryError

from services.llm.base import BaseLLMProvider
from services.llm.factory import LLMProviderFactory
from services.llm.gemma_provider import GemmaProvider


class TestGemmaProviderInit:
    """Tests for GemmaProvider initialisation."""

    def test_default_init(self):
        """Test provider initialises with default base_url and model."""
        provider = GemmaProvider()

        assert isinstance(provider, BaseLLMProvider)
        assert provider.model == "gemma4:latest"
        assert provider._base_url == "http://localhost:11435/v1"

    def test_custom_init(self):
        """Test provider initialises with custom base_url and model."""
        provider = GemmaProvider(
            base_url="http://localhost:11435/v1",
            model="gemma4:12b",
        )

        assert provider.model == "gemma4:12b"
        assert provider._base_url == "http://localhost:11435/v1"

    def test_is_base_provider_subclass(self):
        """Test that GemmaProvider is a subclass of BaseLLMProvider."""
        assert issubclass(GemmaProvider, BaseLLMProvider)

    def test_same_interface_as_openai_provider(self):
        """Test that GemmaProvider has the same core interface methods."""
        provider = GemmaProvider()
        assert hasattr(provider, "generate")
        assert hasattr(provider, "generate_stream")
        assert hasattr(provider, "count_tokens")
        assert hasattr(provider, "get_cost")
        assert hasattr(provider, "generate_structured")


class TestGemmaProviderGenerate:
    """Tests for GemmaProvider.generate()."""

    @pytest.mark.asyncio
    async def test_generate_returns_content(self):
        """Test generate() returns text from the model response."""
        provider = GemmaProvider()

        mock_message = MagicMock()
        mock_message.content = "Once upon a time, Oliver built a robot."

        mock_choice = MagicMock()
        mock_choice.message = mock_message

        mock_response = MagicMock()
        mock_response.choices = [mock_choice]

        provider.client.chat.completions.create = AsyncMock(return_value=mock_response)

        result = await provider.generate("Tell me a story", max_tokens=100)

        assert result == "Once upon a time, Oliver built a robot."
        provider.client.chat.completions.create.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_generate_passes_parameters(self):
        """Test generate() forwards parameters to the OpenAI SDK."""
        provider = GemmaProvider(model="gemma4:12b")

        mock_message = MagicMock()
        mock_message.content = "Response text"
        mock_choice = MagicMock()
        mock_choice.message = mock_message
        mock_response = MagicMock()
        mock_response.choices = [mock_choice]

        provider.client.chat.completions.create = AsyncMock(return_value=mock_response)

        await provider.generate("Test prompt", max_tokens=500, temperature=0.3)

        call_kwargs = provider.client.chat.completions.create.call_args.kwargs
        assert call_kwargs["model"] == "gemma4:12b"
        assert call_kwargs["extra_body"] == {"num_predict": 500}
        assert call_kwargs["temperature"] == 0.3
        assert call_kwargs["messages"] == [{"role": "user", "content": "Test prompt"}]

    @pytest.mark.asyncio
    async def test_generate_raises_on_empty_response(self):
        """Test generate() raises ValueError on empty response."""
        provider = GemmaProvider()

        mock_message = MagicMock()
        mock_message.content = None
        mock_choice = MagicMock()
        mock_choice.message = mock_message
        mock_response = MagicMock()
        mock_response.choices = [mock_choice]

        provider.client.chat.completions.create = AsyncMock(return_value=mock_response)

        with pytest.raises(RetryError) as exc_info:
            await provider.generate("Test prompt")
        assert isinstance(exc_info.value.last_attempt.exception(), ValueError)
        assert "Gemma returned empty response" in str(
            exc_info.value.last_attempt.exception()
        )


class TestGemmaProviderGenerateStructured:
    """Tests for GemmaProvider.generate_structured()."""

    @pytest.mark.asyncio
    async def test_generate_structured_returns_dict(self):
        """Test generate_structured() returns parsed JSON dict."""
        provider = GemmaProvider()

        json_content = (
            '{"refined_topic": "How Volcanoes Work", '
            '"learning_objectives": ["Understand magma"]}'
        )
        mock_message = MagicMock()
        mock_message.content = json_content
        mock_choice = MagicMock()
        mock_choice.message = mock_message
        mock_response = MagicMock()
        mock_response.choices = [mock_choice]

        provider.client.chat.completions.create = AsyncMock(return_value=mock_response)

        result = await provider.generate_structured("Generate JSON")

        assert isinstance(result, dict)
        assert result["refined_topic"] == "How Volcanoes Work"
        assert len(result["learning_objectives"]) == 1

        # Verify response_format was passed
        call_kwargs = provider.client.chat.completions.create.call_args.kwargs
        assert call_kwargs["response_format"] == {"type": "json_object"}

    @pytest.mark.asyncio
    async def test_generate_structured_raises_on_invalid_json(self):
        """Test generate_structured() raises ValueError immediately on bad JSON.

        ValueError is not retried (only transient connection errors are),
        so a single attempt should raise directly.
        """
        provider = GemmaProvider()

        mock_message = MagicMock()
        mock_message.content = "This is not valid JSON"
        mock_choice = MagicMock()
        mock_choice.message = mock_message
        mock_response = MagicMock()
        mock_response.choices = [mock_choice]

        provider.client.chat.completions.create = AsyncMock(return_value=mock_response)

        with pytest.raises(ValueError, match="not valid JSON"):
            await provider.generate_structured("Generate JSON")

        # Verify only a single attempt was made (no retries for ValueError)
        assert provider.client.chat.completions.create.await_count == 1


class TestGemmaProviderStream:
    """Tests for GemmaProvider.generate_stream()."""

    @pytest.mark.asyncio
    async def test_generate_stream_yields_chunks(self):
        """Test generate_stream() yields content chunks."""
        provider = GemmaProvider()

        # Build mock stream chunks
        chunks = []
        for text in ["Once ", "upon ", "a time"]:
            delta = MagicMock()
            delta.content = text
            choice = MagicMock()
            choice.delta = delta
            chunk = MagicMock()
            chunk.choices = [choice]
            chunks.append(chunk)

        async def mock_stream():
            for c in chunks:
                yield c

        provider.client.chat.completions.create = AsyncMock(return_value=mock_stream())

        result_chunks: list[str] = []
        async for text in provider.generate_stream("Tell a story"):
            result_chunks.append(text)

        assert result_chunks == ["Once ", "upon ", "a time"]


class TestGemmaProviderTokensAndCost:
    """Tests for count_tokens() and get_cost()."""

    def test_count_tokens_estimation(self):
        """Test token counting uses character-based estimation."""
        provider = GemmaProvider()
        text = "Hello world! This is a test sentence."
        tokens = provider.count_tokens(text)

        assert tokens == len(text) // 4
        assert tokens > 0

    def test_get_cost_always_zero(self):
        """Test cost is always zero for local inference."""
        provider = GemmaProvider()

        assert provider.get_cost(1000, 500) == 0.0
        assert provider.get_cost(0, 0) == 0.0
        assert provider.get_cost(100000, 100000) == 0.0


class TestGemmaProviderConnectionErrors:
    """Tests for error handling on connection failures."""

    @pytest.mark.asyncio
    async def test_generate_raises_on_connection_error(self):
        """Test generate() propagates connection errors after retries."""
        provider = GemmaProvider()

        provider.client.chat.completions.create = AsyncMock(
            side_effect=ConnectionError("Cannot connect to ollama")
        )

        # tenacity will retry 3 times then wrap in RetryError
        with pytest.raises(RetryError) as exc_info:
            await provider.generate("Test prompt")
        assert isinstance(exc_info.value.last_attempt.exception(), ConnectionError)

        assert provider.client.chat.completions.create.await_count == 3


class TestGemmaProviderFactory:
    """Tests for creating GemmaProvider via the factory."""

    def test_factory_creates_gemma_provider(self):
        """Test factory creates GemmaProvider for 'gemma' type."""
        provider = LLMProviderFactory.create_provider("gemma")

        assert isinstance(provider, GemmaProvider)
        assert isinstance(provider, BaseLLMProvider)
        assert provider.model == "gemma4:latest"

    def test_factory_creates_gemma_with_custom_model(self):
        """Test factory passes custom model to GemmaProvider."""
        provider = LLMProviderFactory.create_provider("gemma", model="gemma4:12b")

        assert isinstance(provider, GemmaProvider)
        assert provider.model == "gemma4:12b"

    def test_factory_creates_gemma_with_custom_base_url(self):
        """Test factory passes custom base_url to GemmaProvider."""
        provider = LLMProviderFactory.create_provider(
            "gemma", base_url="http://localhost:11435/v1"
        )

        assert isinstance(provider, GemmaProvider)
        assert provider._base_url == "http://localhost:11435/v1"

    def test_factory_gemma_no_api_key_required(self):
        """Test factory does not require api_key for gemma."""
        # Should not raise
        provider = LLMProviderFactory.create_provider("gemma")
        assert isinstance(provider, GemmaProvider)

    def test_factory_error_message_includes_gemma(self):
        """Test that invalid provider error lists gemma as an option."""
        with pytest.raises(ValueError, match="gemma"):
            LLMProviderFactory.create_provider("invalid")
