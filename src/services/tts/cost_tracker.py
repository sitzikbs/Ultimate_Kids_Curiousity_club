"""Cost tracking for TTS API usage."""

from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from pydantic import BaseModel, Field


class TTSCostEntry(BaseModel):
    """A single TTS cost entry."""

    timestamp: datetime = Field(
        default_factory=lambda: datetime.now(UTC),
        description="When the request was made",
    )
    provider: str = Field(..., description="TTS provider name")
    voice_id: str = Field(..., description="Voice ID used")
    characters: int = Field(..., description="Number of characters synthesized")
    cost: float = Field(..., description="Cost in USD")
    segment_id: str | None = Field(None, description="Optional segment identifier")


class TTSCostReport(BaseModel):
    """Aggregated cost report."""

    total_cost: float = Field(..., description="Total cost in USD")
    total_characters: int = Field(..., description="Total characters synthesized")
    entry_count: int = Field(..., description="Number of cost entries")
    by_provider: dict[str, float] = Field(
        default_factory=dict, description="Cost breakdown by provider"
    )
    by_voice: dict[str, float] = Field(
        default_factory=dict, description="Cost breakdown by voice"
    )
    entries: list[TTSCostEntry] = Field(
        default_factory=list, description="Individual cost entries"
    )


class TTSCostTracker:
    """Tracker for TTS API usage and costs."""

    def __init__(self, budget_threshold: float | None = None):
        """Initialize cost tracker.

        Args:
            budget_threshold: Optional budget threshold in USD for warnings.
                            Warnings are printed to stdout by default.
        """
        self.budget_threshold = budget_threshold
        self.entries: list[TTSCostEntry] = []
        self._total_cost = 0.0
        self._total_characters = 0

    def track_request(
        self,
        provider: str,
        voice_id: str,
        characters: int,
        cost: float,
        segment_id: str | None = None,
    ) -> TTSCostEntry:
        """Track a TTS API request.

        Args:
            provider: TTS provider name
            voice_id: Voice ID used
            characters: Number of characters synthesized
            cost: Cost in USD
            segment_id: Optional segment identifier

        Returns:
            TTSCostEntry for the request
        """
        entry = TTSCostEntry(
            provider=provider,
            voice_id=voice_id,
            characters=characters,
            cost=cost,
            segment_id=segment_id,
        )

        self.entries.append(entry)
        self._total_cost += cost
        self._total_characters += characters

        # Check budget threshold
        if self.budget_threshold and self._total_cost >= self.budget_threshold:
            self._issue_budget_warning()

        return entry

    def _issue_budget_warning(self) -> None:
        """Issue a warning when budget threshold is exceeded.

        Note: This prints to stdout by default. For production use,
        consider integrating with a logging system or event handler.
        """
        print(
            f"⚠️  Budget threshold exceeded: ${self._total_cost:.2f} / "
            f"${self.budget_threshold:.2f}"
        )

    def get_total_cost(self) -> float:
        """Get total cost across all entries.

        Returns:
            Total cost in USD
        """
        return self._total_cost

    def get_total_characters(self) -> int:
        """Get total characters across all entries.

        Returns:
            Total number of characters synthesized
        """
        return self._total_characters

    def get_cost_by_provider(self) -> dict[str, float]:
        """Get cost breakdown by provider.

        Returns:
            Dictionary mapping provider names to costs
        """
        by_provider: dict[str, float] = {}
        for entry in self.entries:
            provider = entry.provider
            by_provider[provider] = by_provider.get(provider, 0.0) + entry.cost
        return by_provider

    def get_cost_by_voice(self) -> dict[str, float]:
        """Get cost breakdown by voice.

        Returns:
            Dictionary mapping voice IDs to costs
        """
        by_voice: dict[str, float] = {}
        for entry in self.entries:
            by_voice[entry.voice_id] = by_voice.get(entry.voice_id, 0.0) + entry.cost
        return by_voice

    def generate_report(self) -> TTSCostReport:
        """Generate a comprehensive cost report.

        Returns:
            TTSCostReport with aggregated cost data
        """
        return TTSCostReport(
            total_cost=self._total_cost,
            total_characters=self._total_characters,
            entry_count=len(self.entries),
            by_provider=self.get_cost_by_provider(),
            by_voice=self.get_cost_by_voice(),
            entries=self.entries,
        )

    def save_to_file(self, output_path: Path) -> None:
        """Save cost data to JSON file.

        Args:
            output_path: Path to save the cost data
        """
        report = self.generate_report()
        output_path.parent.mkdir(parents=True, exist_ok=True)

        # Write JSON
        with open(output_path, "w") as f:
            f.write(report.model_dump_json(indent=2))

    def load_from_file(self, input_path: Path) -> None:
        """Load cost data from JSON file.

        Args:
            input_path: Path to load the cost data from
        """
        if not input_path.exists():
            return

        # Read JSON
        with open(input_path) as f:
            report = TTSCostReport.model_validate_json(f.read())

        # Restore state
        self.entries = report.entries
        self._total_cost = report.total_cost
        self._total_characters = report.total_characters

    def reset(self) -> None:
        """Reset all cost tracking data."""
        self.entries = []
        self._total_cost = 0.0
        self._total_characters = 0

    def get_episode_cost_summary(self) -> dict[str, Any]:
        """Get a summary suitable for episode checkpoints.

        Returns:
            Dictionary with cost summary data
        """
        return {
            "total_cost": self._total_cost,
            "total_characters": self._total_characters,
            "entry_count": len(self.entries),
            "by_provider": self.get_cost_by_provider(),
            "budget_threshold": self.budget_threshold,
            "budget_exceeded": (
                self._total_cost >= self.budget_threshold
                if self.budget_threshold
                else False
            ),
        }

    def print_summary(self) -> None:
        """Print a human-readable cost summary."""
        print("\n" + "=" * 60)
        print("TTS COST SUMMARY")
        print("=" * 60)
        print(f"Total Cost: ${self._total_cost:.2f}")
        print(f"Total Characters: {self._total_characters:,}")
        print(f"Total Requests: {len(self.entries)}")

        if self.budget_threshold:
            print(f"Budget Threshold: ${self.budget_threshold:.2f}")
            remaining = self.budget_threshold - self._total_cost
            if remaining > 0:
                print(f"Remaining Budget: ${remaining:.2f}")
            else:
                print(f"Budget Exceeded By: ${-remaining:.2f}")

        # Print by provider
        print("\nBy Provider:")
        for provider, cost in self.get_cost_by_provider().items():
            print(f"  {provider}: ${cost:.2f}")

        # Print by voice (top 5)
        print("\nTop 5 Voices by Cost:")
        by_voice = sorted(
            self.get_cost_by_voice().items(), key=lambda x: x[1], reverse=True
        )[:5]
        for voice_id, cost in by_voice:
            print(f"  {voice_id}: ${cost:.2f}")

        print("=" * 60 + "\n")
