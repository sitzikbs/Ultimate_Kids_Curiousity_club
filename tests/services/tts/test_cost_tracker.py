"""Unit tests for TTS Cost Tracker."""

from pathlib import Path

import pytest

from services.tts.cost_tracker import TTSCostTracker


@pytest.mark.unit
class TestTTSCostTracker:
    """Tests for TTSCostTracker."""

    @pytest.fixture
    def tracker(self):
        """Create a cost tracker."""
        return TTSCostTracker()

    @pytest.fixture
    def tracker_with_budget(self):
        """Create a cost tracker with budget threshold."""
        return TTSCostTracker(budget_threshold=10.0)

    def test_tracker_creation(self, tracker):
        """Test creating a cost tracker."""
        assert tracker is not None
        assert tracker.get_total_cost() == 0.0
        assert tracker.get_total_characters() == 0

    def test_track_single_request(self, tracker):
        """Test tracking a single request."""
        entry = tracker.track_request(
            provider="elevenlabs",
            voice_id="test_voice",
            characters=1000,
            cost=0.30,
        )

        assert entry.provider == "elevenlabs"
        assert entry.voice_id == "test_voice"
        assert entry.characters == 1000
        assert entry.cost == 0.30

        assert tracker.get_total_cost() == 0.30
        assert tracker.get_total_characters() == 1000

    def test_track_multiple_requests(self, tracker):
        """Test tracking multiple requests."""
        tracker.track_request("elevenlabs", "voice1", 1000, 0.30)
        tracker.track_request("google", "voice2", 500000, 2.00)
        tracker.track_request("openai", "voice3", 100000, 1.50)

        assert tracker.get_total_cost() == 3.80
        assert tracker.get_total_characters() == 601000

    def test_get_cost_by_provider(self, tracker):
        """Test getting cost breakdown by provider."""
        tracker.track_request("elevenlabs", "voice1", 1000, 0.30)
        tracker.track_request("elevenlabs", "voice2", 1000, 0.30)
        tracker.track_request("google", "voice3", 500000, 2.00)

        by_provider = tracker.get_cost_by_provider()

        assert by_provider["elevenlabs"] == 0.60
        assert by_provider["google"] == 2.00

    def test_get_cost_by_voice(self, tracker):
        """Test getting cost breakdown by voice."""
        tracker.track_request("elevenlabs", "voice1", 1000, 0.30)
        tracker.track_request("elevenlabs", "voice1", 1000, 0.30)
        tracker.track_request("elevenlabs", "voice2", 1000, 0.30)

        by_voice = tracker.get_cost_by_voice()

        assert by_voice["voice1"] == 0.60
        assert by_voice["voice2"] == 0.30

    def test_generate_report(self, tracker):
        """Test generating a cost report."""
        tracker.track_request("elevenlabs", "voice1", 1000, 0.30)
        tracker.track_request("google", "voice2", 500000, 2.00)

        report = tracker.generate_report()

        assert report.total_cost == 2.30
        assert report.total_characters == 501000
        assert report.entry_count == 2
        assert "elevenlabs" in report.by_provider
        assert "google" in report.by_provider

    def test_save_and_load_file(self, tracker, tmp_path: Path):
        """Test saving and loading cost data."""
        tracker.track_request("elevenlabs", "voice1", 1000, 0.30)
        tracker.track_request("google", "voice2", 500000, 2.00)

        # Save to file
        output_path = tmp_path / "costs.json"
        tracker.save_to_file(output_path)

        assert output_path.exists()

        # Load in new tracker
        new_tracker = TTSCostTracker()
        new_tracker.load_from_file(output_path)

        assert new_tracker.get_total_cost() == 2.30
        assert new_tracker.get_total_characters() == 501000

    def test_reset(self, tracker):
        """Test resetting tracker."""
        tracker.track_request("elevenlabs", "voice1", 1000, 0.30)
        assert tracker.get_total_cost() > 0

        tracker.reset()

        assert tracker.get_total_cost() == 0.0
        assert tracker.get_total_characters() == 0
        assert len(tracker.entries) == 0

    def test_budget_threshold_warning(self, tracker_with_budget, capsys):
        """Test budget threshold warning."""
        # Track requests that exceed budget
        tracker_with_budget.track_request("elevenlabs", "voice1", 35000, 10.50)

        captured = capsys.readouterr()
        assert "Budget threshold exceeded" in captured.out

    def test_get_episode_cost_summary(self, tracker):
        """Test getting episode cost summary."""
        tracker.track_request("elevenlabs", "voice1", 1000, 0.30)

        summary = tracker.get_episode_cost_summary()

        assert "total_cost" in summary
        assert "total_characters" in summary
        assert "by_provider" in summary
        assert summary["total_cost"] == 0.30

    def test_print_summary(self, tracker, capsys):
        """Test printing cost summary."""
        tracker.track_request("elevenlabs", "voice1", 1000, 0.30)
        tracker.track_request("google", "voice2", 500000, 2.00)

        tracker.print_summary()

        captured = capsys.readouterr()
        assert "TTS COST SUMMARY" in captured.out
        assert "$2.30" in captured.out
        assert "elevenlabs" in captured.out
        assert "google" in captured.out
