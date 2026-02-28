"""Shared fixtures for orchestrator tests."""

from pathlib import Path
from unittest.mock import AsyncMock, MagicMock

import pytest

from models.episode import Episode
from models.show import (
    Character,
    ConceptsHistory,
    Protagonist,
    Show,
    ShowBlueprint,
    WorldDescription,
)
from models.story import (
    Script,
    ScriptBlock,
    StoryBeat,
    StoryOutline,
    StorySegment,
)
from modules.episode_storage import EpisodeStorage
from modules.show_blueprint_manager import ShowBlueprintManager
from orchestrator.approval import ApprovalWorkflow
from orchestrator.pipeline import PipelineOrchestrator
from services.tts.synthesis_service import AudioSegmentResult

# ---------------------------------------------------------------------------
# Show Blueprint fixture
# ---------------------------------------------------------------------------


@pytest.fixture
def sample_show() -> Show:
    """Minimal Show model for testing."""
    return Show(
        show_id="olivers_workshop",
        title="Oliver's STEM Adventures",
        description="Fun STEM explorations",
        theme="Science and Engineering",
        narrator_voice_config={
            "provider": "mock",
            "voice_id": "mock_narrator",
            "stability": 0.7,
        },
    )


@pytest.fixture
def sample_protagonist() -> Protagonist:
    """Minimal Protagonist for testing."""
    return Protagonist(
        name="Oliver",
        age=10,
        description="A curious young inventor",
        values=["curiosity", "creativity"],
        catchphrases=["Let's find out!"],
        backstory="Loves building things in his workshop",
        voice_config={
            "provider": "mock",
            "voice_id": "mock_oliver",
            "stability": 0.5,
        },
    )


@pytest.fixture
def sample_world() -> WorldDescription:
    """Minimal WorldDescription for testing."""
    return WorldDescription(
        setting="Oliver's Workshop",
        rules=["Physics applies", "Imagination helps"],
        atmosphere="Bright and cheerful",
        locations=[
            {"name": "The Workshop", "description": "Full of tools and gadgets"}
        ],
    )


@pytest.fixture
def sample_characters() -> list[Character]:
    """Supporting characters for testing."""
    return [
        Character(
            name="Robbie Robot",
            role="Assistant",
            description="A friendly helper robot",
            personality="Enthusiastic and literal-minded",
            voice_config={
                "provider": "mock",
                "voice_id": "mock_robbie",
                "stability": 0.4,
            },
        ),
    ]


@pytest.fixture
def sample_blueprint(
    sample_show: Show,
    sample_protagonist: Protagonist,
    sample_world: WorldDescription,
    sample_characters: list[Character],
) -> ShowBlueprint:
    """Complete ShowBlueprint for testing."""
    return ShowBlueprint(
        show=sample_show,
        protagonist=sample_protagonist,
        world=sample_world,
        characters=sample_characters,
        concepts_history=ConceptsHistory(),
        episodes=[],
    )


# ---------------------------------------------------------------------------
# Story model fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def sample_concept() -> str:
    """Sample ideation concept text."""
    return (
        "Oliver discovers that rockets work by pushing hot gas "
        "downward, which propels them upward — Newton's Third Law "
        "in action! He decides to build a model rocket in his "
        "workshop to see the science for himself."
    )


@pytest.fixture
def sample_outline() -> StoryOutline:
    """Sample story outline with beats."""
    return StoryOutline(
        episode_id="ep_test",
        show_id="olivers_workshop",
        topic="rockets",
        title="Rockets and Newton's Third Law",
        educational_concept="Newton's Third Law of Motion",
        story_beats=[
            StoryBeat(
                beat_number=1,
                title="The Big Question",
                description="Oliver wonders how rockets fly",
                educational_focus="Introducing action-reaction forces",
                key_moments=["Oliver sees a rocket launch on TV"],
            ),
            StoryBeat(
                beat_number=2,
                title="Building the Rocket",
                description="Oliver builds a model rocket",
                educational_focus="Newton's Third Law explanation",
                key_moments=["Robbie helps with the fins"],
            ),
            StoryBeat(
                beat_number=3,
                title="Launch Day",
                description="The rocket launches successfully",
                educational_focus="Applying the concept practically",
                key_moments=["Countdown and liftoff"],
            ),
        ],
    )


@pytest.fixture
def sample_segments() -> list[StorySegment]:
    """Sample story segments."""
    return [
        StorySegment(
            segment_number=1,
            beat_number=1,
            description="Oliver watches a rocket launch on TV",
            characters_involved=["Oliver", "Narrator"],
            setting="Oliver's Workshop",
            educational_content="Rockets use thrust to overcome gravity",
        ),
        StorySegment(
            segment_number=2,
            beat_number=2,
            description="Oliver and Robbie build a model rocket",
            characters_involved=["Oliver", "Robbie Robot"],
            setting="Workshop bench",
            educational_content="Newton's Third Law: every action has a reaction",
        ),
    ]


@pytest.fixture
def sample_scripts() -> list[Script]:
    """Sample scripts with dialogue blocks."""
    return [
        Script(
            segment_number=1,
            script_blocks=[
                ScriptBlock(
                    speaker="Narrator",
                    text="One sunny morning, Oliver was watching TV in his workshop.",
                    speaker_voice_id="mock_narrator",
                    duration_estimate=3.0,
                ),
                ScriptBlock(
                    speaker="Oliver",
                    text="Wow, look at that rocket go! I wonder how it works!",
                    speaker_voice_id="mock_oliver",
                    duration_estimate=2.5,
                ),
            ],
        ),
        Script(
            segment_number=2,
            script_blocks=[
                ScriptBlock(
                    speaker="Narrator",
                    text="Oliver headed to his workbench with Robbie.",
                    speaker_voice_id="mock_narrator",
                    duration_estimate=2.0,
                ),
                ScriptBlock(
                    speaker="Oliver",
                    text="Let's find out! We'll build our own rocket!",
                    speaker_voice_id="mock_oliver",
                    duration_estimate=2.0,
                ),
            ],
        ),
    ]


# ---------------------------------------------------------------------------
# Mock services
# ---------------------------------------------------------------------------


@pytest.fixture
def mock_prompt_enhancer() -> MagicMock:
    """Mock PromptEnhancer."""
    mock = MagicMock()
    mock.enhance_ideation_prompt.return_value = "Enhanced ideation prompt"
    mock.enhance_outline_prompt.return_value = "Enhanced outline prompt"
    mock.enhance_segment_prompt.return_value = "Enhanced segment prompt"
    mock.enhance_script_prompt.return_value = "Enhanced script prompt"
    return mock


@pytest.fixture
def mock_ideation_service(sample_concept: str) -> MagicMock:
    """Mock IdeationService with async generate_concept."""
    mock = MagicMock()
    mock.generate_concept = AsyncMock(return_value=sample_concept)
    return mock


@pytest.fixture
def mock_outline_service(sample_outline: StoryOutline) -> MagicMock:
    """Mock OutlineService with async generate_outline."""
    mock = MagicMock()
    mock.generate_outline = AsyncMock(return_value=sample_outline)
    return mock


@pytest.fixture
def mock_segment_service(sample_segments: list[StorySegment]) -> MagicMock:
    """Mock SegmentGenerationService with async generate_segments."""
    mock = MagicMock()
    mock.generate_segments = AsyncMock(return_value=sample_segments)
    return mock


@pytest.fixture
def mock_script_service(sample_scripts: list[Script]) -> MagicMock:
    """Mock ScriptGenerationService with async generate_scripts."""
    mock = MagicMock()
    mock.generate_scripts = AsyncMock(return_value=sample_scripts)
    return mock


@pytest.fixture
def mock_synthesis_service(tmp_path: Path) -> MagicMock:
    """Mock AudioSynthesisService that creates actual files."""
    mock = MagicMock()

    call_counter = {"n": 0}

    def _synth(
        text: str,
        character_id: str,
        voice_config: dict,
        segment_number: int,
        emotion: str | None = None,
    ) -> AudioSegmentResult:
        call_counter["n"] += 1
        audio_path = tmp_path / f"segment_{call_counter['n']:03d}_{character_id}.mp3"
        # Create a minimal valid file so mixer can read it
        audio_path.write_bytes(b"\x00" * 100)
        return AudioSegmentResult(
            segment_number=segment_number,
            character_id=character_id,
            text=text,
            audio_path=audio_path,
            duration=len(text.split()) / 150 * 60,
            characters=len(text),
        )

    mock.synthesize_segment = MagicMock(side_effect=_synth)
    return mock


@pytest.fixture
def mock_audio_mixer_service(tmp_path: Path) -> MagicMock:
    """Mock AudioMixer that returns a pydub-like AudioSegment stub."""
    mock = MagicMock()

    # mix_segments returns an object with .export()
    audio_segment = MagicMock()
    audio_segment.export = MagicMock()
    mock.mix_segments.return_value = audio_segment

    return mock


@pytest.fixture
def mock_show_manager(sample_blueprint: ShowBlueprint) -> MagicMock:
    """Mock ShowBlueprintManager."""
    mock = MagicMock(spec=ShowBlueprintManager)
    mock.load_show.return_value = sample_blueprint
    mock.add_concept.return_value = None
    return mock


@pytest.fixture
def mock_episode_storage(tmp_path: Path) -> MagicMock:
    """Mock EpisodeStorage that stores episodes in memory."""
    mock = MagicMock(spec=EpisodeStorage)

    episodes: dict[str, Episode] = {}

    def _save(episode: Episode) -> None:
        key = f"{episode.show_id}/{episode.episode_id}"
        episodes[key] = episode.model_copy(deep=True)

    def _load(show_id: str, episode_id: str) -> Episode:
        key = f"{show_id}/{episode_id}"
        if key not in episodes:
            raise FileNotFoundError(f"Episode not found: {episode_id}")
        return episodes[key].model_copy(deep=True)

    def _list(show_id: str) -> list[str]:
        return [k.split("/")[1] for k in episodes if k.startswith(f"{show_id}/")]

    def _get_path(show_id: str, episode_id: str) -> Path:
        p = tmp_path / show_id / "episodes" / episode_id
        p.mkdir(parents=True, exist_ok=True)
        return p

    mock.save_episode.side_effect = _save
    mock.load_episode.side_effect = _load
    mock.list_episodes.side_effect = _list
    mock.get_episode_path.side_effect = _get_path

    # Expose the internal store for test assertions
    mock._episodes = episodes

    return mock


@pytest.fixture
def mock_event_callback() -> AsyncMock:
    """Async event callback that records all events."""
    return AsyncMock()


# ---------------------------------------------------------------------------
# Orchestrator & approval workflow fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def orchestrator(
    mock_prompt_enhancer: MagicMock,
    mock_ideation_service: MagicMock,
    mock_outline_service: MagicMock,
    mock_segment_service: MagicMock,
    mock_script_service: MagicMock,
    mock_synthesis_service: MagicMock,
    mock_audio_mixer_service: MagicMock,
    mock_show_manager: MagicMock,
    mock_episode_storage: MagicMock,
    mock_event_callback: AsyncMock,
) -> PipelineOrchestrator:
    """Fully wired PipelineOrchestrator with mock services."""
    return PipelineOrchestrator(
        prompt_enhancer=mock_prompt_enhancer,
        ideation_service=mock_ideation_service,
        outline_service=mock_outline_service,
        segment_service=mock_segment_service,
        script_service=mock_script_service,
        synthesis_service=mock_synthesis_service,
        audio_mixer=mock_audio_mixer_service,
        show_blueprint_manager=mock_show_manager,
        episode_storage=mock_episode_storage,
        event_callback=mock_event_callback,
    )


@pytest.fixture
def approval_workflow(
    mock_episode_storage: MagicMock,
    mock_event_callback: AsyncMock,
) -> ApprovalWorkflow:
    """ApprovalWorkflow wired with mock storage."""
    return ApprovalWorkflow(
        episode_storage=mock_episode_storage,
        event_callback=mock_event_callback,
    )
