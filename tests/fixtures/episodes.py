"""Episode fixtures for testing."""

from datetime import datetime
from typing import Any

import pytest


@pytest.fixture
def new_episode() -> dict[str, Any]:
    """New episode in IDEATION status.

    Returns a dictionary representing a newly created episode
    at the beginning of the production pipeline.
    """
    return {
        "id": "test_ep001",
        "title": "How Rockets Work",
        "topic": "Space exploration and rocket science",
        "duration_minutes": 15,
        "characters": ["oliver", "hannah"],
        "status": "IDEATION",
        "created_at": datetime.now().isoformat(),
        "updated_at": datetime.now().isoformat(),
        "checkpoints": {},
    }


@pytest.fixture
def scripting_episode(new_episode: dict[str, Any]) -> dict[str, Any]:
    """Episode in SCRIPTING status with completed ideation.

    Returns an episode that has completed ideation phase and is ready
    for script generation.
    """
    episode = new_episode.copy()
    episode["status"] = "SCRIPTING"
    episode["checkpoints"] = {
        "ideation": {
            "completed_at": "2024-01-15T10:05:00Z",
            "output": {
                "refined_topic": "How Rockets Work and Space Travel",
                "learning_objectives": [
                    "Newton's Third Law of Motion",
                    "Different types of rocket fuel",
                    "Living in space",
                ],
                "key_points": [
                    "Rockets push gas down to go up",
                    "Fuel is stored in big tanks",
                    "No air in space",
                    "Astronauts need special suits",
                    "Rockets go really fast",
                ],
            },
        }
    }
    return episode


@pytest.fixture
def audio_synthesis_episode(scripting_episode: dict[str, Any]) -> dict[str, Any]:
    """Episode in AUDIO_SYNTHESIS status with completed script.

    Returns an episode with completed script ready for audio generation.
    """
    episode = scripting_episode.copy()
    episode["status"] = "AUDIO_SYNTHESIS"
    episode["checkpoints"]["scripting"] = {
        "completed_at": "2024-01-15T10:10:00Z",
        "output": {
            "segments": [
                {
                    "segment_id": 1,
                    "character": "narrator",
                    "text": "Have you ever wondered how rockets fly to space?",
                },
                {
                    "segment_id": 2,
                    "character": "oliver",
                    "text": "I think about it all the time!",
                },
            ]
        },
    }
    return episode


@pytest.fixture
def complete_episode(audio_synthesis_episode: dict[str, Any]) -> dict[str, Any]:
    """Completed episode with all checkpoints.

    Returns a fully completed episode with all production stages finished.
    """
    episode = audio_synthesis_episode.copy()
    episode["status"] = "COMPLETE"
    episode["checkpoints"]["audio_synthesis"] = {
        "completed_at": "2024-01-15T10:20:00Z",
        "audio_segments": [
            {"segment_id": 1, "audio_path": "data/audio/test_ep001/segment_001.mp3"},
            {"segment_id": 2, "audio_path": "data/audio/test_ep001/segment_002.mp3"},
        ],
    }
    episode["checkpoints"]["audio_mixing"] = {
        "completed_at": "2024-01-15T10:25:00Z",
        "final_audio_path": "data/audio/test_ep001/final.mp3",
    }
    return episode


@pytest.fixture
def episode_with_show_blueprint() -> dict[str, Any]:
    """Episode with Show Blueprint data included.

    Returns an episode that includes full Show Blueprint context with
    protagonist, world building, and character details.
    """
    return {
        "id": "test_ep002",
        "title": "The Mystery of Ancient Egypt",
        "topic": "Egyptian pyramids and pharaohs",
        "duration_minutes": 20,
        "characters": ["hannah", "narrator"],
        "status": "IDEATION",
        "created_at": datetime.now().isoformat(),
        "show_blueprint": {
            "protagonist": {
                "name": "Hannah the Historian",
                "core_traits": ["Curious", "Analytical", "Storyteller"],
            },
            "world": {
                "setting": "Educational adventure world",
                "tone": "Friendly and encouraging",
            },
            "learning_approach": "Discovery through storytelling",
        },
    }


@pytest.fixture
def episodes_list(
    new_episode: dict[str, Any],
    scripting_episode: dict[str, Any],
    complete_episode: dict[str, Any],
) -> list[dict[str, Any]]:
    """List of episodes at various stages."""
    return [new_episode, scripting_episode, complete_episode]
