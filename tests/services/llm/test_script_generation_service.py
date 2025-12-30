"""Tests for ScriptGenerationService."""

import pytest

from models import (
    Protagonist,
    Show,
    ShowBlueprint,
    StorySegment,
    WorldDescription,
)
from modules.prompts.enhancer import PromptEnhancer
from services.llm.cost_tracker import CostTracker
from services.llm.mock_provider import MockLLMProvider
from services.llm.script_generation_service import ScriptGenerationService


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
        catchphrases=["Let's find out!", "Amazing!"],
        voice_config={"voice_id": "test_oliver", "stability": 0.7},
    )

    world = WorldDescription(
        setting="Oliver's Workshop",
        rules=["Science-based adventures"],
        atmosphere="Exciting and educational",
    )

    return ShowBlueprint(show=show, protagonist=protagonist, world=world)


@pytest.fixture
def sample_segments():
    """Create sample segments for testing."""
    return [
        StorySegment(
            segment_number=1,
            beat_number=1,
            description="Oliver is in his workshop examining a model volcano",
            characters_involved=["Oliver"],
            setting="Oliver's Workshop",
            educational_content="Introduction to volcanic eruptions",
        ),
        StorySegment(
            segment_number=2,
            beat_number=1,
            description="Oliver starts experimenting with different materials",
            characters_involved=["Oliver"],
            setting="Oliver's Workshop",
            educational_content="Different types of volcanic rock",
        ),
    ]


class TestScriptGenerationService:
    """Tests for ScriptGenerationService."""

    @pytest.mark.asyncio
    async def test_generate_scripts_basic(
        self, sample_segments, mock_show_blueprint
    ):
        """Test basic script generation."""
        provider = MockLLMProvider()
        enhancer = PromptEnhancer()
        service = ScriptGenerationService(provider, enhancer)

        scripts = await service.generate_scripts(
            segments=sample_segments, show_blueprint=mock_show_blueprint
        )

        assert scripts
        assert isinstance(scripts, list)
        assert len(scripts) == len(sample_segments)

        # Check script structure
        for script in scripts:
            assert script.segment_number > 0
            assert len(script.script_blocks) > 0

    @pytest.mark.asyncio
    async def test_generate_scripts_with_cost_tracker(
        self, sample_segments, mock_show_blueprint
    ):
        """Test script generation with cost tracking."""
        provider = MockLLMProvider()
        enhancer = PromptEnhancer()
        cost_tracker = CostTracker()
        service = ScriptGenerationService(provider, enhancer, cost_tracker)

        scripts = await service.generate_scripts(
            segments=sample_segments, show_blueprint=mock_show_blueprint
        )

        assert scripts
        # Check that cost was tracked
        assert len(cost_tracker.calls) == 1
        assert cost_tracker.calls[0].stage == "script"
        assert cost_tracker.get_episode_cost() >= 0

    @pytest.mark.asyncio
    async def test_generate_scripts_includes_narrator(
        self, sample_segments, mock_show_blueprint
    ):
        """Test that scripts include narrator blocks."""
        provider = MockLLMProvider()
        service = ScriptGenerationService(provider)

        scripts = await service.generate_scripts(
            segments=sample_segments, show_blueprint=mock_show_blueprint
        )

        # Check that at least some scripts have narrator
        has_narrator = False
        for script in scripts:
            for block in script.script_blocks:
                if block.speaker.upper() in ("NARRATOR", "NARRATION"):
                    has_narrator = True
                    break

        assert has_narrator, "Scripts should include narrator blocks"

    @pytest.mark.asyncio
    async def test_generate_scripts_empty_segments(self, mock_show_blueprint):
        """Test that empty segments raises error."""
        provider = MockLLMProvider()
        service = ScriptGenerationService(provider)

        with pytest.raises(ValueError, match="cannot be empty"):
            await service.generate_scripts(
                segments=[], show_blueprint=mock_show_blueprint
            )

    @pytest.mark.asyncio
    async def test_generate_scripts_with_custom_params(
        self, sample_segments, mock_show_blueprint
    ):
        """Test script generation with custom parameters."""
        provider = MockLLMProvider()
        service = ScriptGenerationService(provider)

        scripts = await service.generate_scripts(
            segments=sample_segments,
            show_blueprint=mock_show_blueprint,
            max_tokens=3000,
            temperature=0.5,
        )

        assert scripts
        assert len(scripts) == len(sample_segments)

    @pytest.mark.asyncio
    async def test_script_blocks_have_duration(
        self, sample_segments, mock_show_blueprint
    ):
        """Test that all script blocks have duration estimates."""
        provider = MockLLMProvider()
        service = ScriptGenerationService(provider)

        scripts = await service.generate_scripts(
            segments=sample_segments, show_blueprint=mock_show_blueprint
        )

        for script in scripts:
            for block in script.script_blocks:
                assert block.duration_estimate is not None
                assert block.duration_estimate > 0

    @pytest.mark.asyncio
    async def test_script_blocks_have_required_fields(
        self, sample_segments, mock_show_blueprint
    ):
        """Test that script blocks have all required fields."""
        provider = MockLLMProvider()
        service = ScriptGenerationService(provider)

        scripts = await service.generate_scripts(
            segments=sample_segments, show_blueprint=mock_show_blueprint
        )

        for script in scripts:
            for block in script.script_blocks:
                assert block.speaker
                assert block.text
                assert block.speaker_voice_id
                assert block.duration_estimate

    def test_estimate_durations(self):
        """Test duration estimation for script blocks."""
        provider = MockLLMProvider()
        service = ScriptGenerationService(provider)

        from models import ScriptBlock

        # Create blocks without duration
        blocks = [
            ScriptBlock(
                speaker="NARRATOR",
                text="This is a test sentence with exactly ten words here.",
                speaker_voice_id="narrator",
                duration_estimate=None,
            ),
            ScriptBlock(
                speaker="OLIVER",
                text="Short text",
                speaker_voice_id="oliver",
                duration_estimate=None,
            ),
        ]

        # Estimate durations
        result = service._estimate_durations(blocks)

        # Check that durations were added
        for block in result:
            assert block.duration_estimate is not None
            assert block.duration_estimate > 0

    def test_organize_into_scripts(self, sample_segments):
        """Test organizing script blocks into scripts."""
        provider = MockLLMProvider()
        service = ScriptGenerationService(provider)

        from models import ScriptBlock

        # Create 6 blocks for 2 segments
        blocks = [
            ScriptBlock(
                speaker="NARRATOR",
                text=f"Block {i}",
                speaker_voice_id="narrator",
                duration_estimate=3.0,
            )
            for i in range(6)
        ]

        scripts = service._organize_into_scripts(blocks, sample_segments)

        assert len(scripts) == len(sample_segments)
        # Each script should have ~3 blocks (6 blocks / 2 segments)
        assert all(len(s.script_blocks) >= 2 for s in scripts)

    def test_validate_scripts_empty(self):
        """Test validation fails on empty scripts."""
        provider = MockLLMProvider()
        service = ScriptGenerationService(provider)

        with pytest.raises(ValueError, match="No scripts generated"):
            service._validate_scripts([], [])

    def test_validate_scripts_count_mismatch(self, sample_segments):
        """Test validation fails when script count doesn't match segments."""
        provider = MockLLMProvider()
        service = ScriptGenerationService(provider)

        from models import Script

        # Create only 1 script but have 2 segments
        scripts = [Script(segment_number=1, script_blocks=[])]

        with pytest.raises(ValueError, match="Expected 2 scripts"):
            service._validate_scripts(scripts, sample_segments)


@pytest.mark.integration
class TestScriptGenerationServiceIntegration:
    """Integration tests for ScriptGenerationService."""

    @pytest.mark.asyncio
    async def test_full_script_generation_flow(
        self, sample_segments, mock_show_blueprint
    ):
        """Test complete script generation flow."""
        provider = MockLLMProvider()
        enhancer = PromptEnhancer()
        cost_tracker = CostTracker()
        service = ScriptGenerationService(provider, enhancer, cost_tracker)

        # Generate scripts
        scripts = await service.generate_scripts(
            segments=sample_segments, show_blueprint=mock_show_blueprint
        )

        # Validate outputs
        assert scripts
        assert len(scripts) == len(sample_segments)

        # Check script structure
        for i, script in enumerate(scripts):
            assert script.segment_number == sample_segments[i].segment_number
            assert len(script.script_blocks) > 0

            # Check blocks
            for block in script.script_blocks:
                assert block.speaker
                assert block.text
                assert block.speaker_voice_id
                assert block.duration_estimate > 0

        # Check cost tracking
        report = cost_tracker.export_report()
        assert report["total_cost"] >= 0
        assert "script" in report["stage_breakdown"]

    @pytest.mark.asyncio
    async def test_script_total_duration(
        self, sample_segments, mock_show_blueprint
    ):
        """Test that scripts have reasonable total duration."""
        provider = MockLLMProvider()
        service = ScriptGenerationService(provider)

        scripts = await service.generate_scripts(
            segments=sample_segments, show_blueprint=mock_show_blueprint
        )

        # Calculate total duration
        for script in scripts:
            total_duration = sum(
                block.duration_estimate for block in script.script_blocks
            )
            assert total_duration > 0
            # Should be reasonable (not too short or too long)
            assert 1 < total_duration < 600  # Between 1 second and 10 minutes
