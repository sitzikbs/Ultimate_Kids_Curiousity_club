"""Tests for pipeline state machine and transitions."""

import pytest

from models import Episode, PipelineStage


def _import_orchestrator():
    """Lazy import of orchestrator modules."""
    from orchestrator.pipeline import PipelineOrchestrator

    return PipelineOrchestrator


class TestStateTransitions:
    """Test state transition validation."""

    def test_valid_transition_pending_to_ideation(
        self, orchestrator, test_episode: Episode
    ):
        """Test valid transition from PENDING to IDEATION."""
        test_episode.current_stage = PipelineStage.PENDING
        assert orchestrator.can_transition_to(test_episode, PipelineStage.IDEATION)

    def test_valid_transition_ideation_to_outlining(
        self, orchestrator, test_episode: Episode
    ):
        """Test valid transition from IDEATION to OUTLINING."""
        test_episode.current_stage = PipelineStage.IDEATION
        assert orchestrator.can_transition_to(test_episode, PipelineStage.OUTLINING)

    def test_valid_transition_outlining_to_awaiting_approval(
        self, orchestrator, test_episode: Episode
    ):
        """Test valid transition from OUTLINING to AWAITING_APPROVAL."""
        test_episode.current_stage = PipelineStage.OUTLINING
        assert orchestrator.can_transition_to(
            test_episode, PipelineStage.AWAITING_APPROVAL
        )

    def test_valid_transition_awaiting_approval_to_segment(
        self, orchestrator, test_episode: Episode
    ):
        """Test valid transition from AWAITING_APPROVAL to SEGMENT_GENERATION."""
        test_episode.current_stage = PipelineStage.AWAITING_APPROVAL
        assert orchestrator.can_transition_to(
            test_episode, PipelineStage.SEGMENT_GENERATION
        )

    def test_valid_transition_awaiting_approval_to_rejected(
        self, orchestrator, test_episode: Episode
    ):
        """Test valid transition from AWAITING_APPROVAL to REJECTED."""
        test_episode.current_stage = PipelineStage.AWAITING_APPROVAL
        assert orchestrator.can_transition_to(test_episode, PipelineStage.REJECTED)

    def test_valid_transition_rejected_to_ideation(
        self, orchestrator, test_episode: Episode
    ):
        """Test valid transition from REJECTED back to IDEATION."""
        test_episode.current_stage = PipelineStage.REJECTED
        assert orchestrator.can_transition_to(test_episode, PipelineStage.IDEATION)

    def test_invalid_transition_pending_to_outlining(
        self, orchestrator, test_episode: Episode
    ):
        """Test invalid transition - can't skip IDEATION."""
        test_episode.current_stage = PipelineStage.PENDING
        assert not orchestrator.can_transition_to(
            test_episode, PipelineStage.OUTLINING
        )

    def test_invalid_transition_ideation_to_segment(
        self, orchestrator, test_episode: Episode
    ):
        """Test invalid transition - can't skip OUTLINING and APPROVAL."""
        test_episode.current_stage = PipelineStage.IDEATION
        assert not orchestrator.can_transition_to(
            test_episode, PipelineStage.SEGMENT_GENERATION
        )

    def test_invalid_transition_complete_to_ideation(
        self, orchestrator, test_episode: Episode
    ):
        """Test invalid transition - can't go back from COMPLETE."""
        test_episode.current_stage = PipelineStage.COMPLETE
        assert not orchestrator.can_transition_to(test_episode, PipelineStage.IDEATION)


class TestPipelineExecution:
    """Test pipeline stage execution."""

    @pytest.mark.asyncio
    async def test_execute_ideation_from_pending(
        self, orchestrator, test_episode: Episode
    ):
        """Test executing ideation stage from PENDING."""
        test_episode.current_stage = PipelineStage.PENDING

        # Save initial episode
        orchestrator.storage.save_episode(test_episode)

        # Execute ideation
        result = await orchestrator.execute_stage(test_episode)

        assert result.current_stage == PipelineStage.IDEATION
        assert result.concept is not None  # Concept stored in concept field

    @pytest.mark.asyncio
    async def test_execute_outlining_from_ideation(
        self, orchestrator, test_episode: Episode
    ):
        """Test executing outlining stage from IDEATION."""
        test_episode.current_stage = PipelineStage.IDEATION
        test_episode.concept = "Test concept"

        # Save episode
        orchestrator.storage.save_episode(test_episode)

        # Execute outlining
        result = await orchestrator.execute_stage(test_episode)

        assert result.current_stage == PipelineStage.AWAITING_APPROVAL
        assert result.outline is not None
        assert result.approval_status == "pending"

    @pytest.mark.asyncio
    async def test_execute_stage_awaiting_approval_raises_error(
        self, orchestrator, test_episode: Episode
    ):
        """Test that executing stage at AWAITING_APPROVAL raises error."""
        test_episode.current_stage = PipelineStage.AWAITING_APPROVAL

        with pytest.raises(ValueError, match="awaiting approval"):
            await orchestrator.execute_stage(test_episode)

    @pytest.mark.asyncio
    async def test_execute_stage_rejected_raises_error(
        self, orchestrator, test_episode: Episode
    ):
        """Test that executing stage at REJECTED raises error."""
        test_episode.current_stage = PipelineStage.REJECTED

        with pytest.raises(ValueError, match="rejected"):
            await orchestrator.execute_stage(test_episode)

    @pytest.mark.asyncio
    async def test_execute_stage_complete_raises_error(
        self, orchestrator, test_episode: Episode
    ):
        """Test that executing stage at COMPLETE raises error."""
        test_episode.current_stage = PipelineStage.COMPLETE

        with pytest.raises(ValueError, match="already complete"):
            await orchestrator.execute_stage(test_episode)

    @pytest.mark.asyncio
    async def test_execute_outlining_invalid_stage_raises_error(
        self, orchestrator, test_episode: Episode
    ):
        """Test that executing outlining from wrong stage raises error."""
        test_episode.current_stage = PipelineStage.PENDING

        with pytest.raises(ValueError, match="Cannot execute outlining"):
            await orchestrator._execute_outlining(test_episode)


class TestGenerateEpisode:
    """Test full episode generation workflow."""

    @pytest.mark.asyncio
    async def test_generate_episode_creates_new_episode(
        self, orchestrator
    ):
        """Test that generate_episode creates and saves new episode."""
        result = await orchestrator.generate_episode(
            show_id="test_show",
            topic="testing",
            
        )

        assert result.episode_id is not None
        assert result.show_id == "test_show"
        assert result.topic == "testing"
        assert result.current_stage == PipelineStage.AWAITING_APPROVAL
        assert result.outline is not None

    @pytest.mark.asyncio
    async def test_generate_episode_generates_id_from_topic(
        self, orchestrator
    ):
        """Test that episode ID is generated from topic."""
        result = await orchestrator.generate_episode(
            show_id="test_show",
            topic="how rockets work",
            
        )

        assert "how_rockets_work" in result.episode_id
        assert "_" in result.episode_id  # Should have timestamp

    @pytest.mark.asyncio
    async def test_generate_episode_generates_title(
        self, orchestrator
    ):
        """Test that episode title is generated from topic."""
        result = await orchestrator.generate_episode(
            show_id="test_show",
            topic="how rockets work",
            
        )

        assert result.title == "How Rockets Work"

    @pytest.mark.asyncio
    async def test_generate_episode_calls_services(
        self,
        orchestrator,
        mock_ideation_service,
        mock_outline_service,
    ):
        """Test that generate_episode calls ideation and outline services."""
        await orchestrator.generate_episode(
            show_id="test_show",
            topic="testing",
            
        )

        mock_ideation_service.generate_concept.assert_called_once()
        mock_outline_service.generate_outline.assert_called_once()


class TestShowBlueprintIntegration:
    """Test Show Blueprint context injection."""

    @pytest.mark.asyncio
    async def test_generate_episode_loads_show_blueprint(
        self, orchestrator, mock_show_manager
    ):
        """Test that Show Blueprint is loaded at pipeline start."""
        await orchestrator.generate_episode(
            show_id="test_show",
            topic="testing",
        )

        mock_show_manager.load_show.assert_called_with("test_show")

    @pytest.mark.asyncio
    async def test_show_blueprint_passed_to_ideation(
        self,
        orchestrator,
        mock_ideation_service,
        test_show_blueprint,
    ):
        """Test that Show Blueprint is passed to ideation service."""
        await orchestrator.generate_episode(
            show_id="test_show",
            topic="testing",
        )

        call_args = mock_ideation_service.generate_concept.call_args
        assert call_args.kwargs["show_blueprint"] == test_show_blueprint

    @pytest.mark.asyncio
    async def test_show_blueprint_passed_to_outline(
        self,
        orchestrator,
        mock_outline_service,
        test_show_blueprint,
    ):
        """Test that Show Blueprint is passed to outline service."""
        await orchestrator.generate_episode(
            show_id="test_show",
            topic="testing",
        )

        call_args = mock_outline_service.generate_outline.call_args
        assert call_args.kwargs["show_blueprint"] == test_show_blueprint
