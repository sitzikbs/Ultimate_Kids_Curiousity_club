"""Tests for SegmentGenerationService."""

import pytest

from models import (
    Protagonist,
    Show,
    ShowBlueprint,
    StoryBeat,
    StoryOutline,
    WorldDescription,
)
from modules.prompts.enhancer import PromptEnhancer
from services.llm.cost_tracker import CostTracker
from services.llm.mock_provider import MockLLMProvider
from services.llm.segment_generation_service import SegmentGenerationService


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
def sample_outline():
    """Create a sample story outline for testing."""
    return StoryOutline(
        episode_id="test_episode",
        show_id="test_show",
        topic="How Things Work",
        title="Oliver's Discovery",
        educational_concept="Scientific inquiry",
        story_beats=[
            StoryBeat(
                beat_number=1,
                title="The Question",
                description="Oliver discovers something puzzling",
                educational_focus="Introduction to scientific observation",
                key_moments=["Oliver notices something unusual"],
            ),
            StoryBeat(
                beat_number=2,
                title="The Investigation",
                description="Oliver explores and experiments",
                educational_focus="Scientific method and experimentation",
                key_moments=["Oliver tests his ideas"],
            ),
        ],
    )


class TestSegmentGenerationService:
    """Tests for SegmentGenerationService."""

    @pytest.mark.asyncio
    async def test_generate_segments_basic(
        self, sample_outline, mock_show_blueprint
    ):
        """Test basic segment generation."""
        provider = MockLLMProvider()
        enhancer = PromptEnhancer()
        service = SegmentGenerationService(provider, enhancer)

        segments = await service.generate_segments(
            outline=sample_outline, show_blueprint=mock_show_blueprint
        )

        assert segments
        assert isinstance(segments, list)
        assert len(segments) > 0
        # Check that segments have required fields
        for segment in segments:
            assert segment.segment_number > 0
            assert segment.beat_number > 0
            assert segment.description
            assert segment.setting
            assert segment.educational_content
            assert segment.characters_involved

    @pytest.mark.asyncio
    async def test_generate_segments_with_cost_tracker(
        self, sample_outline, mock_show_blueprint
    ):
        """Test segment generation with cost tracking."""
        provider = MockLLMProvider()
        enhancer = PromptEnhancer()
        cost_tracker = CostTracker()
        service = SegmentGenerationService(provider, enhancer, cost_tracker)

        segments = await service.generate_segments(
            outline=sample_outline, show_blueprint=mock_show_blueprint
        )

        assert segments
        # Check that cost was tracked
        assert len(cost_tracker.calls) == 1
        assert cost_tracker.calls[0].stage == "segment"
        assert cost_tracker.get_episode_cost() >= 0

    @pytest.mark.asyncio
    async def test_generate_segments_empty_outline(self, mock_show_blueprint):
        """Test that empty outline raises error."""
        provider = MockLLMProvider()
        service = SegmentGenerationService(provider)

        outline = StoryOutline(
            episode_id="test",
            show_id="test",
            topic="Test",
            title="Test",
            educational_concept="Test",
            story_beats=[],  # Empty beats
        )

        with pytest.raises(ValueError, match="at least one story beat"):
            await service.generate_segments(
                outline=outline, show_blueprint=mock_show_blueprint
            )

    @pytest.mark.asyncio
    async def test_generate_segments_validates_beats(
        self, sample_outline, mock_show_blueprint
    ):
        """Test that segments cover all beats."""
        provider = MockLLMProvider()
        service = SegmentGenerationService(provider)

        segments = await service.generate_segments(
            outline=sample_outline, show_blueprint=mock_show_blueprint
        )

        # Check that all beats are represented
        beat_numbers = {beat.beat_number for beat in sample_outline.story_beats}
        segment_beats = {seg.beat_number for seg in segments}

        # All beats should have at least one segment
        assert beat_numbers.issubset(segment_beats)

    @pytest.mark.asyncio
    async def test_generate_segments_with_custom_params(
        self, sample_outline, mock_show_blueprint
    ):
        """Test segment generation with custom parameters."""
        provider = MockLLMProvider()
        service = SegmentGenerationService(provider)

        segments = await service.generate_segments(
            outline=sample_outline,
            show_blueprint=mock_show_blueprint,
            max_tokens=2000,
            temperature=0.5,
        )

        assert segments
        assert len(segments) > 0

    @pytest.mark.asyncio
    async def test_validate_segments_missing_beats(self, mock_show_blueprint):
        """Test validation fails when segments missing for beats."""
        provider = MockLLMProvider()
        service = SegmentGenerationService(provider)

        outline = StoryOutline(
            episode_id="test",
            show_id="test",
            topic="Test",
            title="Test",
            educational_concept="Test",
            story_beats=[
                StoryBeat(
                    beat_number=1,
                    title="Beat 1",
                    description="Test",
                    educational_focus="Test",
                ),
                StoryBeat(
                    beat_number=2,
                    title="Beat 2",
                    description="Test",
                    educational_focus="Test",
                ),
            ],
        )

        # Create segments with only beat 1
        from models import StorySegment

        segments = [
            StorySegment(
                segment_number=1,
                beat_number=1,
                description="Test",
                characters_involved=["Oliver"],
                setting="Workshop",
                educational_content="Test",
            )
        ]

        # This should raise error about missing beat 2
        with pytest.raises(ValueError, match="Missing segments for beats"):
            service._validate_segments(segments, outline)

    def test_validate_segments_missing_fields(self):
        """Test validation catches missing required fields."""
        provider = MockLLMProvider()
        service = SegmentGenerationService(provider)

        from models import StorySegment

        # Create segment with missing description
        segments = [
            StorySegment(
                segment_number=1,
                beat_number=1,
                description="",  # Empty
                characters_involved=["Oliver"],
                setting="Workshop",
                educational_content="Test",
            )
        ]

        outline = StoryOutline(
            episode_id="test",
            show_id="test",
            topic="Test",
            title="Test",
            educational_concept="Test",
            story_beats=[
                StoryBeat(
                    beat_number=1,
                    title="Beat 1",
                    description="Test",
                    educational_focus="Test",
                )
            ],
        )

        with pytest.raises(ValueError, match="missing description"):
            service._validate_segments(segments, outline)


@pytest.mark.integration
class TestSegmentGenerationServiceIntegration:
    """Integration tests for SegmentGenerationService."""

    @pytest.mark.asyncio
    async def test_full_segment_generation_flow(
        self, sample_outline, mock_show_blueprint
    ):
        """Test complete segment generation flow."""
        provider = MockLLMProvider()
        enhancer = PromptEnhancer()
        cost_tracker = CostTracker()
        service = SegmentGenerationService(provider, enhancer, cost_tracker)

        # Generate segments
        segments = await service.generate_segments(
            outline=sample_outline, show_blueprint=mock_show_blueprint
        )

        # Validate outputs
        assert segments
        assert len(segments) >= len(sample_outline.story_beats)

        # Check segment structure
        for segment in segments:
            assert segment.segment_number > 0
            assert segment.beat_number in [1, 2]  # Should match our beats
            assert len(segment.description) > 20
            assert segment.setting
            assert segment.educational_content
            assert len(segment.characters_involved) > 0

        # Check cost tracking
        report = cost_tracker.export_report()
        assert report["total_cost"] >= 0
        assert "segment" in report["stage_breakdown"]
