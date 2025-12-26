"""Unit tests for episode fixtures."""

import pytest


@pytest.mark.unit
def test_new_episode_fixture(new_episode) -> None:
    """Test new episode fixture structure."""
    assert new_episode["id"] == "test_ep001"
    assert new_episode["title"] == "How Rockets Work"
    assert new_episode["status"] == "IDEATION"
    assert new_episode["duration_minutes"] == 15
    assert "oliver" in new_episode["characters"]
    assert "hannah" in new_episode["characters"]


@pytest.mark.unit
def test_scripting_episode_fixture(scripting_episode) -> None:
    """Test scripting episode has ideation checkpoint."""
    assert scripting_episode["status"] == "SCRIPTING"
    assert "ideation" in scripting_episode["checkpoints"]

    ideation = scripting_episode["checkpoints"]["ideation"]
    assert "completed_at" in ideation
    assert "output" in ideation
    assert "refined_topic" in ideation["output"]
    assert "learning_objectives" in ideation["output"]


@pytest.mark.unit
def test_audio_synthesis_episode_fixture(audio_synthesis_episode) -> None:
    """Test audio synthesis episode has script checkpoint."""
    assert audio_synthesis_episode["status"] == "AUDIO_SYNTHESIS"
    assert "scripting" in audio_synthesis_episode["checkpoints"]

    scripting = audio_synthesis_episode["checkpoints"]["scripting"]
    assert "segments" in scripting["output"]


@pytest.mark.unit
def test_complete_episode_fixture(complete_episode) -> None:
    """Test complete episode has all checkpoints."""
    assert complete_episode["status"] == "COMPLETE"

    checkpoints = complete_episode["checkpoints"]
    assert "ideation" in checkpoints
    assert "scripting" in checkpoints
    assert "audio_synthesis" in checkpoints
    assert "audio_mixing" in checkpoints

    # Verify final audio path
    assert "final_audio_path" in checkpoints["audio_mixing"]


@pytest.mark.unit
def test_episode_with_show_blueprint_fixture(episode_with_show_blueprint) -> None:
    """Test episode with show blueprint data."""
    assert "show_blueprint" in episode_with_show_blueprint

    blueprint = episode_with_show_blueprint["show_blueprint"]
    assert "protagonist" in blueprint
    assert "world" in blueprint
    assert blueprint["protagonist"]["name"] == "Hannah the Historian"


@pytest.mark.unit
def test_episodes_list_fixture(episodes_list) -> None:
    """Test episodes list fixture."""
    assert isinstance(episodes_list, list)
    assert len(episodes_list) == 3

    statuses = [ep["status"] for ep in episodes_list]
    assert "IDEATION" in statuses
    assert "SCRIPTING" in statuses
    assert "COMPLETE" in statuses
