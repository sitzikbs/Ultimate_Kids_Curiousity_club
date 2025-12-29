"""Unit tests for Voice Manager."""

from pathlib import Path

import pytest

from services.tts.factory import TTSProviderFactory
from services.tts.voice_manager import VoiceManager


@pytest.mark.unit
class TestVoiceManager:
    """Tests for VoiceManager."""

    @pytest.fixture
    def mock_provider(self):
        """Create a mock TTS provider."""
        return TTSProviderFactory.create_provider("mock")

    @pytest.fixture
    def voice_manager(self, mock_provider):
        """Create a voice manager."""
        return VoiceManager(tts_provider=mock_provider)

    def test_voice_manager_creation(self, voice_manager):
        """Test creating a voice manager."""
        assert voice_manager is not None

    def test_validate_voice_id_valid(self, voice_manager):
        """Test validating a valid voice ID."""
        assert voice_manager.validate_voice_id("mock_narrator") is True
        assert voice_manager.validate_voice_id("mock_oliver") is True
        assert voice_manager.validate_voice_id("mock_hannah") is True

    def test_validate_voice_id_invalid(self, voice_manager):
        """Test validating an invalid voice ID."""
        assert voice_manager.validate_voice_id("nonexistent_voice") is False

    def test_get_voice_info_valid(self, voice_manager):
        """Test getting info for a valid voice."""
        info = voice_manager.get_voice_info("mock_narrator")
        assert info is not None
        assert info["voice_id"] == "mock_narrator"
        assert info["name"] == "Mock Narrator"

    def test_get_voice_info_invalid(self, voice_manager):
        """Test getting info for an invalid voice."""
        info = voice_manager.get_voice_info("nonexistent_voice")
        assert info is None

    def test_list_available_voices(self, voice_manager):
        """Test listing available voices."""
        voices = voice_manager.list_available_voices()
        assert len(voices) > 0
        assert any(v["voice_id"] == "mock_narrator" for v in voices)

    def test_map_emotion_to_params_excited(self, voice_manager):
        """Test mapping excited emotion to parameters."""
        params = voice_manager.map_emotion_to_params("excited")
        assert "stability" in params
        assert params["stability"] == 0.3

    def test_map_emotion_to_params_calm(self, voice_manager):
        """Test mapping calm emotion to parameters."""
        params = voice_manager.map_emotion_to_params("calm")
        assert "stability" in params
        assert params["stability"] == 0.7

    def test_map_emotion_to_params_with_base(self, voice_manager):
        """Test mapping emotion with base parameters."""
        base_params = {"similarity_boost": 0.8, "stability": 0.5}
        params = voice_manager.map_emotion_to_params("excited", base_params)

        # Emotion params should override base
        assert params["stability"] == 0.3
        # Base params should be preserved if not in emotion mapping
        assert params["similarity_boost"] == 0.8

    def test_map_emotion_unknown(self, voice_manager):
        """Test mapping unknown emotion returns empty."""
        params = voice_manager.map_emotion_to_params("unknown_emotion")
        assert params == {}

    def test_preview_voice_no_sample_dir(self, voice_manager):
        """Test preview voice fails without sample directory."""
        with pytest.raises(ValueError, match="sample_dir must be set"):
            voice_manager.preview_voice("mock_narrator")

    def test_preview_voice_with_sample_dir(self, mock_provider, tmp_path: Path):
        """Test preview voice with sample directory."""
        voice_manager = VoiceManager(
            tts_provider=mock_provider,
            sample_dir=tmp_path / "samples",
        )

        preview_path = voice_manager.preview_voice(
            voice_id="mock_narrator",
            sample_text="This is a test.",
        )

        assert preview_path.exists()
        assert preview_path.name == "mock_narrator_preview.mp3"

    def test_validate_voice_config_valid(self, voice_manager):
        """Test validating a valid voice config."""
        config = {
            "voice_id": "mock_narrator",
            "stability": 0.5,
            "similarity_boost": 0.75,
        }

        is_valid, error = voice_manager.validate_voice_config(config)
        assert is_valid is True
        assert error == ""

    def test_validate_voice_config_missing_voice_id(self, voice_manager):
        """Test validating config without voice_id."""
        config = {"stability": 0.5}

        is_valid, error = voice_manager.validate_voice_config(config)
        assert is_valid is False
        assert "voice_id" in error

    def test_validate_voice_config_invalid_voice_id(self, voice_manager):
        """Test validating config with invalid voice_id."""
        config = {"voice_id": "nonexistent_voice"}

        is_valid, error = voice_manager.validate_voice_config(config)
        assert is_valid is False
        assert "not found" in error

    def test_validate_voice_config_invalid_stability(self, voice_manager):
        """Test validating config with invalid stability."""
        config = {
            "voice_id": "mock_narrator",
            "stability": 1.5,  # Out of range
        }

        is_valid, error = voice_manager.validate_voice_config(config)
        assert is_valid is False
        assert "stability" in error

    def test_validate_voice_config_invalid_similarity_boost(self, voice_manager):
        """Test validating config with invalid similarity_boost."""
        config = {
            "voice_id": "mock_narrator",
            "similarity_boost": -0.1,  # Out of range
        }

        is_valid, error = voice_manager.validate_voice_config(config)
        assert is_valid is False
        assert "similarity_boost" in error

    def test_clone_voice_not_supported(self, voice_manager, tmp_path: Path):
        """Test voice cloning with unsupported provider."""
        with pytest.raises(NotImplementedError, match="not supported"):
            voice_manager.clone_voice(
                name="Test Voice",
                description="A test voice",
                reference_audio_path=tmp_path / "audio.mp3",
            )
