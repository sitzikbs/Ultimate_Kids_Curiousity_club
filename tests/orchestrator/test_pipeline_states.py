"""Tests for pipeline state machine transitions and stage execution."""

import pytest

from models.episode import Episode, PipelineStage
from orchestrator.error_handler import StageExecutionError
from orchestrator.events import EventType
from orchestrator.pipeline import PipelineOrchestrator
from orchestrator.transitions import VALID_TRANSITIONS

# ---------------------------------------------------------------------------
# State transition validation
# ---------------------------------------------------------------------------


class TestCanTransitionTo:
    """Tests for PipelineOrchestrator.can_transition_to()."""

    @pytest.mark.parametrize(
        "current,target",
        [
            (PipelineStage.PENDING, PipelineStage.IDEATION),
            (PipelineStage.IDEATION, PipelineStage.OUTLINING),
            (PipelineStage.OUTLINING, PipelineStage.AWAITING_APPROVAL),
            (PipelineStage.AWAITING_APPROVAL, PipelineStage.APPROVED),
            (PipelineStage.AWAITING_APPROVAL, PipelineStage.REJECTED),
            (PipelineStage.APPROVED, PipelineStage.SEGMENT_GENERATION),
            (PipelineStage.SEGMENT_GENERATION, PipelineStage.SCRIPT_GENERATION),
            (PipelineStage.SCRIPT_GENERATION, PipelineStage.AUDIO_SYNTHESIS),
            (PipelineStage.AUDIO_SYNTHESIS, PipelineStage.AUDIO_MIXING),
            (PipelineStage.AUDIO_MIXING, PipelineStage.COMPLETE),
            (PipelineStage.REJECTED, PipelineStage.IDEATION),
        ],
    )
    def test_valid_transitions(self, current: PipelineStage, target: PipelineStage):
        """All forward transitions in the happy path are valid."""
        assert PipelineOrchestrator.can_transition_to(current, target) is True

    @pytest.mark.parametrize(
        "current,target",
        [
            # Cannot skip stages
            (PipelineStage.PENDING, PipelineStage.OUTLINING),
            (PipelineStage.IDEATION, PipelineStage.SEGMENT_GENERATION),
            (PipelineStage.OUTLINING, PipelineStage.SCRIPT_GENERATION),
            # Cannot go backward (except REJECTED→IDEATION)
            (PipelineStage.COMPLETE, PipelineStage.IDEATION),
            (PipelineStage.AUDIO_MIXING, PipelineStage.SEGMENT_GENERATION),
            # Cannot bypass approval
            (PipelineStage.OUTLINING, PipelineStage.SEGMENT_GENERATION),
            (PipelineStage.AWAITING_APPROVAL, PipelineStage.SEGMENT_GENERATION),
        ],
    )
    def test_invalid_transitions(self, current: PipelineStage, target: PipelineStage):
        """Invalid transitions are rejected."""
        assert PipelineOrchestrator.can_transition_to(current, target) is False

    def test_failed_is_reachable_from_any_active_stage(self):
        """Any active stage can transition to FAILED."""
        active_stages = [
            PipelineStage.IDEATION,
            PipelineStage.OUTLINING,
            PipelineStage.AWAITING_APPROVAL,
            PipelineStage.APPROVED,
            PipelineStage.SEGMENT_GENERATION,
            PipelineStage.SCRIPT_GENERATION,
            PipelineStage.AUDIO_SYNTHESIS,
            PipelineStage.AUDIO_MIXING,
        ]
        for stage in active_stages:
            assert PipelineOrchestrator.can_transition_to(
                stage, PipelineStage.FAILED
            ), f"{stage} should be able to transition to FAILED"

    def test_complete_has_no_outgoing_transitions(self):
        """COMPLETE is a terminal state."""
        for target in PipelineStage:
            assert (
                PipelineOrchestrator.can_transition_to(PipelineStage.COMPLETE, target)
                is False
            )

    def test_all_stages_covered_in_transition_map(self):
        """Every PipelineStage appears in the transition map."""
        for stage in PipelineStage:
            assert stage in VALID_TRANSITIONS


# ---------------------------------------------------------------------------
# generate_episode() — pre-approval pipeline
# ---------------------------------------------------------------------------


class TestGenerateEpisode:
    """Tests for PipelineOrchestrator.generate_episode()."""

    @pytest.mark.asyncio
    async def test_raises_approval_required(self, orchestrator):
        """generate_episode() returns PipelineResult with APPROVAL_REQUIRED."""
        result = await orchestrator.generate_episode("olivers_workshop", "rockets")
        assert result.is_approval_required

    @pytest.mark.asyncio
    async def test_episode_saved_at_awaiting_approval(
        self, orchestrator, mock_episode_storage
    ):
        """Episode is persisted in AWAITING_APPROVAL stage."""
        result = await orchestrator.generate_episode("olivers_workshop", "rockets")
        assert result.is_approval_required

        # The last save should be at AWAITING_APPROVAL
        saved_calls = mock_episode_storage.save_episode.call_args_list
        last_saved: Episode = saved_calls[-1][0][0]
        assert last_saved.current_stage == PipelineStage.AWAITING_APPROVAL
        assert last_saved.approval_status == "pending"

    @pytest.mark.asyncio
    async def test_ideation_service_called(
        self, orchestrator, mock_ideation_service, sample_blueprint
    ):
        """IdeationService.generate_concept() is invoked with topic and blueprint."""
        result = await orchestrator.generate_episode("olivers_workshop", "rockets")
        assert result.is_approval_required

        mock_ideation_service.generate_concept.assert_awaited_once()
        call_kwargs = mock_ideation_service.generate_concept.call_args
        assert call_kwargs.kwargs["topic"] == "rockets"
        assert call_kwargs.kwargs["show_blueprint"] == sample_blueprint

    @pytest.mark.asyncio
    async def test_outline_service_called(
        self, orchestrator, mock_outline_service, sample_concept
    ):
        """OutlineService.generate_outline() is invoked with concept and blueprint."""
        result = await orchestrator.generate_episode("olivers_workshop", "rockets")
        assert result.is_approval_required

        mock_outline_service.generate_outline.assert_awaited_once()
        call_kwargs = mock_outline_service.generate_outline.call_args
        assert call_kwargs.kwargs["concept"] == sample_concept

    @pytest.mark.asyncio
    async def test_episode_has_concept_and_outline(
        self, orchestrator, mock_episode_storage
    ):
        """Episode stores both concept and outline after pre-approval stages."""
        result = await orchestrator.generate_episode("olivers_workshop", "rockets")
        assert result.is_approval_required

        saved: Episode = mock_episode_storage.save_episode.call_args_list[-1][0][0]
        assert saved.concept is not None
        assert saved.outline is not None

    @pytest.mark.asyncio
    async def test_auto_generated_title(self, orchestrator, mock_episode_storage):
        """Title is auto-generated when not explicitly provided."""
        await orchestrator.generate_episode("olivers_workshop", "rockets")

        saved: Episode = mock_episode_storage.save_episode.call_args_list[0][0][0]
        assert saved.title == "Rockets"

    @pytest.mark.asyncio
    async def test_explicit_title(self, orchestrator, mock_episode_storage):
        """Explicit title is used when provided."""
        await orchestrator.generate_episode(
            "olivers_workshop", "rockets", title="Blast Off!"
        )

        saved: Episode = mock_episode_storage.save_episode.call_args_list[0][0][0]
        assert saved.title == "Blast Off!"

    @pytest.mark.asyncio
    async def test_events_emitted(self, orchestrator, mock_event_callback):
        """Pipeline events are emitted during generation."""
        await orchestrator.generate_episode("olivers_workshop", "rockets")

        # Should have stage_started/completed for ideation and outlining,
        # plus approval_required
        assert mock_event_callback.await_count >= 3
        event_types = [
            call.args[0].event_type for call in mock_event_callback.call_args_list
        ]
        assert EventType.APPROVAL_REQUIRED in event_types


# ---------------------------------------------------------------------------
# resume_episode() — post-approval pipeline
# ---------------------------------------------------------------------------


class TestResumeEpisode:
    """Tests for PipelineOrchestrator.resume_episode()."""

    @pytest.mark.asyncio
    async def test_full_pipeline_to_complete(
        self,
        orchestrator,
        mock_episode_storage,
        sample_outline,
        sample_concept,
    ):
        """Resume from APPROVED runs through all remaining stages to COMPLETE."""
        # Pre-populate an approved episode in storage
        episode = Episode(
            episode_id="ep_test_001",
            show_id="olivers_workshop",
            topic="rockets",
            title="Rockets",
            concept=sample_concept,
            outline=sample_outline,
            current_stage=PipelineStage.APPROVED,
            approval_status="approved",
        )
        mock_episode_storage.save_episode(episode)

        result = await orchestrator.resume_episode("olivers_workshop", "ep_test_001")

        assert result.current_stage == PipelineStage.COMPLETE
        assert result.segments  # segments populated
        assert result.scripts  # scripts populated
        assert result.audio_path is not None

    @pytest.mark.asyncio
    async def test_segment_service_called_with_blueprint(
        self,
        orchestrator,
        mock_episode_storage,
        mock_segment_service,
        sample_outline,
        sample_concept,
        sample_blueprint,
    ):
        """SegmentGenerationService receives outline and blueprint."""
        episode = Episode(
            episode_id="ep_test_002",
            show_id="olivers_workshop",
            topic="rockets",
            title="Rockets",
            concept=sample_concept,
            outline=sample_outline,
            current_stage=PipelineStage.APPROVED,
            approval_status="approved",
        )
        mock_episode_storage.save_episode(episode)

        await orchestrator.resume_episode("olivers_workshop", "ep_test_002")

        mock_segment_service.generate_segments.assert_awaited_once()
        call_kwargs = mock_segment_service.generate_segments.call_args
        assert call_kwargs.kwargs["outline"] == sample_outline
        assert call_kwargs.kwargs["show_blueprint"] == sample_blueprint

    @pytest.mark.asyncio
    async def test_script_service_called(
        self,
        orchestrator,
        mock_episode_storage,
        mock_script_service,
        sample_outline,
        sample_concept,
    ):
        """ScriptGenerationService is called with generated segments."""
        episode = Episode(
            episode_id="ep_test_003",
            show_id="olivers_workshop",
            topic="rockets",
            title="Rockets",
            concept=sample_concept,
            outline=sample_outline,
            current_stage=PipelineStage.APPROVED,
            approval_status="approved",
        )
        mock_episode_storage.save_episode(episode)

        await orchestrator.resume_episode("olivers_workshop", "ep_test_003")

        mock_script_service.generate_scripts.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_synthesis_service_called_per_block(
        self,
        orchestrator,
        mock_episode_storage,
        mock_synthesis_service,
        sample_outline,
        sample_concept,
        sample_scripts,
    ):
        """AudioSynthesisService is called once per ScriptBlock."""
        episode = Episode(
            episode_id="ep_test_004",
            show_id="olivers_workshop",
            topic="rockets",
            title="Rockets",
            concept=sample_concept,
            outline=sample_outline,
            current_stage=PipelineStage.APPROVED,
            approval_status="approved",
        )
        mock_episode_storage.save_episode(episode)

        await orchestrator.resume_episode("olivers_workshop", "ep_test_004")

        total_blocks = sum(len(s.script_blocks) for s in sample_scripts)
        assert mock_synthesis_service.synthesize_segment.call_count == total_blocks

    @pytest.mark.asyncio
    async def test_audio_mixer_called(
        self,
        orchestrator,
        mock_episode_storage,
        mock_audio_mixer_service,
        sample_outline,
        sample_concept,
    ):
        """AudioMixer.mix_segments() is called with segment paths."""
        episode = Episode(
            episode_id="ep_test_005",
            show_id="olivers_workshop",
            topic="rockets",
            title="Rockets",
            concept=sample_concept,
            outline=sample_outline,
            current_stage=PipelineStage.APPROVED,
            approval_status="approved",
        )
        mock_episode_storage.save_episode(episode)

        await orchestrator.resume_episode("olivers_workshop", "ep_test_005")

        mock_audio_mixer_service.mix_segments.assert_called_once()

    @pytest.mark.asyncio
    async def test_concepts_updated_after_complete(
        self,
        orchestrator,
        mock_episode_storage,
        mock_show_manager,
        sample_outline,
        sample_concept,
    ):
        """ShowBlueprintManager.add_concept() is called after COMPLETE."""
        episode = Episode(
            episode_id="ep_test_006",
            show_id="olivers_workshop",
            topic="rockets",
            title="Rockets",
            concept=sample_concept,
            outline=sample_outline,
            current_stage=PipelineStage.APPROVED,
            approval_status="approved",
        )
        mock_episode_storage.save_episode(episode)

        await orchestrator.resume_episode("olivers_workshop", "ep_test_006")

        mock_show_manager.add_concept.assert_called_once_with(
            show_id="olivers_workshop",
            concept="rockets",
            episode_id="ep_test_006",
        )

    @pytest.mark.asyncio
    async def test_cannot_resume_from_pending(self, orchestrator, mock_episode_storage):
        """Cannot resume an episode that hasn't started."""
        episode = Episode(
            episode_id="ep_pending",
            show_id="olivers_workshop",
            topic="rockets",
            title="Rockets",
            current_stage=PipelineStage.PENDING,
        )
        mock_episode_storage.save_episode(episode)

        with pytest.raises(ValueError, match="not in a resumable stage"):
            await orchestrator.resume_episode("olivers_workshop", "ep_pending")

    @pytest.mark.asyncio
    async def test_cannot_resume_from_awaiting_approval(
        self, orchestrator, mock_episode_storage
    ):
        """Cannot resume until approval is submitted."""
        episode = Episode(
            episode_id="ep_awaiting",
            show_id="olivers_workshop",
            topic="rockets",
            title="Rockets",
            current_stage=PipelineStage.AWAITING_APPROVAL,
        )
        mock_episode_storage.save_episode(episode)

        with pytest.raises(ValueError, match="not in a resumable stage"):
            await orchestrator.resume_episode("olivers_workshop", "ep_awaiting")

    @pytest.mark.asyncio
    async def test_cannot_resume_completed_episode(
        self, orchestrator, mock_episode_storage
    ):
        """Cannot resume an already completed episode."""
        episode = Episode(
            episode_id="ep_done",
            show_id="olivers_workshop",
            topic="rockets",
            title="Rockets",
            current_stage=PipelineStage.COMPLETE,
        )
        mock_episode_storage.save_episode(episode)

        with pytest.raises(ValueError, match="not in a resumable stage"):
            await orchestrator.resume_episode("olivers_workshop", "ep_done")


# ---------------------------------------------------------------------------
# Internal transition validation
# ---------------------------------------------------------------------------


class TestTransitionValidation:
    """Test that the orchestrator enforces valid transitions internally."""

    @pytest.mark.asyncio
    async def test_transition_raises_on_invalid(self, orchestrator):
        """_transition() raises ValueError for invalid transitions."""
        episode = Episode(
            episode_id="ep_bad",
            show_id="test",
            topic="t",
            title="T",
            current_stage=PipelineStage.COMPLETE,
        )
        with pytest.raises(ValueError, match="Invalid transition"):
            orchestrator._transition(episode, PipelineStage.IDEATION)

    @pytest.mark.asyncio
    async def test_transition_updates_stage_and_timestamp(self, orchestrator):
        """_transition() updates current_stage and updated_at."""
        episode = Episode(
            episode_id="ep_tr",
            show_id="test",
            topic="t",
            title="T",
            current_stage=PipelineStage.PENDING,
        )
        original_time = episode.updated_at

        result = orchestrator._transition(episode, PipelineStage.IDEATION)

        assert result.current_stage == PipelineStage.IDEATION
        assert result.updated_at >= original_time


# ---------------------------------------------------------------------------
# End-to-end: generate → approve → resume → complete
# ---------------------------------------------------------------------------


class TestEndToEnd:
    """Full pipeline integration test with mock services."""

    @pytest.mark.asyncio
    async def test_full_pipeline(
        self,
        orchestrator,
        mock_episode_storage,
        approval_workflow,
        sample_concept,
        sample_outline,
    ):
        """Complete flow: generate → approve → resume → COMPLETE."""
        # 1. Generate — should pause at approval
        result = await orchestrator.generate_episode("olivers_workshop", "rockets")
        assert result.is_approval_required

        # Find the saved episode
        saved_episodes = mock_episode_storage._episodes
        assert len(saved_episodes) == 1
        ep_key = list(saved_episodes.keys())[0]
        show_id, episode_id = ep_key.split("/")

        # Verify it's at AWAITING_APPROVAL
        episode = mock_episode_storage.load_episode(show_id, episode_id)
        assert episode.current_stage == PipelineStage.AWAITING_APPROVAL

        # 2. Approve
        approved = approval_workflow.submit_approval(
            show_id=show_id,
            episode_id=episode_id,
            approved=True,
            feedback="Looks great!",
        )
        assert approved.current_stage == PipelineStage.APPROVED

        # 3. Resume — should run to COMPLETE
        result = await orchestrator.resume_episode(show_id, episode_id)
        assert result.current_stage == PipelineStage.COMPLETE
        assert result.audio_path is not None


# ---------------------------------------------------------------------------
# execute_single_stage — debug / selective re-run
# ---------------------------------------------------------------------------


class TestExecuteSingleStage:
    """Tests for PipelineOrchestrator.execute_single_stage()."""

    @pytest.mark.asyncio
    async def test_execute_ideation_only(
        self,
        orchestrator,
        mock_episode_storage,
        sample_concept,
    ):
        """execute_single_stage runs IDEATION without advancing further."""
        episode = Episode(
            episode_id="ep_single_idea",
            show_id="olivers_workshop",
            topic="magnets",
            title="Magnets",
            current_stage=PipelineStage.PENDING,
        )
        mock_episode_storage.save_episode(episode)

        result = await orchestrator.execute_single_stage(
            "olivers_workshop",
            "ep_single_idea",
            PipelineStage.IDEATION,
        )

        # Ideation runner stays at IDEATION; OUTLINING entry is that runner's job
        assert result.current_stage == PipelineStage.IDEATION
        assert result.concept is not None

    @pytest.mark.asyncio
    async def test_execute_single_stage_invalid_stage(
        self,
        orchestrator,
        mock_episode_storage,
    ):
        """execute_single_stage raises ValueError for non-executable stages."""
        episode = Episode(
            episode_id="ep_single_bad",
            show_id="olivers_workshop",
            topic="magnets",
            title="Magnets",
            current_stage=PipelineStage.AWAITING_APPROVAL,
        )
        mock_episode_storage.save_episode(episode)

        with pytest.raises(ValueError, match="No runner for stage"):
            await orchestrator.execute_single_stage(
                "olivers_workshop",
                "ep_single_bad",
                PipelineStage.AWAITING_APPROVAL,
            )

    @pytest.mark.asyncio
    async def test_execute_segment_generation_only(
        self,
        orchestrator,
        mock_episode_storage,
        sample_concept,
        sample_outline,
    ):
        """execute_single_stage runs SEGMENT_GENERATION independently."""
        episode = Episode(
            episode_id="ep_single_seg",
            show_id="olivers_workshop",
            topic="magnets",
            title="Magnets",
            concept=sample_concept,
            outline=sample_outline,
            current_stage=PipelineStage.APPROVED,
            approval_status="approved",
        )
        mock_episode_storage.save_episode(episode)

        result = await orchestrator.execute_single_stage(
            "olivers_workshop",
            "ep_single_seg",
            PipelineStage.SEGMENT_GENERATION,
        )

        # Segment generation transitions to SCRIPT_GENERATION
        assert result.current_stage == PipelineStage.SCRIPT_GENERATION
        assert result.segments is not None


# ---------------------------------------------------------------------------
# FAILED transition — error handling
# ---------------------------------------------------------------------------


class TestFailedTransitions:
    """Tests for automatic FAILED transitions when services raise."""

    @pytest.mark.asyncio
    async def test_generate_episode_transitions_to_failed_on_ideation_error(
        self,
        orchestrator,
        mock_episode_storage,
        mock_ideation_service,
    ):
        """generate_episode transitions to FAILED if ideation raises."""
        mock_ideation_service.generate_concept.side_effect = RuntimeError("LLM down")

        with pytest.raises(RuntimeError, match="LLM down"):
            await orchestrator.generate_episode("olivers_workshop", "rockets")

        # The episode should be persisted in FAILED stage
        saved_calls = mock_episode_storage.save_episode.call_args_list
        last_saved: Episode = saved_calls[-1][0][0]
        assert last_saved.current_stage == PipelineStage.FAILED

    @pytest.mark.asyncio
    async def test_generate_episode_transitions_to_failed_on_outline_error(
        self,
        orchestrator,
        mock_episode_storage,
        mock_outline_service,
    ):
        """generate_episode transitions to FAILED if outlining raises."""
        mock_outline_service.generate_outline.side_effect = RuntimeError("LLM timeout")

        with pytest.raises(RuntimeError, match="LLM timeout"):
            await orchestrator.generate_episode("olivers_workshop", "rockets")

        saved_calls = mock_episode_storage.save_episode.call_args_list
        last_saved: Episode = saved_calls[-1][0][0]
        assert last_saved.current_stage == PipelineStage.FAILED

    @pytest.mark.asyncio
    async def test_resume_episode_transitions_to_failed_on_segment_error(
        self,
        orchestrator,
        mock_episode_storage,
        mock_segment_service,
        sample_outline,
        sample_concept,
    ):
        """resume_episode transitions to FAILED if segment generation raises."""
        mock_segment_service.generate_segments.side_effect = RuntimeError("API error")

        episode = Episode(
            episode_id="ep_fail_seg",
            show_id="olivers_workshop",
            topic="rockets",
            title="Rockets",
            concept=sample_concept,
            outline=sample_outline,
            current_stage=PipelineStage.APPROVED,
            approval_status="approved",
        )
        mock_episode_storage.save_episode(episode)

        with pytest.raises(StageExecutionError, match="API error"):
            await orchestrator.resume_episode("olivers_workshop", "ep_fail_seg")

        saved_calls = mock_episode_storage.save_episode.call_args_list
        last_saved: Episode = saved_calls[-1][0][0]
        assert last_saved.current_stage == PipelineStage.FAILED

    @pytest.mark.asyncio
    async def test_resume_episode_transitions_to_failed_on_script_error(
        self,
        orchestrator,
        mock_episode_storage,
        mock_script_service,
        sample_outline,
        sample_concept,
    ):
        """resume_episode transitions to FAILED if script generation raises."""
        mock_script_service.generate_scripts.side_effect = RuntimeError("Script error")

        episode = Episode(
            episode_id="ep_fail_scr",
            show_id="olivers_workshop",
            topic="rockets",
            title="Rockets",
            concept=sample_concept,
            outline=sample_outline,
            current_stage=PipelineStage.APPROVED,
            approval_status="approved",
        )
        mock_episode_storage.save_episode(episode)

        with pytest.raises(StageExecutionError, match="Script error"):
            await orchestrator.resume_episode("olivers_workshop", "ep_fail_scr")

        saved_calls = mock_episode_storage.save_episode.call_args_list
        last_saved: Episode = saved_calls[-1][0][0]
        assert last_saved.current_stage == PipelineStage.FAILED


# ---------------------------------------------------------------------------
# retry_failed_episode / retry_rejected_episode
# ---------------------------------------------------------------------------


class TestRetryFailedEpisode:
    """Tests for PipelineOrchestrator.retry_failed_episode()."""

    @pytest.mark.asyncio
    async def test_retry_failed_reruns_to_approval(
        self,
        orchestrator,
        mock_episode_storage,
        sample_concept,
        sample_outline,
    ):
        """retry_failed_episode resets and re-generates up to approval gate."""
        episode = Episode(
            episode_id="ep_retry_fail",
            show_id="olivers_workshop",
            topic="rockets",
            title="Rockets",
            current_stage=PipelineStage.FAILED,
        )
        mock_episode_storage.save_episode(episode)

        result = await orchestrator.retry_failed_episode(
            "olivers_workshop", "ep_retry_fail"
        )
        assert result.is_approval_required

        loaded = mock_episode_storage.load_episode("olivers_workshop", "ep_retry_fail")
        assert loaded.current_stage == PipelineStage.AWAITING_APPROVAL
        assert loaded.concept is not None
        assert loaded.outline is not None

    @pytest.mark.asyncio
    async def test_retry_non_failed_raises(
        self,
        orchestrator,
        mock_episode_storage,
    ):
        """retry_failed_episode raises ValueError if episode is not FAILED."""
        episode = Episode(
            episode_id="ep_not_fail",
            show_id="olivers_workshop",
            topic="rockets",
            title="Rockets",
            current_stage=PipelineStage.PENDING,
        )
        mock_episode_storage.save_episode(episode)

        with pytest.raises(ValueError, match="not in FAILED stage"):
            await orchestrator.retry_failed_episode("olivers_workshop", "ep_not_fail")


class TestRetryRejectedEpisode:
    """Tests for PipelineOrchestrator.retry_rejected_episode()."""

    @pytest.mark.asyncio
    async def test_retry_rejected_reruns_to_approval(
        self,
        orchestrator,
        mock_episode_storage,
        sample_concept,
        sample_outline,
    ):
        """retry_rejected_episode re-generates content up to approval gate."""
        episode = Episode(
            episode_id="ep_retry_rej",
            show_id="olivers_workshop",
            topic="rockets",
            title="Rockets",
            current_stage=PipelineStage.REJECTED,
            approval_status="rejected",
        )
        mock_episode_storage.save_episode(episode)

        result = await orchestrator.retry_rejected_episode(
            "olivers_workshop", "ep_retry_rej"
        )
        assert result.is_approval_required

        loaded = mock_episode_storage.load_episode("olivers_workshop", "ep_retry_rej")
        assert loaded.current_stage == PipelineStage.AWAITING_APPROVAL
        assert loaded.concept is not None
        assert loaded.outline is not None

    @pytest.mark.asyncio
    async def test_retry_non_rejected_raises(
        self,
        orchestrator,
        mock_episode_storage,
    ):
        """retry_rejected_episode raises ValueError if episode is not REJECTED."""
        episode = Episode(
            episode_id="ep_not_rej",
            show_id="olivers_workshop",
            topic="rockets",
            title="Rockets",
            current_stage=PipelineStage.APPROVED,
            approval_status="approved",
        )
        mock_episode_storage.save_episode(episode)

        with pytest.raises(ValueError, match="not in REJECTED stage"):
            await orchestrator.retry_rejected_episode("olivers_workshop", "ep_not_rej")
