"""Unit tests for Audio Synthesis Service."""

from pathlib import Path

import pytest

from services.tts.factory import TTSProviderFactory
from services.tts.synthesis_service import AudioSynthesisService


@pytest.mark.unit
class TestAudioSynthesisService:
    """Tests for AudioSynthesisService."""

    @pytest.fixture
    def mock_provider(self):
        """Create a mock TTS provider."""
        return TTSProviderFactory.create_provider("mock", fast_mode=True)

    @pytest.fixture
    def synthesis_service(self, mock_provider, tmp_path: Path):
        """Create an audio synthesis service."""
        return AudioSynthesisService(
            tts_provider=mock_provider,
            output_dir=tmp_path / "audio",
        )

    @pytest.fixture
    def sample_voice_config(self):
        """Sample voice configuration."""
        return {
            "provider": "mock",
            "voice_id": "mock_oliver",
            "stability": 0.5,
            "similarity_boost": 0.75,
        }

    def test_service_creation(self, synthesis_service):
        """Test creating an audio synthesis service."""
        assert synthesis_service is not None
        assert synthesis_service.output_dir.exists()

    def test_synthesize_single_segment(
        self, synthesis_service, sample_voice_config
    ):
        """Test synthesizing a single segment."""
        text = "Hello! This is a test segment."

        result = synthesis_service.synthesize_segment(
            text=text,
            character_id="oliver",
            voice_config=sample_voice_config,
            segment_number=1,
        )

        assert result.segment_number == 1
        assert result.character_id == "oliver"
        assert result.text == text
        assert result.characters == len(text)
        assert result.duration > 0
        assert result.audio_path.exists()
        assert result.audio_path.name == "segment_001_oliver.mp3"

    def test_synthesize_with_emotion(self, synthesis_service, sample_voice_config):
        """Test synthesizing with emotion mapping."""
        voice_config_with_emotion = {
            **sample_voice_config,
            "emotion_mappings": {
                "excited": {"stability": 0.3, "style": 0.8},
            },
        }

        result = synthesis_service.synthesize_segment(
            text="Wow! This is amazing!",
            character_id="oliver",
            voice_config=voice_config_with_emotion,
            segment_number=1,
            emotion="excited",
        )

        assert result is not None
        assert result.audio_path.exists()

    def test_chunk_text_short(self, synthesis_service):
        """Test chunking short text."""
        text = "This is a short text."
        chunks = synthesis_service._chunk_text(text, max_chars=100)

        assert len(chunks) == 1
        assert chunks[0] == text

    def test_chunk_text_long(self, synthesis_service):
        """Test chunking long text at sentence boundaries."""
        sentences = ["First sentence.", "Second sentence.", "Third sentence."]
        text = " ".join(sentences)

        chunks = synthesis_service._chunk_text(text, max_chars=30)

        assert len(chunks) > 1
        # Each chunk should be under max_chars
        for chunk in chunks:
            assert len(chunk) <= 30 or chunk == sentences[0]  # Allow first if can't split

    def test_synthesize_batch(self, synthesis_service, sample_voice_config):
        """Test batch synthesis of multiple segments."""
        segments = [
            {
                "text": "First segment.",
                "character_id": "oliver",
                "voice_config": sample_voice_config,
                "segment_number": 1,
            },
            {
                "text": "Second segment.",
                "character_id": "hannah",
                "voice_config": sample_voice_config,
                "segment_number": 2,
            },
        ]

        results = synthesis_service.synthesize_batch(segments, add_padding=False)

        assert len(results) == 2
        assert results[0].segment_number == 1
        assert results[1].segment_number == 2
        assert results[0].audio_path.exists()
        assert results[1].audio_path.exists()

    def test_synthesize_batch_with_padding(
        self, synthesis_service, sample_voice_config
    ):
        """Test batch synthesis with silence padding."""
        segments = [
            {
                "text": "First segment.",
                "character_id": "oliver",
                "voice_config": sample_voice_config,
                "segment_number": 1,
            },
            {
                "text": "Second segment.",
                "character_id": "hannah",
                "voice_config": sample_voice_config,
                "segment_number": 2,
            },
        ]

        results = synthesis_service.synthesize_batch(segments, add_padding=True)

        # Should have 2 segments + 1 padding (between segments)
        assert len(results) == 3
        assert results[1].character_id == "_padding"

    def test_get_total_duration(self, synthesis_service, sample_voice_config):
        """Test calculating total duration."""
        segments = [
            {
                "text": "First segment.",
                "character_id": "oliver",
                "voice_config": sample_voice_config,
                "segment_number": 1,
            },
            {
                "text": "Second segment.",
                "character_id": "hannah",
                "voice_config": sample_voice_config,
                "segment_number": 2,
            },
        ]

        results = synthesis_service.synthesize_batch(segments, add_padding=False)
        total_duration = synthesis_service.get_total_duration(results)

        assert total_duration > 0
        assert total_duration == sum(r.duration for r in results)

    def test_get_total_cost(self, synthesis_service, sample_voice_config):
        """Test calculating total cost."""
        segments = [
            {
                "text": "First segment.",
                "character_id": "oliver",
                "voice_config": sample_voice_config,
                "segment_number": 1,
            },
        ]

        results = synthesis_service.synthesize_batch(segments)
        total_cost = synthesis_service.get_total_cost(results)

        # Mock provider should be free
        assert total_cost == 0.0
