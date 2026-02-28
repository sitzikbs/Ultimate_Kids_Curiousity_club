"""Shared fixtures for CLI tests."""

from __future__ import annotations

import pytest
from typer.testing import CliRunner

from models.episode import Episode, PipelineStage
from orchestrator.result import PipelineResult, PipelineResultStatus


@pytest.fixture
def cli_runner() -> CliRunner:
    """Typer CliRunner for invoking CLI commands."""
    return CliRunner()


# -----------------------------------------------------------------------
# Sample data — mirrors orchestrator/conftest.py but lighter-weight
# -----------------------------------------------------------------------


@pytest.fixture
def sample_episode() -> Episode:
    """A minimal episode in AWAITING_APPROVAL."""
    return Episode(
        episode_id="ep_test_001",
        show_id="olivers_workshop",
        topic="rockets",
        title="Rockets",
        current_stage=PipelineStage.AWAITING_APPROVAL,
        approval_status="pending",
        concept="A fun look at how rockets work.",
    )


@pytest.fixture
def completed_episode() -> Episode:
    """A fully completed episode."""
    return Episode(
        episode_id="ep_done_001",
        show_id="olivers_workshop",
        topic="volcanoes",
        title="Volcanoes",
        current_stage=PipelineStage.COMPLETE,
        approval_status="approved",
        concept="Why do volcanoes erupt?",
        audio_path="/tmp/volcanoes.mp3",
        total_cost=0.15,
        checkpoints={
            "ideation": {"completed_at": "2025-01-01", "output": {}, "cost": 0.02},
            "outlining": {"completed_at": "2025-01-01", "output": {}, "cost": 0.03},
            "segment_generation": {
                "completed_at": "2025-01-01",
                "output": {},
                "cost": 0.04,
            },
            "script_generation": {
                "completed_at": "2025-01-01",
                "output": {},
                "cost": 0.03,
            },
            "audio_synthesis": {
                "completed_at": "2025-01-01",
                "output": {},
                "cost": 0.02,
            },
            "audio_mixing": {
                "completed_at": "2025-01-01",
                "output": {},
                "cost": 0.01,
            },
        },
    )


@pytest.fixture
def failed_episode() -> Episode:
    """An episode in FAILED state."""
    return Episode(
        episode_id="ep_fail_001",
        show_id="olivers_workshop",
        topic="magnets",
        title="Magnets",
        current_stage=PipelineStage.FAILED,
        last_error={"stage": "audio_synthesis", "error": "TTS down"},
    )


@pytest.fixture
def rejected_episode() -> Episode:
    """An episode in REJECTED state."""
    return Episode(
        episode_id="ep_rej_001",
        show_id="olivers_workshop",
        topic="magnets",
        title="Magnets",
        current_stage=PipelineStage.REJECTED,
        approval_status="rejected",
    )


@pytest.fixture
def approval_result(sample_episode: Episode) -> PipelineResult:
    """PipelineResult for a generate_episode call (approval required)."""
    return PipelineResult(
        status=PipelineResultStatus.APPROVAL_REQUIRED,
        episode=sample_episode,
        message="Awaiting approval",
    )


@pytest.fixture
def completed_result(completed_episode: Episode) -> PipelineResult:
    """PipelineResult for a resume_episode call (completed)."""
    return PipelineResult(
        status=PipelineResultStatus.COMPLETED,
        episode=completed_episode,
        message="Episode complete",
    )
