"""Human approval workflow for episode outline review."""

import logging
from datetime import UTC, datetime, timedelta

from models import Episode, PipelineStage, StoryOutline
from modules.episode_storage import EpisodeStorage

logger = logging.getLogger(__name__)


class ApprovalWorkflow:
    """Manages human approval workflow for episode outlines.

    Handles submission of approval decisions, outline editing,
    and timeout warnings for episodes awaiting review.
    """

    def __init__(self, episode_storage: EpisodeStorage):
        """Initialize approval workflow.

        Args:
            episode_storage: Storage for episode persistence
        """
        self.storage = episode_storage

    def submit_approval(
        self,
        show_id: str,
        episode_id: str,
        approved: bool,
        edited_outline: StoryOutline | None = None,
        feedback: str | None = None,
    ) -> Episode:
        """Submit approval decision for episode outline.

        Args:
            show_id: Show identifier
            episode_id: Episode identifier
            approved: True to approve, False to reject
            edited_outline: Optional edited outline to replace original
            feedback: Optional feedback message (required for rejection)

        Returns:
            Updated episode

        Raises:
            ValueError: If episode is not awaiting approval
        """
        episode = self.storage.load_episode(show_id, episode_id)

        if episode.current_stage != PipelineStage.AWAITING_APPROVAL:
            raise ValueError(
                f"Episode {episode_id} is not awaiting approval "
                f"(current stage: {episode.current_stage})"
            )

        if approved:
            # Update outline if edited
            if edited_outline:
                episode.outline = edited_outline
                logger.info(f"Updated outline for episode {episode_id}")

            # Transition to next stage
            episode.current_stage = PipelineStage.SEGMENT_GENERATION
            episode.approval_status = "approved"
            episode.updated_at = datetime.now(UTC)

            logger.info(
                f"Episode {episode_id} approved, proceeding to segment generation"
            )
        else:
            # Reject and store feedback
            episode.current_stage = PipelineStage.REJECTED
            episode.approval_status = "rejected"
            episode.approval_feedback = feedback or "No feedback provided"
            episode.updated_at = datetime.now(UTC)

            logger.warning(f"Episode {episode_id} rejected: {feedback}")

        self.storage.save_episode(episode)
        self._emit_approval_event(episode, approved)

        return episode

    def check_approval_timeout(
        self, episode: Episode, timeout_days: int = 7
    ) -> bool:
        """Check if episode has been awaiting approval for too long.

        Args:
            episode: Episode to check
            timeout_days: Number of days before timeout (default: 7)

        Returns:
            True if episode has exceeded timeout, False otherwise
        """
        if episode.current_stage != PipelineStage.AWAITING_APPROVAL:
            return False

        # Check when episode was created or last updated
        check_time = episode.updated_at or episode.created_at

        time_waiting = datetime.now(UTC) - check_time
        return time_waiting > timedelta(days=timeout_days)

    def get_pending_approvals(
        self, show_id: str, include_timeout_info: bool = True
    ) -> list[dict]:
        """Get list of episodes awaiting approval for a show.

        Args:
            show_id: Show identifier
            include_timeout_info: Include timeout status in results

        Returns:
            List of episode info dictionaries
        """
        episode_ids = self.storage.list_episodes(show_id)
        pending = []

        for episode_id in episode_ids:
            try:
                episode = self.storage.load_episode(show_id, episode_id)

                if episode.current_stage == PipelineStage.AWAITING_APPROVAL:
                    info = {
                        "episode_id": episode_id,
                        "title": episode.title,
                        "topic": episode.topic,
                        "created_at": episode.created_at,
                        "updated_at": episode.updated_at,
                    }

                    if include_timeout_info:
                        info["has_timeout"] = self.check_approval_timeout(
                            episode
                        )
                        check_time = episode.updated_at or episode.created_at
                        info["days_waiting"] = (
                            datetime.now(UTC) - check_time
                        ).days

                    pending.append(info)
            except Exception as e:
                logger.error(
                    f"Error loading episode {episode_id} for approval check: {e}"
                )
                continue

        return pending

    def _emit_approval_event(self, episode: Episode, approved: bool) -> None:
        """Emit event for UI notifications (WebSocket).

        Future: Implement WebSocket/SSE notification system.

        Args:
            episode: Episode that was approved/rejected
            approved: True if approved, False if rejected
        """
        event_data = {
            "episode_id": episode.episode_id,
            "show_id": episode.show_id,
            "approved": approved,
            "stage": episode.current_stage.value,
            "timestamp": datetime.now(UTC).isoformat(),
        }

        logger.debug(
            f"Approval event: episode={episode.episode_id}, "
            f"approved={approved}, data={event_data}"
        )

        # Future: Send to WebSocket handler
        # websocket_manager.broadcast_event("approval", event_data)
