"""Unit tests for PromptEnhancer."""

import pytest

from models import (
    Character,
    ConceptsHistory,
    Protagonist,
    Show,
    ShowBlueprint,
    StoryBeat,
    StoryOutline,
    StorySegment,
    WorldDescription,
)
from modules.prompts import PromptEnhancer


@pytest.fixture
def test_show():
    """Create a test Show."""
    return Show(
        show_id="test_show_001",
        title="Test Science Show",
        description="Educational science adventures",
        theme="STEM and Discovery",
        narrator_voice_config={"provider": "test", "voice_id": "narrator_01"},
    )


@pytest.fixture
def test_protagonist():
    """Create a test Protagonist."""
    return Protagonist(
        name="Oliver",
        age=10,
        description="A curious inventor who loves to learn",
        values=["curiosity", "creativity", "persistence"],
        catchphrases=["How does it work?", "Let's find out!"],
        backstory="Oliver grew up in a laboratory",
        voice_config={"provider": "test", "voice_id": "oliver_voice"},
    )


@pytest.fixture
def test_world():
    """Create a test WorldDescription."""
    return WorldDescription(
        setting="A magical laboratory in a treehouse",
        rules=["Science works", "Curiosity is rewarded", "Experiments are fun"],
        atmosphere="Exciting and educational",
        locations=[
            {"name": "Main Lab", "description": "Where experiments happen"},
            {"name": "Library", "description": "Books and research"},
        ],
    )


@pytest.fixture
def test_characters():
    """Create test supporting Characters."""
    return [
        Character(
            name="Hannah",
            role="Lab Assistant",
            description="Helpful scientist",
            personality="Kind and knowledgeable",
            voice_config={"provider": "test", "voice_id": "hannah_voice"},
        ),
        Character(
            name="Professor Quirk",
            role="Mentor",
            description="Eccentric scientist",
            personality="Enthusiastic and wise",
            voice_config={"provider": "test", "voice_id": "quirk_voice"},
        ),
    ]


@pytest.fixture
def test_concepts_history():
    """Create test ConceptsHistory."""
    return ConceptsHistory(
        concepts=[
            {"episode_id": "ep001", "topic": "Gravity", "date": "2024-01-15"},
            {"episode_id": "ep002", "topic": "Magnetism", "date": "2024-01-16"},
        ]
    )


@pytest.fixture
def test_show_blueprint(
    test_show, test_protagonist, test_world, test_characters, test_concepts_history
):
    """Create a complete test ShowBlueprint."""
    return ShowBlueprint(
        show=test_show,
        protagonist=test_protagonist,
        world=test_world,
        characters=test_characters,
        concepts_history=test_concepts_history,
    )


@pytest.fixture
def test_story_outline():
    """Create a test StoryOutline."""
    return StoryOutline(
        episode_id="ep003",
        show_id="test_show_001",
        topic="Solar System",
        title="Journey Through the Solar System",
        educational_concept="Planets orbit the sun",
        story_beats=[
            StoryBeat(
                beat_number=1,
                title="Introduction to Space",
                description="Oliver looks up at the night sky",
                educational_focus="What is the solar system",
                key_moments=["See the stars", "Wonder about planets"],
            ),
            StoryBeat(
                beat_number=2,
                title="Building a Model",
                description="Oliver builds a solar system model",
                educational_focus="Order of planets from the sun",
                key_moments=["Research planets", "Build the model"],
            ),
        ],
    )


@pytest.fixture
def test_story_segments():
    """Create test StorySegments."""
    return [
        StorySegment(
            segment_number=1,
            beat_number=1,
            description="Oliver and Hannah look at the night sky from the treehouse",
            characters_involved=["Oliver", "Hannah"],
            setting="Treehouse observatory at night",
            educational_content="The solar system contains the sun and planets",
        ),
        StorySegment(
            segment_number=2,
            beat_number=1,
            description="They decide to learn more about the planets",
            characters_involved=["Oliver", "Hannah"],
            setting="Main Lab",
            educational_content="There are 8 planets in our solar system",
        ),
    ]


@pytest.fixture
def prompt_enhancer():
    """Create a PromptEnhancer instance."""
    return PromptEnhancer(version="1.0.0")


class TestPromptEnhancerInit:
    """Tests for PromptEnhancer initialization."""

    def test_init_default(self):
        """Test initialization with default parameters."""
        enhancer = PromptEnhancer()
        assert enhancer.version == "1.0.0"
        assert enhancer.template_dir.exists()
        assert enhancer.env is not None

    def test_init_custom_version(self):
        """Test initialization with custom version."""
        enhancer = PromptEnhancer(version="2.0.0")
        assert enhancer.version == "2.0.0"

    def test_init_custom_template_dir(self, tmp_path):
        """Test initialization with custom template directory."""
        custom_dir = tmp_path / "templates"
        custom_dir.mkdir()
        enhancer = PromptEnhancer(template_dir=custom_dir)
        assert enhancer.template_dir == custom_dir

    def test_custom_filters_registered(self, prompt_enhancer):
        """Test that custom filters are registered in Jinja environment."""
        assert "format_list" in prompt_enhancer.env.filters
        assert "truncate_smart" in prompt_enhancer.env.filters
        assert "capitalize_speaker" in prompt_enhancer.env.filters


class TestEnhanceIdeationPrompt:
    """Tests for enhance_ideation_prompt method."""

    def test_enhance_ideation_basic(self, prompt_enhancer, test_show_blueprint):
        """Test basic ideation prompt enhancement."""
        result = prompt_enhancer.enhance_ideation_prompt(
            topic="How gravity works",
            show_blueprint=test_show_blueprint,
        )

        assert "gravity" in result.lower()
        assert test_show_blueprint.show.title in result
        assert test_show_blueprint.protagonist.name in result
        assert test_show_blueprint.world.setting in result
        assert "1.0.0" in result  # Version should be included

    def test_enhance_ideation_includes_protagonist(
        self, prompt_enhancer, test_show_blueprint
    ):
        """Test that protagonist details are included."""
        result = prompt_enhancer.enhance_ideation_prompt(
            topic="Test topic",
            show_blueprint=test_show_blueprint,
        )

        assert test_show_blueprint.protagonist.name in result
        assert str(test_show_blueprint.protagonist.age) in result
        assert test_show_blueprint.protagonist.description in result

    def test_enhance_ideation_includes_values(
        self, prompt_enhancer, test_show_blueprint
    ):
        """Test that protagonist values are included."""
        result = prompt_enhancer.enhance_ideation_prompt(
            topic="Test topic",
            show_blueprint=test_show_blueprint,
        )

        # Check that at least one value is present
        assert any(value in result for value in test_show_blueprint.protagonist.values)

    def test_enhance_ideation_includes_world_rules(
        self, prompt_enhancer, test_show_blueprint
    ):
        """Test that world rules are included."""
        result = prompt_enhancer.enhance_ideation_prompt(
            topic="Test topic",
            show_blueprint=test_show_blueprint,
        )

        # Check that at least one rule is present
        assert any(rule in result for rule in test_show_blueprint.world.rules)

    def test_enhance_ideation_includes_covered_concepts(
        self, prompt_enhancer, test_show_blueprint
    ):
        """Test that covered concepts are included."""
        result = prompt_enhancer.enhance_ideation_prompt(
            topic="Test topic",
            show_blueprint=test_show_blueprint,
        )

        # Check that previously covered topics are mentioned
        assert "Gravity" in result
        assert "Magnetism" in result


class TestEnhanceOutlinePrompt:
    """Tests for enhance_outline_prompt method."""

    def test_enhance_outline_basic(self, prompt_enhancer, test_show_blueprint):
        """Test basic outline prompt enhancement."""
        concept = "Oliver discovers how gravity pulls objects toward Earth"
        result = prompt_enhancer.enhance_outline_prompt(
            concept=concept,
            show_blueprint=test_show_blueprint,
        )

        assert concept in result
        assert test_show_blueprint.protagonist.name in result
        assert test_show_blueprint.world.setting in result
        assert "1.0.0" in result

    def test_enhance_outline_includes_characters(
        self, prompt_enhancer, test_show_blueprint
    ):
        """Test that supporting characters are included."""
        result = prompt_enhancer.enhance_outline_prompt(
            concept="Test concept",
            show_blueprint=test_show_blueprint,
        )

        # Check that characters are mentioned
        assert "Hannah" in result
        assert "Professor Quirk" in result

    def test_enhance_outline_includes_locations(
        self, prompt_enhancer, test_show_blueprint
    ):
        """Test that world locations are included."""
        result = prompt_enhancer.enhance_outline_prompt(
            concept="Test concept",
            show_blueprint=test_show_blueprint,
        )

        # Check that at least one location is present
        assert "Main Lab" in result or "Library" in result


class TestEnhanceSegmentPrompt:
    """Tests for enhance_segment_prompt method."""

    def test_enhance_segment_basic(
        self, prompt_enhancer, test_story_outline, test_show_blueprint
    ):
        """Test basic segment prompt enhancement."""
        result = prompt_enhancer.enhance_segment_prompt(
            outline=test_story_outline,
            show_blueprint=test_show_blueprint,
        )

        assert test_story_outline.title in result
        assert test_story_outline.topic in result
        assert test_show_blueprint.protagonist.name in result
        assert "1.0.0" in result

    def test_enhance_segment_includes_story_beats(
        self, prompt_enhancer, test_story_outline, test_show_blueprint
    ):
        """Test that story beats are included."""
        result = prompt_enhancer.enhance_segment_prompt(
            outline=test_story_outline,
            show_blueprint=test_show_blueprint,
        )

        # Check that beat titles are present
        assert "Introduction to Space" in result
        assert "Building a Model" in result

    def test_enhance_segment_includes_educational_focus(
        self, prompt_enhancer, test_story_outline, test_show_blueprint
    ):
        """Test that educational focus is included."""
        result = prompt_enhancer.enhance_segment_prompt(
            outline=test_story_outline,
            show_blueprint=test_show_blueprint,
        )

        assert "What is the solar system" in result
        assert "Order of planets from the sun" in result


class TestEnhanceScriptPrompt:
    """Tests for enhance_script_prompt method."""

    def test_enhance_script_basic(
        self, prompt_enhancer, test_story_segments, test_show_blueprint
    ):
        """Test basic script prompt enhancement."""
        result = prompt_enhancer.enhance_script_prompt(
            segments=test_story_segments,
            show_blueprint=test_show_blueprint,
        )

        assert test_show_blueprint.protagonist.name in result
        assert test_story_segments[0].description in result
        assert "1.0.0" in result

    def test_enhance_script_includes_segments(
        self, prompt_enhancer, test_story_segments, test_show_blueprint
    ):
        """Test that all segments are included."""
        result = prompt_enhancer.enhance_script_prompt(
            segments=test_story_segments,
            show_blueprint=test_show_blueprint,
        )

        # Check both segments are present
        assert test_story_segments[0].description in result
        assert test_story_segments[1].description in result

    def test_enhance_script_includes_catchphrases(
        self, prompt_enhancer, test_story_segments, test_show_blueprint
    ):
        """Test that catchphrases are included."""
        result = prompt_enhancer.enhance_script_prompt(
            segments=test_story_segments,
            show_blueprint=test_show_blueprint,
        )

        # Check that catchphrases are mentioned
        assert any(
            phrase in result for phrase in test_show_blueprint.protagonist.catchphrases
        )

    def test_enhance_script_includes_narrator_config(
        self, prompt_enhancer, test_story_segments, test_show_blueprint
    ):
        """Test that narrator voice config is included."""
        result = prompt_enhancer.enhance_script_prompt(
            segments=test_story_segments,
            show_blueprint=test_show_blueprint,
        )

        # The narrator voice config should be referenced
        assert "narrator" in result.lower()


class TestMinimalShowBlueprint:
    """Tests with minimal ShowBlueprint (testing edge cases)."""

    def test_minimal_protagonist(self, prompt_enhancer):
        """Test with minimal protagonist (no optional fields)."""
        show = Show(
            show_id="minimal",
            title="Minimal Show",
            description="Test",
            theme="Test",
            narrator_voice_config={},
        )
        protagonist = Protagonist(
            name="Test",
            age=10,
            description="Test character",
            voice_config={},
        )
        world = WorldDescription(
            setting="Test World",
            atmosphere="Test",
        )
        blueprint = ShowBlueprint(
            show=show,
            protagonist=protagonist,
            world=world,
        )

        result = prompt_enhancer.enhance_ideation_prompt(
            topic="Test topic",
            show_blueprint=blueprint,
        )

        assert result  # Should not fail
        assert "Test topic" in result
        assert "Test" in result

    def test_no_covered_concepts(self, prompt_enhancer):
        """Test with no covered concepts."""
        show = Show(
            show_id="test",
            title="Test",
            description="Test",
            theme="Test",
            narrator_voice_config={},
        )
        protagonist = Protagonist(
            name="Test",
            age=10,
            description="Test",
            voice_config={},
        )
        world = WorldDescription(
            setting="Test",
            atmosphere="Test",
        )
        blueprint = ShowBlueprint(
            show=show,
            protagonist=protagonist,
            world=world,
            concepts_history=ConceptsHistory(concepts=[]),
        )

        result = prompt_enhancer.enhance_ideation_prompt(
            topic="New topic",
            show_blueprint=blueprint,
        )

        assert result
        assert "New topic" in result

    def test_empty_characters_list(self, prompt_enhancer):
        """Test with empty characters list."""
        show = Show(
            show_id="test",
            title="Test",
            description="Test",
            theme="Test",
            narrator_voice_config={},
        )
        protagonist = Protagonist(
            name="Test",
            age=10,
            description="Test",
            voice_config={},
        )
        world = WorldDescription(
            setting="Test",
            atmosphere="Test",
        )
        blueprint = ShowBlueprint(
            show=show,
            protagonist=protagonist,
            world=world,
            characters=[],
        )

        result = prompt_enhancer.enhance_outline_prompt(
            concept="Test concept",
            show_blueprint=blueprint,
        )

        assert result
        assert "Test concept" in result
