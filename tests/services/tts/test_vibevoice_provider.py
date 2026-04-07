"""Unit tests for the VibeVoice TTS provider."""

from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import httpx
import pytest

from services.tts.factory import TTSProviderFactory
from services.tts.vibevoice_provider import VibeVoiceProvider

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

FAKE_AUDIO = b"\xff\xfb\x90\x00" + b"\x00" * 256  # Minimal fake MP3 bytes


@pytest.fixture()
def provider() -> VibeVoiceProvider:
    """Return a VibeVoice provider pointed at a test URL."""
    return VibeVoiceProvider(base_url="http://localhost:8100", timeout=10.0)


# ---------------------------------------------------------------------------
# Single-speaker synthesis
# ---------------------------------------------------------------------------


@pytest.mark.unit
class TestSynthesizeSingleSpeaker:
    """Tests for single-speaker synthesis."""

    def test_synthesize_returns_result_dict(
        self, provider: VibeVoiceProvider, tmp_path: Path
    ) -> None:
        """Successful synthesis returns a well-formed result dict."""
        output = tmp_path / "segment_001.mp3"
        mock_response = MagicMock(spec=httpx.Response)
        mock_response.content = FAKE_AUDIO
        mock_response.raise_for_status = MagicMock()

        with patch(
            "services.tts.vibevoice_provider.httpx.post",
            return_value=mock_response,
        ):
            result = provider.synthesize(
                text="Hello world!",
                voice_id="narrator",
                output_path=output,
                speed=1.0,
            )

        assert result["characters"] == len("Hello world!")
        assert result["audio_path"] == output
        assert result["voice_id"] == "narrator"
        assert result["duration"] > 0
        assert output.exists()
        assert output.read_bytes() == FAKE_AUDIO

    def test_synthesize_passes_emotion_and_speed(
        self, provider: VibeVoiceProvider, tmp_path: Path
    ) -> None:
        """Emotion and speed kwargs are forwarded to the API."""
        output = tmp_path / "seg.mp3"
        mock_response = MagicMock(spec=httpx.Response)
        mock_response.content = FAKE_AUDIO
        mock_response.raise_for_status = MagicMock()

        with patch(
            "services.tts.vibevoice_provider.httpx.post",
            return_value=mock_response,
        ) as mock_post:
            provider.synthesize(
                text="Wow!",
                voice_id="lily",
                output_path=output,
                speed=1.2,
                emotion="excited",
            )

        call_kwargs = mock_post.call_args
        body = call_kwargs.kwargs["json"]
        assert body["speaker"] == "lily"
        assert body["speed"] == 1.2
        assert body["emotion"] == "excited"

    def test_synthesize_creates_parent_dirs(
        self, provider: VibeVoiceProvider, tmp_path: Path
    ) -> None:
        """Parent directories are created automatically."""
        output = tmp_path / "nested" / "deep" / "audio.mp3"
        mock_response = MagicMock(spec=httpx.Response)
        mock_response.content = FAKE_AUDIO
        mock_response.raise_for_status = MagicMock()

        with patch(
            "services.tts.vibevoice_provider.httpx.post",
            return_value=mock_response,
        ):
            provider.synthesize("Hi", "narrator", output)

        assert output.exists()


# ---------------------------------------------------------------------------
# Multi-speaker synthesis
# ---------------------------------------------------------------------------


@pytest.mark.unit
class TestSynthesizeDialogue:
    """Tests for multi-speaker dialogue synthesis."""

    @pytest.mark.asyncio
    async def test_synthesize_dialogue_returns_path(
        self, provider: VibeVoiceProvider
    ) -> None:
        """Multi-speaker synthesis returns a valid file path."""
        mock_response = MagicMock(spec=httpx.Response)
        mock_response.content = FAKE_AUDIO
        mock_response.raise_for_status = MagicMock()

        mock_client = AsyncMock(spec=httpx.AsyncClient)
        mock_client.post = AsyncMock(return_value=mock_response)
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=False)

        segments = [
            {"speaker": "narrator", "text": "Once upon a time..."},
            {"speaker": "oliver the inventor", "text": "I have an idea!"},
        ]

        with patch(
            "services.tts.vibevoice_provider.httpx.AsyncClient",
            return_value=mock_client,
        ):
            result = await provider.synthesize_dialogue(segments, output_format="mp3")

        assert isinstance(result, Path)
        assert result.suffix == ".mp3"
        assert result.read_bytes() == FAKE_AUDIO


# ---------------------------------------------------------------------------
# Speaker mapping
# ---------------------------------------------------------------------------


@pytest.mark.unit
class TestSpeakerMapping:
    """Tests for speaker/voice listing."""

    def test_list_voices_returns_all_characters(
        self, provider: VibeVoiceProvider
    ) -> None:
        """All six show characters are present in the voice list."""
        voices = provider.list_voices()
        ids = {v["voice_id"] for v in voices}
        assert "narrator" in ids
        assert "oliver the inventor" in ids
        assert "lily" in ids
        assert "max" in ids
        assert "aisha" in ids
        assert "mrs. chen" in ids

    def test_list_voices_has_required_keys(self, provider: VibeVoiceProvider) -> None:
        """Each voice entry has voice_id, name, and labels."""
        for voice in provider.list_voices():
            assert "voice_id" in voice
            assert "name" in voice
            assert "labels" in voice


# ---------------------------------------------------------------------------
# Cost calculation
# ---------------------------------------------------------------------------


@pytest.mark.unit
class TestCost:
    """VibeVoice is local so cost is always zero."""

    def test_cost_is_zero(self, provider: VibeVoiceProvider) -> None:
        assert provider.get_cost(0) == 0.0
        assert provider.get_cost(1_000) == 0.0
        assert provider.get_cost(1_000_000) == 0.0


# ---------------------------------------------------------------------------
# Error handling
# ---------------------------------------------------------------------------


@pytest.mark.unit
class TestErrorHandling:
    """Tests for connection and timeout errors."""

    def test_connection_error_propagates(
        self, provider: VibeVoiceProvider, tmp_path: Path
    ) -> None:
        """A connection error from httpx is not swallowed."""
        with patch(
            "services.tts.vibevoice_provider.httpx.post",
            side_effect=httpx.ConnectError("Connection refused"),
        ):
            with pytest.raises(httpx.ConnectError):
                provider.synthesize("Hello", "narrator", tmp_path / "out.mp3")

    def test_timeout_error_propagates(
        self, provider: VibeVoiceProvider, tmp_path: Path
    ) -> None:
        """A timeout from httpx is not swallowed."""
        with patch(
            "services.tts.vibevoice_provider.httpx.post",
            side_effect=httpx.ReadTimeout("Read timed out"),
        ):
            with pytest.raises(httpx.ReadTimeout):
                provider.synthesize("Hello", "narrator", tmp_path / "out.mp3")

    def test_http_status_error_propagates(
        self, provider: VibeVoiceProvider, tmp_path: Path
    ) -> None:
        """Non-2xx responses raise HTTPStatusError."""
        mock_response = MagicMock(spec=httpx.Response)
        mock_response.raise_for_status.side_effect = httpx.HTTPStatusError(
            "Server Error",
            request=MagicMock(),
            response=MagicMock(status_code=500),
        )

        with patch(
            "services.tts.vibevoice_provider.httpx.post",
            return_value=mock_response,
        ):
            with pytest.raises(httpx.HTTPStatusError):
                provider.synthesize("Hello", "narrator", tmp_path / "out.mp3")


# ---------------------------------------------------------------------------
# Factory integration
# ---------------------------------------------------------------------------


@pytest.mark.unit
class TestFactoryIntegration:
    """The TTSProviderFactory can create VibeVoice providers."""

    def test_factory_creates_vibevoice_provider(self) -> None:
        """Factory returns a VibeVoiceProvider for 'vibevoice' type."""
        provider = TTSProviderFactory.create_provider("vibevoice", enable_retry=False)
        # Unwrap RetryableTTSProvider if retry is enabled
        assert isinstance(provider, VibeVoiceProvider)

    def test_factory_vibevoice_with_retry(self) -> None:
        """Factory wraps VibeVoice in retry logic when enabled."""
        from services.tts.factory import RetryableTTSProvider

        provider = TTSProviderFactory.create_provider("vibevoice", enable_retry=True)
        assert isinstance(provider, RetryableTTSProvider)

    def test_factory_vibevoice_custom_url(self) -> None:
        """Factory passes base_url through to the provider."""
        provider = TTSProviderFactory.create_provider(
            "vibevoice",
            base_url="http://custom:9999",
            enable_retry=False,
        )
        assert isinstance(provider, VibeVoiceProvider)
        assert provider.base_url == "http://custom:9999"
