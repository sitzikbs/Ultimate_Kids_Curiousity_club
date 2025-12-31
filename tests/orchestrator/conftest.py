"""Fixtures for orchestrator tests."""

from datetime import UTC, datetime
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock

import pytest

from models import (
    Character,
    ConceptsHistory,
    Episode,
    PipelineStage,
    Protagonist,
    Show,
    ShowBlueprint,
    StoryBeat,
    StoryOutline,
    WorldDescription,
)
from modules.episode_storage import EpisodeStorage
from modules.prompts.enhancer import PromptEnhancer
from modules.show_blueprint_manager import ShowBlueprintManager
from services.llm.ideation_service import IdeationService
from services.llm.outline_service import OutlineService
from services.llm.script_generation_service import ScriptGenerationService
from services.llm.segment_generation_service import SegmentGenerationService


def _import_orchestrator():
    """Lazy import of orchestrator modules using importlib."""
    import importlib.util
    import sys
    from pathlib import Path as PathlibPath

    # Get absolute paths to the modules
    src_path = PathlibPath(__file__).parent.parent.parent / "src"
    pipeline_path = src_path / "orchestrator" / "pipeline.py"
    approval_path = src_path / "orchestrator" / "approval.py"

    # Load pipeline module
    spec_pipeline = importlib.util.spec_from_file_location(
        "orchestrator.pipeline", pipeline_path
    )
    pipeline_module = importlib.util.module_from_spec(spec_pipeline)
    sys.modules["orchestrator.pipeline"] = pipeline_module
    spec_pipeline.loader.exec_module(pipeline_module)

    # Load approval module
    spec_approval = importlib.util.spec_from_file_location(
        "orchestrator.approval", approval_path
    )
    approval_module = importlib.util.module_from_spec(spec_approval)
    sys.modules["orchestrator.approval"] = approval_module
    spec_approval.loader.exec_module(approval_module)

    return pipeline_module.PipelineOrchestrator, approval_module.ApprovalWorkflow


@pytest.fixture
def test_show_blueprint() -> ShowBlueprint:
    """Create a test Show Blueprint."""
    show = Show(
        show_id="test_show",
        title="Test Show",
        description="A test show for unit testing",
        theme="Educational testing",
        narrator_voice_config={"provider": "mock", "voice_id": "narrator"},
    )

    protagonist = Protagonist(
        name="Test Hero",
        age=8,
        description="A curious test character",
        values=["curiosity", "learning"],
        catchphrases=["Let's test it!", "Time to learn!"],
        backstory="Born to test things",
        voice_config={"provider": "mock", "voice_id": "hero"},
    )

    world = WorldDescription(
        setting="A test environment",
        rules=["All tests must pass", "Learning is fun"],
        atmosphere="Educational and friendly",
        locations=[{"name": "Test Lab", "description": "Where tests happen"}],
    )

    return ShowBlueprint(
        show=show,
        protagonist=protagonist,
        world=world,
        characters=[],
        concepts_history=ConceptsHistory(concepts=[], last_updated=datetime.now(UTC)),
        episodes=[],
    )


@pytest.fixture
def test_episode() -> Episode:
    """Create a test episode."""
    return Episode(
        episode_id="test_ep_001",
        show_id="test_show",
        topic="testing fundamentals",
        title="Testing Fundamentals",
        current_stage=PipelineStage.PENDING,
    )


@pytest.fixture
def test_episode_awaiting_approval(test_episode: Episode) -> Episode:
    """Create a test episode in AWAITING_APPROVAL stage."""
    episode = test_episode.model_copy()
    episode.current_stage = PipelineStage.AWAITING_APPROVAL
    episode.approval_status = "pending"
    episode.outline = StoryOutline(
        episode_id=episode.episode_id,
        show_id=episode.show_id,
        topic=episode.topic,
        title=episode.title,
        educational_concept="Test concept",
        story_beats=[
            StoryBeat(
                beat_number=1,
                title="Introduction",
                description="Introduction to testing",
                educational_focus="Basic testing concepts",
                key_moments=["Start testing"],
            )
        ],
    )
    return episode


@pytest.fixture
def mock_ideation_service() -> AsyncMock:
    """Create a mock ideation service."""
    service = AsyncMock(spec=IdeationService)
    service.generate_concept.return_value = "A test concept about testing"
    return service


@pytest.fixture
def mock_outline_service() -> AsyncMock:
    """Create a mock outline service."""
    service = AsyncMock(spec=OutlineService)

    def generate_outline(concept, show_blueprint, episode_id):
        return StoryOutline(
            episode_id=episode_id,
            show_id=show_blueprint.show.show_id,
            topic=concept,
            title="Test Outline",
            educational_concept="Testing concepts",
            story_beats=[
                StoryBeat(
                    beat_number=1,
                    title="Beat 1",
                    description="First beat",
                    educational_focus="Learn testing",
                    key_moments=["Start", "Middle", "End"],
                )
            ],
        )

    service.generate_outline.side_effect = generate_outline
    return service


@pytest.fixture
def mock_segment_service() -> AsyncMock:
    """Create a mock segment service."""
    service = AsyncMock(spec=SegmentGenerationService)
    service.generate_segments.return_value = []
    return service


@pytest.fixture
def mock_script_service() -> AsyncMock:
    """Create a mock script service."""
    service = AsyncMock(spec=ScriptGenerationService)
    service.generate_scripts.return_value = []
    return service


@pytest.fixture
def mock_show_manager(test_show_blueprint: ShowBlueprint, tmp_path: Path) -> MagicMock:
    """Create a mock show blueprint manager."""
    manager = MagicMock(spec=ShowBlueprintManager)
    manager.load_show.return_value = test_show_blueprint
    manager.add_concept.return_value = None
    return manager


@pytest.fixture
def episode_storage(tmp_path: Path) -> EpisodeStorage:
    """Create an episode storage instance with temp directory."""
    return EpisodeStorage(shows_dir=tmp_path)


@pytest.fixture
def prompt_enhancer() -> PromptEnhancer:
    """Create a prompt enhancer instance."""
    return PromptEnhancer()


@pytest.fixture
def orchestrator(
    prompt_enhancer: PromptEnhancer,
    mock_ideation_service: AsyncMock,
    mock_outline_service: AsyncMock,
    mock_segment_service: AsyncMock,
    mock_script_service: AsyncMock,
    mock_show_manager: MagicMock,
    episode_storage: EpisodeStorage,
):
    """Create a pipeline orchestrator with mocked services."""
    PipelineOrchestrator, _ = _import_orchestrator()
    return PipelineOrchestrator(
        prompt_enhancer=prompt_enhancer,
        ideation_service=mock_ideation_service,
        outline_service=mock_outline_service,
        segment_service=mock_segment_service,
        script_service=mock_script_service,
        show_blueprint_manager=mock_show_manager,
        episode_storage=episode_storage,
    )


@pytest.fixture
def approval_workflow(episode_storage: EpisodeStorage):
    """Create an approval workflow instance."""
    _, ApprovalWorkflow = _import_orchestrator()
    return ApprovalWorkflow(episode_storage=episode_storage)
