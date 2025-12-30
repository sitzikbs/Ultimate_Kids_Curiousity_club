"""Cost tracking for LLM API calls."""

from dataclasses import dataclass, field
from datetime import UTC, datetime


@dataclass
class LLMCallMetrics:
    """Metrics for a single LLM API call."""

    stage: str  # ideation, outline, segment, script
    prompt_tokens: int
    completion_tokens: int
    total_tokens: int
    cost: float
    duration_seconds: float
    timestamp: datetime
    provider: str
    model: str


@dataclass
class CostTracker:
    """Track LLM API costs and token usage."""

    calls: list[LLMCallMetrics] = field(default_factory=list)
    budget_limit: float | None = None

    def log_call(
        self,
        stage: str,
        prompt_tokens: int,
        completion_tokens: int,
        cost: float,
        duration: float,
        provider: str,
        model: str,
    ) -> None:
        """Log a single LLM API call.

        Args:
            stage: Generation stage (ideation, outline, segment, script)
            prompt_tokens: Number of prompt/input tokens
            completion_tokens: Number of completion/output tokens
            cost: Cost in USD
            duration: Duration in seconds
            provider: Provider name (openai, anthropic, etc.)
            model: Model name (gpt-4, claude-3, etc.)
        """
        total_tokens = prompt_tokens + completion_tokens
        metrics = LLMCallMetrics(
            stage=stage,
            prompt_tokens=prompt_tokens,
            completion_tokens=completion_tokens,
            total_tokens=total_tokens,
            cost=cost,
            duration_seconds=duration,
            timestamp=datetime.now(UTC),
            provider=provider,
            model=model,
        )
        self.calls.append(metrics)

        # Check budget warning
        if self.budget_limit is not None:
            total_cost = self.get_episode_cost()
            if total_cost >= self.budget_limit * 0.8:  # 80% threshold
                remaining = self.budget_limit - total_cost
                print(
                    f"⚠️  Budget Warning: ${total_cost:.4f} of ${self.budget_limit:.2f} "
                    f"used ({(total_cost/self.budget_limit)*100:.1f}%). "
                    f"Remaining: ${remaining:.4f}"
                )

    def get_episode_cost(self) -> float:
        """Get total cost for all calls.

        Returns:
            Total cost in USD
        """
        return sum(call.cost for call in self.calls)

    def get_total_tokens(self) -> int:
        """Get total tokens used across all calls.

        Returns:
            Total number of tokens
        """
        return sum(call.total_tokens for call in self.calls)

    def get_stage_breakdown(self) -> dict[str, dict[str, float]]:
        """Get cost and token breakdown by stage.

        Returns:
            Dictionary with stage names as keys and metrics as values
        """
        breakdown: dict[str, dict[str, float]] = {}
        for call in self.calls:
            if call.stage not in breakdown:
                breakdown[call.stage] = {"cost": 0.0, "tokens": 0, "calls": 0}
            breakdown[call.stage]["cost"] += call.cost
            breakdown[call.stage]["tokens"] += call.total_tokens
            breakdown[call.stage]["calls"] += 1
        return breakdown

    def get_provider_breakdown(self) -> dict[str, dict[str, float]]:
        """Get cost and token breakdown by provider.

        Returns:
            Dictionary with provider names as keys and metrics as values
        """
        breakdown: dict[str, dict[str, float]] = {}
        for call in self.calls:
            if call.provider not in breakdown:
                breakdown[call.provider] = {"cost": 0.0, "tokens": 0, "calls": 0}
            breakdown[call.provider]["cost"] += call.cost
            breakdown[call.provider]["tokens"] += call.total_tokens
            breakdown[call.provider]["calls"] += 1
        return breakdown

    def export_report(self) -> dict:
        """Export cost report for episode checkpoint.

        Returns:
            Dictionary containing complete cost report
        """
        return {
            "total_cost": self.get_episode_cost(),
            "total_tokens": self.get_total_tokens(),
            "stage_breakdown": self.get_stage_breakdown(),
            "provider_breakdown": self.get_provider_breakdown(),
            "call_count": len(self.calls),
            "calls": [
                {
                    "stage": call.stage,
                    "provider": call.provider,
                    "model": call.model,
                    "prompt_tokens": call.prompt_tokens,
                    "completion_tokens": call.completion_tokens,
                    "total_tokens": call.total_tokens,
                    "cost": call.cost,
                    "duration_seconds": call.duration_seconds,
                    "timestamp": call.timestamp.isoformat(),
                }
                for call in self.calls
            ],
        }

    def reset(self) -> None:
        """Reset tracker for a new episode."""
        self.calls.clear()

    def set_budget_limit(self, limit: float) -> None:
        """Set budget limit for warnings.

        Args:
            limit: Budget limit in USD
        """
        self.budget_limit = limit
