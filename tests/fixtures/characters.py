"""Character fixtures for testing."""

from typing import Any

import pytest


@pytest.fixture
def oliver_character() -> dict[str, Any]:
    """Oliver the Inventor character fixture.

    Returns a dictionary representing Oliver, a curious 10-year-old inventor
    who loves building things and explaining how mechanisms work.
    """
    return {
        "id": "oliver",
        "name": "Oliver the Inventor",
        "age": 10,
        "personality": "Curious inventor who loves building things",
        "speaking_style": "Uses simple technical words, gets excited about mechanisms",
        "vocabulary_level": "INTERMEDIATE",
        "voice_config": {
            "provider": "mock",
            "voice_id": "mock_oliver",
            "stability": 0.5,
            "similarity_boost": 0.75,
        },
    }


@pytest.fixture
def hannah_character() -> dict[str, Any]:
    """Hannah the Historian character fixture.

    Returns a dictionary representing Hannah, an 11-year-old history enthusiast
    who loves storytelling and sharing interesting facts.
    """
    return {
        "id": "hannah",
        "name": "Hannah the Historian",
        "age": 11,
        "personality": "Loves history and storytelling",
        "speaking_style": "Uses narrative style, often starts with 'Did you know...'",
        "vocabulary_level": "INTERMEDIATE",
        "voice_config": {
            "provider": "mock",
            "voice_id": "mock_hannah",
            "stability": 0.6,
            "similarity_boost": 0.7,
        },
    }


@pytest.fixture
def narrator_character() -> dict[str, Any]:
    """Narrator character fixture.

    Returns a dictionary representing the main narrator, who guides
    the story and provides context.
    """
    return {
        "id": "narrator",
        "name": "The Narrator",
        "age": None,
        "personality": "Friendly, encouraging, and educational",
        "speaking_style": "Clear, engaging, warm tone suitable for kids",
        "vocabulary_level": "INTERMEDIATE",
        "voice_config": {
            "provider": "mock",
            "voice_id": "mock_narrator",
            "stability": 0.7,
            "similarity_boost": 0.8,
        },
    }


@pytest.fixture
def all_characters(
    oliver_character: dict[str, Any],
    hannah_character: dict[str, Any],
    narrator_character: dict[str, Any],
) -> list[dict[str, Any]]:
    """All default characters as a list."""
    return [oliver_character, hannah_character, narrator_character]


@pytest.fixture
def generic_character() -> dict[str, Any]:
    """Generic character fixture for testing purposes."""
    return {
        "id": "test_character",
        "name": "Test Character",
        "age": 10,
        "personality": "Test personality",
        "speaking_style": "Test speaking style",
        "vocabulary_level": "BASIC",
        "voice_config": {
            "provider": "mock",
            "voice_id": "mock_test",
            "stability": 0.5,
            "similarity_boost": 0.5,
        },
    }
