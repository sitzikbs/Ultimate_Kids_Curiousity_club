"""Tests for data models."""

from datetime import datetime

import pytest

from src.models import (
    Character,
    Episode,
    Location,
    PipelineStage,
    Protagonist,
    Show,
    VoiceConfig,
)


class TestVoiceConfig:
    """Tests for VoiceConfig model."""

    def test_voice_config_creation(self, voice_config):
        """Test voice config can be created."""
        assert voice_config.provider == "mock"
        assert voice_config.voice_id == "mock_voice_123"
        assert voice_config.stability == 0.5

    def test_voice_config_defaults(self):
        """Test voice config with defaults."""
        config = VoiceConfig()
        assert config.stability == 0.5
        assert config.similarity_boost == 0.75
        assert config.style == 0.3


class TestShow:
    """Tests for Show model."""

    def test_show_creation(self, show):
        """Test show can be created."""
        assert show.show_id == "test_show"
        assert show.title == "Test Show"
        assert show.theme == "Testing and learning"

    def test_show_id_validation(self):
        """Test show ID validation."""
        # Valid show IDs
        Show(show_id="valid_show", title="Test", description="Test", theme="Test")
        Show(show_id="show123", title="Test", description="Test", theme="Test")

        # Invalid show IDs
        with pytest.raises(ValueError, match="lowercase"):
            Show(show_id="InvalidShow", title="Test", description="Test", theme="Test")

        with pytest.raises(ValueError, match="letters, numbers, and underscores"):
            Show(
                show_id="invalid-show!",
                title="Test",
                description="Test",
                theme="Test",
            )

    def test_show_has_created_at(self, show):
        """Test show has created_at timestamp."""
        assert isinstance(show.created_at, datetime)


class TestProtagonist:
    """Tests for Protagonist model."""

    def test_protagonist_creation(self, protagonist):
        """Test protagonist can be created."""
        assert protagonist.name == "Test Hero"
        assert protagonist.age == 8
        assert "curiosity" in protagonist.values

    def test_protagonist_age_validation(self):
        """Test protagonist age must be 5-12."""
        # Valid ages
        Protagonist(name="Kid", age=5, description="Test")
        Protagonist(name="Kid", age=12, description="Test")

        # Invalid ages
        with pytest.raises(ValueError, match="5 and 12"):
            Protagonist(name="Kid", age=4, description="Test")

        with pytest.raises(ValueError, match="5 and 12"):
            Protagonist(name="Kid", age=13, description="Test")


class TestWorldDescription:
    """Tests for WorldDescription model."""

    def test_world_creation(self, world):
        """Test world can be created."""
        assert "Testville" in world.setting
        assert len(world.rules) == 2
        assert len(world.locations) == 2

    def test_location_creation(self):
        """Test location can be created."""
        loc = Location(name="Test Place", description="A test location")
        assert loc.name == "Test Place"
        assert loc.description == "A test location"


class TestCharacter:
    """Tests for Character model."""

    def test_character_creation(self, character):
        """Test character can be created."""
        assert character.name == "Test Friend"
        assert character.role == "Best Friend"
        assert character.personality == "Optimistic and supportive"


class TestShowBlueprint:
    """Tests for ShowBlueprint model."""

    def test_blueprint_creation(self, show_blueprint):
        """Test show blueprint can be created."""
        assert show_blueprint.show.show_id == "test_show"
        assert show_blueprint.protagonist.name == "Test Hero"
        assert len(show_blueprint.characters) == 1

    def test_add_episode(self, show_blueprint):
        """Test adding episode to blueprint."""
        show_blueprint.add_episode("ep_001")
        assert "ep_001" in show_blueprint.episodes

        # Adding same episode twice should not duplicate
        show_blueprint.add_episode("ep_001")
        assert show_blueprint.episodes.count("ep_001") == 1

    def test_add_character(self, show_blueprint):
        """Test adding character to blueprint."""
        new_char = Character(
            name="New Friend",
            role="Mentor",
            description="Wise and helpful",
            personality="Patient and knowledgeable",
        )
        show_blueprint.add_character(new_char)
        assert len(show_blueprint.characters) == 2

        # Adding same character should not duplicate
        show_blueprint.add_character(new_char)
        assert len(show_blueprint.characters) == 2

    def test_add_concept(self, show_blueprint):
        """Test adding concept to blueprint."""
        show_blueprint.add_concept("magnetism", "ep_001", "introductory")
        concepts = show_blueprint.concepts_history.get_covered_concepts()
        assert "magnetism" in concepts


class TestStoryBeat:
    """Tests for StoryBeat model."""

    def test_story_beat_creation(self, story_beat):
        """Test story beat can be created."""
        assert story_beat.beat_number == 1
        assert story_beat.title == "The Discovery"
        assert len(story_beat.key_moments) == 2


class TestEpisode:
    """Tests for Episode model."""

    def test_episode_creation(self, episode):
        """Test episode can be created."""
        assert episode.episode_id == "test_ep_001"
        assert episode.show_id == "test_show"
        assert episode.current_stage == PipelineStage.PENDING

    def test_episode_id_validation(self):
        """Test episode ID validation."""
        # Valid episode IDs
        Episode(episode_id="ep_001", show_id="test", topic="Test")
        Episode(episode_id="test-ep-001", show_id="test", topic="Test")

        # Invalid episode IDs
        with pytest.raises(ValueError, match="Episode ID"):
            Episode(episode_id="", show_id="test", topic="Test")

        with pytest.raises(ValueError, match="Episode ID"):
            Episode(episode_id="ep@001", show_id="test", topic="Test")

    def test_update_stage(self, episode):
        """Test updating episode stage."""
        old_time = episode.updated_at
        episode.update_stage(PipelineStage.OUTLINING)
        assert episode.current_stage == PipelineStage.OUTLINING
        assert episode.updated_at >= old_time

    def test_is_complete(self, episode):
        """Test checking if episode is complete."""
        assert not episode.is_complete()
        episode.update_stage(PipelineStage.COMPLETE)
        assert episode.is_complete()

    def test_is_failed(self, episode):
        """Test checking if episode failed."""
        assert not episode.is_failed()
        episode.update_stage(PipelineStage.FAILED)
        assert episode.is_failed()

    def test_has_timestamps(self, episode):
        """Test episode has timestamps."""
        assert isinstance(episode.created_at, datetime)
        assert isinstance(episode.updated_at, datetime)
