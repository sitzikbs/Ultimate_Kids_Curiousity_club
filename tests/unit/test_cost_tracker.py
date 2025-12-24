"""Unit tests for cost tracking utilities."""

from datetime import datetime

import pytest

from tests.utils.cost_tracker import APICall, CostTracker


@pytest.mark.unit
def test_cost_tracker_initialization() -> None:
    """Test that cost tracker initializes correctly."""
    tracker = CostTracker()

    assert tracker.get_total_cost() == 0.0
    assert len(tracker.calls) == 0
    assert tracker._budget_limit == 10.0


@pytest.mark.unit
def test_cost_tracker_record_call() -> None:
    """Test recording an API call."""
    tracker = CostTracker()

    tracker.record_call(
        service="openai",
        operation="completion",
        cost_usd=0.05,
        tokens_used=500,
    )

    assert len(tracker.calls) == 1
    assert tracker.get_total_cost() == 0.05
    assert tracker.calls[0].service == "openai"
    assert tracker.calls[0].tokens_used == 500


@pytest.mark.unit
def test_cost_tracker_multiple_calls() -> None:
    """Test recording multiple API calls."""
    tracker = CostTracker()

    tracker.record_call("openai", "completion", 0.05)
    tracker.record_call("anthropic", "completion", 0.08)
    tracker.record_call("elevenlabs", "tts", 0.15)

    assert len(tracker.calls) == 3
    assert tracker.get_total_cost() == 0.28


@pytest.mark.unit
def test_cost_tracker_by_service() -> None:
    """Test getting costs by service."""
    tracker = CostTracker()

    tracker.record_call("openai", "completion", 0.05)
    tracker.record_call("openai", "completion", 0.03)
    tracker.record_call("anthropic", "completion", 0.08)

    assert tracker.get_cost_by_service("openai") == 0.08
    assert tracker.get_cost_by_service("anthropic") == 0.08
    assert tracker.get_cost_by_service("elevenlabs") == 0.0


@pytest.mark.unit
def test_cost_tracker_budget_check() -> None:
    """Test budget checking."""
    tracker = CostTracker()
    tracker.set_budget_limit(1.0)

    # Within budget
    tracker.record_call("openai", "completion", 0.50)
    within_budget, remaining = tracker.check_budget()
    assert within_budget is True
    assert pytest.approx(remaining, abs=0.01) == 0.50

    # Over budget
    tracker.record_call("openai", "completion", 0.60)
    within_budget, remaining = tracker.check_budget()
    assert within_budget is False
    assert pytest.approx(remaining, abs=0.01) == -0.10


@pytest.mark.unit
def test_cost_tracker_summary() -> None:
    """Test getting cost summary."""
    tracker = CostTracker()
    tracker.set_budget_limit(5.0)

    tracker.record_call("openai", "completion", 0.05)
    tracker.record_call("openai", "completion", 0.03)
    tracker.record_call("elevenlabs", "tts", 0.15)

    summary = tracker.get_summary()

    assert pytest.approx(summary["total_cost_usd"], abs=0.01) == 0.23
    assert summary["total_calls"] == 3
    assert summary["budget_limit_usd"] == 5.0
    assert summary["within_budget"] is True
    assert "openai" in summary["by_service"]
    assert "elevenlabs" in summary["by_service"]
    assert summary["by_service"]["openai"]["call_count"] == 2
    assert summary["by_service"]["elevenlabs"]["call_count"] == 1


@pytest.mark.unit
def test_api_call_dataclass() -> None:
    """Test APICall dataclass creation."""
    call = APICall(
        service="openai",
        operation="completion",
        timestamp=datetime.now(),
        cost_usd=0.05,
        tokens_used=500,
        metadata={"model": "gpt-4"},
    )

    assert call.service == "openai"
    assert call.operation == "completion"
    assert call.cost_usd == 0.05
    assert call.tokens_used == 500
    assert call.metadata["model"] == "gpt-4"
