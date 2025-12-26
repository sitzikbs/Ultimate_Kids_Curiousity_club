"""Unit tests for TTS providers."""

from pathlib import Path

import pytest

from services.tts.factory import TTSProviderFactory
from services.tts.mock_provider import MockTTSProvider


@pytest.mark.unit
class TestMockTTSProvider:
    """Tests for MockTTSProvider."""

    def test_mock_provider_creation(self):
        """Test creating a mock TTS provider."""
        provider = MockTTSProvider()
        assert provider is not None
        assert provider.fast_mode is False
        assert provider.add_noise is False

    def test_mock_provider_fast_mode(self):
        """Test mock provider in fast mode."""
        provider = MockTTSProvider(fast_mode=True)
        assert provider.fast_mode is True

    def test_mock_provider_synthesize(self, tmp_path: Path):
        """Test mock provider synthesis."""
        provider = MockTTSProvider()
        text = "Hello world! This is a test."
        output_path = tmp_path / "test_audio.mp3"

        result = provider.synthesize(
            text=text,
            voice_id="mock_test",
            output_path=output_path,
        )

        assert result["characters"] == len(text)
        assert result["duration"] > 0
        assert result["audio_path"] == output_path
        assert output_path.exists()

    def test_mock_provider_synthesize_fast_mode(self, tmp_path: Path):
        """Test mock provider synthesis in fast mode."""
        provider = MockTTSProvider(fast_mode=True)
        text = "Hello world!"
        output_path = tmp_path / "test_audio.mp3"

        result = provider.synthesize(
            text=text,
            voice_id="mock_test",
            output_path=output_path,
        )

        assert result["characters"] == len(text)
        assert result["duration"] > 0
        assert output_path.exists()

    def test_mock_provider_list_voices(self):
        """Test listing mock voices."""
        provider = MockTTSProvider()
        voices = provider.list_voices()

        assert len(voices) > 0
        assert any(v["voice_id"] == "mock_narrator" for v in voices)
        assert any(v["voice_id"] == "mock_oliver" for v in voices)
        assert any(v["voice_id"] == "mock_hannah" for v in voices)

    def test_mock_provider_cost(self):
        """Test mock provider cost calculation."""
        provider = MockTTSProvider()
        cost = provider.get_cost(1000)
        assert cost == 0.0

    def test_mock_provider_duration_calculation(self, tmp_path: Path):
        """Test duration is calculated based on text length."""
        provider = MockTTSProvider()

        # Short text
        short_text = "Hello"
        short_path = tmp_path / "short.mp3"
        short_result = provider.synthesize(short_text, "mock_test", short_path)

        # Long text
        long_text = " ".join(["word"] * 100)
        long_path = tmp_path / "long.mp3"
        long_result = provider.synthesize(long_text, "mock_test", long_path)

        assert long_result["duration"] > short_result["duration"]


@pytest.mark.unit
class TestTTSProviderFactory:
    """Tests for TTSProviderFactory."""

    def test_factory_create_mock_provider(self):
        """Test factory creates mock provider."""
        provider = TTSProviderFactory.create_provider("mock")
        assert isinstance(provider, MockTTSProvider)

    def test_factory_create_mock_with_options(self):
        """Test factory creates mock provider with options."""
        provider = TTSProviderFactory.create_provider(
            "mock", fast_mode=True, add_noise=True
        )
        assert isinstance(provider, MockTTSProvider)
        assert provider.fast_mode is True
        assert provider.add_noise is True

    def test_factory_invalid_provider_type(self):
        """Test factory raises error for invalid provider type."""
        with pytest.raises(ValueError, match="Invalid provider type"):
            TTSProviderFactory.create_provider("invalid_provider")

    def test_factory_elevenlabs_requires_api_key(self):
        """Test factory requires API key for ElevenLabs."""
        with pytest.raises(ValueError, match="API key is required"):
            TTSProviderFactory.create_provider("elevenlabs")

    def test_factory_openai_requires_api_key(self):
        """Test factory requires API key for OpenAI."""
        with pytest.raises(ValueError, match="API key is required"):
            TTSProviderFactory.create_provider("openai")

    def test_factory_google_provider(self):
        """Test factory creates Google TTS provider."""
        provider = TTSProviderFactory.create_provider("google")
        assert provider is not None


@pytest.mark.unit
class TestProviderCostCalculations:
    """Tests for provider cost calculations."""

    def test_mock_provider_cost(self):
        """Test mock provider is always free."""
        provider = MockTTSProvider()
        assert provider.get_cost(0) == 0.0
        assert provider.get_cost(1000) == 0.0
        assert provider.get_cost(1000000) == 0.0

    def test_elevenlabs_provider_cost(self):
        """Test ElevenLabs provider cost calculation."""
        from services.tts.elevenlabs_provider import ElevenLabsProvider

        # Mock provider without API key (for cost calculation only)
        provider = ElevenLabsProvider("test_key")

        # $0.30 per 1K characters
        assert provider.get_cost(1000) == 0.30
        assert provider.get_cost(500) == 0.15
        assert provider.get_cost(2000) == 0.60

    def test_google_provider_cost(self):
        """Test Google TTS provider cost calculation."""
        from services.tts.google_provider import GoogleTTSProvider

        provider = GoogleTTSProvider()

        # $4.00 per 1M characters
        assert provider.get_cost(1_000_000) == 4.00
        assert provider.get_cost(500_000) == 2.00
        assert provider.get_cost(250_000) == 1.00

    def test_openai_provider_cost(self):
        """Test OpenAI TTS provider cost calculation."""
        from services.tts.openai_provider import OpenAITTSProvider

        provider = OpenAITTSProvider("test_key")

        # $15.00 per 1M characters
        assert provider.get_cost(1_000_000) == 15.00
        assert provider.get_cost(500_000) == 7.50
        assert provider.get_cost(100_000) == 1.50
