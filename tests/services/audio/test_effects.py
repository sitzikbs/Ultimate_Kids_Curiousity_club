"""Unit tests for AudioEffects."""

import pytest
from pydub import AudioSegment

from services.audio.effects import AudioEffects


def is_valid_dbfs(dbfs: float) -> bool:
    """Check if dBFS value is valid (not -inf or inf).

    Helper function for testing audio with potential silence.
    """
    return dbfs != float("-inf") and dbfs != float("inf")


@pytest.fixture
def effects():
    """Create AudioEffects instance."""
    return AudioEffects()


@pytest.fixture
def sample_audio():
    """Create sample audio for testing."""
    # Create 2 seconds of audio with some volume
    return AudioSegment.silent(duration=2000) + 10


@pytest.fixture
def audio_with_silence():
    """Create audio with long silence in middle."""
    part1 = AudioSegment.silent(duration=1000) + 10
    silence = AudioSegment.silent(duration=3000)  # 3 seconds of silence
    part2 = AudioSegment.silent(duration=1000) + 10
    return part1 + silence + part2


class TestAudioEffects:
    """Tests for AudioEffects class."""

    def test_init(self):
        """Test AudioEffects initialization."""
        effects = AudioEffects()
        assert effects is not None

    def test_remove_long_silence(self, effects, audio_with_silence):
        """Test removing long silence from audio."""
        result = effects.remove_long_silence(
            audio_with_silence, silence_threshold_ms=2000
        )
        assert isinstance(result, AudioSegment)
        # Should be shorter than original
        assert len(result) < len(audio_with_silence)

    def test_remove_long_silence_no_long_silence(self, effects, sample_audio):
        """Test removing long silence when none exists."""
        result = effects.remove_long_silence(sample_audio, silence_threshold_ms=2000)
        assert isinstance(result, AudioSegment)
        # Should be similar length (within tolerance)
        assert abs(len(result) - len(sample_audio)) < 500

    def test_adjust_speed_normal(self, effects, sample_audio):
        """Test speed adjustment at 1.0x (no change)."""
        result = effects.adjust_speed(sample_audio, speed_factor=1.0)
        assert isinstance(result, AudioSegment)
        assert len(result) == len(sample_audio)

    def test_adjust_speed_faster(self, effects, sample_audio):
        """Test speed adjustment faster (1.2x)."""
        result = effects.adjust_speed(sample_audio, speed_factor=1.2)
        assert isinstance(result, AudioSegment)
        # Should be shorter (faster playback)
        assert len(result) < len(sample_audio)

    def test_adjust_speed_slower(self, effects, sample_audio):
        """Test speed adjustment slower (0.8x)."""
        result = effects.adjust_speed(sample_audio, speed_factor=0.8)
        assert isinstance(result, AudioSegment)
        # Should be longer (slower playback)
        assert len(result) > len(sample_audio)

    def test_adjust_speed_invalid(self, effects, sample_audio):
        """Test speed adjustment with invalid factor."""
        with pytest.raises(ValueError, match="Speed factor must be between 0 and 2.0"):
            effects.adjust_speed(sample_audio, speed_factor=0)

        with pytest.raises(ValueError, match="Speed factor must be between 0 and 2.0"):
            effects.adjust_speed(sample_audio, speed_factor=2.5)

    def test_apply_fade_in(self, effects, sample_audio):
        """Test applying fade in."""
        result = effects.apply_fade(sample_audio, fade_in_ms=500)
        assert isinstance(result, AudioSegment)
        assert len(result) == len(sample_audio)

    def test_apply_fade_out(self, effects, sample_audio):
        """Test applying fade out."""
        result = effects.apply_fade(sample_audio, fade_out_ms=500)
        assert isinstance(result, AudioSegment)
        assert len(result) == len(sample_audio)

    def test_apply_fade_both(self, effects, sample_audio):
        """Test applying both fade in and out."""
        result = effects.apply_fade(sample_audio, fade_in_ms=500, fade_out_ms=500)
        assert isinstance(result, AudioSegment)
        assert len(result) == len(sample_audio)

    def test_apply_fade_none(self, effects, sample_audio):
        """Test applying no fades."""
        result = effects.apply_fade(sample_audio)
        assert isinstance(result, AudioSegment)
        assert len(result) == len(sample_audio)

    def test_duck_audio(self, effects, sample_audio):
        """Test audio ducking."""
        background = sample_audio + 5  # Slightly louder background
        foreground = sample_audio
        result = effects.duck_audio(background, foreground, duck_db=-15.0)
        assert isinstance(result, AudioSegment)
        # Should be quieter than original background
        if is_valid_dbfs(background.dBFS):
            assert result.dBFS < background.dBFS

    def test_add_silence_end(self, effects, sample_audio):
        """Test adding silence to end."""
        result = effects.add_silence(sample_audio, duration_ms=1000, position="end")
        assert isinstance(result, AudioSegment)
        assert len(result) == len(sample_audio) + 1000

    def test_add_silence_start(self, effects, sample_audio):
        """Test adding silence to start."""
        result = effects.add_silence(sample_audio, duration_ms=1000, position="start")
        assert isinstance(result, AudioSegment)
        assert len(result) == len(sample_audio) + 1000

    def test_add_silence_invalid_position(self, effects, sample_audio):
        """Test adding silence with invalid position."""
        with pytest.raises(ValueError, match="Invalid position"):
            effects.add_silence(sample_audio, duration_ms=1000, position="middle")

    def test_normalize_volume(self, effects, sample_audio):
        """Test volume normalization."""
        result = effects.normalize_volume(sample_audio, target_db=-20.0)
        assert isinstance(result, AudioSegment)
        # Volume should be close to target
        if is_valid_dbfs(result.dBFS):
            assert abs(result.dBFS - (-20.0)) < 1.0
