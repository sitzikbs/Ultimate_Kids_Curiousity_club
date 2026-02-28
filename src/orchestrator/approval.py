"""Human approval workflow for the pipeline orchestrator.

Handles the approval gate between OUTLINING and SEGMENT_GENERATION,
supporting approve, reject, and outline editing operations.
"""

import asyncio
import inspect
import logging
from datetime import UTC, datetime, timedelta

from models.episode import Episode, PipelineStage
from models.story import StoryOutline
from orchestrator.events import EventCallback, EventType, PipelineEvent
from orchestrator.transitions import can_transition_to
from services.protocols import EpisodeStorageProtocol

logger = logging.getLogger(__name__)


class ApprovalWorkflow:
    """Manages human approval/rejection of episode outlines.

    After the pipeline reaches AWAITING_APPROVAL, this class handles
    the review decision and prepares the episode for resumption.
    """

    def __init__(
        self,
        episode_storage: EpisodeStorageProtocol,
        event_callback: EventCallback | None = None,
    ) -> None:
        """Initialize approval workflow.

        Args:
            episode_storage: Storage for persisting episode state
            event_callback: Optional callback for approval events
        """
        self.storage = episode_storage
        self.event_callback = event_callback

    def submit_approval(
        self,
        show_id: str,
        episode_id: str,
        approved: bool,
        edited_outline: StoryOutline | None = None,
        feedback: str | None = None,
    ) -> Episode:
        """Submit an approval decision for an episode outline.

        Args:
            show_id: Show identifier (required for storage lookup)
            episode_id: Episode identifier
            approved: Whether the outline is approved
            edited_outline: Optional replacement outline (only if approved)
            feedback: Optional feedback text (especially useful for rejections)

        Returns:
            Updated Episode with new stage and approval metadata

        Raises:
            ValueError: If episode is not in AWAITING_APPROVAL stage
        """
        episode = self.storage.load_episode(show_id, episode_id)

        if episode.current_stage != PipelineStage.AWAITING_APPROVAL:
            raise ValueError(
                f"Episode {episode_id} is not awaiting approval "
                f"(current stage: {episode.current_stage.value})"
            )

        if approved:
            self._approve(episode, edited_outline, feedback)
        else:
            self._reject(episode, feedback)

        self.storage.save_episode(episode)

        # Emit event (fire-and-forget for sync callers)
        event = PipelineEvent(
            event_type=EventType.APPROVAL_SUBMITTED,
            episode_id=episode.episode_id,
            show_id=episode.show_id,
            stage=episode.current_stage,
            data={
                "approved": approved,
                "feedback": feedback,
                "outline_edited": edited_outline is not None,
            },
        )
        self._fire_event(event)

        return episode

    def check_approval_timeout(
        self,
        episode: Episode,
        timeout_days: int = 7,
    ) -> bool:
        """Check if an episode has been waiting for approval too long.

        Args:
            episode: Episode to check
            timeout_days: Number of days before timeout warning (default: 7)

        Returns:
            True if the episode has exceeded the timeout threshold
        """
        if episode.current_stage != PipelineStage.AWAITING_APPROVAL:
            return False

        threshold = datetime.now(UTC) - timedelta(days=timeout_days)
        return episode.updated_at < threshold

    def list_pending_approvals(
        self,
        show_id: str,
    ) -> list[Episode]:
        """List all episodes awaiting approval for a show.

        Args:
            show_id: Show identifier

        Returns:
            List of episodes in AWAITING_APPROVAL stage
        """
        pending: list[Episode] = []
        for ep_id in self.storage.list_episodes(show_id):
            try:
                episode = self.storage.load_episode(show_id, ep_id)
                if episode.current_stage == PipelineStage.AWAITING_APPROVAL:
                    pending.append(episode)
            except Exception:
                logger.warning("Could not load episode %s", ep_id, exc_info=True)
        return pending

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    def _approve(
        self,
        episode: Episode,
        edited_outline: StoryOutline | None,
        feedback: str | None,
    ) -> None:
        """Apply approval to episode."""
        target = PipelineStage.APPROVED
        if not can_transition_to(episode.current_stage, target):
            raise ValueError(
                f"Invalid transition: "
                f"{episode.current_stage.value} \u2192 {target.value}"
            )

        if edited_outline is not None:
            episode.outline = edited_outline
            logger.info(
                "Updated outline for episode %s before approval",
                episode.episode_id,
            )

        episode.current_stage = target
        episode.approval_status = "approved"
        episode.approval_feedback = feedback
        episode.updated_at = datetime.now(UTC)
        logger.info("Episode %s approved", episode.episode_id)

    def _reject(
        self,
        episode: Episode,
        feedback: str | None,
    ) -> None:
        """Apply rejection to episode."""
        target = PipelineStage.REJECTED
        if not can_transition_to(episode.current_stage, target):
            raise ValueError(
                f"Invalid transition: "
                f"{episode.current_stage.value} \u2192 {target.value}"
            )
        episode.current_stage = target
        episode.approval_status = "rejected"
        episode.approval_feedback = feedback
        episode.updated_at = datetime.now(UTC)
        logger.warning("Episode %s rejected: %s", episode.episode_id, feedback)

    def _fire_event(self, event: PipelineEvent) -> None:
        """Fire event callback if registered (handles sync context)."""
        if self.event_callback is None:
            return
        result = self.event_callback(event)
        if inspect.isawaitable(result):
            # Best-effort in sync context — schedule on running loop if available
            try:
                loop = asyncio.get_running_loop()
                loop.create_task(result)  # type: ignore[arg-type]
            except RuntimeError:
                # No event loop running; close the coroutine to avoid warnings
                result.close()
                logger.debug("No event loop; skipping async approval event callback")
