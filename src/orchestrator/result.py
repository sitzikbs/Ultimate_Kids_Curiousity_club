"""Pipeline result types for explicit control flow.

Replaces exception-based signalling (``ApprovalRequiredError``) with
typed result objects so that the approval gate is an ordinary return
path rather than an exception.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import Enum
from typing import Any

from models.episode import Episode


class PipelineResultStatus(str, Enum):
    """Possible outcomes of a pipeline execution."""

    APPROVAL_REQUIRED = "approval_required"
    COMPLETED = "completed"
    FAILED = "failed"


@dataclass(frozen=True)
class PipelineResult:
    """Typed result returned by pipeline public methods.

    Attributes:
        status: Outcome of the pipeline run.
        episode: The episode in its current state.
        message: Human-readable summary.
        data: Optional extra payload (e.g. outline for review).
    """

    status: PipelineResultStatus
    episode: Episode
    message: str = ""
    data: dict[str, Any] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=lambda: datetime.now(UTC))

    # Convenience predicates
    @property
    def is_approval_required(self) -> bool:
        """True when the pipeline paused for human review."""
        return self.status == PipelineResultStatus.APPROVAL_REQUIRED

    @property
    def is_completed(self) -> bool:
        """True when the pipeline finished successfully."""
        return self.status == PipelineResultStatus.COMPLETED

    @property
    def is_failed(self) -> bool:
        """True when the pipeline ended in a failure state."""
        return self.status == PipelineResultStatus.FAILED
