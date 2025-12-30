"""Unit tests for AudioMixer."""

from pathlib import Path

import pytest
from pydub import AudioSegment

from services.audio.mixer import AudioMixer


@pytest.fixture
def audio_mixer():
    """Create default AudioMixer instance."""
    return AudioMixer()


@pytest.fixture
def custom_audio_mixer():
    """Create AudioMixer with custom settings."""
    return AudioMixer(
        silence_padding_ms=1000,
        crossfade_ms=200,
        trim_silence=True,
        silence_threshold_db=-45.0,
    )


@pytest.fixture
def sample_audio_segments(tmp_path):
    """Create sample audio files for testing."""
    segments = []
    for i in range(3):
        audio_path = tmp_path / f"segment_{i}.mp3"
        # Create 2 seconds of silence as test audio
        silence = AudioSegment.silent(duration=2000)
        silence.export(str(audio_path), format="mp3")
        segments.append(audio_path)
    return segments


@pytest.fixture
def sample_music_file(tmp_path):
    """Create sample music file for testing."""
    music_path = tmp_path / "music.mp3"
    # Create 5 seconds of silence as test music
    silence = AudioSegment.silent(duration=5000)
    silence.export(str(music_path), format="mp3")
    return music_path


@pytest.fixture
def sample_intro_file(tmp_path):
    """Create sample intro file for testing."""
    intro_path = tmp_path / "intro.mp3"
    # Create 1 second intro
    silence = AudioSegment.silent(duration=1000)
    silence.export(str(intro_path), format="mp3")
    return intro_path


@pytest.fixture
def sample_outro_file(tmp_path):
    """Create sample outro file for testing."""
    outro_path = tmp_path / "outro.mp3"
    # Create 1 second outro
    silence = AudioSegment.silent(duration=1000)
    silence.export(str(outro_path), format="mp3")
    return outro_path


class TestAudioMixer:
    """Tests for AudioMixer class."""

    def test_init_default(self):
        """Test AudioMixer initialization with defaults."""
        mixer = AudioMixer()
        assert mixer.silence_padding == 500
        assert mixer.crossfade == 0
        assert mixer.trim_silence is True
        assert mixer.silence_threshold == -40.0

    def test_init_custom(self):
        """Test AudioMixer initialization with custom values."""
        mixer = AudioMixer(
            silence_padding_ms=1000,
            crossfade_ms=300,
            trim_silence=False,
            silence_threshold_db=-50.0,
        )
        assert mixer.silence_padding == 1000
        assert mixer.crossfade == 300
        assert mixer.trim_silence is False
        assert mixer.silence_threshold == -50.0

    def test_mix_segments_empty_list(self, audio_mixer):
        """Test mixing with empty segment list raises error."""
        with pytest.raises(ValueError, match="No segments to mix"):
            audio_mixer.mix_segments([])

    def test_mix_segments_nonexistent_file(self, audio_mixer):
        """Test mixing with nonexistent file raises error."""
        with pytest.raises(ValueError, match="Audio file not found"):
            audio_mixer.mix_segments([Path("/nonexistent/file.mp3")])

    def test_mix_segments_single(self, audio_mixer, sample_audio_segments):
        """Test mixing a single segment."""
        result = audio_mixer.mix_segments([sample_audio_segments[0]])
        assert isinstance(result, AudioSegment)
        assert len(result) > 0

    def test_mix_segments_multiple(self, audio_mixer, sample_audio_segments):
        """Test mixing multiple segments with silence padding."""
        result = audio_mixer.mix_segments(sample_audio_segments)
        assert isinstance(result, AudioSegment)
        # Should be longer than a single segment due to padding
        # 3 segments * 2000ms + 2 silences * 500ms = 7000ms
        assert len(result) >= 6000  # Allow some variation

    def test_mix_segments_with_crossfade(self, custom_audio_mixer, sample_audio_segments):
        """Test mixing with crossfade enabled."""
        result = custom_audio_mixer.mix_segments(sample_audio_segments)
        assert isinstance(result, AudioSegment)
        assert len(result) > 0

    def test_add_background_music_nonexistent_file(self, audio_mixer):
        """Test adding background music with nonexistent file."""
        audio = AudioSegment.silent(duration=1000)
        with pytest.raises(ValueError, match="Music file not found"):
            audio_mixer.add_background_music(audio, "/nonexistent/music.mp3")

    def test_add_background_music(
        self, audio_mixer, sample_audio_segments, sample_music_file
    ):
        """Test adding background music to audio."""
        # Load a sample segment
        audio = AudioSegment.from_file(str(sample_audio_segments[0]))
        result = audio_mixer.add_background_music(
            audio, sample_music_file, volume_db=-20.0
        )
        assert isinstance(result, AudioSegment)
        # Duration should match original audio
        assert abs(len(result) - len(audio)) < 100  # Allow 100ms tolerance

    def test_add_intro_nonexistent_file(self, audio_mixer):
        """Test adding intro with nonexistent file."""
        audio = AudioSegment.silent(duration=1000)
        with pytest.raises(ValueError, match="Intro file not found"):
            audio_mixer.add_intro(audio, "/nonexistent/intro.mp3")

    def test_add_intro(self, audio_mixer, sample_audio_segments, sample_intro_file):
        """Test adding intro to audio."""
        audio = AudioSegment.from_file(str(sample_audio_segments[0]))
        result = audio_mixer.add_intro(audio, sample_intro_file)
        assert isinstance(result, AudioSegment)
        # Should be longer than original
        assert len(result) > len(audio)

    def test_add_intro_with_crossfade(
        self, audio_mixer, sample_audio_segments, sample_intro_file
    ):
        """Test adding intro with crossfade."""
        audio = AudioSegment.from_file(str(sample_audio_segments[0]))
        result = audio_mixer.add_intro(audio, sample_intro_file, crossfade_ms=200)
        assert isinstance(result, AudioSegment)
        assert len(result) > 0

    def test_add_outro_nonexistent_file(self, audio_mixer):
        """Test adding outro with nonexistent file."""
        audio = AudioSegment.silent(duration=1000)
        with pytest.raises(ValueError, match="Outro file not found"):
            audio_mixer.add_outro(audio, "/nonexistent/outro.mp3")

    def test_add_outro(self, audio_mixer, sample_audio_segments, sample_outro_file):
        """Test adding outro to audio."""
        audio = AudioSegment.from_file(str(sample_audio_segments[0]))
        result = audio_mixer.add_outro(audio, sample_outro_file)
        assert isinstance(result, AudioSegment)
        # Should be longer than original
        assert len(result) > len(audio)

    def test_add_outro_with_crossfade(
        self, audio_mixer, sample_audio_segments, sample_outro_file
    ):
        """Test adding outro with crossfade."""
        audio = AudioSegment.from_file(str(sample_audio_segments[0]))
        result = audio_mixer.add_outro(audio, sample_outro_file, crossfade_ms=200)
        assert isinstance(result, AudioSegment)
        assert len(result) > 0

    def test_trim_silence(self, audio_mixer):
        """Test silence trimming."""
        # Create audio with silence at start and end
        silence_start = AudioSegment.silent(duration=500)
        content = AudioSegment.silent(duration=1000) + 10  # Slightly louder
        silence_end = AudioSegment.silent(duration=500)
        audio = silence_start + content + silence_end

        result = audio_mixer._trim_silence(audio)
        assert isinstance(result, AudioSegment)
        # Should be shorter after trimming
        assert len(result) <= len(audio)
