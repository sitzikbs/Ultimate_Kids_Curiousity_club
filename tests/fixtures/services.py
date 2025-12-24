"""Service fixtures for testing (mock services)."""

from typing import Any
from unittest.mock import MagicMock

import pytest


@pytest.fixture
def mock_llm_service() -> MagicMock:
    """Mock LLM service for testing.

    Returns a mock LLM service that simulates API calls without
    incurring costs.
    """
    mock = MagicMock()

    # Mock ideation response
    mock.refine_topic.return_value = {
        "refined_topic": "How Airplanes Fly Through the Sky",
        "learning_objectives": [
            "Understanding lift and air pressure",
            "Parts of an airplane",
            "History of flight",
        ],
        "key_points": [
            "Wings create lift",
            "Engines provide thrust",
            "Pilots control the plane",
            "Airplanes need runways",
            "Flying is safe and amazing",
        ],
    }

    # Mock scripting response
    mock.generate_script.return_value = {
        "segments": [
            {
                "segment_id": 1,
                "character": "narrator",
                "text": "Today we're learning about airplanes!",
            },
            {
                "segment_id": 2,
                "character": "oliver",
                "text": "I love airplanes! Let me tell you how they work.",
            },
        ]
    }

    return mock


@pytest.fixture
def mock_tts_service() -> MagicMock:
    """Mock Text-to-Speech service for testing.

    Returns a mock TTS service that simulates audio generation
    without calling real APIs.
    """
    mock = MagicMock()

    # Mock audio synthesis - returns path to mock audio file
    mock.synthesize_speech.return_value = {
        "audio_path": "/tmp/mock_audio.mp3",
        "duration_seconds": 5.0,
    }

    mock.get_voice_list.return_value = [
        {"voice_id": "mock_oliver", "name": "Oliver Voice"},
        {"voice_id": "mock_hannah", "name": "Hannah Voice"},
        {"voice_id": "mock_narrator", "name": "Narrator Voice"},
    ]

    return mock


@pytest.fixture
def mock_audio_mixer() -> MagicMock:
    """Mock audio mixer service for testing.

    Returns a mock audio mixer that simulates combining audio segments
    without actual audio processing.
    """
    mock = MagicMock()

    # Mock mixing result
    mock.mix_segments.return_value = {
        "final_audio_path": "/tmp/final_episode.mp3",
        "total_duration_seconds": 900.0,  # 15 minutes
    }

    mock.add_background_music.return_value = True
    mock.normalize_audio.return_value = True

    return mock


@pytest.fixture
def mock_image_service() -> MagicMock:
    """Mock image generation service for testing.

    Returns a mock image service that simulates image generation
    without calling real APIs.
    """
    mock = MagicMock()

    mock.generate_image.return_value = {
        "image_path": "/tmp/mock_image.png",
        "width": 1024,
        "height": 1024,
    }

    return mock


@pytest.fixture
def mock_orchestrator(
    mock_llm_service: MagicMock,
    mock_tts_service: MagicMock,
    mock_audio_mixer: MagicMock,
) -> MagicMock:
    """Mock orchestrator with all service dependencies.

    Returns a complete mock orchestrator that coordinates all services
    for end-to-end episode production testing.
    """
    orchestrator = MagicMock()
    orchestrator.llm_service = mock_llm_service
    orchestrator.tts_service = mock_tts_service
    orchestrator.audio_mixer = mock_audio_mixer

    # Mock full pipeline execution
    orchestrator.produce_episode.return_value = {
        "episode_id": "test_ep001",
        "status": "COMPLETE",
        "final_audio_path": "/tmp/final_episode.mp3",
        "duration_seconds": 900.0,
    }

    return orchestrator


@pytest.fixture
def service_settings() -> dict[str, Any]:
    """Service configuration settings for testing."""
    return {
        "llm": {
            "provider": "mock",
            "model": "mock-gpt-4",
            "temperature": 0.7,
            "max_tokens": 2000,
        },
        "tts": {
            "provider": "mock",
            "default_voice": "mock_narrator",
        },
        "audio": {
            "output_format": "mp3",
            "sample_rate": 44100,
            "bitrate": "192k",
        },
    }
