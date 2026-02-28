"""Tests for WP6b ProgressTracker: stage progress, substage, time estimation."""

from orchestrator.progress_tracker import ProgressTracker

# ---------------------------------------------------------------------------
# Basic lifecycle
# ---------------------------------------------------------------------------


class TestProgressTrackerLifecycle:
    """Tests for start/complete stage lifecycle."""

    def test_initial_state(self):
        """Tracker starts with zero completions and no current stage."""
        tracker = ProgressTracker(total_stages=6)
        assert tracker.completed_stages == 0
        assert tracker.current_stage is None
        assert tracker.stage_start_time is None

    def test_start_stage_sets_current(self):
        """start_stage records the current stage name and timestamp."""
        tracker = ProgressTracker()
        tracker.start_stage("Ideation")
        assert tracker.current_stage == "Ideation"
        assert tracker.stage_start_time is not None

    def test_complete_stage_increments_count(self):
        """complete_stage increments completed_stages and clears current."""
        tracker = ProgressTracker()
        tracker.start_stage("Ideation")
        duration = tracker.complete_stage("Ideation")

        assert tracker.completed_stages == 1
        assert tracker.current_stage is None
        assert tracker.stage_start_time is None
        assert duration >= 0.0

    def test_multiple_stages(self):
        """Multiple start/complete cycles accumulate properly."""
        tracker = ProgressTracker(total_stages=3)

        for stage in ["Ideation", "Outlining", "Segment Generation"]:
            tracker.start_stage(stage)
            tracker.complete_stage(stage)

        assert tracker.completed_stages == 3

    def test_complete_without_start_returns_zero(self):
        """Completing without starting returns 0 duration."""
        tracker = ProgressTracker()
        duration = tracker.complete_stage("Unknown")
        assert duration == 0.0
        assert tracker.completed_stages == 1


# ---------------------------------------------------------------------------
# Substage progress
# ---------------------------------------------------------------------------


class TestSubstageProgress:
    """Tests for report_substage_progress."""

    def test_substage_progress_logs(self, caplog):
        """Substage progress is logged with percentage."""
        tracker = ProgressTracker()

        import logging

        with caplog.at_level(logging.INFO):
            tracker.report_substage_progress(3, 10, "Synthesizing segments")

        assert "3/10" in caplog.text
        assert "30%" in caplog.text

    def test_substage_progress_zero_total(self, caplog):
        """Zero total should not cause division by zero."""
        tracker = ProgressTracker()

        import logging

        with caplog.at_level(logging.INFO):
            tracker.report_substage_progress(0, 0, "Nothing")

        # Should not raise, and nothing meaningful logged
        assert True


# ---------------------------------------------------------------------------
# Time estimation
# ---------------------------------------------------------------------------


class TestTimeEstimation:
    """Tests for estimate_time_remaining."""

    def test_no_data_returns_none(self):
        """With no completed stages, estimation returns None."""
        tracker = ProgressTracker(total_stages=6)
        assert tracker.estimate_time_remaining() is None

    def test_estimates_from_average(self):
        """Estimation uses average of observed durations."""
        tracker = ProgressTracker(total_stages=4)

        # Simulate two completed stages manually
        tracker.start_stage("Stage 1")
        tracker.complete_stage("Stage 1")
        tracker.start_stage("Stage 2")
        tracker.complete_stage("Stage 2")

        remaining = tracker.estimate_time_remaining()
        assert remaining is not None
        assert remaining >= 0.0
        # With 2 completed and 4 total, 2 remaining
        # The remaining estimate = avg_duration * 2


# ---------------------------------------------------------------------------
# Progress summary
# ---------------------------------------------------------------------------


class TestProgressSummary:
    """Tests for get_progress_summary."""

    def test_summary_structure(self):
        """Summary contains required keys."""
        tracker = ProgressTracker(total_stages=6)
        summary = tracker.get_progress_summary()

        assert "completed_stages" in summary
        assert "total_stages" in summary
        assert "current_stage" in summary
        assert "percent_complete" in summary
        assert "estimated_remaining_seconds" in summary

    def test_summary_percent_calculation(self):
        """Percent complete is correctly calculated."""
        tracker = ProgressTracker(total_stages=4)
        tracker.start_stage("S1")
        tracker.complete_stage("S1")
        tracker.start_stage("S2")
        tracker.complete_stage("S2")

        summary = tracker.get_progress_summary()
        assert summary["percent_complete"] == 50.0
        assert summary["completed_stages"] == 2
        assert summary["total_stages"] == 4


# ---------------------------------------------------------------------------
# Reset
# ---------------------------------------------------------------------------


class TestProgressReset:
    """Tests for tracker reset."""

    def test_reset_clears_all_state(self):
        """reset() restores initial state."""
        tracker = ProgressTracker(total_stages=6)
        tracker.start_stage("S1")
        tracker.complete_stage("S1")
        tracker.start_stage("S2")

        tracker.reset()

        assert tracker.completed_stages == 0
        assert tracker.current_stage is None
        assert tracker.stage_start_time is None
        assert tracker.estimate_time_remaining() is None
