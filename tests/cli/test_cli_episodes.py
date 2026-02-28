"""Tests for episode CLI commands (Task 7.7.1–7.7.3, 7.7.5)."""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

from typer.testing import CliRunner

from cli.main import app
from models.episode import Episode, PipelineStage
from orchestrator.result import PipelineResult

# ---------------------------------------------------------------------------
# episodes create
# ---------------------------------------------------------------------------


class TestCreateEpisode:
    """Tests for the 'episodes create' command."""

    def test_create_success(
        self,
        cli_runner: CliRunner,
        approval_result: PipelineResult,
    ):
        """Successful creation prints approval panel."""
        mock_pipeline = MagicMock()
        mock_pipeline.generate_episode = AsyncMock(return_value=approval_result)

        with patch("cli.episodes.create_pipeline", return_value=mock_pipeline):
            result = cli_runner.invoke(
                app,
                ["episodes", "create", "olivers_workshop", "rockets"],
            )
        assert result.exit_code == 0
        assert "Approval Required" in result.stdout or "ep_test_001" in result.stdout
        mock_pipeline.generate_episode.assert_awaited_once()

    def test_create_show_not_found(self, cli_runner: CliRunner):
        """FileNotFoundError → exit code 1."""
        mock_pipeline = MagicMock()
        mock_pipeline.generate_episode = AsyncMock(
            side_effect=FileNotFoundError("No such show")
        )

        with patch("cli.episodes.create_pipeline", return_value=mock_pipeline):
            result = cli_runner.invoke(
                app,
                ["episodes", "create", "missing_show", "rockets"],
            )
        assert result.exit_code == 1
        assert "not found" in result.stdout.lower()

    def test_create_with_explicit_title(
        self,
        cli_runner: CliRunner,
        approval_result: PipelineResult,
    ):
        """--title is forwarded to generate_episode."""
        mock_pipeline = MagicMock()
        mock_pipeline.generate_episode = AsyncMock(return_value=approval_result)

        with patch("cli.episodes.create_pipeline", return_value=mock_pipeline):
            result = cli_runner.invoke(
                app,
                [
                    "episodes",
                    "create",
                    "olivers_workshop",
                    "rockets",
                    "--title",
                    "Blast Off!",
                ],
            )
        assert result.exit_code == 0
        call_kwargs = mock_pipeline.generate_episode.call_args
        assert call_kwargs.kwargs.get("title") == "Blast Off!"


# ---------------------------------------------------------------------------
# episodes list
# ---------------------------------------------------------------------------


class TestListEpisodes:
    """Tests for the 'episodes list' command."""

    def test_list_with_episodes(
        self,
        cli_runner: CliRunner,
        sample_episode: Episode,
    ):
        """Lists episodes in a table."""
        mock_storage = MagicMock()
        mock_storage.list_episodes.return_value = ["ep_test_001"]
        mock_storage.load_episode.return_value = sample_episode

        with patch("cli.episodes.create_storage", return_value=mock_storage):
            result = cli_runner.invoke(
                app,
                ["episodes", "list", "olivers_workshop"],
            )
        assert result.exit_code == 0
        assert "ep_test_001" in result.stdout

    def test_list_empty(self, cli_runner: CliRunner):
        """Empty show prints a helpful message."""
        mock_storage = MagicMock()
        mock_storage.list_episodes.return_value = []

        with patch("cli.episodes.create_storage", return_value=mock_storage):
            result = cli_runner.invoke(
                app,
                ["episodes", "list", "olivers_workshop"],
            )
        assert result.exit_code == 0
        assert "No episodes found" in result.stdout

    def test_list_show_not_found(self, cli_runner: CliRunner):
        """Missing show → exit code 1."""
        mock_storage = MagicMock()
        mock_storage.list_episodes.side_effect = FileNotFoundError("No show")

        with patch("cli.episodes.create_storage", return_value=mock_storage):
            result = cli_runner.invoke(
                app,
                ["episodes", "list", "nonexistent"],
            )
        assert result.exit_code == 1


# ---------------------------------------------------------------------------
# episodes show
# ---------------------------------------------------------------------------


class TestShowEpisode:
    """Tests for the 'episodes show' command."""

    def test_show_success(
        self,
        cli_runner: CliRunner,
        sample_episode: Episode,
    ):
        """Prints episode details panel."""
        mock_storage = MagicMock()
        mock_storage.load_episode.return_value = sample_episode

        with patch("cli.episodes.create_storage", return_value=mock_storage):
            result = cli_runner.invoke(
                app,
                ["episodes", "show", "olivers_workshop", "ep_test_001"],
            )
        assert result.exit_code == 0
        assert "ep_test_001" in result.stdout
        assert "rockets" in result.stdout.lower()

    def test_show_with_checkpoints(
        self,
        cli_runner: CliRunner,
        completed_episode: Episode,
    ):
        """Completed episode shows checkpoint table and cost."""
        mock_storage = MagicMock()
        mock_storage.load_episode.return_value = completed_episode

        with patch("cli.episodes.create_storage", return_value=mock_storage):
            result = cli_runner.invoke(
                app,
                ["episodes", "show", "olivers_workshop", "ep_done_001"],
            )
        assert result.exit_code == 0
        assert "Checkpoints" in result.stdout
        assert "Total cost" in result.stdout

    def test_show_not_found(self, cli_runner: CliRunner):
        """Missing episode → exit code 1."""
        mock_storage = MagicMock()
        mock_storage.load_episode.side_effect = FileNotFoundError("nope")

        with patch("cli.episodes.create_storage", return_value=mock_storage):
            result = cli_runner.invoke(
                app,
                ["episodes", "show", "olivers_workshop", "missing"],
            )
        assert result.exit_code == 1


# ---------------------------------------------------------------------------
# episodes approve
# ---------------------------------------------------------------------------


class TestApproveEpisode:
    """Tests for the 'episodes approve' command."""

    def test_approve_success(self, cli_runner: CliRunner):
        """Basic approval succeeds."""
        mock_wf = MagicMock()

        with patch("cli.episodes.create_approval_workflow", return_value=mock_wf):
            result = cli_runner.invoke(
                app,
                ["episodes", "approve", "olivers_workshop", "ep_test_001"],
            )
        assert result.exit_code == 0
        assert "approved" in result.stdout.lower()
        mock_wf.submit_approval.assert_called_once()

    def test_approve_with_feedback(self, cli_runner: CliRunner):
        """--feedback is forwarded."""
        mock_wf = MagicMock()

        with patch("cli.episodes.create_approval_workflow", return_value=mock_wf):
            result = cli_runner.invoke(
                app,
                [
                    "episodes",
                    "approve",
                    "olivers_workshop",
                    "ep_test_001",
                    "--feedback",
                    "Looks great",
                ],
            )
        assert result.exit_code == 0
        call_kwargs = mock_wf.submit_approval.call_args
        assert call_kwargs.kwargs.get("feedback") == "Looks great"

    def test_approve_with_resume(
        self,
        cli_runner: CliRunner,
        completed_result: PipelineResult,
    ):
        """--resume approves then resumes pipeline."""
        mock_wf = MagicMock()
        mock_pipeline = MagicMock()
        mock_pipeline.resume_episode = AsyncMock(return_value=completed_result)

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
                    "ep_test_001",
                    "--resume",
                ],
            )
        assert result.exit_code == 0
        assert "approved" in result.stdout.lower()
        mock_pipeline.resume_episode.assert_awaited_once()

    def test_approve_invalid_episode(self, cli_runner: CliRunner):
        """ValueError from workflow → exit code 1."""
        mock_wf = MagicMock()
        mock_wf.submit_approval.side_effect = ValueError("Not awaiting approval")

        with patch("cli.episodes.create_approval_workflow", return_value=mock_wf):
            result = cli_runner.invoke(
                app,
                ["episodes", "approve", "olivers_workshop", "bad_ep"],
            )
        assert result.exit_code == 1
        assert "Not awaiting approval" in result.stdout


# ---------------------------------------------------------------------------
# episodes reject
# ---------------------------------------------------------------------------


class TestRejectEpisode:
    """Tests for the 'episodes reject' command."""

    def test_reject_success(self, cli_runner: CliRunner):
        """Basic rejection succeeds."""
        mock_wf = MagicMock()

        with patch("cli.episodes.create_approval_workflow", return_value=mock_wf):
            result = cli_runner.invoke(
                app,
                [
                    "episodes",
                    "reject",
                    "olivers_workshop",
                    "ep_test_001",
                    "--feedback",
                    "Needs more detail",
                ],
            )
        assert result.exit_code == 0
        assert "rejected" in result.stdout.lower()
        call_kwargs = mock_wf.submit_approval.call_args
        assert call_kwargs.kwargs.get("approved") is False

    def test_reject_invalid(self, cli_runner: CliRunner):
        """ValueError → exit code 1."""
        mock_wf = MagicMock()
        mock_wf.submit_approval.side_effect = ValueError("Wrong state")

        with patch("cli.episodes.create_approval_workflow", return_value=mock_wf):
            result = cli_runner.invoke(
                app,
                ["episodes", "reject", "olivers_workshop", "ep_test_001"],
            )
        assert result.exit_code == 1


# ---------------------------------------------------------------------------
# episodes resume
# ---------------------------------------------------------------------------


class TestResumeEpisode:
    """Tests for the 'episodes resume' command."""

    def test_resume_success(
        self,
        cli_runner: CliRunner,
        completed_result: PipelineResult,
    ):
        """Successful resume prints completion and cost."""
        mock_pipeline = MagicMock()
        mock_pipeline.resume_episode = AsyncMock(return_value=completed_result)

        with patch("cli.episodes.create_pipeline", return_value=mock_pipeline):
            result = cli_runner.invoke(
                app,
                ["episodes", "resume", "olivers_workshop", "ep_done_001"],
            )
        assert result.exit_code == 0
        assert "complete" in result.stdout.lower()
        assert "cost" in result.stdout.lower()

    def test_resume_invalid_state(self, cli_runner: CliRunner):
        """ValueError (not resumable) → exit code 1."""
        mock_pipeline = MagicMock()
        mock_pipeline.resume_episode = AsyncMock(
            side_effect=ValueError("not in a resumable stage")
        )

        with patch("cli.episodes.create_pipeline", return_value=mock_pipeline):
            result = cli_runner.invoke(
                app,
                ["episodes", "resume", "olivers_workshop", "ep_pending"],
            )
        assert result.exit_code == 1
        assert "resumable" in result.stdout.lower()


# ---------------------------------------------------------------------------
# episodes retry
# ---------------------------------------------------------------------------


class TestRetryEpisode:
    """Tests for the 'episodes retry' command."""

    def test_retry_failed(
        self,
        cli_runner: CliRunner,
        failed_episode: Episode,
        approval_result: PipelineResult,
    ):
        """Retry a FAILED episode calls retry_failed_episode."""
        mock_storage = MagicMock()
        mock_storage.load_episode.return_value = failed_episode

        mock_pipeline = MagicMock()
        mock_pipeline.retry_failed_episode = AsyncMock(return_value=approval_result)

        with (
            patch("cli.episodes.create_storage", return_value=mock_storage),
            patch("cli.episodes.create_pipeline", return_value=mock_pipeline),
        ):
            result = cli_runner.invoke(
                app,
                ["episodes", "retry", "olivers_workshop", "ep_fail_001"],
            )
        assert result.exit_code == 0
        mock_pipeline.retry_failed_episode.assert_awaited_once()

    def test_retry_rejected(
        self,
        cli_runner: CliRunner,
        rejected_episode: Episode,
        approval_result: PipelineResult,
    ):
        """Retry a REJECTED episode calls retry_rejected_episode."""
        mock_storage = MagicMock()
        mock_storage.load_episode.return_value = rejected_episode

        mock_pipeline = MagicMock()
        mock_pipeline.retry_rejected_episode = AsyncMock(return_value=approval_result)

        with (
            patch("cli.episodes.create_storage", return_value=mock_storage),
            patch("cli.episodes.create_pipeline", return_value=mock_pipeline),
        ):
            result = cli_runner.invoke(
                app,
                ["episodes", "retry", "olivers_workshop", "ep_rej_001"],
            )
        assert result.exit_code == 0
        mock_pipeline.retry_rejected_episode.assert_awaited_once()

    def test_retry_wrong_state(
        self,
        cli_runner: CliRunner,
        sample_episode: Episode,
    ):
        """Retrying an episode not in FAILED/REJECTED → exit code 1."""
        mock_storage = MagicMock()
        mock_storage.load_episode.return_value = sample_episode  # AWAITING_APPROVAL

        with (
            patch("cli.episodes.create_storage", return_value=mock_storage),
            patch("cli.episodes.create_pipeline", return_value=MagicMock()),
        ):
            result = cli_runner.invoke(
                app,
                ["episodes", "retry", "olivers_workshop", "ep_test_001"],
            )
        assert result.exit_code == 1
        assert "FAILED" in result.stdout or "REJECTED" in result.stdout


# ---------------------------------------------------------------------------
# episodes reset
# ---------------------------------------------------------------------------


class TestResetEpisode:
    """Tests for the 'episodes reset' command."""

    def test_reset_with_confirm(
        self,
        cli_runner: CliRunner,
        sample_episode: Episode,
    ):
        """Reset with -y flag skips confirmation."""
        reset_ep = sample_episode.model_copy(
            update={"current_stage": PipelineStage.IDEATION}
        )
        mock_pipeline = MagicMock()
        mock_pipeline.reset_to_stage = AsyncMock(return_value=reset_ep)

        with patch("cli.episodes.create_pipeline", return_value=mock_pipeline):
            result = cli_runner.invoke(
                app,
                [
                    "episodes",
                    "reset",
                    "olivers_workshop",
                    "ep_test_001",
                    "ideation",
                    "-y",
                ],
            )
        assert result.exit_code == 0
        assert "reset" in result.stdout.lower()

    def test_reset_invalid_stage(self, cli_runner: CliRunner):
        """Invalid stage name → exit code 1."""
        mock_pipeline = MagicMock()
        mock_pipeline.reset_to_stage = AsyncMock(
            side_effect=ValueError("Invalid stage name: bogus")
        )

        with patch("cli.episodes.create_pipeline", return_value=mock_pipeline):
            result = cli_runner.invoke(
                app,
                [
                    "episodes",
                    "reset",
                    "olivers_workshop",
                    "ep_test_001",
                    "bogus",
                    "-y",
                ],
            )
        assert result.exit_code == 1
        assert "Invalid stage name" in result.stdout


# ---------------------------------------------------------------------------
# episodes delete
# ---------------------------------------------------------------------------


class TestDeleteEpisode:
    """Tests for the 'episodes delete' command."""

    def test_delete_with_confirm(self, cli_runner: CliRunner):
        """Delete with -y flag succeeds."""
        mock_storage = MagicMock()

        with patch("cli.episodes.create_storage", return_value=mock_storage):
            result = cli_runner.invoke(
                app,
                [
                    "episodes",
                    "delete",
                    "olivers_workshop",
                    "ep_test_001",
                    "-y",
                ],
            )
        assert result.exit_code == 0
        assert "deleted" in result.stdout.lower()
        mock_storage.delete_episode.assert_called_once_with(
            "olivers_workshop", "ep_test_001"
        )

    def test_delete_not_found(self, cli_runner: CliRunner):
        """Missing episode → exit code 1."""
        mock_storage = MagicMock()
        mock_storage.delete_episode.side_effect = FileNotFoundError("nope")

        with patch("cli.episodes.create_storage", return_value=mock_storage):
            result = cli_runner.invoke(
                app,
                [
                    "episodes",
                    "delete",
                    "olivers_workshop",
                    "missing",
                    "-y",
                ],
            )
        assert result.exit_code == 1


# ---------------------------------------------------------------------------
# episodes pending
# ---------------------------------------------------------------------------


class TestPendingApprovals:
    """Tests for the 'episodes pending' command."""

    def test_pending_with_results(
        self,
        cli_runner: CliRunner,
        sample_episode: Episode,
    ):
        """Pending approvals listed in table."""
        mock_wf = MagicMock()
        mock_wf.list_pending_approvals.return_value = [sample_episode]

        with patch("cli.episodes.create_approval_workflow", return_value=mock_wf):
            result = cli_runner.invoke(
                app,
                ["episodes", "pending", "olivers_workshop"],
            )
        assert result.exit_code == 0
        assert "ep_test_001" in result.stdout

    def test_pending_none(self, cli_runner: CliRunner):
        """No pending → success message."""
        mock_wf = MagicMock()
        mock_wf.list_pending_approvals.return_value = []

        with patch("cli.episodes.create_approval_workflow", return_value=mock_wf):
            result = cli_runner.invoke(
                app,
                ["episodes", "pending", "olivers_workshop"],
            )
        assert result.exit_code == 0
        assert "No episodes" in result.stdout
