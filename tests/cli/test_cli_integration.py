"""End-to-end CLI integration tests for episode workflows (Task 7.7).

Validates the full create → approve → resume → complete workflow,
as well as create → reject → retry paths, all via the Typer CLI runner.
"""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from typer.testing import CliRunner

from cli.main import app
from models.episode import Episode, PipelineStage
from orchestrator.result import PipelineResult, PipelineResultStatus


@pytest.fixture
def cli_runner() -> CliRunner:
    return CliRunner()


# ---------------------------------------------------------------------------
# Shared mock factories
# ---------------------------------------------------------------------------


def _make_episode(
    episode_id: str = "ep_int_001",
    stage: PipelineStage = PipelineStage.AWAITING_APPROVAL,
    **overrides,
) -> Episode:
    defaults = dict(
        episode_id=episode_id,
        show_id="olivers_workshop",
        topic="rockets",
        title="Rockets",
        concept="Rockets go up!",
        current_stage=stage,
        approval_status="pending",
    )
    defaults.update(overrides)
    return Episode(**defaults)


def _approval_result(episode: Episode) -> PipelineResult:
    return PipelineResult(
        status=PipelineResultStatus.APPROVAL_REQUIRED,
        episode=episode,
        message="Awaiting approval",
    )


def _completed_result(episode: Episode) -> PipelineResult:
    completed = episode.model_copy(
        update={
            "current_stage": PipelineStage.COMPLETE,
            "approval_status": "approved",
            "audio_path": "/tmp/rockets.mp3",
            "total_cost": 0.10,
        }
    )
    return PipelineResult(
        status=PipelineResultStatus.COMPLETED,
        episode=completed,
        message="Complete",
    )


# ---------------------------------------------------------------------------
# Full workflow: create → approve → resume → complete
# ---------------------------------------------------------------------------


class TestCreateApproveResumeWorkflow:
    """Integration: create → approve → resume → complete."""

    def test_full_happy_path(self, cli_runner: CliRunner):
        """Create, approve, then resume to completion."""
        episode = _make_episode()
        approval_res = _approval_result(episode)
        completed_res = _completed_result(episode)

        mock_pipeline = MagicMock()
        mock_pipeline.generate_episode = AsyncMock(return_value=approval_res)
        mock_pipeline.resume_episode = AsyncMock(return_value=completed_res)

        mock_wf = MagicMock()

        # Step 1: Create episode
        with patch("cli.episodes.create_pipeline", return_value=mock_pipeline):
            result = cli_runner.invoke(
                app,
                ["episodes", "create", "olivers_workshop", "rockets"],
            )
        assert result.exit_code == 0
        assert "ep_int_001" in result.stdout

        # Step 2: Approve
        with patch("cli.episodes.create_approval_workflow", return_value=mock_wf):
            result = cli_runner.invoke(
                app,
                ["episodes", "approve", "olivers_workshop", "ep_int_001"],
            )
        assert result.exit_code == 0
        assert "approved" in result.stdout.lower()

        # Step 3: Resume
        with patch("cli.episodes.create_pipeline", return_value=mock_pipeline):
            result = cli_runner.invoke(
                app,
                ["episodes", "resume", "olivers_workshop", "ep_int_001"],
            )
        assert result.exit_code == 0
        assert "complete" in result.stdout.lower()

    def test_approve_with_resume_flag(self, cli_runner: CliRunner):
        """Approve --resume does both in one command."""
        episode = _make_episode()
        approval_res = _approval_result(episode)
        completed_res = _completed_result(episode)

        mock_pipeline = MagicMock()
        mock_pipeline.generate_episode = AsyncMock(return_value=approval_res)
        mock_pipeline.resume_episode = AsyncMock(return_value=completed_res)

        mock_wf = MagicMock()

        # Create
        with patch("cli.episodes.create_pipeline", return_value=mock_pipeline):
            cli_runner.invoke(
                app,
                ["episodes", "create", "olivers_workshop", "rockets"],
            )

        # Approve + resume
        with (
            patch("cli.episodes.create_approval_workflow", return_value=mock_wf),
            patch("cli.episodes.create_pipeline", return_value=mock_pipeline),
        ):
            result = cli_runner.invoke(
                app,
                [
                    "episodes",
                    "approve",
                    "olivers_workshop",
                    "ep_int_001",
                    "--resume",
                ],
            )
        assert result.exit_code == 0
        assert "approved" in result.stdout.lower()
        mock_pipeline.resume_episode.assert_awaited()


# ---------------------------------------------------------------------------
# Reject → retry workflow
# ---------------------------------------------------------------------------


class TestRejectRetryWorkflow:
    """Integration: create → reject → retry → re-approve."""

    def test_reject_then_retry(self, cli_runner: CliRunner):
        """Reject, retry_rejected, then re-approve."""
        rejected = _make_episode(
            stage=PipelineStage.REJECTED,
            approval_status="rejected",
        )
        re_generated = _make_episode(
            episode_id="ep_int_001",
            stage=PipelineStage.AWAITING_APPROVAL,
        )

        mock_wf = MagicMock()
        mock_storage = MagicMock()
        mock_storage.load_episode.return_value = rejected

        mock_pipeline = MagicMock()
        mock_pipeline.retry_rejected_episode = AsyncMock(
            return_value=_approval_result(re_generated)
        )

        # Step 1: Reject
        with patch("cli.episodes.create_approval_workflow", return_value=mock_wf):
            result = cli_runner.invoke(
                app,
                [
                    "episodes",
                    "reject",
                    "olivers_workshop",
                    "ep_int_001",
                    "--feedback",
                    "Too short",
                ],
            )
        assert result.exit_code == 0
        assert "rejected" in result.stdout.lower()

        # Step 2: Retry
        with (
            patch("cli.episodes.create_storage", return_value=mock_storage),
            patch("cli.episodes.create_pipeline", return_value=mock_pipeline),
        ):
            result = cli_runner.invoke(
                app,
                ["episodes", "retry", "olivers_workshop", "ep_int_001"],
            )
        assert result.exit_code == 0
        mock_pipeline.retry_rejected_episode.assert_awaited_once()


# ---------------------------------------------------------------------------
# Error handling integration
# ---------------------------------------------------------------------------


class TestErrorHandlingIntegration:
    """CLI gracefully handles pipeline errors."""

    def test_create_pipeline_error(self, cli_runner: CliRunner):
        """Runtime error in generate_episode → exit code 1."""
        mock_pipeline = MagicMock()
        mock_pipeline.generate_episode = AsyncMock(side_effect=RuntimeError("LLM down"))

        with patch("cli.episodes.create_pipeline", return_value=mock_pipeline):
            result = cli_runner.invoke(
                app,
                ["episodes", "create", "olivers_workshop", "rockets"],
            )
        assert result.exit_code == 1
        assert "Error" in result.stdout or "error" in result.stdout

    def test_resume_pipeline_error(self, cli_runner: CliRunner):
        """Runtime error in resume_episode → exit code 1."""
        mock_pipeline = MagicMock()
        mock_pipeline.resume_episode = AsyncMock(
            side_effect=RuntimeError("Synthesis crash")
        )

        with patch("cli.episodes.create_pipeline", return_value=mock_pipeline):
            result = cli_runner.invoke(
                app,
                ["episodes", "resume", "olivers_workshop", "ep_int_001"],
            )
        assert result.exit_code == 1

    def test_list_config_then_episodes(self, cli_runner: CliRunner):
        """Can invoke config then episodes commands in sequence."""
        mock_settings = MagicMock()
        mock_settings.USE_MOCK_SERVICES = True
        mock_settings.LLM_PROVIDER = "mock"
        mock_settings.TTS_PROVIDER = "mock"
        mock_settings.IMAGE_PROVIDER = "mock"
        mock_settings.OPENAI_API_KEY = None
        mock_settings.ANTHROPIC_API_KEY = None
        mock_settings.GEMINI_API_KEY = None
        mock_settings.ELEVENLABS_API_KEY = None
        mock_settings.DATA_DIR = "/tmp/data"
        mock_settings.SHOWS_DIR = "/tmp/shows"
        mock_settings.EPISODES_DIR = "/tmp/episodes"
        mock_settings.ASSETS_DIR = "/tmp/assets"
        mock_settings.AUDIO_OUTPUT_DIR = "/tmp/audio"

        with patch("cli.config.get_settings", return_value=mock_settings):
            result = cli_runner.invoke(app, ["config", "show"])
        assert result.exit_code == 0
        assert "LLM_PROVIDER" in result.stdout

        mock_storage = MagicMock()
        mock_storage.list_episodes.return_value = []
        with patch("cli.episodes.create_storage", return_value=mock_storage):
            result = cli_runner.invoke(app, ["episodes", "list", "olivers_workshop"])
        assert result.exit_code == 0
