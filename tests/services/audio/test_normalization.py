"""Unit tests for LoudnessNormalizer."""

import pytest
from pydub import AudioSegment

from services.audio.normalization import LoudnessNormalizer


@pytest.fixture
def normalizer():
    """Create default LoudnessNormalizer instance."""
    return LoudnessNormalizer()


@pytest.fixture
def custom_normalizer():
    """Create LoudnessNormalizer with custom target."""
    return LoudnessNormalizer(target_lufs=-18.0, sample_rate=48000)


@pytest.fixture
def sample_audio():
    """Create sample audio for testing."""
    # Create 2 seconds of silence with some volume
    return AudioSegment.silent(duration=2000) + 10


class TestLoudnessNormalizer:
    """Tests for LoudnessNormalizer class."""

    def test_init_default(self):
        """Test LoudnessNormalizer initialization with defaults."""
        normalizer = LoudnessNormalizer()
        assert normalizer.target_lufs == -16.0
        assert normalizer.sample_rate == 44100

    def test_init_custom(self):
        """Test LoudnessNormalizer initialization with custom values."""
        normalizer = LoudnessNormalizer(target_lufs=-18.0, sample_rate=48000)
        assert normalizer.target_lufs == -18.0
        assert normalizer.sample_rate == 48000

    def test_normalize(self, normalizer, sample_audio):
        """Test audio normalization."""
        result = normalizer.normalize(sample_audio)
        assert isinstance(result, AudioSegment)
        assert len(result) == len(sample_audio)

    def test_measure_loudness(self, normalizer, sample_audio):
        """Test loudness measurement."""
        loudness = normalizer.measure_loudness(sample_audio)
        assert isinstance(loudness, float)
        # Loudness should be negative (in LUFS)
        assert loudness < 0

    def test_get_loudness_stats(self, normalizer, sample_audio):
        """Test getting loudness statistics."""
        stats = normalizer.get_loudness_stats(sample_audio)
        assert isinstance(stats, dict)
        assert "integrated_lufs" in stats
        assert "peak_db" in stats
        assert "rms_db" in stats
        assert "target_lufs" in stats
        assert "gain_needed_db" in stats

    def test_apply_limiter(self, normalizer, sample_audio):
        """Test peak limiter application."""
        # Create loud audio that needs limiting
        loud_audio = sample_audio + 20  # Make it very loud
        result = normalizer._apply_limiter(loud_audio, threshold_db=-1.0)
        assert isinstance(result, AudioSegment)
        # Peak should be at or below threshold
        assert result.max_dBFS <= -1.0

    def test_normalize_with_custom_target(self, custom_normalizer, sample_audio):
        """Test normalization with custom target LUFS."""
        result = custom_normalizer.normalize(sample_audio)
        assert isinstance(result, AudioSegment)
        # Verify target is set correctly
        assert custom_normalizer.target_lufs == -18.0
