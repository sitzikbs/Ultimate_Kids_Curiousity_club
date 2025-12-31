"""Utility functions for loading test fixtures."""

import json
from pathlib import Path
from typing import Any


def load_json_fixture(fixture_path: Path) -> dict[str, Any]:
    """Load a JSON fixture file.

    Args:
        fixture_path: Path to the JSON fixture file

    Returns:
        Dictionary containing the parsed JSON data

    Raises:
        FileNotFoundError: If the fixture file doesn't exist
        json.JSONDecodeError: If the file contains invalid JSON
    """
    if not fixture_path.exists():
        msg = f"Fixture file not found: {fixture_path}"
        raise FileNotFoundError(msg)

    return json.loads(fixture_path.read_text())


def load_llm_ideation_fixture(topic_name: str, fixtures_dir: Path) -> dict[str, Any]:
    """Load an LLM ideation fixture by topic name.

    Args:
        topic_name: Name of the topic (e.g., 'airplanes', 'immune_system')
        fixtures_dir: Path to the fixtures directory (should be data/fixtures)

    Returns:
        Dictionary containing the ideation response data
    """
    # fixtures_dir is already data/fixtures, so we don't need to add fixtures
    if fixtures_dir.name == "llm":
        # Already in the llm subdirectory
        fixture_path = fixtures_dir / f"ideation_{topic_name}.json"
    else:
        # Need to navigate to llm subdirectory
        fixture_path = fixtures_dir / "llm" / f"ideation_{topic_name}.json"
    return load_json_fixture(fixture_path)


def load_llm_script_fixture(script_name: str, fixtures_dir: Path) -> dict[str, Any]:
    """Load an LLM scripting fixture by name.

    Args:
        script_name: Name of the script fixture
        fixtures_dir: Path to the fixtures directory (should be data/fixtures)

    Returns:
        Dictionary containing the script data with segments
    """
    # fixtures_dir is already data/fixtures, so we don't need to add fixtures
    if fixtures_dir.name == "llm":
        # Already in the llm subdirectory
        fixture_path = fixtures_dir / f"script_{script_name}.json"
    else:
        # Need to navigate to llm subdirectory
        fixture_path = fixtures_dir / "llm" / f"script_{script_name}.json"
    return load_json_fixture(fixture_path)


def list_available_fixtures(fixtures_dir: Path, category: str) -> list[str]:
    """List all available fixture files in a category.

    Args:
        fixtures_dir: Path to the fixtures directory
        category: Category name ('llm', 'audio', 'images')

    Returns:
        List of fixture file names (without extension)
    """
    category_dir = fixtures_dir / category
    if not category_dir.exists():
        return []

    fixtures = []
    for path in category_dir.glob("*.json"):
        fixtures.append(path.stem)

    return sorted(fixtures)


def create_mock_audio_file(output_path: Path, duration_seconds: float = 1.0) -> Path:
    """Create a minimal silent MP3 file for testing.

    Note: This creates a minimal valid MP3 file header without actual audio data.
    For real audio testing, use proper audio generation libraries.

    Args:
        output_path: Where to save the mock audio file
        duration_seconds: Simulated duration (stored in metadata only)

    Returns:
        Path to the created file
    """
    # Create parent directory if it doesn't exist
    output_path.parent.mkdir(parents=True, exist_ok=True)

    # Write a minimal MP3 header (ID3v2.4 tag)
    # This is a minimal valid MP3 that won't actually play
    # but will pass basic file validation checks
    mp3_header = bytes(
        [
            0xFF,
            0xFB,
            0x90,
            0x00,  # MP3 frame sync
            0x00,
            0x00,
            0x00,
            0x00,
        ]
    )

    output_path.write_bytes(mp3_header)
    return output_path


def validate_fixture_structure(
    fixture_data: dict[str, Any], required_fields: list[str]
) -> bool:
    """Validate that a fixture has all required fields.

    Args:
        fixture_data: The fixture data to validate
        required_fields: List of required field names

    Returns:
        True if all fields are present, False otherwise
    """
    return all(field in fixture_data for field in required_fields)
