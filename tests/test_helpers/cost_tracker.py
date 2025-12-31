"""Cost tracking utilities for real API tests."""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any


@dataclass
class APICall:
    """Record of a single API call and its cost."""

    service: str  # 'openai', 'anthropic', 'elevenlabs', etc.
    operation: str  # 'completion', 'tts_synthesis', etc.
    timestamp: datetime
    cost_usd: float
    tokens_used: int | None = None
    metadata: dict[str, Any] = field(default_factory=dict)


class CostTracker:
    """Track costs for real API calls during testing."""

    def __init__(self) -> None:
        """Initialize the cost tracker."""
        self.calls: list[APICall] = []
        self._budget_limit = 10.0  # Default $10 budget

    def record_call(
        self,
        service: str,
        operation: str,
        cost_usd: float,
        tokens_used: int | None = None,
        **metadata: Any,
    ) -> None:
        """Record an API call with its cost.

        Args:
            service: Name of the service (e.g., 'openai', 'anthropic')
            operation: Type of operation (e.g., 'completion', 'tts')
            cost_usd: Cost of the call in USD
            tokens_used: Number of tokens used (if applicable)
            **metadata: Additional metadata about the call
        """
        call = APICall(
            service=service,
            operation=operation,
            timestamp=datetime.now(),
            cost_usd=cost_usd,
            tokens_used=tokens_used,
            metadata=metadata,
        )
        self.calls.append(call)

    def get_total_cost(self) -> float:
        """Get total cost of all recorded calls.

        Returns:
            Total cost in USD
        """
        return sum(call.cost_usd for call in self.calls)

    def get_cost_by_service(self, service: str) -> float:
        """Get total cost for a specific service.

        Args:
            service: Name of the service

        Returns:
            Total cost for that service in USD
        """
        return sum(call.cost_usd for call in self.calls if call.service == service)

    def check_budget(self) -> tuple[bool, float]:
        """Check if the budget limit has been exceeded.

        Returns:
            Tuple of (within_budget, remaining_budget)
        """
        total = self.get_total_cost()
        remaining = self._budget_limit - total
        return remaining >= 0, remaining

    def set_budget_limit(self, limit_usd: float) -> None:
        """Set the budget limit for testing.

        Args:
            limit_usd: Budget limit in USD
        """
        self._budget_limit = limit_usd

    def get_summary(self) -> dict[str, Any]:
        """Get a summary of all tracked costs.

        Returns:
            Dictionary with cost breakdown by service
        """
        services = set(call.service for call in self.calls)
        summary = {
            "total_cost_usd": self.get_total_cost(),
            "total_calls": len(self.calls),
            "by_service": {},
            "budget_limit_usd": self._budget_limit,
        }

        for service in services:
            service_calls = [c for c in self.calls if c.service == service]
            summary["by_service"][service] = {
                "cost_usd": self.get_cost_by_service(service),
                "call_count": len(service_calls),
            }

        within_budget, remaining = self.check_budget()
        summary["within_budget"] = within_budget
        summary["remaining_budget_usd"] = remaining

        return summary

    def print_summary(self) -> None:
        """Print a formatted summary of costs."""
        summary = self.get_summary()
        print("\n" + "=" * 60)
        print("💰 API COST SUMMARY")
        print("=" * 60)
        print(f"Total Cost: ${summary['total_cost_usd']:.4f}")
        print(f"Total Calls: {summary['total_calls']}")
        print(f"Budget Limit: ${summary['budget_limit_usd']:.2f}")
        print(f"Remaining Budget: ${summary['remaining_budget_usd']:.2f}")
        status = "✓ Within Budget" if summary["within_budget"] else "⚠ Over Budget"
        print(f"Status: {status}")
        print("\nBreakdown by Service:")
        for service, data in summary["by_service"].items():
            cost = data["cost_usd"]
            count = data["call_count"]
            print(f"  {service}: ${cost:.4f} ({count} calls)")
        print("=" * 60 + "\n")
