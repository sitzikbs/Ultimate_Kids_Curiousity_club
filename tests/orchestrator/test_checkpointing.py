"""Tests for WP6b checkpointing: save/restore, cost tracking, validation."""

import pytest

from models.episode import Episode, PipelineStage

# ---------------------------------------------------------------------------
# Checkpoint save after each stage
# ---------------------------------------------------------------------------


class TestCheckpointSaving:
    """Verify that a checkpoint dict entry is written after every stage."""

    @pytest.mark.asyncio
    async def test_checkpoint_saved_after_ideation(
        self,
        orchestrator,
        mock_episode_storage,
    ):
        """Ideation checkpoint records concept_length."""
        result = await orchestrator.generate_episode("olivers_workshop", "rockets")
        assert result.is_approval_required

        saved: Episode = mock_episode_storage.save_episode.call_args_list[-1][0][0]
        assert "ideation" in saved.checkpoints
        cp = saved.checkpoints["ideation"]
        assert "completed_at" in cp
        assert "output" in cp
        assert "concept_length" in cp["output"]

    @pytest.mark.asyncio
    async def test_checkpoint_saved_after_outlining(
        self,
        orchestrator,
        mock_episode_storage,
    ):
        """Outlining checkpoint records beat count."""
        result = await orchestrator.generate_episode("olivers_workshop", "rockets")
        assert result.is_approval_required

        saved: Episode = mock_episode_storage.save_episode.call_args_list[-1][0][0]
        assert "outlining" in saved.checkpoints
        cp = saved.checkpoints["outlining"]
        assert "beats" in cp["output"]

    @pytest.mark.asyncio
    async def test_checkpoints_saved_after_all_post_approval_stages(
        self,
        orchestrator,
        mock_episode_storage,
        sample_concept,
        sample_outline,
    ):
        """Resume through all post-approval stages creates 4 checkpoints."""
        episode = Episode(
            episode_id="ep_chk_all",
            show_id="olivers_workshop",
            topic="rockets",
            title="Rockets",
            concept=sample_concept,
            outline=sample_outline,
            current_stage=PipelineStage.APPROVED,
            approval_status="approved",
        )
        mock_episode_storage.save_episode(episode)

        result = await orchestrator.resume_episode("olivers_workshop", "ep_chk_all")
        ep = result.episode

        assert ep.current_stage == PipelineStage.COMPLETE
        for stage_name in [
            "segment_generation",
            "script_generation",
            "audio_synthesis",
            "audio_mixing",
        ]:
            assert stage_name in ep.checkpoints, f"Missing checkpoint: {stage_name}"
            cp = ep.checkpoints[stage_name]
            assert "completed_at" in cp
            assert "output" in cp


# ---------------------------------------------------------------------------
# Cost tracking
# ---------------------------------------------------------------------------


class TestCostTracking:
    """Verify total_cost accumulation across checkpoints."""

    @pytest.mark.asyncio
    async def test_total_cost_is_sum_of_checkpoint_costs(
        self,
        orchestrator,
        mock_episode_storage,
    ):
        """total_cost equals the sum of individual checkpoint cost values."""
        result = await orchestrator.generate_episode("olivers_workshop", "rockets")
        assert result.is_approval_required

        saved: Episode = mock_episode_storage.save_episode.call_args_list[-1][0][0]
        expected_total = sum(cp.get("cost", 0.0) for cp in saved.checkpoints.values())
        assert saved.total_cost == expected_total

    @pytest.mark.asyncio
    async def test_total_cost_accumulates_across_stages(
        self,
        orchestrator,
        mock_episode_storage,
        sample_concept,
        sample_outline,
    ):
        """total_cost should be >= 0 after running all post-approval stages."""
        episode = Episode(
            episode_id="ep_cost",
            show_id="olivers_workshop",
            topic="rockets",
            title="Rockets",
            concept=sample_concept,
            outline=sample_outline,
            current_stage=PipelineStage.APPROVED,
            approval_status="approved",
        )
        mock_episode_storage.save_episode(episode)

        result = await orchestrator.resume_episode("olivers_workshop", "ep_cost")
        ep = result.episode

        assert ep.total_cost >= 0.0
        # Every checkpoint should have a cost key
        for stage_name, cp in ep.checkpoints.items():
            assert "cost" in cp, f"Checkpoint {stage_name} missing cost key"


# ---------------------------------------------------------------------------
# Checkpoint validation (reset_to_stage)
# ---------------------------------------------------------------------------


class TestCheckpointResetToStage:
    """Verify reset_to_stage clears subsequent checkpoints."""

    @pytest.mark.asyncio
    async def test_reset_clears_subsequent_checkpoints(
        self,
        orchestrator,
        mock_episode_storage,
        sample_concept,
        sample_outline,
    ):
        """Resetting to segment_generation should clear script+audio checkpoints."""
        episode = Episode(
            episode_id="ep_reset",
            show_id="olivers_workshop",
            topic="rockets",
            title="Rockets",
            concept=sample_concept,
            outline=sample_outline,
            current_stage=PipelineStage.APPROVED,
            approval_status="approved",
        )
        mock_episode_storage.save_episode(episode)

        completed = await orchestrator.resume_episode("olivers_workshop", "ep_reset")
        assert completed.episode.current_stage == PipelineStage.COMPLETE

        # Now reset to segment_generation
        mock_episode_storage.save_episode(completed.episode)
        reset_ep = await orchestrator.reset_to_stage(
            "olivers_workshop", "ep_reset", "segment_generation"
        )

        assert reset_ep.current_stage == PipelineStage.SEGMENT_GENERATION
        # Stages after segment_generation should be cleared
        for later_stage in ["script_generation", "audio_synthesis", "audio_mixing"]:
            assert later_stage not in reset_ep.checkpoints

    @pytest.mark.asyncio
    async def test_reset_recalculates_total_cost(
        self,
        orchestrator,
        mock_episode_storage,
    ):
        """After reset, total_cost should only include remaining checkpoints."""
        episode = Episode(
            episode_id="ep_cost_reset",
            show_id="olivers_workshop",
            topic="rockets",
            title="Rockets",
            current_stage=PipelineStage.COMPLETE,
            checkpoints={
                "ideation": {"completed_at": "2025-01-01", "output": {}, "cost": 0.02},
                "outlining": {"completed_at": "2025-01-01", "output": {}, "cost": 0.03},
                "segment_generation": {
                    "completed_at": "2025-01-01",
                    "output": {},
                    "cost": 0.05,
                },
                "script_generation": {
                    "completed_at": "2025-01-01",
                    "output": {},
                    "cost": 0.08,
                },
            },
            total_cost=0.18,
        )
        mock_episode_storage.save_episode(episode)

        reset_ep = await orchestrator.reset_to_stage(
            "olivers_workshop", "ep_cost_reset", "outlining"
        )

        # Only ideation + outlining should remain
        assert "segment_generation" not in reset_ep.checkpoints
        assert "script_generation" not in reset_ep.checkpoints
        assert reset_ep.total_cost == pytest.approx(0.05)  # 0.02 + 0.03

    @pytest.mark.asyncio
    async def test_reset_clears_error_state(
        self,
        orchestrator,
        mock_episode_storage,
    ):
        """After reset, last_error and retry_count should be cleared."""
        episode = Episode(
            episode_id="ep_err_reset",
            show_id="olivers_workshop",
            topic="rockets",
            title="Rockets",
            current_stage=PipelineStage.FAILED,
            last_error={"stage": "audio_synthesis", "error": "timeout"},
            retry_count=3,
            checkpoints={
                "ideation": {"completed_at": "2025-01-01", "output": {}, "cost": 0.0},
            },
        )
        mock_episode_storage.save_episode(episode)

        # reset_to_stage needs a valid target_stage — FAILED can't be directly
        # set via reset, so we'll directly modify then reset
        # First fix the stage so storage load works
        episode.current_stage = PipelineStage.AUDIO_SYNTHESIS
        mock_episode_storage.save_episode(episode)

        reset_ep = await orchestrator.reset_to_stage(
            "olivers_workshop", "ep_err_reset", "ideation"
        )

        assert reset_ep.last_error is None
        assert reset_ep.retry_count == 0

    @pytest.mark.asyncio
    async def test_reset_to_invalid_stage_raises(
        self, orchestrator, mock_episode_storage
    ):
        """reset_to_stage raises ValueError for unknown stage names."""
        episode = Episode(
            episode_id="ep_bad_reset",
            show_id="olivers_workshop",
            topic="rockets",
            title="Rockets",
            current_stage=PipelineStage.COMPLETE,
        )
        mock_episode_storage.save_episode(episode)

        with pytest.raises(ValueError, match="Invalid stage name"):
            await orchestrator.reset_to_stage(
                "olivers_workshop", "ep_bad_reset", "nonexistent_stage"
            )
