"""Progress tracking for the pipeline orchestrator.

Provides real-time visibility into pipeline execution through structured
logging of stage progress, substage progress (e.g. per-segment TTS), and
estimated time remaining.
"""

import logging
from datetime import datetime, timezone
from typing import Any

logger = logging.getLogger(__name__)


class ProgressTracker:
    """Tracks pipeline execution progress with stage-level granularity.

    Reports stage starts/completions, substage progress within a stage
    (e.g. "Synthesizing segment 3/10"), and estimates time remaining
    based on observed stage durations.

    Attributes:
        total_stages: Total number of pipeline stages.
        completed_stages: Number of stages completed so far.
    """

    def __init__(self, total_stages: int = 8) -> None:
        """Initialize progress tracker.

        Args:
            total_stages: Total number of pipeline stages to track.
        """
        self.total_stages = total_stages
        self.completed_stages = 0
        self.current_stage: str | None = None
        self.stage_start_time: datetime | None = None
        self._stage_durations: list[float] = []

    def start_stage(self, stage_name: str) -> None:
        """Mark a stage as started.

        Args:
            stage_name: Human-readable stage name.
        """
        self.current_stage = stage_name
        self.stage_start_time = datetime.now(timezone.utc)
        logger.info(
            "▶ Starting stage: %s (%d/%d)",
            stage_name,
            self.completed_stages + 1,
            self.total_stages,
        )

    def complete_stage(self, stage_name: str) -> float:
        """Mark a stage as completed.

        Args:
            stage_name: Human-readable stage name.

        Returns:
            Duration of the stage in seconds.
        """
        duration = 0.0
        if self.stage_start_time:
            duration = (
                datetime.now(timezone.utc) - self.stage_start_time
            ).total_seconds()
            self._stage_durations.append(duration)
            logger.info(
                "✓ Completed stage: %s (%.1fs)",
                stage_name,
                duration,
            )
        else:
            logger.info("✓ Completed stage: %s", stage_name)

        self.completed_stages += 1
        self.current_stage = None
        self.stage_start_time = None

        return duration

    def report_substage_progress(
        self,
        current: int,
        total: int,
        description: str,
    ) -> None:
        """Report progress within a stage.

        Args:
            current: Current item number (1-based).
            total: Total items to process.
            description: Description of what is being processed.
        """
        if total <= 0:
            return
        percentage = (current / total) * 100
        logger.info(
            "  ⌛ %s: %d/%d (%.0f%%)",
            description,
            current,
            total,
            percentage,
        )

    def estimate_time_remaining(self) -> float | None:
        """Estimate time remaining based on observed average stage duration.

        Returns:
            Estimated seconds remaining, or None if no data yet.
        """
        if not self._stage_durations:
            return None

        avg_duration = sum(self._stage_durations) / len(self._stage_durations)
        remaining_stages = self.total_stages - self.completed_stages
        return remaining_stages * avg_duration

    def get_progress_summary(self) -> dict[str, Any]:
        """Return a snapshot of current progress.

        Returns:
            Dict with completed_stages, total_stages, current_stage,
            percent_complete, estimated_remaining_seconds.
        """
        pct = (
            (self.completed_stages / self.total_stages) * 100
            if self.total_stages > 0
            else 0.0
        )
        return {
            "completed_stages": self.completed_stages,
            "total_stages": self.total_stages,
            "current_stage": self.current_stage,
            "percent_complete": round(pct, 1),
            "estimated_remaining_seconds": self.estimate_time_remaining(),
        }

    def reset(self) -> None:
        """Reset all tracking state."""
        self.completed_stages = 0
        self.current_stage = None
        self.stage_start_time = None
        self._stage_durations.clear()
