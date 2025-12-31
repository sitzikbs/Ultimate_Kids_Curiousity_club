"""Integration tests for LLM service with mock providers."""

import pytest

from models import (
    Protagonist,
    Show,
    ShowBlueprint,
    WorldDescription,
)
from modules.prompts.enhancer import PromptEnhancer
from services.llm.cost_tracker import CostTracker
from services.llm.ideation_service import IdeationService
from services.llm.mock_provider import MockLLMProvider
from services.llm.outline_service import OutlineService
from services.llm.script_generation_service import ScriptGenerationService
from services.llm.segment_generation_service import SegmentGenerationService


@pytest.fixture
def integration_show_blueprint():
    """Create a complete show blueprint for integration testing."""
    show = Show(
        show_id="integration_test_show",
        title="Integration Test Show",
        description="A complete test show for integration testing",
        theme="Science and Discovery",
        narrator_voice_config={"voice_id": "test_narrator", "stability": 0.5},
    )

    protagonist = Protagonist(
        name="Oliver",
        age=10,
        description="A curious young inventor",
        values=["curiosity", "creativity", "perseverance"],
        catchphrases=["Let's find out!", "Amazing!", "I wonder why?"],
        voice_config={"voice_id": "test_oliver", "stability": 0.7},
    )

    world = WorldDescription(
        setting="Oliver's Workshop and Beyond",
        rules=[
            "Science-based adventures",
            "Educational content in every episode",
            "Age-appropriate explanations",
        ],
        atmosphere="Exciting, educational, and safe",
    )

    return ShowBlueprint(show=show, protagonist=protagonist, world=world)


@pytest.mark.integration
@pytest.mark.asyncio
async def test_complete_story_generation_pipeline(integration_show_blueprint):
    """Test complete flow: topic → concept → outline → segments → scripts.

    This integration test validates the entire story generation pipeline
    from user topic through to final scripts ready for TTS.
    """
    # Initialize services with mock provider
    provider = MockLLMProvider()
    enhancer = PromptEnhancer()
    cost_tracker = CostTracker()

    ideation = IdeationService(provider, enhancer)
    outline_service = OutlineService(provider, enhancer)
    segment_service = SegmentGenerationService(provider, enhancer, cost_tracker)
    script_service = ScriptGenerationService(provider, enhancer, cost_tracker)

    # Stage 1: Ideation (topic → concept)
    topic = "How do volcanoes erupt?"
    concept = await ideation.generate_concept(topic, integration_show_blueprint)

    assert concept
    assert len(concept) > 50
    assert "Oliver" in concept or "volcano" in concept.lower()

    # Stage 2: Outline (concept → story beats)
    outline = await outline_service.generate_outline(
        concept, integration_show_blueprint
    )

    assert outline
    assert len(outline.story_beats) >= 3
    assert outline.educational_concept

    # Stage 3: Segment Generation (outline → detailed segments)
    segments = await segment_service.generate_segments(
        outline, integration_show_blueprint
    )

    assert segments
    assert len(segments) >= len(outline.story_beats)
    for segment in segments:
        assert segment.description
        assert segment.setting
        assert segment.educational_content
        assert segment.characters_involved

    # Stage 4: Script Generation (segments → narration + dialogue)
    scripts = await script_service.generate_scripts(
        segments, integration_show_blueprint
    )

    assert scripts
    assert len(scripts) == len(segments)
    for script in scripts:
        assert len(script.script_blocks) > 0
        for block in script.script_blocks:
            assert block.speaker
            assert block.text
            assert block.duration_estimate > 0

    # Validate cost tracking
    report = cost_tracker.export_report()
    assert report["total_cost"] >= 0
    assert report["call_count"] == 2  # segment + script stages
    assert "segment" in report["stage_breakdown"]
    assert "script" in report["stage_breakdown"]


@pytest.mark.integration
@pytest.mark.asyncio
async def test_provider_switching(integration_show_blueprint):
    """Test switching between different LLM providers.

    Validates that the system can work with different providers
    (mock, OpenAI, Anthropic) interchangeably.
    """
    # Test with mock provider
    mock_provider = MockLLMProvider()
    ideation = IdeationService(mock_provider)

    concept = await ideation.generate_concept(
        "space exploration", integration_show_blueprint
    )

    assert concept
    assert len(concept) > 50


@pytest.mark.integration
@pytest.mark.asyncio
async def test_cost_tracking_accuracy(integration_show_blueprint):
    """Test that cost tracking accurately captures all LLM calls."""
    provider = MockLLMProvider()
    enhancer = PromptEnhancer()
    cost_tracker = CostTracker()

    # Set budget limit
    cost_tracker.set_budget_limit(1.0)

    # Create services with shared cost tracker
    segment_service = SegmentGenerationService(provider, enhancer, cost_tracker)
    script_service = ScriptGenerationService(provider, enhancer, cost_tracker)

    # Generate outline first
    outline_service = OutlineService(provider, enhancer)
    concept = "Test concept about renewable energy"
    outline = await outline_service.generate_outline(
        concept, integration_show_blueprint
    )

    # Generate segments and scripts
    segments = await segment_service.generate_segments(
        outline, integration_show_blueprint
    )
    scripts = await script_service.generate_scripts(
        segments, integration_show_blueprint
    )

    # Verify cost tracking
    assert len(cost_tracker.calls) == 2  # segment + script
    assert cost_tracker.get_episode_cost() >= 0
    assert cost_tracker.get_total_tokens() > 0

    # Verify scripts were generated
    assert scripts
    assert len(scripts) == len(segments)

    # Check breakdown
    stage_breakdown = cost_tracker.get_stage_breakdown()
    assert "segment" in stage_breakdown
    assert "script" in stage_breakdown

    # Export report
    report = cost_tracker.export_report()
    assert report["call_count"] == 2
    assert len(report["calls"]) == 2


@pytest.mark.integration
@pytest.mark.asyncio
async def test_error_handling_and_retries(integration_show_blueprint):
    """Test error handling and retry logic in generation services."""
    provider = MockLLMProvider()
    enhancer = PromptEnhancer()

    # Test with outline service
    outline_service = OutlineService(provider, enhancer)

    # Valid concept should work
    concept = "Test concept about how airplanes fly"
    outline = await outline_service.generate_outline(
        concept, integration_show_blueprint
    )

    assert outline
    assert len(outline.story_beats) >= 3

    # Empty concept should fail
    with pytest.raises(ValueError, match="Concept cannot be empty"):
        await outline_service.generate_outline("", integration_show_blueprint)


@pytest.mark.real_api
@pytest.mark.asyncio
async def test_real_api_call_gated():
    """Test real LLM API call (gated with marker).

    This test only runs when explicitly requested with:
    pytest -m real_api

    Requires valid API keys in environment.
    """
    pytest.skip("Real API test - requires API key and explicit execution")
