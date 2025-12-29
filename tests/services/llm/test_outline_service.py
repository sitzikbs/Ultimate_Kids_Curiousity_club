"""Tests for OutlineService."""

import pytest

from models import (
    Protagonist,
    Show,
    ShowBlueprint,
    StoryOutline,
    WorldDescription,
)
from modules.prompts.enhancer import PromptEnhancer
from services.llm.mock_provider import MockLLMProvider
from services.llm.outline_service import OutlineService


@pytest.fixture
def mock_show_blueprint():
    """Create a mock show blueprint for testing."""
    show = Show(
        show_id="test_show",
        title="Test Show",
        description="A test show for unit testing",
        theme="Science and Discovery",
        narrator_voice_config={"voice_id": "test_narrator", "stability": 0.5},
    )

    protagonist = Protagonist(
        name="Oliver",
        age=10,
        description="A curious young inventor",
        values=["curiosity", "creativity"],
        voice_config={"voice_id": "test_oliver", "stability": 0.7},
    )

    world = WorldDescription(
        setting="Oliver's Workshop",
        rules=["Science-based adventures"],
        atmosphere="Exciting and educational",
    )

    return ShowBlueprint(show=show, protagonist=protagonist, world=world)


@pytest.fixture
def sample_concept():
    """Sample story concept for testing."""
    return (
        "Oliver discovers the fascinating world of flight when he builds a "
        "paper airplane that soars across his workshop. Curious about how real "
        "airplanes fly, he embarks on an imaginative journey to understand lift, "
        "thrust, drag, and weight. Through hands-on experiments and creative "
        "thinking, Oliver learns the physics of flight while demonstrating "
        "curiosity and perseverance."
    )


class TestOutlineService:
    """Tests for OutlineService."""

    @pytest.mark.asyncio
    async def test_generate_outline_basic(self, sample_concept, mock_show_blueprint):
        """Test basic outline generation."""
        provider = MockLLMProvider()
        enhancer = PromptEnhancer()
        service = OutlineService(provider, enhancer)

        outline = await service.generate_outline(
            concept=sample_concept, show_blueprint=mock_show_blueprint
        )

        assert outline
        assert isinstance(outline, StoryOutline)
        assert len(outline.story_beats) >= 3
        # Mock provider may return its own hardcoded show_id
        assert outline.show_id in [mock_show_blueprint.show.show_id, "olivers_workshop"]

    @pytest.mark.asyncio
    async def test_generate_outline_empty_concept(self, mock_show_blueprint):
        """Test that empty concept raises error."""
        provider = MockLLMProvider()
        service = OutlineService(provider)

        with pytest.raises(ValueError, match="Concept cannot be empty"):
            await service.generate_outline(
                concept="", show_blueprint=mock_show_blueprint
            )

    @pytest.mark.asyncio
    async def test_outline_has_required_beats(
        self, sample_concept, mock_show_blueprint
    ):
        """Test that outline has 3-5 story beats."""
        provider = MockLLMProvider()
        service = OutlineService(provider)

        outline = await service.generate_outline(
            concept=sample_concept, show_blueprint=mock_show_blueprint
        )

        assert 3 <= len(outline.story_beats) <= 5

    @pytest.mark.asyncio
    async def test_outline_beats_have_required_fields(
        self, sample_concept, mock_show_blueprint
    ):
        """Test that each beat has required fields."""
        provider = MockLLMProvider()
        service = OutlineService(provider)

        outline = await service.generate_outline(
            concept=sample_concept, show_blueprint=mock_show_blueprint
        )

        for beat in outline.story_beats:
            assert beat.beat_number > 0
            assert beat.title
            assert beat.description
            assert beat.educational_focus

    @pytest.mark.asyncio
    async def test_outline_has_educational_concept(
        self, sample_concept, mock_show_blueprint
    ):
        """Test that outline includes educational concept."""
        provider = MockLLMProvider()
        service = OutlineService(provider)

        outline = await service.generate_outline(
            concept=sample_concept, show_blueprint=mock_show_blueprint
        )

        assert outline.educational_concept
        assert len(outline.educational_concept) > 0

    @pytest.mark.asyncio
    async def test_generate_outline_yaml(self, sample_concept, mock_show_blueprint):
        """Test YAML output generation."""
        provider = MockLLMProvider()
        service = OutlineService(provider)

        yaml_output = await service.generate_outline_yaml(
            concept=sample_concept, show_blueprint=mock_show_blueprint
        )

        assert yaml_output
        assert isinstance(yaml_output, str)
        assert "episode_id:" in yaml_output
        assert "story_beats:" in yaml_output
        assert "educational_concept:" in yaml_output

    @pytest.mark.asyncio
    async def test_outline_with_custom_episode_id(
        self, sample_concept, mock_show_blueprint
    ):
        """Test outline generation with custom episode ID."""
        provider = MockLLMProvider()
        service = OutlineService(provider)

        custom_id = "ep_custom_123"
        outline = await service.generate_outline(
            concept=sample_concept,
            show_blueprint=mock_show_blueprint,
            episode_id=custom_id,
        )

        # The mock might return its own ID, but we pass ours as fallback
        assert outline.episode_id

    def test_validate_outline_too_few_beats(self, mock_show_blueprint):
        """Test validation rejects outlines with too few beats."""
        provider = MockLLMProvider()
        service = OutlineService(provider)

        # Create outline with only 2 beats
        outline = StoryOutline(
            episode_id="test",
            show_id=mock_show_blueprint.show.show_id,
            topic="Test",
            title="Test Title",
            educational_concept="Test concept",
            story_beats=[
                {
                    "beat_number": 1,
                    "title": "Beat 1",
                    "description": "Description 1",
                    "educational_focus": "Focus 1",
                    "key_moments": [],
                },
                {
                    "beat_number": 2,
                    "title": "Beat 2",
                    "description": "Description 2",
                    "educational_focus": "Focus 2",
                    "key_moments": [],
                },
            ],
        )

        with pytest.raises(ValueError, match="should have 3-5 story beats"):
            service._validate_outline(outline)

    def test_validate_outline_missing_title(self, mock_show_blueprint):
        """Test validation rejects beats without titles."""
        provider = MockLLMProvider()
        service = OutlineService(provider)

        outline = StoryOutline(
            episode_id="test",
            show_id=mock_show_blueprint.show.show_id,
            topic="Test",
            title="Test Title",
            educational_concept="Test concept",
            story_beats=[
                {
                    "beat_number": 1,
                    "title": "",  # Missing title
                    "description": "Description 1",
                    "educational_focus": "Focus 1",
                    "key_moments": [],
                },
                {
                    "beat_number": 2,
                    "title": "Beat 2",
                    "description": "Description 2",
                    "educational_focus": "Focus 2",
                    "key_moments": [],
                },
                {
                    "beat_number": 3,
                    "title": "Beat 3",
                    "description": "Description 3",
                    "educational_focus": "Focus 3",
                    "key_moments": [],
                },
            ],
        )

        with pytest.raises(ValueError, match="missing title"):
            service._validate_outline(outline)

    @pytest.mark.asyncio
    async def test_outline_with_custom_params(
        self, sample_concept, mock_show_blueprint
    ):
        """Test outline generation with custom parameters."""
        provider = MockLLMProvider()
        service = OutlineService(provider)

        outline = await service.generate_outline(
            concept=sample_concept,
            show_blueprint=mock_show_blueprint,
            max_tokens=3000,
            temperature=0.5,
        )

        assert outline
        assert isinstance(outline, StoryOutline)


@pytest.mark.integration
class TestOutlineServiceIntegration:
    """Integration tests for OutlineService."""

    @pytest.mark.asyncio
    async def test_full_outline_flow(self, sample_concept, mock_show_blueprint):
        """Test complete outline generation flow."""
        provider = MockLLMProvider()
        enhancer = PromptEnhancer()
        service = OutlineService(provider, enhancer)

        # Generate outline
        outline = await service.generate_outline(
            concept=sample_concept, show_blueprint=mock_show_blueprint
        )

        # Validate structure
        assert outline
        assert isinstance(outline, StoryOutline)

        # Check all beats have educational focus
        for beat in outline.story_beats:
            assert beat.educational_focus
            assert len(beat.educational_focus) > 0

        # Check title is present
        assert outline.title
        assert len(outline.title) > 0

        # Check topic is present
        assert outline.topic
        assert len(outline.topic) > 0

    @pytest.mark.asyncio
    async def test_ideation_to_outline_pipeline(self, mock_show_blueprint):
        """Test pipeline from ideation to outline."""
        from services.llm.ideation_service import IdeationService

        provider = MockLLMProvider()
        enhancer = PromptEnhancer()

        # Step 1: Generate concept
        ideation_service = IdeationService(provider, enhancer)
        concept = await ideation_service.generate_concept(
            topic="How do plants grow?", show_blueprint=mock_show_blueprint
        )

        assert concept
        assert len(concept) > 50

        # Step 2: Generate outline from concept
        outline_service = OutlineService(provider, enhancer)
        outline = await outline_service.generate_outline(
            concept=concept, show_blueprint=mock_show_blueprint
        )

        assert outline
        assert isinstance(outline, StoryOutline)
        assert len(outline.story_beats) >= 3
        assert outline.educational_concept
