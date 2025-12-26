"""Audio fixtures for testing."""

from pathlib import Path
from typing import Any

import pytest


@pytest.fixture
def mock_audio_segment() -> dict[str, Any]:
    """Mock audio segment metadata.

    Returns metadata for a single audio segment without actual audio data.
    """
    return {
        "segment_id": 1,
        "character": "narrator",
        "text": "Welcome to our show!",
        "audio_path": "/tmp/mock_segment_001.mp3",
        "duration_seconds": 3.5,
        "sample_rate": 44100,
        "format": "mp3",
    }


@pytest.fixture
def mock_audio_segments_list() -> list[dict[str, Any]]:
    """List of mock audio segments.

    Returns a list of audio segment metadata for testing
    multi-segment audio mixing.
    """
    return [
        {
            "segment_id": 1,
            "character": "narrator",
            "text": "Today we're learning about space!",
            "audio_path": "/tmp/mock_segment_001.mp3",
            "duration_seconds": 4.2,
        },
        {
            "segment_id": 2,
            "character": "oliver",
            "text": "I love space! It's so exciting!",
            "audio_path": "/tmp/mock_segment_002.mp3",
            "duration_seconds": 3.8,
        },
        {
            "segment_id": 3,
            "character": "hannah",
            "text": "Did you know that space is a vacuum?",
            "audio_path": "/tmp/mock_segment_003.mp3",
            "duration_seconds": 4.5,
        },
    ]


@pytest.fixture
def silent_mp3_path(tmp_path: Path) -> Path:
    """Path to a silent MP3 file for testing.

    Note: This returns a path but doesn't create the actual file.
    Tests should create the file if needed or use mocks.
    """
    return tmp_path / "silent.mp3"


@pytest.fixture
def background_music_metadata() -> dict[str, Any]:
    """Background music metadata for testing."""
    return {
        "track_id": "bg_001",
        "title": "Curious Adventures Theme",
        "duration_seconds": 120.0,
        "bpm": 120,
        "mood": "upbeat",
        "volume_adjustment": -12,  # dB
    }


@pytest.fixture
def audio_processing_config() -> dict[str, Any]:
    """Audio processing configuration for testing."""
    return {
        "normalization": {
            "target_loudness": -16,  # LUFS
            "peak_limit": -1,  # dB
        },
        "mixing": {
            "dialogue_volume": 0,  # dB
            "music_volume": -20,  # dB
            "crossfade_duration": 0.5,  # seconds
        },
        "output": {
            "format": "mp3",
            "sample_rate": 44100,
            "bitrate": "192k",
            "channels": "stereo",
        },
    }


@pytest.fixture
def episode_audio_metadata() -> dict[str, Any]:
    """Complete episode audio metadata.

    Returns metadata for a finished episode audio file.
    """
    return {
        "episode_id": "test_ep001",
        "final_audio_path": "/tmp/test_ep001_final.mp3",
        "duration_seconds": 900.0,  # 15 minutes
        "segment_count": 45,
        "has_background_music": True,
        "normalized": True,
        "file_size_mb": 12.5,
    }
