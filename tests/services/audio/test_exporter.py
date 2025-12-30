"""Unit tests for MP3Exporter."""

from datetime import datetime
from pathlib import Path

import pytest
from mutagen.easyid3 import EasyID3
from mutagen.id3 import ID3
from pydub import AudioSegment

from services.audio.exporter import MP3Exporter


@pytest.fixture
def exporter():
    """Create default MP3Exporter instance."""
    return MP3Exporter()


@pytest.fixture
def custom_exporter():
    """Create MP3Exporter with custom settings."""
    return MP3Exporter(bitrate="128k", quality="2")


@pytest.fixture
def sample_audio():
    """Create sample audio for testing."""
    return AudioSegment.silent(duration=2000)


@pytest.fixture
def sample_metadata():
    """Create sample metadata for testing."""
    return {
        "title": "Test Episode",
        "artist": "Kids Curiosity Club",
        "album": "Test Album",
        "genre": "Educational",
        "year": 2024,
        "comment": "Test comment",
    }


@pytest.fixture
def sample_album_art(tmp_path):
    """Create sample album art image."""
    from PIL import Image

    img_path = tmp_path / "album_art.png"
    img = Image.new("RGB", (300, 300), color="blue")
    img.save(img_path)
    return img_path


class TestMP3Exporter:
    """Tests for MP3Exporter class."""

    def test_init_default(self):
        """Test MP3Exporter initialization with defaults."""
        exporter = MP3Exporter()
        assert exporter.bitrate == "192k"
        assert exporter.quality == "0"

    def test_init_custom(self):
        """Test MP3Exporter initialization with custom values."""
        exporter = MP3Exporter(bitrate="128k", quality="2")
        assert exporter.bitrate == "128k"
        assert exporter.quality == "2"

    def test_export_basic(self, exporter, sample_audio, tmp_path):
        """Test basic audio export without metadata."""
        output_path = tmp_path / "test_output.mp3"
        exporter.export(sample_audio, output_path)

        assert output_path.exists()
        # Verify it's a valid MP3
        loaded = AudioSegment.from_mp3(str(output_path))
        assert len(loaded) > 0

    def test_export_with_metadata(
        self, exporter, sample_audio, sample_metadata, tmp_path
    ):
        """Test audio export with ID3 metadata."""
        output_path = tmp_path / "test_output.mp3"
        exporter.export(sample_audio, output_path, metadata=sample_metadata)

        assert output_path.exists()

        # Verify ID3 tags
        audio_file = EasyID3(str(output_path))
        assert audio_file["title"][0] == "Test Episode"
        assert audio_file["artist"][0] == "Kids Curiosity Club"
        assert audio_file["album"][0] == "Test Album"
        assert audio_file["genre"][0] == "Educational"

    def test_export_with_album_art(
        self, exporter, sample_audio, sample_album_art, tmp_path
    ):
        """Test audio export with album art."""
        output_path = tmp_path / "test_output.mp3"
        exporter.export(
            sample_audio, output_path, metadata={"title": "Test"}, album_art_path=sample_album_art
        )

        assert output_path.exists()

        # Verify album art is embedded
        audio_file = ID3(str(output_path))
        assert "APIC" in audio_file

    def test_export_with_generation_metadata(
        self, exporter, sample_audio, tmp_path
    ):
        """Test export with generation metadata in comment."""
        metadata = {
            "title": "Test Episode",
            "generation_metadata": {
                "date": "2024-01-01",
                "cost": 1.50,
                "models": ["gpt-4", "elevenlabs"],
            },
        }
        output_path = tmp_path / "test_output.mp3"
        exporter.export(sample_audio, output_path, metadata=metadata)

        assert output_path.exists()

        # Verify comment contains generation metadata
        audio_file = EasyID3(str(output_path))
        assert "comment" in audio_file
        comment = audio_file["comment"][0]
        assert "Generated" in comment
        assert "Cost" in comment
        assert "Models" in comment

    def test_export_creates_directory(self, exporter, sample_audio, tmp_path):
        """Test that export creates output directory if needed."""
        output_path = tmp_path / "subdir" / "test_output.mp3"
        exporter.export(sample_audio, output_path)

        assert output_path.exists()
        assert output_path.parent.exists()

    def test_add_album_art_nonexistent_file(
        self, exporter, sample_audio, tmp_path
    ):
        """Test adding album art with nonexistent file raises error."""
        output_path = tmp_path / "test_output.mp3"
        exporter.export(sample_audio, output_path)

        with pytest.raises(ValueError, match="Album art file not found"):
            exporter._add_album_art(output_path, Path("/nonexistent/image.png"))

    def test_get_mime_type(self, exporter):
        """Test MIME type detection from file extension."""
        assert exporter._get_mime_type(Path("test.png")) == "image/png"
        assert exporter._get_mime_type(Path("test.jpg")) == "image/jpeg"
        assert exporter._get_mime_type(Path("test.jpeg")) == "image/jpeg"
        assert exporter._get_mime_type(Path("test.gif")) == "image/gif"
        assert exporter._get_mime_type(Path("test.bmp")) == "image/bmp"
        assert exporter._get_mime_type(Path("test.unknown")) == "image/jpeg"  # default

    def test_export_with_custom_bitrate(
        self, custom_exporter, sample_audio, tmp_path
    ):
        """Test export with custom bitrate."""
        output_path = tmp_path / "test_output.mp3"
        custom_exporter.export(sample_audio, output_path)

        assert output_path.exists()
        assert custom_exporter.bitrate == "128k"
