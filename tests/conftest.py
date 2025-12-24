"""Global pytest fixtures for Ultimate Kids Curiosity Club tests."""

from pathlib import Path

import pytest

from tests.fixtures.audio import (
    audio_processing_config,
    background_music_metadata,
    episode_audio_metadata,
    mock_audio_segment,
    mock_audio_segments_list,
    silent_mp3_path,
)

# Import fixtures from fixture modules
from tests.fixtures.characters import (
    all_characters,
    generic_character,
    hannah_character,
    narrator_character,
    oliver_character,
)
from tests.fixtures.episodes import (
    audio_synthesis_episode,
    complete_episode,
    episode_with_show_blueprint,
    episodes_list,
    new_episode,
    scripting_episode,
)
from tests.fixtures.services import (
    mock_audio_mixer,
    mock_image_service,
    mock_llm_service,
    mock_orchestrator,
    mock_tts_service,
    service_settings,
)

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
