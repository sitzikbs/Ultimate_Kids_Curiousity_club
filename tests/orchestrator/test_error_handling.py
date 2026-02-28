"""Tests for WP6b error handling: retry, circuit breaker, error context."""

import time

import pytest

from models.episode import Episode, PipelineStage
from orchestrator.error_handler import (
    STAGE_SERVICE_MAP,
    CircuitBreaker,
    CircuitBreakerOpenError,
    StageExecutionError,
    build_error_context,
)
from utils.errors import APIError

# ---------------------------------------------------------------------------
# CircuitBreaker unit tests
# ---------------------------------------------------------------------------


class TestCircuitBreaker:
    """Tests for the CircuitBreaker class."""

    def test_starts_closed(self):
        """New circuit breaker is in closed state for unknown services."""
        cb = CircuitBreaker(failure_threshold=3)
        assert cb.get_state("llm") == "closed"
        assert not cb.is_open("llm")

    def test_opens_after_threshold_failures(self):
        """Circuit opens after failure_threshold consecutive failures."""
        cb = CircuitBreaker(failure_threshold=3, recovery_timeout=60.0)

        cb.record_failure("llm")
        assert cb.get_state("llm") == "closed"

        cb.record_failure("llm")
        assert cb.get_state("llm") == "closed"

        cb.record_failure("llm")
        assert cb.get_state("llm") == "open"
        assert cb.is_open("llm")

    def test_check_raises_when_open(self):
        """check() raises CircuitBreakerOpenError when open."""
        cb = CircuitBreaker(failure_threshold=2)

        cb.record_failure("tts")
        cb.record_failure("tts")

        with pytest.raises(CircuitBreakerOpenError, match="tts"):
            cb.check("tts")

    def test_success_resets_failure_count(self):
        """A success resets the counter and closes the circuit."""
        cb = CircuitBreaker(failure_threshold=3)

        cb.record_failure("llm")
        cb.record_failure("llm")
        cb.record_success("llm")

        assert cb.get_state("llm") == "closed"
        assert not cb.is_open("llm")

    def test_recovery_timeout_transitions_to_half_open(self):
        """After recovery_timeout, circuit moves to half-open."""
        cb = CircuitBreaker(failure_threshold=2, recovery_timeout=0.05)

        cb.record_failure("llm")
        cb.record_failure("llm")
        assert cb.is_open("llm")

        # Wait for recovery
        time.sleep(0.06)
        assert not cb.is_open("llm")
        assert cb.get_state("llm") == "half-open"

    def test_success_after_half_open_closes(self):
        """A success in half-open state closes the circuit."""
        cb = CircuitBreaker(failure_threshold=2, recovery_timeout=0.05)

        cb.record_failure("llm")
        cb.record_failure("llm")
        time.sleep(0.06)
        # is_open() triggers the half-open transition when recovery_timeout elapses
        assert not cb.is_open("llm")
        assert cb.get_state("llm") == "half-open"

        cb.record_success("llm")
        assert cb.get_state("llm") == "closed"

    def test_per_service_isolation(self):
        """Failures in one service don't affect another."""
        cb = CircuitBreaker(failure_threshold=2)

        cb.record_failure("llm")
        cb.record_failure("llm")
        assert cb.is_open("llm")
        assert not cb.is_open("tts")

    def test_reset_single_service(self):
        """reset(service) clears only that service."""
        cb = CircuitBreaker(failure_threshold=2)

        cb.record_failure("llm")
        cb.record_failure("llm")
        cb.record_failure("tts")

        cb.reset("llm")
        assert cb.get_state("llm") == "closed"
        # tts should still have 1 failure
        assert cb.get_state("tts") == "closed"

    def test_reset_all(self):
        """reset(None) clears all services."""
        cb = CircuitBreaker(failure_threshold=2)

        cb.record_failure("llm")
        cb.record_failure("llm")
        cb.record_failure("tts")
        cb.record_failure("tts")

        cb.reset()
        assert cb.get_state("llm") == "closed"
        assert cb.get_state("tts") == "closed"


# ---------------------------------------------------------------------------
# build_error_context
# ---------------------------------------------------------------------------


class TestBuildErrorContext:
    """Tests for the build_error_context helper."""

    def test_returns_required_keys(self):
        """Error context has stage, timestamp, error, error_type."""
        exc = RuntimeError("something went wrong")
        ctx = build_error_context("audio_synthesis", exc)

        assert ctx["stage"] == "audio_synthesis"
        assert "timestamp" in ctx
        assert ctx["error"] == "something went wrong"
        assert ctx["error_type"] == "RuntimeError"

    def test_api_error_type(self):
        """APIError is captured with correct error_type."""
        exc = APIError("rate limited")
        ctx = build_error_context("ideation", exc)
        assert ctx["error_type"] == "APIError"


# ---------------------------------------------------------------------------
# _execute_stage_with_error_handling (via orchestrator)
# ---------------------------------------------------------------------------


class TestStageErrorHandling:
    """Tests for error handling in resume_episode flows."""

    @pytest.mark.asyncio
    async def test_stage_failure_stores_last_error(
        self,
        orchestrator,
        mock_episode_storage,
        mock_segment_service,
        sample_concept,
        sample_outline,
    ):
        """On failure, episode.last_error is populated."""
        mock_segment_service.generate_segments.side_effect = RuntimeError("boom")

        episode = Episode(
            episode_id="ep_err",
            show_id="olivers_workshop",
            topic="rockets",
            title="Rockets",
            concept=sample_concept,
            outline=sample_outline,
            current_stage=PipelineStage.APPROVED,
            approval_status="approved",
        )
        mock_episode_storage.save_episode(episode)

        with pytest.raises(StageExecutionError):
            await orchestrator.resume_episode("olivers_workshop", "ep_err")

        saved: Episode = mock_episode_storage.save_episode.call_args_list[-1][0][0]
        assert saved.current_stage == PipelineStage.FAILED
        assert saved.last_error is not None
        assert saved.last_error["stage"] == "segment_generation"
        assert saved.last_error["error_type"] == "RuntimeError"
        assert "boom" in saved.last_error["error"]

    @pytest.mark.asyncio
    async def test_stage_failure_increments_retry_count(
        self,
        orchestrator,
        mock_episode_storage,
        mock_segment_service,
        sample_concept,
        sample_outline,
    ):
        """retry_count should increment on each failure."""
        mock_segment_service.generate_segments.side_effect = RuntimeError("fail")

        episode = Episode(
            episode_id="ep_retry_cnt",
            show_id="olivers_workshop",
            topic="rockets",
            title="Rockets",
            concept=sample_concept,
            outline=sample_outline,
            current_stage=PipelineStage.APPROVED,
            approval_status="approved",
            retry_count=0,
        )
        mock_episode_storage.save_episode(episode)

        with pytest.raises(StageExecutionError):
            await orchestrator.resume_episode("olivers_workshop", "ep_retry_cnt")

        saved: Episode = mock_episode_storage.save_episode.call_args_list[-1][0][0]
        assert saved.retry_count >= 1

    @pytest.mark.asyncio
    async def test_circuit_breaker_blocks_stage_execution(
        self,
        orchestrator,
        mock_episode_storage,
        sample_concept,
        sample_outline,
    ):
        """If circuit breaker is open, stage doesn't even execute."""
        # Force the breaker open for llm
        orchestrator.circuit_breaker = CircuitBreaker(failure_threshold=1)
        orchestrator.circuit_breaker.record_failure("llm")

        episode = Episode(
            episode_id="ep_cb",
            show_id="olivers_workshop",
            topic="rockets",
            title="Rockets",
            concept=sample_concept,
            outline=sample_outline,
            current_stage=PipelineStage.APPROVED,
            approval_status="approved",
        )
        mock_episode_storage.save_episode(episode)

        with pytest.raises(CircuitBreakerOpenError, match="llm"):
            await orchestrator.resume_episode("olivers_workshop", "ep_cb")


# ---------------------------------------------------------------------------
# STAGE_SERVICE_MAP
# ---------------------------------------------------------------------------


class TestStageServiceMap:
    """Verify stage → service mapping for circuit breaker."""

    def test_llm_stages_map_to_llm(self):
        """LLM stages should map to 'llm' service."""
        for stage in [
            PipelineStage.IDEATION,
            PipelineStage.OUTLINING,
            PipelineStage.SEGMENT_GENERATION,
            PipelineStage.SCRIPT_GENERATION,
        ]:
            assert STAGE_SERVICE_MAP[stage] == "llm"

    def test_tts_stage_maps_to_tts(self):
        """AUDIO_SYNTHESIS maps to 'tts'."""
        assert STAGE_SERVICE_MAP[PipelineStage.AUDIO_SYNTHESIS] == "tts"

    def test_audio_stage_maps_to_audio(self):
        """AUDIO_MIXING maps to 'audio'."""
        assert STAGE_SERVICE_MAP[PipelineStage.AUDIO_MIXING] == "audio"
