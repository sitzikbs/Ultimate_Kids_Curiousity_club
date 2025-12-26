"""Unit tests for fixture loading utilities."""

from pathlib import Path

import pytest

# Import from tests.utils since fixture_loader is in tests/utils/
from tests.utils.fixture_loader import (
    list_available_fixtures,
    load_json_fixture,
    load_llm_ideation_fixture,
    load_llm_script_fixture,
    validate_fixture_structure,
)


@pytest.mark.unit
def test_load_llm_ideation_fixture(llm_fixtures_dir: Path) -> None:
    """Test loading an LLM ideation fixture."""
    fixture = load_llm_ideation_fixture("airplanes", llm_fixtures_dir)

    assert "refined_topic" in fixture
    assert "learning_objectives" in fixture
    assert "key_points" in fixture
    assert isinstance(fixture["learning_objectives"], list)
    assert len(fixture["learning_objectives"]) >= 3


@pytest.mark.unit
def test_load_llm_script_fixture(llm_fixtures_dir: Path) -> None:
    """Test loading an LLM script fixture."""
    fixture = load_llm_script_fixture("airplanes_two_characters", llm_fixtures_dir)

    assert "segments" in fixture
    assert "total_segments" in fixture
    assert isinstance(fixture["segments"], list)
    assert len(fixture["segments"]) > 0


@pytest.mark.unit
def test_list_available_fixtures(test_data_dir: Path) -> None:
    """Test listing available fixtures."""
    fixtures = list_available_fixtures(test_data_dir, "llm")

    assert isinstance(fixtures, list)
    assert len(fixtures) > 0
    assert "ideation_airplanes" in fixtures


@pytest.mark.unit
def test_validate_fixture_structure() -> None:
    """Test fixture structure validation."""
    valid_fixture = {
        "refined_topic": "Test",
        "learning_objectives": [],
        "key_points": [],
    }

    required_fields = ["refined_topic", "learning_objectives", "key_points"]
    assert validate_fixture_structure(valid_fixture, required_fields)

    # Missing field
    invalid_fixture = {"refined_topic": "Test"}
    assert not validate_fixture_structure(invalid_fixture, required_fields)


@pytest.mark.unit
def test_load_json_fixture_not_found(tmp_path: Path) -> None:
    """Test loading non-existent fixture raises FileNotFoundError."""
    fake_path = tmp_path / "nonexistent.json"

    with pytest.raises(FileNotFoundError):
        load_json_fixture(fake_path)
