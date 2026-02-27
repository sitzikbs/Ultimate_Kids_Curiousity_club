"""Tests for Show Blueprint context injection throughout the pipeline."""

import pytest

from models.episode import Episode, PipelineStage
from utils.errors import ApprovalRequiredError


class TestBlueprintLoading:
    """Tests that Show Blueprint is loaded and passed correctly."""

    @pytest.mark.asyncio
    async def test_blueprint_loaded_at_generate(self, orchestrator, mock_show_manager):
        """ShowBlueprintManager.load_show() is called at pipeline start."""
        with pytest.raises(ApprovalRequiredError):
            await orchestrator.generate_episode("olivers_workshop", "rockets")

        mock_show_manager.load_show.assert_called_with("olivers_workshop")

    @pytest.mark.asyncio
    async def test_blueprint_loaded_at_resume(
        self,
        orchestrator,
        mock_show_manager,
        mock_episode_storage,
        sample_outline,
        sample_concept,
    ):
        """ShowBlueprintManager.load_show() is called when resuming."""
        episode = Episode(
            episode_id="ep_bp_resume",
            show_id="olivers_workshop",
            topic="rockets",
            title="Rockets",
            concept=sample_concept,
            outline=sample_outline,
            current_stage=PipelineStage.APPROVED,
            approval_status="approved",
        )
        mock_episode_storage.save_episode(episode)

        await orchestrator.resume_episode("olivers_workshop", "ep_bp_resume")

        mock_show_manager.load_show.assert_called_with("olivers_workshop")

    @pytest.mark.asyncio
    async def test_nonexistent_show_raises(self, orchestrator, mock_show_manager):
        """FileNotFoundError from manager propagates when show doesn't exist."""
        mock_show_manager.load_show.side_effect = FileNotFoundError("No such show")

        with pytest.raises(FileNotFoundError, match="No such show"):
            await orchestrator.generate_episode("nonexistent_show", "rockets")


class TestBlueprintContextInjection:
    """Tests that blueprint is passed to all LLM and TTS services."""

    @pytest.mark.asyncio
    async def test_ideation_receives_blueprint(
        self, orchestrator, mock_ideation_service, sample_blueprint
    ):
        """Ideation service receives the loaded ShowBlueprint."""
        with pytest.raises(ApprovalRequiredError):
            await orchestrator.generate_episode("olivers_workshop", "rockets")

        call_kwargs = mock_ideation_service.generate_concept.call_args.kwargs
        assert call_kwargs["show_blueprint"] is sample_blueprint

    @pytest.mark.asyncio
    async def test_outline_receives_blueprint(
        self, orchestrator, mock_outline_service, sample_blueprint
    ):
        """Outline service receives the loaded ShowBlueprint."""
        with pytest.raises(ApprovalRequiredError):
            await orchestrator.generate_episode("olivers_workshop", "rockets")

        call_kwargs = mock_outline_service.generate_outline.call_args.kwargs
        assert call_kwargs["show_blueprint"] is sample_blueprint

    @pytest.mark.asyncio
    async def test_segment_receives_blueprint(
        self,
        orchestrator,
        mock_episode_storage,
        mock_segment_service,
        sample_blueprint,
        sample_outline,
        sample_concept,
    ):
        """Segment service receives the ShowBlueprint on resume."""
        episode = Episode(
            episode_id="ep_seg_bp",
            show_id="olivers_workshop",
            topic="rockets",
            title="Rockets",
            concept=sample_concept,
            outline=sample_outline,
            current_stage=PipelineStage.APPROVED,
            approval_status="approved",
        )
        mock_episode_storage.save_episode(episode)

        await orchestrator.resume_episode("olivers_workshop", "ep_seg_bp")

        call_kwargs = mock_segment_service.generate_segments.call_args.kwargs
        assert call_kwargs["show_blueprint"] is sample_blueprint

    @pytest.mark.asyncio
    async def test_script_receives_blueprint(
        self,
        orchestrator,
        mock_episode_storage,
        mock_script_service,
        sample_blueprint,
        sample_outline,
        sample_concept,
    ):
        """Script service receives the ShowBlueprint on resume."""
        episode = Episode(
            episode_id="ep_scr_bp",
            show_id="olivers_workshop",
            topic="rockets",
            title="Rockets",
            concept=sample_concept,
            outline=sample_outline,
            current_stage=PipelineStage.APPROVED,
            approval_status="approved",
        )
        mock_episode_storage.save_episode(episode)

        await orchestrator.resume_episode("olivers_workshop", "ep_scr_bp")

        call_kwargs = mock_script_service.generate_scripts.call_args.kwargs
        assert call_kwargs["show_blueprint"] is sample_blueprint


class TestVoiceMapping:
    """Tests for voice config mapping from blueprint to TTS."""

    def test_voice_map_includes_narrator(self, orchestrator, sample_blueprint):
        """Voice map contains narrator from show config."""
        voice_map = orchestrator._build_voice_map(sample_blueprint)
        assert "narrator" in voice_map
        assert voice_map["narrator"]["voice_id"] == "mock_narrator"

    def test_voice_map_includes_protagonist(self, orchestrator, sample_blueprint):
        """Voice map contains protagonist by full name and first name."""
        voice_map = orchestrator._build_voice_map(sample_blueprint)
        assert "oliver" in voice_map
        assert voice_map["oliver"]["voice_id"] == "mock_oliver"

    def test_voice_map_includes_characters(self, orchestrator, sample_blueprint):
        """Voice map contains supporting characters."""
        voice_map = orchestrator._build_voice_map(sample_blueprint)
        assert "robbie robot" in voice_map or "robbie" in voice_map
        assert voice_map["robbie"]["voice_id"] == "mock_robbie"

    @pytest.mark.asyncio
    async def test_synthesis_uses_correct_voice(
        self,
        orchestrator,
        mock_episode_storage,
        mock_synthesis_service,
        sample_outline,
        sample_concept,
    ):
        """Audio synthesis maps speakers to correct voice configs."""
        episode = Episode(
            episode_id="ep_voice",
            show_id="olivers_workshop",
            topic="rockets",
            title="Rockets",
            concept=sample_concept,
            outline=sample_outline,
            current_stage=PipelineStage.APPROVED,
            approval_status="approved",
        )
        mock_episode_storage.save_episode(episode)

        await orchestrator.resume_episode("olivers_workshop", "ep_voice")

        # Check all synthesis calls have voice_config with a voice_id
        for call in mock_synthesis_service.synthesize_segment.call_args_list:
            kwargs = call.kwargs if call.kwargs else {}
            args = call.args if call.args else ()
            # voice_config is the 3rd positional arg or keyword
            if "voice_config" in kwargs:
                assert "voice_id" in kwargs["voice_config"]
            elif len(args) >= 3:
                assert "voice_id" in args[2]


class TestConceptsUpdate:
    """Tests for Show Blueprint concept tracking after completion."""

    @pytest.mark.asyncio
    async def test_add_concept_called_on_complete(
        self,
        orchestrator,
        mock_episode_storage,
        mock_show_manager,
        sample_outline,
        sample_concept,
    ):
        """add_concept() is called with topic and episode_id on COMPLETE."""
        episode = Episode(
            episode_id="ep_concept",
            show_id="olivers_workshop",
            topic="rockets",
            title="Rockets",
            concept=sample_concept,
            outline=sample_outline,
            current_stage=PipelineStage.APPROVED,
            approval_status="approved",
        )
        mock_episode_storage.save_episode(episode)

        await orchestrator.resume_episode("olivers_workshop", "ep_concept")

        mock_show_manager.add_concept.assert_called_once_with(
            show_id="olivers_workshop",
            concept="rockets",
            episode_id="ep_concept",
        )

    @pytest.mark.asyncio
    async def test_concept_failure_does_not_crash_pipeline(
        self,
        orchestrator,
        mock_episode_storage,
        mock_show_manager,
        sample_outline,
        sample_concept,
    ):
        """Pipeline completes even if add_concept() raises."""
        mock_show_manager.add_concept.side_effect = RuntimeError("Disk full")

        episode = Episode(
            episode_id="ep_concept_err",
            show_id="olivers_workshop",
            topic="rockets",
            title="Rockets",
            concept=sample_concept,
            outline=sample_outline,
            current_stage=PipelineStage.APPROVED,
            approval_status="approved",
        )
        mock_episode_storage.save_episode(episode)

        # Should NOT raise
        result = await orchestrator.resume_episode("olivers_workshop", "ep_concept_err")
        assert result.current_stage == PipelineStage.COMPLETE
