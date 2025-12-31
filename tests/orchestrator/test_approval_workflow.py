"""Tests for approval workflow."""

from datetime import UTC, datetime, timedelta

import pytest

from models import Episode, PipelineStage, StoryBeat, StoryOutline


class TestSubmitApproval:
    """Test approval submission."""

    def test_submit_approval_approved(
        self,
        approval_workflow,
        test_episode_awaiting_approval: Episode,
    ):
        """Test submitting approval decision with approve=True."""
        # Save episode
        approval_workflow.storage.save_episode(test_episode_awaiting_approval)

        # Submit approval
        result = approval_workflow.submit_approval(
            show_id=test_episode_awaiting_approval.show_id,
            episode_id=test_episode_awaiting_approval.episode_id,
            approved=True,
        )

        assert result.current_stage == PipelineStage.SEGMENT_GENERATION
        assert result.approval_status == "approved"

    def test_submit_approval_rejected(
        self,
        approval_workflow,
        test_episode_awaiting_approval: Episode,
    ):
        """Test submitting approval decision with approve=False."""
        # Save episode
        approval_workflow.storage.save_episode(test_episode_awaiting_approval)

        # Submit rejection
        result = approval_workflow.submit_approval(
            show_id=test_episode_awaiting_approval.show_id,
            episode_id=test_episode_awaiting_approval.episode_id,
            approved=False,
            feedback="Needs more detail",
        )

        assert result.current_stage == PipelineStage.REJECTED
        assert result.approval_status == "rejected"
        assert result.approval_feedback == "Needs more detail"

    def test_submit_approval_with_edited_outline(
        self,
        approval_workflow,
        test_episode_awaiting_approval: Episode,
    ):
        """Test submitting approval with edited outline."""
        # Save episode
        approval_workflow.storage.save_episode(test_episode_awaiting_approval)

        # Create edited outline
        edited_outline = StoryOutline(
            episode_id=test_episode_awaiting_approval.episode_id,
            show_id=test_episode_awaiting_approval.show_id,
            topic="edited topic",
            title="Edited Title",
            educational_concept="Edited concept",
            story_beats=[
                StoryBeat(
                    beat_number=1,
                    title="New Beat",
                    description="Edited description",
                    educational_focus="New focus",
                    key_moments=["Edited moment"],
                )
            ],
        )

        # Submit approval with edited outline
        result = approval_workflow.submit_approval(
            show_id=test_episode_awaiting_approval.show_id,
            episode_id=test_episode_awaiting_approval.episode_id,
            approved=True,
            edited_outline=edited_outline,
        )

        assert result.current_stage == PipelineStage.SEGMENT_GENERATION
        assert result.outline.title == "Edited Title"
        assert result.outline.topic == "edited topic"

    def test_submit_approval_wrong_stage_raises_error(
        self,
        approval_workflow,
        test_episode: Episode,
    ):
        """Test that submitting approval for wrong stage raises error."""
        test_episode.current_stage = PipelineStage.IDEATION

        # Save episode
        approval_workflow.storage.save_episode(test_episode)

        # Try to submit approval
        with pytest.raises(ValueError, match="not awaiting approval"):
            approval_workflow.submit_approval(
                show_id=test_episode.show_id,
                episode_id=test_episode.episode_id,
                approved=True,
            )

    def test_submit_approval_rejected_without_feedback(
        self,
        approval_workflow,
        test_episode_awaiting_approval: Episode,
    ):
        """Test submitting rejection without feedback (should use default)."""
        # Save episode
        approval_workflow.storage.save_episode(test_episode_awaiting_approval)

        # Submit rejection without feedback
        result = approval_workflow.submit_approval(
            show_id=test_episode_awaiting_approval.show_id,
            episode_id=test_episode_awaiting_approval.episode_id,
            approved=False,
        )

        assert result.approval_feedback == "No feedback provided"


class TestApprovalTimeout:
    """Test approval timeout checking."""

    def test_check_approval_timeout_not_timed_out(
        self, approval_workflow, test_episode_awaiting_approval: Episode
    ):
        """Test checking timeout for recently created episode."""
        test_episode_awaiting_approval.updated_at = datetime.now(UTC)

        result = approval_workflow.check_approval_timeout(test_episode_awaiting_approval)

        assert result is False

    def test_check_approval_timeout_timed_out(
        self, approval_workflow, test_episode_awaiting_approval: Episode
    ):
        """Test checking timeout for old episode."""
        # Set updated_at to 8 days ago
        test_episode_awaiting_approval.updated_at = datetime.now(UTC) - timedelta(
            days=8
        )

        result = approval_workflow.check_approval_timeout(test_episode_awaiting_approval)

        assert result is True

    def test_check_approval_timeout_custom_days(
        self, approval_workflow, test_episode_awaiting_approval: Episode
    ):
        """Test checking timeout with custom timeout days."""
        # Set updated_at to 2 days ago
        test_episode_awaiting_approval.updated_at = datetime.now(UTC) - timedelta(
            days=2
        )

        # Should not timeout with default 7 days
        result = approval_workflow.check_approval_timeout(
            test_episode_awaiting_approval, timeout_days=7
        )
        assert result is False

        # Should timeout with 1 day
        result = approval_workflow.check_approval_timeout(
            test_episode_awaiting_approval, timeout_days=1
        )
        assert result is True

    def test_check_approval_timeout_wrong_stage(
        self, approval_workflow, test_episode: Episode
    ):
        """Test checking timeout for episode not awaiting approval."""
        test_episode.current_stage = PipelineStage.IDEATION
        test_episode.updated_at = datetime.now(UTC) - timedelta(days=10)

        result = approval_workflow.check_approval_timeout(test_episode)

        assert result is False


class TestGetPendingApprovals:
    """Test getting list of pending approvals."""

    def test_get_pending_approvals_empty(
        self, approval_workflow
    ):
        """Test getting pending approvals with no episodes."""
        result = approval_workflow.get_pending_approvals("test_show")

        assert result == []

    def test_get_pending_approvals_single_episode(
        self,
        approval_workflow,
        test_episode_awaiting_approval: Episode,
    ):
        """Test getting pending approvals with one episode."""
        # Save episode
        approval_workflow.storage.save_episode(test_episode_awaiting_approval)

        result = approval_workflow.get_pending_approvals(
            test_episode_awaiting_approval.show_id
        )

        assert len(result) == 1
        assert result[0]["episode_id"] == test_episode_awaiting_approval.episode_id
        assert result[0]["title"] == test_episode_awaiting_approval.title
        assert result[0]["topic"] == test_episode_awaiting_approval.topic
        assert "has_timeout" in result[0]
        assert "days_waiting" in result[0]

    def test_get_pending_approvals_multiple_episodes(
        self,
        approval_workflow,
        test_episode_awaiting_approval: Episode,
    ):
        """Test getting pending approvals with multiple episodes."""
        # Create and save multiple episodes
        episode1 = test_episode_awaiting_approval.model_copy()
        episode1.episode_id = "ep_001"

        episode2 = test_episode_awaiting_approval.model_copy()
        episode2.episode_id = "ep_002"

        episode3 = test_episode_awaiting_approval.model_copy()
        episode3.episode_id = "ep_003"
        episode3.current_stage = PipelineStage.COMPLETE  # Not awaiting approval

        approval_workflow.storage.save_episode(episode1)
        approval_workflow.storage.save_episode(episode2)
        approval_workflow.storage.save_episode(episode3)

        result = approval_workflow.get_pending_approvals(episode1.show_id)

        # Should only get episodes awaiting approval
        assert len(result) == 2
        episode_ids = [ep["episode_id"] for ep in result]
        assert "ep_001" in episode_ids
        assert "ep_002" in episode_ids
        assert "ep_003" not in episode_ids

    def test_get_pending_approvals_without_timeout_info(
        self,
        approval_workflow,
        test_episode_awaiting_approval: Episode,
    ):
        """Test getting pending approvals without timeout info."""
        # Save episode
        approval_workflow.storage.save_episode(test_episode_awaiting_approval)

        result = approval_workflow.get_pending_approvals(
            test_episode_awaiting_approval.show_id,
            include_timeout_info=False,
        )

        assert len(result) == 1
        assert "has_timeout" not in result[0]
        assert "days_waiting" not in result[0]

    def test_get_pending_approvals_with_timeout(
        self,
        approval_workflow,
        test_episode_awaiting_approval: Episode,
    ):
        """Test getting pending approvals shows timeout status."""
        # Set episode to have timed out
        test_episode_awaiting_approval.updated_at = datetime.now(UTC) - timedelta(
            days=10
        )

        # Save episode - note: save_episode will update updated_at
        # So we need to save, then manually update the file
        approval_workflow.storage.save_episode(test_episode_awaiting_approval)
        
        # Reload and manually set the time back
        episode = approval_workflow.storage.load_episode(
            test_episode_awaiting_approval.show_id,
            test_episode_awaiting_approval.episode_id
        )
        episode.updated_at = datetime.now(UTC) - timedelta(days=10)
        # Directly save without triggering the auto-update
        import json
        episode_path = approval_workflow.storage.get_episode_path(
            episode.show_id, episode.episode_id
        )
        episode_file = episode_path / "episode.json"
        with open(episode_file, 'w') as f:
            f.write(episode.model_dump_json(indent=2))

        result = approval_workflow.get_pending_approvals(
            test_episode_awaiting_approval.show_id
        )

        assert len(result) == 1
        assert result[0]["has_timeout"] is True
        assert result[0]["days_waiting"] >= 10
