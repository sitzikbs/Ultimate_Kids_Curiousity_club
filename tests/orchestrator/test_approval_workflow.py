"""Tests for the human approval workflow."""

from datetime import UTC, datetime, timedelta

import pytest

from models.episode import Episode, PipelineStage
from models.story import StoryBeat, StoryOutline
from orchestrator.events import EventType


class TestSubmitApproval:
    """Tests for ApprovalWorkflow.submit_approval()."""

    def test_approve_happy_path(
        self, approval_workflow, mock_episode_storage, sample_outline, sample_concept
    ):
        """Approving transitions episode to APPROVED."""
        episode = Episode(
            episode_id="ep_approve",
            show_id="olivers_workshop",
            topic="rockets",
            title="Rockets",
            concept=sample_concept,
            outline=sample_outline,
            current_stage=PipelineStage.AWAITING_APPROVAL,
            approval_status="pending",
        )
        mock_episode_storage.save_episode(episode)

        result = approval_workflow.submit_approval(
            show_id="olivers_workshop",
            episode_id="ep_approve",
            approved=True,
        )

        assert result.current_stage == PipelineStage.APPROVED
        assert result.approval_status == "approved"

    def test_reject_with_feedback(
        self, approval_workflow, mock_episode_storage, sample_outline, sample_concept
    ):
        """Rejecting transitions episode to REJECTED with feedback."""
        episode = Episode(
            episode_id="ep_reject",
            show_id="olivers_workshop",
            topic="rockets",
            title="Rockets",
            concept=sample_concept,
            outline=sample_outline,
            current_stage=PipelineStage.AWAITING_APPROVAL,
            approval_status="pending",
        )
        mock_episode_storage.save_episode(episode)

        result = approval_workflow.submit_approval(
            show_id="olivers_workshop",
            episode_id="ep_reject",
            approved=False,
            feedback="Too long, needs more educational content",
        )

        assert result.current_stage == PipelineStage.REJECTED
        assert result.approval_status == "rejected"
        assert result.approval_feedback == "Too long, needs more educational content"

    def test_approve_with_edited_outline(
        self, approval_workflow, mock_episode_storage, sample_outline, sample_concept
    ):
        """Approving with an edited outline replaces the original."""
        episode = Episode(
            episode_id="ep_edit",
            show_id="olivers_workshop",
            topic="rockets",
            title="Rockets",
            concept=sample_concept,
            outline=sample_outline,
            current_stage=PipelineStage.AWAITING_APPROVAL,
            approval_status="pending",
        )
        mock_episode_storage.save_episode(episode)

        edited_outline = StoryOutline(
            episode_id="ep_edit",
            show_id="olivers_workshop",
            topic="rockets",
            title="Rockets — Revised",
            educational_concept="Advanced propulsion",
            story_beats=[
                StoryBeat(
                    beat_number=1,
                    title="Revised Beat",
                    description="A new angle on rockets",
                    educational_focus="Propulsion physics",
                    key_moments=["Updated moment"],
                ),
            ],
        )

        result = approval_workflow.submit_approval(
            show_id="olivers_workshop",
            episode_id="ep_edit",
            approved=True,
            edited_outline=edited_outline,
        )

        assert result.current_stage == PipelineStage.APPROVED
        assert result.outline is not None
        assert result.outline.title == "Rockets — Revised"
        assert len(result.outline.story_beats) == 1

    def test_approve_with_feedback(
        self, approval_workflow, mock_episode_storage, sample_outline, sample_concept
    ):
        """Approval feedback is stored even on approve."""
        episode = Episode(
            episode_id="ep_fb",
            show_id="olivers_workshop",
            topic="rockets",
            title="Rockets",
            concept=sample_concept,
            outline=sample_outline,
            current_stage=PipelineStage.AWAITING_APPROVAL,
            approval_status="pending",
        )
        mock_episode_storage.save_episode(episode)

        result = approval_workflow.submit_approval(
            show_id="olivers_workshop",
            episode_id="ep_fb",
            approved=True,
            feedback="Minor tweak suggestion for beat 2",
        )

        assert result.approval_feedback == "Minor tweak suggestion for beat 2"

    def test_cannot_approve_wrong_stage(self, approval_workflow, mock_episode_storage):
        """Cannot approve episode that is not in AWAITING_APPROVAL."""
        episode = Episode(
            episode_id="ep_wrong",
            show_id="olivers_workshop",
            topic="rockets",
            title="Rockets",
            current_stage=PipelineStage.IDEATION,
        )
        mock_episode_storage.save_episode(episode)

        with pytest.raises(ValueError, match="not awaiting approval"):
            approval_workflow.submit_approval(
                show_id="olivers_workshop",
                episode_id="ep_wrong",
                approved=True,
            )

    def test_cannot_approve_completed_episode(
        self, approval_workflow, mock_episode_storage
    ):
        """Cannot approve an already completed episode."""
        episode = Episode(
            episode_id="ep_done",
            show_id="olivers_workshop",
            topic="rockets",
            title="Rockets",
            current_stage=PipelineStage.COMPLETE,
        )
        mock_episode_storage.save_episode(episode)

        with pytest.raises(ValueError, match="not awaiting approval"):
            approval_workflow.submit_approval(
                show_id="olivers_workshop",
                episode_id="ep_done",
                approved=True,
            )

    def test_event_emitted_on_approval(
        self,
        approval_workflow,
        mock_episode_storage,
        mock_event_callback,
        sample_concept,
    ):
        """An event is fired when approval is submitted."""
        episode = Episode(
            episode_id="ep_evt",
            show_id="olivers_workshop",
            topic="rockets",
            title="Rockets",
            concept=sample_concept,
            current_stage=PipelineStage.AWAITING_APPROVAL,
            approval_status="pending",
        )
        mock_episode_storage.save_episode(episode)

        approval_workflow.submit_approval(
            show_id="olivers_workshop",
            episode_id="ep_evt",
            approved=True,
        )

        # The callback was invoked (in sync context the coroutine is closed,
        # but the mock records the call)
        assert mock_event_callback.called
        event = mock_event_callback.call_args[0][0]
        assert event.event_type == EventType.APPROVAL_SUBMITTED
        assert event.episode_id == "ep_evt"


class TestApprovalTimeout:
    """Tests for approval timeout detection."""

    def test_no_timeout_within_threshold(self, approval_workflow):
        """Episode within timeout threshold is not flagged."""
        episode = Episode(
            episode_id="ep_ok",
            show_id="olivers_workshop",
            topic="rockets",
            title="Rockets",
            current_stage=PipelineStage.AWAITING_APPROVAL,
            updated_at=datetime.now(UTC) - timedelta(days=3),
        )

        assert approval_workflow.check_approval_timeout(episode) is False

    def test_timeout_exceeded(self, approval_workflow):
        """Episode exceeding timeout threshold is flagged."""
        episode = Episode(
            episode_id="ep_old",
            show_id="olivers_workshop",
            topic="rockets",
            title="Rockets",
            current_stage=PipelineStage.AWAITING_APPROVAL,
            updated_at=datetime.now(UTC) - timedelta(days=10),
        )

        assert approval_workflow.check_approval_timeout(episode) is True

    def test_custom_timeout_days(self, approval_workflow):
        """Custom timeout threshold is respected."""
        episode = Episode(
            episode_id="ep_custom",
            show_id="olivers_workshop",
            topic="rockets",
            title="Rockets",
            current_stage=PipelineStage.AWAITING_APPROVAL,
            updated_at=datetime.now(UTC) - timedelta(days=2),
        )

        assert approval_workflow.check_approval_timeout(episode, timeout_days=1) is True
        assert (
            approval_workflow.check_approval_timeout(episode, timeout_days=3) is False
        )

    def test_timeout_only_for_awaiting_approval(self, approval_workflow):
        """Timeout check returns False for non-AWAITING_APPROVAL stages."""
        episode = Episode(
            episode_id="ep_other",
            show_id="olivers_workshop",
            topic="rockets",
            title="Rockets",
            current_stage=PipelineStage.IDEATION,
            updated_at=datetime.now(UTC) - timedelta(days=30),
        )

        assert approval_workflow.check_approval_timeout(episode) is False
