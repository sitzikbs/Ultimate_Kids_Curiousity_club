"""Tests for CostTracker."""

from datetime import datetime

from services.llm.cost_tracker import CostTracker, LLMCallMetrics


class TestLLMCallMetrics:
    """Tests for LLMCallMetrics dataclass."""

    def test_create_metrics(self):
        """Test creating metrics instance."""
        metrics = LLMCallMetrics(
            stage="ideation",
            prompt_tokens=100,
            completion_tokens=200,
            total_tokens=300,
            cost=0.05,
            duration_seconds=2.5,
            timestamp=datetime.now(),
            provider="openai",
            model="gpt-4",
        )

        assert metrics.stage == "ideation"
        assert metrics.prompt_tokens == 100
        assert metrics.completion_tokens == 200
        assert metrics.total_tokens == 300
        assert metrics.cost == 0.05


class TestCostTracker:
    """Tests for CostTracker."""

    def test_init_empty(self):
        """Test tracker initializes empty."""
        tracker = CostTracker()
        assert len(tracker.calls) == 0
        assert tracker.get_episode_cost() == 0.0
        assert tracker.get_total_tokens() == 0

    def test_log_single_call(self):
        """Test logging a single call."""
        tracker = CostTracker()
        tracker.log_call(
            stage="ideation",
            prompt_tokens=100,
            completion_tokens=200,
            cost=0.05,
            duration=2.5,
            provider="openai",
            model="gpt-4",
        )

        assert len(tracker.calls) == 1
        assert tracker.get_episode_cost() == 0.05
        assert tracker.get_total_tokens() == 300

    def test_log_multiple_calls(self):
        """Test logging multiple calls."""
        tracker = CostTracker()

        # Log ideation
        tracker.log_call(
            stage="ideation",
            prompt_tokens=100,
            completion_tokens=200,
            cost=0.05,
            duration=2.5,
            provider="openai",
            model="gpt-4",
        )

        # Log outline
        tracker.log_call(
            stage="outline",
            prompt_tokens=150,
            completion_tokens=300,
            cost=0.08,
            duration=3.0,
            provider="openai",
            model="gpt-4",
        )

        assert len(tracker.calls) == 2
        assert tracker.get_episode_cost() == 0.13
        assert tracker.get_total_tokens() == 750

    def test_stage_breakdown(self):
        """Test getting cost breakdown by stage."""
        tracker = CostTracker()

        # Log multiple calls to different stages
        tracker.log_call(
            stage="ideation",
            prompt_tokens=100,
            completion_tokens=200,
            cost=0.05,
            duration=2.5,
            provider="openai",
            model="gpt-4",
        )

        tracker.log_call(
            stage="outline",
            prompt_tokens=150,
            completion_tokens=300,
            cost=0.08,
            duration=3.0,
            provider="openai",
            model="gpt-4",
        )

        tracker.log_call(
            stage="ideation",
            prompt_tokens=120,
            completion_tokens=180,
            cost=0.04,
            duration=2.0,
            provider="anthropic",
            model="claude-3",
        )

        breakdown = tracker.get_stage_breakdown()

        assert "ideation" in breakdown
        assert "outline" in breakdown
        assert breakdown["ideation"]["cost"] == 0.09
        assert breakdown["ideation"]["tokens"] == 600
        assert breakdown["ideation"]["calls"] == 2
        assert breakdown["outline"]["cost"] == 0.08
        assert breakdown["outline"]["tokens"] == 450
        assert breakdown["outline"]["calls"] == 1

    def test_provider_breakdown(self):
        """Test getting cost breakdown by provider."""
        tracker = CostTracker()

        # Log calls to different providers
        tracker.log_call(
            stage="ideation",
            prompt_tokens=100,
            completion_tokens=200,
            cost=0.05,
            duration=2.5,
            provider="openai",
            model="gpt-4",
        )

        tracker.log_call(
            stage="outline",
            prompt_tokens=150,
            completion_tokens=300,
            cost=0.08,
            duration=3.0,
            provider="anthropic",
            model="claude-3",
        )

        breakdown = tracker.get_provider_breakdown()

        assert "openai" in breakdown
        assert "anthropic" in breakdown
        assert breakdown["openai"]["cost"] == 0.05
        assert breakdown["anthropic"]["cost"] == 0.08

    def test_export_report(self):
        """Test exporting cost report."""
        tracker = CostTracker()

        tracker.log_call(
            stage="ideation",
            prompt_tokens=100,
            completion_tokens=200,
            cost=0.05,
            duration=2.5,
            provider="openai",
            model="gpt-4",
        )

        report = tracker.export_report()

        assert report["total_cost"] == 0.05
        assert report["total_tokens"] == 300
        assert report["call_count"] == 1
        assert "stage_breakdown" in report
        assert "provider_breakdown" in report
        assert "calls" in report
        assert len(report["calls"]) == 1
        assert report["calls"][0]["stage"] == "ideation"
        assert report["calls"][0]["provider"] == "openai"

    def test_reset(self):
        """Test resetting tracker."""
        tracker = CostTracker()

        tracker.log_call(
            stage="ideation",
            prompt_tokens=100,
            completion_tokens=200,
            cost=0.05,
            duration=2.5,
            provider="openai",
            model="gpt-4",
        )

        assert len(tracker.calls) == 1
        tracker.reset()
        assert len(tracker.calls) == 0
        assert tracker.get_episode_cost() == 0.0

    def test_budget_warning(self, caplog):
        """Test budget warning when approaching limit."""
        import logging

        tracker = CostTracker(budget_limit=1.0)

        # Log call that exceeds 80% of budget
        with caplog.at_level(logging.WARNING):
            tracker.log_call(
                stage="ideation",
                prompt_tokens=1000,
                completion_tokens=2000,
                cost=0.85,
                duration=5.0,
                provider="openai",
                model="gpt-4",
            )

        assert "Budget Warning" in caplog.text

    def test_set_budget_limit(self):
        """Test setting budget limit."""
        tracker = CostTracker()
        assert tracker.budget_limit is None

        tracker.set_budget_limit(2.0)
        assert tracker.budget_limit == 2.0

    def test_no_budget_warning_below_threshold(self, caplog):
        """Test no warning when below threshold."""
        import logging

        tracker = CostTracker(budget_limit=1.0)

        # Log call under 80% of budget
        with caplog.at_level(logging.WARNING):
            tracker.log_call(
                stage="ideation",
                prompt_tokens=100,
                completion_tokens=200,
                cost=0.50,
                duration=2.5,
                provider="openai",
                model="gpt-4",
            )

        assert "Budget Warning" not in caplog.text
