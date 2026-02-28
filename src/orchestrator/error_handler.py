"""Error handling and retry utilities for the pipeline orchestrator.

Provides a circuit breaker for repeated API failures and structured error
context storage on the Episode model.
"""

import logging
import time
from datetime import UTC, datetime

from models.episode import PipelineStage
from utils.errors import PodcastError

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Custom exceptions
# ---------------------------------------------------------------------------


class PipelineError(PodcastError):
    """Base error for pipeline-level failures."""

    pass


class StageExecutionError(PipelineError):
    """A pipeline stage failed after all retry attempts."""

    pass


class CircuitBreakerOpenError(PipelineError):
    """Service circuit breaker is open — calls are being short-circuited."""

    pass


# ---------------------------------------------------------------------------
# Circuit Breaker
# ---------------------------------------------------------------------------


class CircuitBreaker:
    """Circuit breaker for protecting against repeated API failures.

    Tracks consecutive failures per service and opens the circuit after a
    configurable threshold, preventing further calls until a recovery window
    has passed.

    Note:
        This implementation is **not** thread-safe. If multiple episodes are
        generated concurrently, wrap calls with an external lock or switch
        to ``threading.Lock``-guarded state.

    Attributes:
        failure_threshold: Number of consecutive failures before opening.
        recovery_timeout: Seconds to wait before allowing a test request.
    """

    def __init__(
        self,
        failure_threshold: int = 5,
        recovery_timeout: float = 60.0,
    ) -> None:
        """Initialize circuit breaker.

        Args:
            failure_threshold: Consecutive failures before circuit opens.
            recovery_timeout: Seconds before half-open state allows a probe.
        """
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout

        # Per-service state
        self._failures: dict[str, int] = {}
        self._last_failure_time: dict[str, float] = {}
        self._state: dict[str, str] = {}  # "closed", "open", "half-open"

    def record_success(self, service: str) -> None:
        """Record a successful call — resets the failure counter.

        Args:
            service: Logical service name (e.g. "llm", "tts", "audio").
        """
        self._failures[service] = 0
        self._state[service] = "closed"

    def record_failure(self, service: str) -> None:
        """Record a failed call — may trip the breaker.

        Args:
            service: Logical service name.
        """
        self._failures[service] = self._failures.get(service, 0) + 1
        self._last_failure_time[service] = time.monotonic()

        if self._failures[service] >= self.failure_threshold:
            self._state[service] = "open"
            logger.error(
                "Circuit breaker OPEN for service '%s' after %d consecutive failures",
                service,
                self._failures[service],
            )

    def is_open(self, service: str) -> bool:
        """Check if the circuit is open (blocking calls).

        Args:
            service: Logical service name.

        Returns:
            True if calls should be blocked.
        """
        state = self._state.get(service, "closed")

        if state == "closed":
            return False

        if state == "open":
            # Check if recovery window has elapsed → half-open
            elapsed = time.monotonic() - self._last_failure_time.get(service, 0.0)
            if elapsed >= self.recovery_timeout:
                self._state[service] = "half-open"
                logger.info(
                    "Circuit breaker HALF-OPEN for service '%s' — allowing probe",
                    service,
                )
                return False
            return True

        # half-open — allow single probe
        return False

    def check(self, service: str) -> None:
        """Raise if the circuit is open.

        Args:
            service: Logical service name.

        Raises:
            CircuitBreakerOpenError: If the circuit is open.
        """
        if self.is_open(service):
            raise CircuitBreakerOpenError(
                f"Circuit breaker open for service '{service}' — "
                f"too many consecutive failures "
                f"({self._failures.get(service, 0)}/{self.failure_threshold})",
                service=service,
            )

    def get_state(self, service: str) -> str:
        """Return the current circuit state for a service.

        Args:
            service: Logical service name.

        Returns:
            One of "closed", "open", "half-open".
        """
        return self._state.get(service, "closed")

    def reset(self, service: str | None = None) -> None:
        """Reset circuit breaker state.

        Args:
            service: Service to reset.  If None, resets all services.
        """
        if service is None:
            self._failures.clear()
            self._last_failure_time.clear()
            self._state.clear()
        else:
            self._failures.pop(service, None)
            self._last_failure_time.pop(service, None)
            self._state.pop(service, None)


# ---------------------------------------------------------------------------
# Error context helpers
# ---------------------------------------------------------------------------

# Mapping from PipelineStage to the logical service name for the circuit
# breaker.  Pre-approval LLM stages and post-approval LLM stages share the
# "llm" service; TTS and audio mixing have their own.
STAGE_SERVICE_MAP: dict[PipelineStage, str] = {
    PipelineStage.IDEATION: "llm",
    PipelineStage.OUTLINING: "llm",
    PipelineStage.SEGMENT_GENERATION: "llm",
    PipelineStage.SCRIPT_GENERATION: "llm",
    PipelineStage.AUDIO_SYNTHESIS: "tts",
    PipelineStage.AUDIO_MIXING: "audio",
}

# Ordered list of stage names for checkpoint management
STAGE_ORDER: list[str] = [
    "ideation",
    "outlining",
    "segment_generation",
    "script_generation",
    "audio_synthesis",
    "audio_mixing",
]

# Map from stage string name to PipelineStage enum
STAGE_NAME_TO_ENUM: dict[str, PipelineStage] = {
    "ideation": PipelineStage.IDEATION,
    "outlining": PipelineStage.OUTLINING,
    "segment_generation": PipelineStage.SEGMENT_GENERATION,
    "script_generation": PipelineStage.SCRIPT_GENERATION,
    "audio_synthesis": PipelineStage.AUDIO_SYNTHESIS,
    "audio_mixing": PipelineStage.AUDIO_MIXING,
}


def build_error_context(
    stage_name: str,
    error: Exception,
) -> dict[str, str]:
    """Build a structured error context dict for the Episode.last_error field.

    Args:
        stage_name: Human-readable stage name (e.g. "ideation").
        error: The exception that caused the failure.

    Returns:
        Dict with stage, timestamp, error, error_type keys.
    """
    return {
        "stage": stage_name,
        "timestamp": datetime.now(UTC).isoformat(),
        "error": str(error),
        "error_type": type(error).__name__,
    }
