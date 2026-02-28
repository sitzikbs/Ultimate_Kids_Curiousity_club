"""Progress visualization utilities for CLI pipeline commands.

Provides a Rich-based progress display that hooks into the pipeline
event callback to show real-time stage progress, spinners, estimated
time remaining, and cumulative cost tracking.
"""

from __future__ import annotations

import time
from typing import Any

from rich.console import Console
from rich.panel import Panel
from rich.progress import (
    BarColumn,
    Progress,
    SpinnerColumn,
    TaskProgressColumn,
    TextColumn,
    TimeElapsedColumn,
)
from rich.table import Table

from models.episode import PipelineStage
from orchestrator.events import EventType, PipelineEvent

# ---------------------------------------------------------------------------
# Stage metadata — ordering & display names
# ---------------------------------------------------------------------------

PRE_APPROVAL_STAGES: list[str] = ["ideation", "outlining"]
POST_APPROVAL_STAGES: list[str] = [
    "segment_generation",
    "script_generation",
    "audio_synthesis",
    "audio_mixing",
]

ALL_STAGES: list[str] = PRE_APPROVAL_STAGES + POST_APPROVAL_STAGES

STAGE_DISPLAY: dict[str, str] = {
    "ideation": "💡 Ideation",
    "outlining": "📝 Outlining",
    "segment_generation": "🧩 Segment Generation",
    "script_generation": "📜 Script Generation",
    "audio_synthesis": "🎤 Audio Synthesis",
    "audio_mixing": "🎧 Audio Mixing",
}

STAGE_TO_ENUM: dict[str, PipelineStage] = {
    "ideation": PipelineStage.IDEATION,
    "outlining": PipelineStage.OUTLINING,
    "segment_generation": PipelineStage.SEGMENT_GENERATION,
    "script_generation": PipelineStage.SCRIPT_GENERATION,
    "audio_synthesis": PipelineStage.AUDIO_SYNTHESIS,
    "audio_mixing": PipelineStage.AUDIO_MIXING,
}


# ---------------------------------------------------------------------------
# PipelineProgress — Rich-based live display
# ---------------------------------------------------------------------------


class PipelineProgress:
    """Rich-based progress display for pipeline execution.

    Designed to be used as a context manager::

        progress = PipelineProgress(phase="pre-approval")
        async with pipeline.generate_episode(...) as result:
            ...

    Or directly with the event callback.
    """

    def __init__(
        self,
        console: Console | None = None,
        phase: str = "full",
    ) -> None:
        """Initialise progress display.

        Args:
            console: Rich Console instance (uses default if ``None``).
            phase: ``"pre-approval"``, ``"post-approval"``, or ``"full"``.
        """
        self.console = console or Console()
        self.phase = phase
        self._stage_order = self._stages_for_phase(phase)
        self._total = len(self._stage_order)
        self._completed: list[str] = []
        self._current: str | None = None
        self._start_time: float | None = None
        self._stage_start: float | None = None
        self._stage_durations: dict[str, float] = {}
        self._cumulative_cost: float = 0.0

        # Rich progress bar
        self._progress = Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            TaskProgressColumn(),
            TimeElapsedColumn(),
            console=self.console,
        )
        self._task_id: Any = None

    # ------------------------------------------------------------------
    # Phase helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _stages_for_phase(phase: str) -> list[str]:
        """Return stage list for the given phase."""
        if phase == "pre-approval":
            return PRE_APPROVAL_STAGES[:]
        if phase == "post-approval":
            return POST_APPROVAL_STAGES[:]
        return ALL_STAGES[:]

    # ------------------------------------------------------------------
    # Event callback — wired into PipelineOrchestrator
    # ------------------------------------------------------------------

    async def event_callback(self, event: PipelineEvent) -> None:
        """Handle pipeline events to drive the progress display.

        This method matches the ``EventCallback`` signature and can be
        passed directly to :func:`cli.factory.create_pipeline`.
        """
        if event.event_type == EventType.STAGE_STARTED:
            # STAGE_STARTED doesn't carry a stage name in data;
            # derive it from the PipelineStage enum value.
            stage_name = event.stage.value.lower()
            self._on_stage_started(stage_name)
        elif event.event_type == EventType.STAGE_COMPLETED:
            stage_name = event.data.get("stage", event.stage.value.lower())
            cost = event.data.get("cost", 0.0)
            self._on_stage_completed(stage_name, cost)
        elif event.event_type == EventType.APPROVAL_REQUIRED:
            self._on_approval_required()

    # ------------------------------------------------------------------
    # Internal state transitions
    # ------------------------------------------------------------------

    def _on_stage_started(self, stage_name: str) -> None:
        """Update display when a stage begins."""
        self._current = stage_name
        self._stage_start = time.monotonic()
        display = STAGE_DISPLAY.get(stage_name, stage_name)
        if self._task_id is not None:
            self._progress.update(
                self._task_id,
                description=f"[cyan]{display}[/cyan]",
            )

    def _on_stage_completed(self, stage_name: str, cost: float = 0.0) -> None:
        """Update display when a stage finishes."""
        if self._stage_start is not None:
            self._stage_durations[stage_name] = time.monotonic() - self._stage_start
        self._completed.append(stage_name)
        self._cumulative_cost += cost
        self._current = None
        self._stage_start = None

        if self._task_id is not None:
            self._progress.update(
                self._task_id,
                completed=len(self._completed),
            )

    def _on_approval_required(self) -> None:
        """Handle the approval-gate pause."""
        if self._task_id is not None:
            self._progress.update(
                self._task_id,
                description="[yellow]⏸  Awaiting approval[/yellow]",
                completed=len(self._completed),
            )

    # ------------------------------------------------------------------
    # Context manager interface
    # ------------------------------------------------------------------

    def start(self) -> None:
        """Start the progress display (non-context-manager usage)."""
        self._start_time = time.monotonic()
        self._progress.start()
        self._task_id = self._progress.add_task(
            "[cyan]Starting…[/cyan]",
            total=self._total,
        )

    def stop(self) -> None:
        """Stop the progress display."""
        self._progress.stop()

    def __enter__(self) -> PipelineProgress:
        self.start()
        return self

    def __exit__(self, *_: Any) -> None:
        self.stop()

    # ------------------------------------------------------------------
    # Summary helpers
    # ------------------------------------------------------------------

    def format_summary(self) -> Panel:
        """Return a Rich Panel summarising the completed pipeline run."""
        elapsed = (
            time.monotonic() - self._start_time if self._start_time is not None else 0.0
        )

        table = Table.grid(padding=(0, 2))
        table.add_column(style="bold")
        table.add_column()

        for stage_name in self._stage_order:
            display = STAGE_DISPLAY.get(stage_name, stage_name)
            dur = self._stage_durations.get(stage_name)
            if stage_name in self._completed:
                dur_str = f"({dur:.1f}s)" if dur is not None else ""
                table.add_row(f"[green]✓[/green] {display}", f"[dim]{dur_str}[/dim]")
            elif stage_name == self._current:
                table.add_row(f"[cyan]▶[/cyan] {display}", "[cyan]running…[/cyan]")
            else:
                table.add_row(f"[dim]○ {display}[/dim]", "")

        table.add_row("", "")
        table.add_row("[bold]Total time[/bold]", f"{elapsed:.1f}s")
        if self._cumulative_cost > 0:
            table.add_row("[bold]Total cost[/bold]", f"${self._cumulative_cost:.4f}")

        title = (
            "[bold green]Pipeline Complete[/bold green]"
            if len(self._completed) == self._total
            else "[bold yellow]Pipeline Paused[/bold yellow]"
        )

        return Panel(table, title=title, border_style="green")

    def estimate_time_remaining(self) -> float | None:
        """Estimate remaining seconds based on observed stage durations.

        Returns:
            Estimated seconds, or ``None`` if no data.
        """
        durations = list(self._stage_durations.values())
        if not durations:
            return None
        avg = sum(durations) / len(durations)
        remaining = self._total - len(self._completed)
        return avg * remaining


# ---------------------------------------------------------------------------
# Convenience: one-shot progress display for a pipeline run
# ---------------------------------------------------------------------------


def create_progress_callback(
    console: Console | None = None,
    phase: str = "full",
) -> PipelineProgress:
    """Create a ``PipelineProgress`` instance ready for use.

    Returns the instance so the caller can start/stop and access
    ``event_callback`` and ``format_summary()``.
    """
    return PipelineProgress(console=console, phase=phase)
