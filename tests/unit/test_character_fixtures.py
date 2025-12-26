"""Unit tests for character fixtures."""

import pytest


@pytest.mark.unit
def test_oliver_character_fixture(oliver_character) -> None:
    """Test Oliver character fixture has correct structure."""
    assert oliver_character["id"] == "oliver"
    assert oliver_character["name"] == "Oliver the Inventor"
    assert oliver_character["age"] == 10
    assert "voice_config" in oliver_character
    assert oliver_character["voice_config"]["provider"] == "mock"


@pytest.mark.unit
def test_hannah_character_fixture(hannah_character) -> None:
    """Test Hannah character fixture has correct structure."""
    assert hannah_character["id"] == "hannah"
    assert hannah_character["name"] == "Hannah the Historian"
    assert hannah_character["age"] == 11
    assert "voice_config" in hannah_character


@pytest.mark.unit
def test_narrator_character_fixture(narrator_character) -> None:
    """Test narrator character fixture."""
    assert narrator_character["id"] == "narrator"
    assert narrator_character["name"] == "The Narrator"
    assert narrator_character["age"] is None


@pytest.mark.unit
def test_all_characters_fixture(all_characters) -> None:
    """Test all characters fixture returns a list."""
    assert isinstance(all_characters, list)
    assert len(all_characters) == 3

    character_ids = [char["id"] for char in all_characters]
    assert "oliver" in character_ids
    assert "hannah" in character_ids
    assert "narrator" in character_ids


@pytest.mark.unit
def test_generic_character_fixture(generic_character) -> None:
    """Test generic character fixture for testing."""
    assert generic_character["id"] == "test_character"
    assert generic_character["vocabulary_level"] == "BASIC"
