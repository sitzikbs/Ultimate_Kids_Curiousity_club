"""Test suite for data models."""

from datetime import datetime

import pytest

from src.models import (
    Character,
    ConceptsHistory,
    Episode,
    PipelineStage,
    Protagonist,
    Script,
    ScriptBlock,
    Show,
    ShowBlueprint,
    StoryBeat,
    StoryOutline,
    StorySegment,
    WorldDescription,
)


class TestShowModels:
    """Tests for Show Blueprint models."""

    def test_show_creation(self):
        """Test creating a valid Show model."""
        show = Show(
            show_id="test_show_001",
            title="Test Show",
            description="A test show for kids",
            theme="Science and Adventure",
            narrator_voice_config={"provider": "test", "voice_id": "test_narrator"},
        )
        assert show.show_id == "test_show_001"
        assert show.title == "Test Show"
        assert isinstance(show.created_at, datetime)

    def test_show_id_validation(self):
        """Test show_id format validation."""
        with pytest.raises(ValueError, match="alphanumeric"):
            Show(
                show_id="invalid show!",
                title="Test",
                description="Test",
                theme="Test",
                narrator_voice_config={},
            )

    def test_show_id_valid_formats(self):
        """Test valid show_id formats."""
        valid_ids = ["show_001", "show-001", "ShowTest123", "test_show-01"]
        for show_id in valid_ids:
            show = Show(
                show_id=show_id,
                title="Test",
                description="Test",
                theme="Test",
                narrator_voice_config={},
            )
            assert show.show_id == show_id

    def test_protagonist_creation(self):
        """Test creating a valid Protagonist model."""
        protagonist = Protagonist(
            name="Oliver the Inventor",
            age=10,
            description="A curious inventor",
            values=["curiosity", "creativity"],
            catchphrases=["How does it work?"],
            backstory="Oliver loves building things",
            voice_config={"provider": "test", "voice_id": "oliver"},
        )
        assert protagonist.name == "Oliver the Inventor"
        assert protagonist.age == 10
        assert len(protagonist.values) == 2

    def test_protagonist_defaults(self):
        """Test protagonist default values."""
        protagonist = Protagonist(
            name="Test",
            age=10,
            description="Test",
            voice_config={},
        )
        assert protagonist.values == []
        assert protagonist.catchphrases == []
        assert protagonist.backstory == ""
        assert protagonist.image_path is None

    def test_world_description_creation(self):
        """Test creating a valid WorldDescription model."""
        world = WorldDescription(
            setting="A magical laboratory",
            rules=["Science works", "Curiosity is rewarded"],
            atmosphere="Exciting and educational",
            locations=[
                {"name": "Lab", "description": "Main laboratory"},
                {"name": "Library", "description": "Book storage"},
            ],
        )
        assert world.setting == "A magical laboratory"
        assert len(world.rules) == 2
        assert len(world.locations) == 2

    def test_world_location_validation(self):
        """Test location validation requires 'name' key."""
        with pytest.raises(ValueError, match="must have a 'name' key"):
            WorldDescription(
                setting="Test",
                atmosphere="Test",
                locations=[{"description": "Missing name"}],
            )

    def test_character_creation(self):
        """Test creating a valid Character model."""
        character = Character(
            name="Hannah the Helper",
            role="Supporting scientist",
            description="Helpful lab assistant",
            personality="Kind and knowledgeable",
            voice_config={"provider": "test", "voice_id": "hannah"},
        )
        assert character.name == "Hannah the Helper"
        assert character.role == "Supporting scientist"
        assert character.image_path is None

    def test_concepts_history_creation(self):
        """Test creating a ConceptsHistory model."""
        concepts = ConceptsHistory(
            concepts=[
                {"episode_id": "ep001", "topic": "Gravity", "date": "2024-01-15"},
                {"episode_id": "ep002", "topic": "Magnetism", "date": "2024-01-16"},
            ]
        )
        assert len(concepts.concepts) == 2
        assert isinstance(concepts.last_updated, datetime)

    def test_show_blueprint_creation(self):
        """Test creating a complete ShowBlueprint."""
        show = Show(
            show_id="test_show",
            title="Test Show",
            description="Test",
            theme="Test",
            narrator_voice_config={},
        )
        protagonist = Protagonist(
            name="Test Protag",
            age=10,
            description="Test",
            voice_config={},
        )
        world = WorldDescription(
            setting="Test World",
            atmosphere="Test",
            locations=[{"name": "Location1"}],
        )
        character = Character(
            name="Test Char",
            role="Test",
            description="Test",
            personality="Test",
            voice_config={},
        )

        blueprint = ShowBlueprint(
            show=show,
            protagonist=protagonist,
            world=world,
            characters=[character],
            episodes=["ep001", "ep002"],
        )
        assert blueprint.show.show_id == "test_show"
        assert blueprint.protagonist.name == "Test Protag"
        assert len(blueprint.characters) == 1
        assert len(blueprint.episodes) == 2


class TestStoryModels:
    """Tests for Story models."""

    def test_story_beat_creation(self):
        """Test creating a StoryBeat."""
        beat = StoryBeat(
            beat_number=1,
            title="Introduction",
            description="Introduce the topic",
            educational_focus="Basic concept introduction",
            key_moments=["Meet the character", "Introduce the problem"],
        )
        assert beat.beat_number == 1
        assert beat.title == "Introduction"
        assert len(beat.key_moments) == 2

    def test_story_outline_creation(self):
        """Test creating a StoryOutline."""
        beat = StoryBeat(
            beat_number=1,
            title="Test",
            description="Test",
            educational_focus="Test",
        )
        outline = StoryOutline(
            episode_id="ep001",
            show_id="show001",
            topic="Gravity",
            title="Understanding Gravity",
            educational_concept="Objects fall due to gravity",
            story_beats=[beat],
        )
        assert outline.episode_id == "ep001"
        assert outline.topic == "Gravity"
        assert len(outline.story_beats) == 1
        assert isinstance(outline.created_at, datetime)

    def test_story_segment_creation(self):
        """Test creating a StorySegment."""
        segment = StorySegment(
            segment_number=1,
            beat_number=1,
            description="First segment",
            characters_involved=["Oliver", "Hannah"],
            setting="Laboratory",
            educational_content="Gravity pulls objects down",
        )
        assert segment.segment_number == 1
        assert segment.beat_number == 1
        assert len(segment.characters_involved) == 2

    def test_script_block_creation(self):
        """Test creating a ScriptBlock."""
        block = ScriptBlock(
            speaker="Oliver",
            text="How does gravity work?",
            speaker_voice_id="oliver_voice",
            duration_estimate=3.5,
        )
        assert block.speaker == "Oliver"
        assert block.text == "How does gravity work?"
        assert block.duration_estimate == 3.5

    def test_script_block_no_duration(self):
        """Test ScriptBlock without duration estimate."""
        block = ScriptBlock(
            speaker="Oliver",
            text="Test",
            speaker_voice_id="oliver_voice",
        )
        assert block.duration_estimate is None

    def test_script_creation(self):
        """Test creating a Script."""
        block1 = ScriptBlock(
            speaker="Oliver", text="Hello!", speaker_voice_id="oliver_voice"
        )
        block2 = ScriptBlock(
            speaker="Hannah", text="Hi there!", speaker_voice_id="hannah_voice"
        )
        script = Script(segment_number=1, script_blocks=[block1, block2])
        assert script.segment_number == 1
        assert len(script.script_blocks) == 2


class TestEpisodeModels:
    """Tests for Episode models."""

    def test_pipeline_stage_enum(self):
        """Test PipelineStage enum values."""
        assert PipelineStage.PENDING == "PENDING"
        assert PipelineStage.IDEATION == "IDEATION"
        assert PipelineStage.OUTLINING == "OUTLINING"
        assert PipelineStage.AWAITING_APPROVAL == "AWAITING_APPROVAL"
        assert PipelineStage.APPROVED == "APPROVED"
        assert PipelineStage.SEGMENT_GENERATION == "SEGMENT_GENERATION"
        assert PipelineStage.SCRIPT_GENERATION == "SCRIPT_GENERATION"
        assert PipelineStage.AUDIO_SYNTHESIS == "AUDIO_SYNTHESIS"
        assert PipelineStage.AUDIO_MIXING == "AUDIO_MIXING"
        assert PipelineStage.COMPLETE == "COMPLETE"
        assert PipelineStage.FAILED == "FAILED"
        assert PipelineStage.REJECTED == "REJECTED"

    def test_episode_creation_minimal(self):
        """Test creating an Episode with minimal fields."""
        episode = Episode(
            episode_id="ep001",
            show_id="show001",
            topic="Gravity",
            title="Understanding Gravity",
        )
        assert episode.episode_id == "ep001"
        assert episode.show_id == "show001"
        assert episode.current_stage == PipelineStage.PENDING
        assert episode.outline is None
        assert len(episode.segments) == 0
        assert len(episode.scripts) == 0
        assert isinstance(episode.created_at, datetime)
        assert isinstance(episode.updated_at, datetime)

    def test_episode_creation_full(self):
        """Test creating an Episode with all fields."""
        outline = StoryOutline(
            episode_id="ep001",
            show_id="show001",
            topic="Test",
            title="Test",
            educational_concept="Test",
        )
        segment = StorySegment(
            segment_number=1,
            beat_number=1,
            description="Test",
            setting="Test",
            educational_content="Test",
        )
        script = Script(
            segment_number=1,
            script_blocks=[
                ScriptBlock(
                    speaker="Test", text="Test", speaker_voice_id="test_voice"
                )
            ],
        )

        episode = Episode(
            episode_id="ep001",
            show_id="show001",
            topic="Gravity",
            title="Understanding Gravity",
            outline=outline,
            segments=[segment],
            scripts=[script],
            audio_path="/path/to/audio.mp3",
            current_stage=PipelineStage.COMPLETE,
            approval_status="approved",
            approval_feedback="Great episode!",
        )
        assert episode.current_stage == PipelineStage.COMPLETE
        assert episode.outline is not None
        assert len(episode.segments) == 1
        assert len(episode.scripts) == 1
        assert episode.audio_path == "/path/to/audio.mp3"
        assert episode.approval_status == "approved"

    def test_episode_stage_transitions(self):
        """Test changing episode stages."""
        episode = Episode(
            episode_id="ep001",
            show_id="show001",
            topic="Test",
            title="Test",
        )
        assert episode.current_stage == PipelineStage.PENDING

        # Simulate stage transitions
        episode.current_stage = PipelineStage.IDEATION
        assert episode.current_stage == PipelineStage.IDEATION

        episode.current_stage = PipelineStage.OUTLINING
        assert episode.current_stage == PipelineStage.OUTLINING

        episode.current_stage = PipelineStage.COMPLETE
        assert episode.current_stage == PipelineStage.COMPLETE


class TestModelSerialization:
    """Tests for model serialization (JSON schema generation)."""

    def test_show_json_schema(self):
        """Test Show model can generate JSON schema."""
        schema = Show.model_json_schema()
        assert "properties" in schema
        assert "show_id" in schema["properties"]
        assert "title" in schema["properties"]

    def test_episode_json_schema(self):
        """Test Episode model can generate JSON schema."""
        schema = Episode.model_json_schema()
        assert "properties" in schema
        assert "episode_id" in schema["properties"]
        assert "current_stage" in schema["properties"]

    def test_show_blueprint_serialization(self):
        """Test ShowBlueprint serialization to dict."""
        show = Show(
            show_id="test",
            title="Test",
            description="Test",
            theme="Test",
            narrator_voice_config={},
        )
        protagonist = Protagonist(
            name="Test", age=10, description="Test", voice_config={}
        )
        world = WorldDescription(
            setting="Test", atmosphere="Test", locations=[{"name": "Test"}]
        )

        blueprint = ShowBlueprint(show=show, protagonist=protagonist, world=world)
        data = blueprint.model_dump()
        assert data["show"]["show_id"] == "test"
        assert data["protagonist"]["name"] == "Test"
        assert data["world"]["setting"] == "Test"

    def test_episode_serialization(self):
        """Test Episode serialization to dict."""
        episode = Episode(
            episode_id="ep001",
            show_id="show001",
            topic="Test",
            title="Test",
            current_stage=PipelineStage.IDEATION,
        )
        data = episode.model_dump()
        assert data["episode_id"] == "ep001"
        assert data["current_stage"] == "IDEATION"
