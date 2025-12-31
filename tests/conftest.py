"""Global pytest fixtures for Ultimate Kids Curiosity Club tests."""

import sys
from pathlib import Path

import pytest

# Add the tests directory to the Python path (append, not insert at beginning)
tests_dir = Path(__file__).parent
if str(tests_dir) not in sys.path:
    sys.path.append(str(tests_dir))

# Add the src directory to the Python path for imports
project_root = tests_dir.parent
src_dir = project_root / "src"
if str(src_dir) not in sys.path:
    sys.path.insert(0, str(src_dir))

# Import fixtures from fixture modules
# Using try/except to handle import during collection phase
try:
    from fixtures.audio import (
        audio_processing_config,
        background_music_metadata,
        episode_audio_metadata,
        mock_audio_segment,
        mock_audio_segments_list,
        silent_mp3_path,
    )
    from fixtures.characters import (
        all_characters,
        generic_character,
        hannah_character,
        narrator_character,
        oliver_character,
    )
    from fixtures.episodes import (
        audio_synthesis_episode,
        complete_episode,
        episode_with_show_blueprint,
        episodes_list,
        new_episode,
        scripting_episode,
    )
    from fixtures.services import (
        mock_audio_mixer,
        mock_image_service,
        mock_llm_service,
        mock_orchestrator,
        mock_tts_service,
        service_settings,
    )
except ImportError:
    # During early import phase, fixtures may not be available yet
    pass

# Re-export fixtures so they're available to tests
__all__ = [
    # Characters
    "oliver_character",
    "hannah_character",
    "narrator_character",
    "all_characters",
    "generic_character",
    # Episodes
    "new_episode",
    "scripting_episode",
    "audio_synthesis_episode",
    "complete_episode",
    "episode_with_show_blueprint",
    "episodes_list",
    # Services
    "mock_llm_service",
    "mock_tts_service",
    "mock_audio_mixer",
    "mock_image_service",
    "mock_orchestrator",
    "service_settings",
    # Audio
    "mock_audio_segment",
    "mock_audio_segments_list",
    "silent_mp3_path",
    "background_music_metadata",
    "audio_processing_config",
    "episode_audio_metadata",
]


@pytest.fixture
def project_root() -> Path:
    """Return the project root directory."""
    return Path(__file__).parent.parent


@pytest.fixture
def test_data_dir(project_root: Path) -> Path:
    """Return the test data directory."""
    return project_root / "data" / "fixtures"


@pytest.fixture
def llm_fixtures_dir(test_data_dir: Path) -> Path:
    """Return the LLM fixtures directory."""
    return test_data_dir / "llm"


@pytest.fixture
def audio_fixtures_dir(test_data_dir: Path) -> Path:
    """Return the audio fixtures directory."""
    return test_data_dir / "audio"


@pytest.fixture
def image_fixtures_dir(test_data_dir: Path) -> Path:
    """Return the image fixtures directory."""
    return test_data_dir / "images"


@pytest.fixture
def mock_mode_settings() -> dict[str, bool]:
    """Settings for mock mode testing."""
    return {
        "USE_MOCK_SERVICES": True,
        "ENABLE_COST_TRACKING": False,
        "LOG_LEVEL": "INFO",
    }


@pytest.fixture
def real_api_settings() -> dict[str, bool]:
    """Settings for real API testing."""
    return {
        "USE_MOCK_SERVICES": False,
        "ENABLE_COST_TRACKING": True,
        "LOG_LEVEL": "INFO",
    }


@pytest.fixture
def cost_tracker():
    """Cost tracker fixture for real API tests.

    Yields a cost tracker that monitors API costs and enforces budget limits.
    Prints a summary at the end of the test session.
    """
    from tests.test_helpers.cost_tracker import CostTracker

    tracker = CostTracker()
    tracker.set_budget_limit(10.0)  # $10 budget per test session
    yield tracker

    # Print summary after tests
    tracker.print_summary()

    # Fail if budget exceeded
    within_budget, _ = tracker.check_budget()
    if not within_budget:
        pytest.fail(
            f"Test suite exceeded budget: ${tracker.get_total_cost():.2f} > "
            f"${tracker._budget_limit:.2f}"
        )


# Note: This is intentionally commented out to document the approach.
# pytest-benchmark plugin provides the 'benchmark' fixture when installed.
# If users get errors about 'benchmark' fixture not found, they should:
#   pip install pytest-benchmark
# or
#   uv add --dev pytest-benchmark
