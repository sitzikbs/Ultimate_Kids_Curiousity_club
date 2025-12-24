"""Test fixtures for models and managers."""

import pytest

from src.models import (
    Character,
    Episode,
    Location,
    PipelineStage,
    Protagonist,
    Show,
    ShowBlueprint,
    StoryBeat,
    StoryOutline,
    VoiceConfig,
    WorldDescription,
)


@pytest.fixture
def voice_config():
    """Sample voice configuration."""
    return VoiceConfig(
        provider="mock",
        voice_id="mock_voice_123",
        stability=0.5,
        similarity_boost=0.75,
        style=0.3,
    )


@pytest.fixture
def show():
    """Sample show."""
    return Show(
        show_id="test_show",
        title="Test Show",
        description="A test educational show",
        theme="Testing and learning",
    )


@pytest.fixture
def protagonist(voice_config):
    """Sample protagonist."""
    return Protagonist(
        name="Test Hero",
        age=8,
        description="A curious young learner",
        values=["curiosity", "creativity", "kindness"],
        catchphrases=["Let's learn!", "How fascinating!"],
        backstory="Loves exploring and discovering new things",
        voice_config=voice_config,
    )


@pytest.fixture
def world():
    """Sample world description."""
    return WorldDescription(
        setting="A friendly town called Testville",
        rules=[
            "Science is fun",
            "Everyone helps each other",
        ],
        atmosphere="Friendly and encouraging",
        locations=[
            Location(name="Test Lab", description="Where experiments happen"),
            Location(name="Test Library", description="Full of books and knowledge"),
        ],
    )


@pytest.fixture
def character(voice_config):
    """Sample supporting character."""
    return Character(
        name="Test Friend",
        role="Best Friend",
        description="Helpful and enthusiastic",
        personality="Optimistic and supportive",
        voice_config=voice_config,
    )


@pytest.fixture
def show_blueprint(show, protagonist, world, character):
    """Sample show blueprint."""
    blueprint = ShowBlueprint(
        show=show,
        protagonist=protagonist,
        world=world,
        characters=[character],
    )
    return blueprint


@pytest.fixture
def story_beat():
    """Sample story beat."""
    return StoryBeat(
        beat_number=1,
        title="The Discovery",
        description="Our hero discovers something amazing",
        educational_focus="Introduction to the scientific method",
        key_moments=["Hero sees something unusual", "Hero asks questions"],
    )


@pytest.fixture
def story_outline(story_beat):
    """Sample story outline."""
    return StoryOutline(
        episode_id="test_ep_001",
        show_id="test_show",
        topic="How magnets work",
        title="The Magnetic Mystery",
        educational_concept="Magnetism and magnetic fields",
        story_beats=[story_beat],
    )


@pytest.fixture
def episode(story_outline):
    """Sample episode."""
    return Episode(
        episode_id="test_ep_001",
        show_id="test_show",
        topic="How magnets work",
        title="The Magnetic Mystery",
        outline=story_outline,
        current_stage=PipelineStage.PENDING,
    )


@pytest.fixture
def temp_data_dir(tmp_path):
    """Temporary data directory for testing."""
    data_dir = tmp_path / "data"
    data_dir.mkdir()
    shows_dir = data_dir / "shows"
    shows_dir.mkdir()
    episodes_dir = data_dir / "episodes"
    episodes_dir.mkdir()
    return data_dir
