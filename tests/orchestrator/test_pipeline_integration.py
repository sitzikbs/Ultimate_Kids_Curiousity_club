"""End-to-end integration tests for the WP6b reliability-enhanced pipeline.

Covers full pipeline flow with checkpoints, error injection at each stage,
resume from each stage, and cost accumulation.
"""

import pytest

from models.episode import Episode, PipelineStage
from orchestrator.error_handler import StageExecutionError

# ---------------------------------------------------------------------------
# Full pipeline: generate → approve → resume → COMPLETE
# ---------------------------------------------------------------------------


class TestFullPipelineIntegration:
    """End-to-end tests with all mock services."""

    @pytest.mark.asyncio
    async def test_full_pipeline_with_checkpoints(
        self,
        orchestrator,
        mock_episode_storage,
        approval_workflow,
    ):
        """Full pipeline run produces checkpoints at every stage."""
        # --- Pre-approval ---
        result = await orchestrator.generate_episode("olivers_workshop", "gravity")
        assert result.is_approval_required

        episode_id = result.episode.episode_id

        # Verify pre-approval checkpoints
        saved: Episode = mock_episode_storage.save_episode.call_args_list[-1][0][0]
        assert "ideation" in saved.checkpoints
        assert "outlining" in saved.checkpoints

        # --- Approve ---
        approval_workflow.submit_approval(
            show_id="olivers_workshop",
            episode_id=episode_id,
            approved=True,
            feedback="Looks great",
        )

        # --- Post-approval ---
        result = await orchestrator.resume_episode("olivers_workshop", episode_id)
        ep = result.episode

        assert ep.current_stage == PipelineStage.COMPLETE
        assert ep.audio_path is not None

        # All 6 stage checkpoints should exist
        expected_stages = [
            "ideation",
            "outlining",
            "segment_generation",
            "script_generation",
            "audio_synthesis",
            "audio_mixing",
        ]
        for stage in expected_stages:
            assert stage in ep.checkpoints, f"Missing checkpoint: {stage}"

    @pytest.mark.asyncio
    async def test_final_episode_has_all_outputs(
        self,
        orchestrator,
        mock_episode_storage,
        approval_workflow,
    ):
        """Completed episode has concept, outline, segments, scripts, audio."""
        result = await orchestrator.generate_episode("olivers_workshop", "volcanoes")
        assert result.is_approval_required

        episode_id = result.episode.episode_id

        approval_workflow.submit_approval(
            show_id="olivers_workshop",
            episode_id=episode_id,
            approved=True,
        )

        result = await orchestrator.resume_episode("olivers_workshop", episode_id)
        ep = result.episode

        assert ep.concept is not None
        assert ep.outline is not None
        assert len(ep.segments) > 0
        assert len(ep.scripts) > 0
        assert len(ep.audio_segment_paths) > 0
        assert ep.audio_path is not None
        assert ep.total_cost >= 0.0


# ---------------------------------------------------------------------------
# Error injection at each post-approval stage
# ---------------------------------------------------------------------------


class TestErrorInjectionPerStage:
    """Inject failures at each post-approval stage and verify error handling."""

    @pytest.mark.asyncio
    async def test_failure_at_segment_generation(
        self,
        orchestrator,
        mock_episode_storage,
        mock_segment_service,
        sample_concept,
        sample_outline,
    ):
        """Segment generation failure → FAILED with error context."""
        mock_segment_service.generate_segments.side_effect = RuntimeError("seg fail")

        episode = Episode(
            episode_id="ep_inj_seg",
            show_id="olivers_workshop",
            topic="rockets",
            title="Rockets",
            concept=sample_concept,
            outline=sample_outline,
            current_stage=PipelineStage.APPROVED,
            approval_status="approved",
        )
        mock_episode_storage.save_episode(episode)

        with pytest.raises(StageExecutionError, match="seg fail"):
            await orchestrator.resume_episode("olivers_workshop", "ep_inj_seg")

        saved: Episode = mock_episode_storage.save_episode.call_args_list[-1][0][0]
        assert saved.current_stage == PipelineStage.FAILED
        assert saved.last_error is not None
        assert "seg fail" in saved.last_error["error"]

    @pytest.mark.asyncio
    async def test_failure_at_script_generation(
        self,
        orchestrator,
        mock_episode_storage,
        mock_script_service,
        sample_concept,
        sample_outline,
    ):
        """Script generation failure → FAILED with error context."""
        mock_script_service.generate_scripts.side_effect = RuntimeError("script fail")

        episode = Episode(
            episode_id="ep_inj_scr",
            show_id="olivers_workshop",
            topic="rockets",
            title="Rockets",
            concept=sample_concept,
            outline=sample_outline,
            current_stage=PipelineStage.APPROVED,
            approval_status="approved",
        )
        mock_episode_storage.save_episode(episode)

        with pytest.raises(StageExecutionError, match="script fail"):
            await orchestrator.resume_episode("olivers_workshop", "ep_inj_scr")

        saved: Episode = mock_episode_storage.save_episode.call_args_list[-1][0][0]
        assert saved.current_stage == PipelineStage.FAILED
        assert saved.last_error["stage"] == "script_generation"

    @pytest.mark.asyncio
    async def test_failure_at_audio_synthesis(
        self,
        orchestrator,
        mock_episode_storage,
        mock_synthesis_service,
        sample_concept,
        sample_outline,
    ):
        """Audio synthesis failure → FAILED with error context."""
        mock_synthesis_service.synthesize_segment.side_effect = RuntimeError("tts down")

        episode = Episode(
            episode_id="ep_inj_tts",
            show_id="olivers_workshop",
            topic="rockets",
            title="Rockets",
            concept=sample_concept,
            outline=sample_outline,
            current_stage=PipelineStage.APPROVED,
            approval_status="approved",
        )
        mock_episode_storage.save_episode(episode)

        with pytest.raises(StageExecutionError, match="tts down"):
            await orchestrator.resume_episode("olivers_workshop", "ep_inj_tts")

        saved: Episode = mock_episode_storage.save_episode.call_args_list[-1][0][0]
        assert saved.current_stage == PipelineStage.FAILED
        assert saved.last_error["stage"] == "audio_synthesis"

    @pytest.mark.asyncio
    async def test_failure_at_audio_mixing(
        self,
        orchestrator,
        mock_episode_storage,
        mock_audio_mixer_service,
        sample_concept,
        sample_outline,
    ):
        """Audio mixing failure → FAILED with error context."""
        mock_audio_mixer_service.mix_segments.side_effect = RuntimeError("mixer crash")

        episode = Episode(
            episode_id="ep_inj_mix",
            show_id="olivers_workshop",
            topic="rockets",
            title="Rockets",
            concept=sample_concept,
            outline=sample_outline,
            current_stage=PipelineStage.APPROVED,
            approval_status="approved",
        )
        mock_episode_storage.save_episode(episode)

        with pytest.raises(StageExecutionError, match="mixer crash"):
            await orchestrator.resume_episode("olivers_workshop", "ep_inj_mix")

        saved: Episode = mock_episode_storage.save_episode.call_args_list[-1][0][0]
        assert saved.current_stage == PipelineStage.FAILED
        assert saved.last_error["stage"] == "audio_mixing"


# ---------------------------------------------------------------------------
# Resume from each stage
# ---------------------------------------------------------------------------


class TestResumeFromEachStage:
    """Test resuming the pipeline from various stages."""

    @pytest.mark.asyncio
    async def test_resume_from_segment_generation(
        self,
        orchestrator,
        mock_episode_storage,
        sample_concept,
        sample_outline,
    ):
        """Resume from SEGMENT_GENERATION → COMPLETE."""
        episode = Episode(
            episode_id="ep_res_seg",
            show_id="olivers_workshop",
            topic="rockets",
            title="Rockets",
            concept=sample_concept,
            outline=sample_outline,
            current_stage=PipelineStage.SEGMENT_GENERATION,
            approval_status="approved",
        )
        mock_episode_storage.save_episode(episode)

        result = await orchestrator.resume_episode("olivers_workshop", "ep_res_seg")
        assert result.episode.current_stage == PipelineStage.COMPLETE

    @pytest.mark.asyncio
    async def test_resume_from_script_generation(
        self,
        orchestrator,
        mock_episode_storage,
        sample_concept,
        sample_outline,
        sample_segments,
    ):
        """Resume from SCRIPT_GENERATION → COMPLETE."""
        episode = Episode(
            episode_id="ep_res_scr",
            show_id="olivers_workshop",
            topic="rockets",
            title="Rockets",
            concept=sample_concept,
            outline=sample_outline,
            segments=sample_segments,
            current_stage=PipelineStage.SCRIPT_GENERATION,
            approval_status="approved",
        )
        mock_episode_storage.save_episode(episode)

        result = await orchestrator.resume_episode("olivers_workshop", "ep_res_scr")
        assert result.episode.current_stage == PipelineStage.COMPLETE

    @pytest.mark.asyncio
    async def test_resume_from_audio_synthesis(
        self,
        orchestrator,
        mock_episode_storage,
        sample_concept,
        sample_outline,
        sample_segments,
        sample_scripts,
    ):
        """Resume from AUDIO_SYNTHESIS → COMPLETE."""
        episode = Episode(
            episode_id="ep_res_tts",
            show_id="olivers_workshop",
            topic="rockets",
            title="Rockets",
            concept=sample_concept,
            outline=sample_outline,
            segments=sample_segments,
            scripts=sample_scripts,
            current_stage=PipelineStage.AUDIO_SYNTHESIS,
            approval_status="approved",
        )
        mock_episode_storage.save_episode(episode)

        result = await orchestrator.resume_episode("olivers_workshop", "ep_res_tts")
        assert result.episode.current_stage == PipelineStage.COMPLETE
        assert len(result.episode.audio_segment_paths) > 0

    @pytest.mark.asyncio
    async def test_resume_from_audio_mixing(
        self,
        orchestrator,
        mock_episode_storage,
        sample_concept,
        sample_outline,
        sample_segments,
        sample_scripts,
        tmp_path,
    ):
        """Resume from AUDIO_MIXING → COMPLETE."""
        # Need audio segment paths from the synthesis
        audio_paths = [str(tmp_path / f"seg_{i}.mp3") for i in range(4)]
        for p in audio_paths:
            from pathlib import Path

            Path(p).write_bytes(b"\x00" * 100)

        episode = Episode(
            episode_id="ep_res_mix",
            show_id="olivers_workshop",
            topic="rockets",
            title="Rockets",
            concept=sample_concept,
            outline=sample_outline,
            segments=sample_segments,
            scripts=sample_scripts,
            audio_segment_paths=audio_paths,
            current_stage=PipelineStage.AUDIO_MIXING,
            approval_status="approved",
        )
        mock_episode_storage.save_episode(episode)

        result = await orchestrator.resume_episode("olivers_workshop", "ep_res_mix")
        assert result.episode.current_stage == PipelineStage.COMPLETE
        assert result.episode.audio_path is not None


# ---------------------------------------------------------------------------
# Cost accumulation across the full pipeline
# ---------------------------------------------------------------------------


class TestCostAccumulation:
    """Verify cost tracking through full pipeline."""

    @pytest.mark.asyncio
    async def test_cost_accumulates_through_full_pipeline(
        self,
        orchestrator,
        mock_episode_storage,
        sample_concept,
        sample_outline,
    ):
        """total_cost is non-negative and equals sum of checkpoint costs."""
        episode = Episode(
            episode_id="ep_cost_full",
            show_id="olivers_workshop",
            topic="rockets",
            title="Rockets",
            concept=sample_concept,
            outline=sample_outline,
            current_stage=PipelineStage.APPROVED,
            approval_status="approved",
        )
        mock_episode_storage.save_episode(episode)

        result = await orchestrator.resume_episode("olivers_workshop", "ep_cost_full")
        ep = result.episode

        expected_total = sum(cp.get("cost", 0.0) for cp in ep.checkpoints.values())
        assert ep.total_cost == pytest.approx(expected_total)
        assert ep.total_cost >= 0.0


# ---------------------------------------------------------------------------
# Placeholder for real API test (gated)
# ---------------------------------------------------------------------------


@pytest.mark.real_api
class TestRealAPIPipeline:
    """Real API tests — gated behind the real_api marker.

    These tests require real API keys and cost real money ($5-10 budget).
    Run with: pytest -m real_api
    """

    @pytest.mark.skip(reason="Requires real API keys and budget — run manually")
    @pytest.mark.asyncio
    async def test_full_episode_generation_real_api(self):
        """Full episode generation with real APIs (budgeted at $5-10)."""
        # This would require real service instances, real API keys, etc.
        # Placeholder for future implementation.
        pass
