"""Pipeline event system for decoupled stage notifications.

Provides a lightweight event model and callback type for notifying
external systems (WebSocket, CLI, logging) of pipeline state changes.
"""

from collections.abc import Awaitable, Callable
from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Any

from models.episode import PipelineStage


@dataclass
class PipelineEvent:
    """Event emitted when a pipeline stage completes or changes."""

    event_type: str
    episode_id: str
    show_id: str
    stage: PipelineStage
    timestamp: datetime = field(default_factory=lambda: datetime.now(UTC))
    data: dict[str, Any] = field(default_factory=dict)


# Callback type: sync or async function accepting a PipelineEvent
EventCallback = Callable[[PipelineEvent], Awaitable[None] | None]
