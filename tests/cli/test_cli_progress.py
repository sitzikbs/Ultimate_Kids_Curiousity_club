"""Tests for the progress visualization module (Task 7.6)."""

from __future__ import annotations

import pytest
from rich.console import Console

from cli.progress import (
    ALL_STAGES,
    POST_APPROVAL_STAGES,
    PRE_APPROVAL_STAGES,
    STAGE_DISPLAY,
    PipelineProgress,
    create_progress_callback,
)
from models.episode import PipelineStage
from orchestrator.events import EventType, PipelineEvent

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_event(
    event_type: EventType,
    stage: PipelineStage = PipelineStage.IDEATION,
    data: dict | None = None,
) -> PipelineEvent:
    """Create a test PipelineEvent."""
    return PipelineEvent(
        event_type=event_type,
        episode_id="ep_test",
        show_id="test_show",
        stage=stage,
        data=data or {},
    )


# ---------------------------------------------------------------------------
# Phase configuration
# ---------------------------------------------------------------------------


class TestPhaseConfiguration:
    """Phase-based stage lists."""

    def test_pre_approval_stages(self):
        """Pre-approval contains ideation and outlining."""
        p = PipelineProgress(phase="pre-approval")
        assert p._stage_order == PRE_APPROVAL_STAGES
        assert p._total == 2

    def test_post_approval_stages(self):
        """Post-approval contains 4 production stages."""
        p = PipelineProgress(phase="post-approval")
        assert p._stage_order == POST_APPROVAL_STAGES
        assert p._total == 4

    def test_full_stages(self):
        """Full phase contains all 6 stages."""
        p = PipelineProgress(phase="full")
        assert p._stage_order == ALL_STAGES
        assert p._total == 6

    def test_all_stages_have_display_names(self):
        """Every stage key in ALL_STAGES has a display name."""
        for stage in ALL_STAGES:
            assert stage in STAGE_DISPLAY


# ---------------------------------------------------------------------------
# Event handling
# ---------------------------------------------------------------------------


class TestEventCallback:
    """Tests for PipelineProgress.event_callback."""

    @pytest.mark.asyncio
    async def test_stage_started_sets_current(self):
        """STAGE_STARTED updates _current."""
        p = PipelineProgress(phase="pre-approval")
        event = _make_event(EventType.STAGE_STARTED, PipelineStage.IDEATION)

        await p.event_callback(event)

        assert p._current == "ideation"

    @pytest.mark.asyncio
    async def test_stage_completed_increments(self):
        """STAGE_COMPLETED adds to _completed list."""
        p = PipelineProgress(phase="pre-approval")
        event = _make_event(
            EventType.STAGE_COMPLETED,
            PipelineStage.IDEATION,
            data={"stage": "ideation"},
        )

        await p.event_callback(event)

        assert "ideation" in p._completed
        assert p._current is None

    @pytest.mark.asyncio
    async def test_stage_completed_tracks_cost(self):
        """Cost from event data is accumulated."""
        p = PipelineProgress(phase="post-approval")
        event = _make_event(
            EventType.STAGE_COMPLETED,
            PipelineStage.SEGMENT_GENERATION,
            data={"stage": "segment_generation", "cost": 0.05},
        )

        await p.event_callback(event)

        assert p._cumulative_cost == pytest.approx(0.05)

    @pytest.mark.asyncio
    async def test_approval_required_pauses(self):
        """APPROVAL_REQUIRED sets internal state without crash."""
        p = PipelineProgress(phase="pre-approval")
        event = _make_event(
            EventType.APPROVAL_REQUIRED, PipelineStage.AWAITING_APPROVAL
        )

        # Should not raise
        await p.event_callback(event)

    @pytest.mark.asyncio
    async def test_full_pre_approval_flow(self):
        """Simulate ideation → outlining → approval."""
        p = PipelineProgress(phase="pre-approval")

        await p.event_callback(
            _make_event(EventType.STAGE_STARTED, PipelineStage.IDEATION)
        )
        await p.event_callback(
            _make_event(
                EventType.STAGE_COMPLETED,
                PipelineStage.IDEATION,
                data={"stage": "ideation"},
            )
        )
        await p.event_callback(
            _make_event(EventType.STAGE_STARTED, PipelineStage.OUTLINING)
        )
        await p.event_callback(
            _make_event(
                EventType.STAGE_COMPLETED,
                PipelineStage.OUTLINING,
                data={"stage": "outlining"},
            )
        )
        await p.event_callback(
            _make_event(EventType.APPROVAL_REQUIRED, PipelineStage.AWAITING_APPROVAL)
        )

        assert len(p._completed) == 2
        assert "ideation" in p._completed
        assert "outlining" in p._completed


# ---------------------------------------------------------------------------
# Time estimation
# ---------------------------------------------------------------------------


class TestTimeEstimation:
    """Tests for time remaining estimates."""

    def test_no_data_returns_none(self):
        """No completed stages → None."""
        p = PipelineProgress(phase="full")
        assert p.estimate_time_remaining() is None

    @pytest.mark.asyncio
    async def test_estimate_after_one_stage(self):
        """After 1 stage, estimate remaining based on average."""
        p = PipelineProgress(phase="post-approval")
        p._stage_durations["segment_generation"] = 2.0
        p._completed.append("segment_generation")

        remaining = p.estimate_time_remaining()
        assert remaining is not None
        # 3 remaining stages × 2.0s average = 6.0s
        assert remaining == pytest.approx(6.0)


# ---------------------------------------------------------------------------
# Summary output
# ---------------------------------------------------------------------------


class TestFormatSummary:
    """Tests for the format_summary Rich Panel."""

    def test_summary_panel_after_completion(self):
        """format_summary returns a Panel with stage rows."""
        p = PipelineProgress(console=Console(width=80), phase="pre-approval")
        p._start_time = 0.0  # force known start
        p._completed = ["ideation", "outlining"]
        p._stage_durations = {"ideation": 1.5, "outlining": 2.0}

        panel = p.format_summary()

        assert panel is not None
        # It's a Rich Panel — title should reflect completion
        assert "Complete" in str(panel.title) or "Paused" in str(panel.title)

    def test_summary_includes_cost_when_present(self):
        """Cost line appears only when cumulative cost > 0."""
        p = PipelineProgress(console=Console(width=80), phase="post-approval")
        p._start_time = 0.0
        p._cumulative_cost = 0.12
        p._completed = POST_APPROVAL_STAGES[:]

        panel = p.format_summary()
        # Render to string for assertion
        console = Console(width=80, file=None)
        with console.capture() as capture:
            console.print(panel)
        output = capture.get()
        assert "$0.12" in output


# ---------------------------------------------------------------------------
# Context manager
# ---------------------------------------------------------------------------


class TestContextManager:
    """Tests for start/stop lifecycle."""

    def test_context_manager_starts_and_stops(self):
        """__enter__/__exit__ start/stop the progress display."""
        p = PipelineProgress(
            console=Console(width=80, quiet=True), phase="pre-approval"
        )

        with p:
            assert p._task_id is not None
            assert p._start_time is not None

    def test_create_progress_callback_returns_instance(self):
        """Factory function returns a usable PipelineProgress."""
        p = create_progress_callback(phase="post-approval")
        assert isinstance(p, PipelineProgress)
        assert p._total == 4
