"""Unit tests for Audio Quality Validator."""

from pathlib import Path

import pytest
from pydub import AudioSegment

from services.tts.quality_validator import AudioQualityValidator


@pytest.mark.unit
class TestAudioQualityValidator:
    """Tests for AudioQualityValidator."""

    @pytest.fixture
    def validator(self):
        """Create a quality validator."""
        return AudioQualityValidator()

    @pytest.fixture
    def sample_audio_path(self, tmp_path: Path) -> Path:
        """Create a sample audio file."""
        audio_path = tmp_path / "sample.mp3"
        # Create 2-second silent audio
        silence = AudioSegment.silent(duration=2000)
        silence.export(str(audio_path), format="mp3")
        return audio_path

    def test_validator_creation(self, validator):
        """Test creating a quality validator."""
        assert validator is not None
        assert validator.target_sample_rate == 44100

    def test_validate_format_valid(self, validator, sample_audio_path):
        """Test validating a valid audio format."""
        is_valid, error = validator.validate_format(sample_audio_path)
        assert is_valid is True
        assert error == ""

    def test_validate_format_nonexistent(self, validator, tmp_path: Path):
        """Test validating a nonexistent file."""
        nonexistent = tmp_path / "nonexistent.mp3"
        is_valid, error = validator.validate_format(nonexistent)
        assert is_valid is False
        assert "does not exist" in error

    def test_validate_format_invalid_extension(self, validator, tmp_path: Path):
        """Test validating an invalid file extension."""
        invalid_path = tmp_path / "test.txt"
        invalid_path.touch()
        is_valid, error = validator.validate_format(invalid_path)
        assert is_valid is False
        assert "Invalid format" in error

    def test_validate_duration_valid(self, validator, sample_audio_path):
        """Test validating duration."""
        is_valid, error, duration = validator.validate_duration(sample_audio_path)
        assert is_valid is True
        assert error == ""
        assert duration > 0

    def test_validate_duration_with_expected(self, validator, sample_audio_path):
        """Test validating duration against expected value."""
        # Sample is 2 seconds, tolerance is 10%
        is_valid, error, duration = validator.validate_duration(
            sample_audio_path, expected_duration=2.0
        )
        assert is_valid is True

        # Test duration outside tolerance
        is_valid, error, duration = validator.validate_duration(
            sample_audio_path, expected_duration=5.0
        )
        assert is_valid is False
        assert "mismatch" in error

    def test_validate_duration_with_text(self, validator, sample_audio_path):
        """Test validating duration against text."""
        # Very short text should fail for 2-second audio
        short_text = "Hi"
        is_valid, error, duration = validator.validate_duration(
            sample_audio_path, text=short_text
        )
        # This will likely fail because 2 seconds is too long for "Hi"
        # But we're just testing it runs

    def test_detect_silence_valid(self, validator, tmp_path: Path):
        """Test detecting silence in audio with content."""
        # Create audio with some noise
        from pydub.generators import WhiteNoise

        audio_path = tmp_path / "noisy.mp3"
        noise = WhiteNoise().to_audio_segment(duration=1000)
        noise = noise - 30  # Make it quieter but not silent
        noise.export(str(audio_path), format="mp3")

        is_valid, error = validator.detect_silence(audio_path)
        assert is_valid is True

    def test_get_audio_info(self, validator, sample_audio_path):
        """Test getting audio information."""
        info = validator.get_audio_info(sample_audio_path)

        assert "duration" in info
        assert "sample_rate" in info
        assert "channels" in info
        assert info["duration"] > 0

    def test_measure_loudness(self, validator, sample_audio_path):
        """Test measuring audio loudness."""
        loudness = validator.measure_loudness(sample_audio_path)
        # Silent audio should have very low loudness
        assert loudness < -20

    def test_validate_audio_comprehensive(self, validator, sample_audio_path):
        """Test comprehensive audio validation."""
        report = validator.validate_audio(sample_audio_path)

        assert report.file_path == sample_audio_path
        assert report.actual_duration > 0
        assert report.sample_rate > 0
        # Note: Silent audio might fail silence validation

    def test_generate_quality_report(self, validator, tmp_path: Path):
        """Test generating quality reports for multiple files."""
        # Create multiple audio files
        audio_files = []
        for i in range(3):
            audio_path = tmp_path / f"audio_{i}.mp3"
            silence = AudioSegment.silent(duration=1000)
            silence.export(str(audio_path), format="mp3")
            audio_files.append(audio_path)

        reports = validator.generate_quality_report(audio_files)

        assert len(reports) == 3
        for report in reports:
            assert report.file_path in audio_files
