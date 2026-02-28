"""Pipeline orchestrator for coordinating episode generation stages.

Implements the 8-stage state machine:
PENDING → IDEATION → OUTLINING → AWAITING_APPROVAL → (APPROVED) →
SEGMENT_GENERATION → SCRIPT_GENERATION → AUDIO_SYNTHESIS → AUDIO_MIXING → COMPLETE

The pipeline pauses at AWAITING_APPROVAL for human review.
Use ApprovalWorkflow to approve/reject and then resume_episode() to continue.
"""

import asyncio
import inspect
import logging
import re
import uuid
from contextlib import asynccontextmanager
from datetime import UTC, datetime
from typing import Any

from models.episode import Episode, PipelineStage
from models.show import ShowBlueprint
from orchestrator.error_handler import (
    STAGE_NAME_TO_ENUM,
    STAGE_ORDER,
    STAGE_SERVICE_MAP,
    CircuitBreaker,
    StageExecutionError,
    build_error_context,
)
from orchestrator.events import EventCallback, EventType, PipelineEvent
from orchestrator.progress_tracker import ProgressTracker
from orchestrator.result import PipelineResult, PipelineResultStatus
from orchestrator.transitions import can_transition_to
from services.protocols import (
    AudioMixerProtocol,
    AudioSynthesisProtocol,
    BlueprintManagerProtocol,
    EpisodeStorageProtocol,
    IdeationServiceProtocol,
    OutlineServiceProtocol,
    PromptEnhancerProtocol,
    ScriptServiceProtocol,
    SegmentServiceProtocol,
)

logger = logging.getLogger(__name__)


class PipelineOrchestrator:
    """Orchestrates the episode generation pipeline through 8 stages.

    Coordinates all generation services (LLM, TTS, audio mixing) with
    Show Blueprint context injection and a human approval gate.
    """

    def __init__(
        self,
        prompt_enhancer: PromptEnhancerProtocol,
        ideation_service: IdeationServiceProtocol,
        outline_service: OutlineServiceProtocol,
        segment_service: SegmentServiceProtocol,
        script_service: ScriptServiceProtocol,
        synthesis_service: AudioSynthesisProtocol,
        audio_mixer: AudioMixerProtocol,
        show_blueprint_manager: BlueprintManagerProtocol,
        episode_storage: EpisodeStorageProtocol,
        event_callback: EventCallback | None = None,
    ) -> None:
        """Initialize orchestrator with all service dependencies.

        Args:
            prompt_enhancer: Prompt enhancement with Show Blueprint context
            ideation_service: Generates story concepts from topics
            outline_service: Generates story outlines from concepts
            segment_service: Generates segments from outlines
            script_service: Generates scripts from segments
            synthesis_service: Converts scripts to audio via TTS
            audio_mixer: Mixes audio segments into final episode
            show_blueprint_manager: Manages Show Blueprint CRUD
            episode_storage: Persists episode state
            event_callback: Optional callback for pipeline events
        """
        self.prompt_enhancer = prompt_enhancer
        self.ideation = ideation_service
        self.outline = outline_service
        self.segment = segment_service
        self.script = script_service
        self.synthesis = synthesis_service
        self.mixer = audio_mixer
        self.show_manager = show_blueprint_manager
        self.storage = episode_storage
        self.event_callback = event_callback

        # WP6b: reliability components
        self.progress = ProgressTracker()
        self.circuit_breaker = CircuitBreaker()

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    async def generate_episode(
        self,
        show_id: str,
        topic: str,
        title: str | None = None,
    ) -> PipelineResult:
        """Start generating a new episode.

        Creates the episode, runs IDEATION → OUTLINING, then pauses at
        AWAITING_APPROVAL for human review.

        Args:
            show_id: Identifier of the show
            topic: Topic / educational concept for the episode
            title: Optional explicit title; auto-generated if omitted

        Returns:
            PipelineResult with APPROVAL_REQUIRED status on success,
            or FAILED status if a stage raises an exception.

        Raises:
            FileNotFoundError: If show_id does not exist
        """
        # Load Show Blueprint
        show_blueprint = self.show_manager.load_show(show_id)

        # Create episode
        episode_id = self._generate_episode_id(topic)
        episode = Episode(
            episode_id=episode_id,
            show_id=show_id,
            topic=topic,
            title=title or self._generate_title(topic),
        )

        # Save initial state
        self.storage.save_episode(episode)
        self.progress.reset()
        logger.info(
            "Created episode %s for show %s (topic: %s)",
            episode_id,
            show_id,
            topic,
        )

        # Execute pre-approval stages
        try:
            episode = await self._execute_ideation(episode, show_blueprint)
            episode = await self._execute_outlining(episode, show_blueprint)
        except Exception:
            if self.can_transition_to(episode.current_stage, PipelineStage.FAILED):
                self._transition(episode, PipelineStage.FAILED)
                self.storage.save_episode(episode)
            raise

        # Transition to approval gate
        episode = self._transition(episode, PipelineStage.AWAITING_APPROVAL)
        episode.approval_status = "pending"
        self.storage.save_episode(episode)
        await self._emit_event(EventType.APPROVAL_REQUIRED, episode)

        return PipelineResult(
            status=PipelineResultStatus.APPROVAL_REQUIRED,
            episode=episode,
            message=f"Episode {episode.episode_id} awaiting approval",
        )

    async def resume_episode(
        self,
        show_id: str,
        episode_id: str,
    ) -> PipelineResult:
        """Resume an approved episode through remaining stages.

        Continues the pipeline from the episode's current stage to COMPLETE.

        Args:
            show_id: Show identifier
            episode_id: Episode identifier

        Returns:
            PipelineResult with COMPLETED status on success.

        Raises:
            ValueError: If episode is not in a resumable stage
        """
        episode = self.storage.load_episode(show_id, episode_id)
        show_blueprint = self.show_manager.load_show(show_id)

        # Ordered post-approval stage pipeline — runners are sliced from
        # the episode's current position so adding a stage requires only
        # one entry here.  Multiple stages can share a runner (e.g.
        # APPROVED and SEGMENT_GENERATION both enter segment generation).
        post_approval_pipeline: list[tuple[set[PipelineStage], Any, str]] = [
            (
                {PipelineStage.APPROVED, PipelineStage.SEGMENT_GENERATION},
                self._execute_segment_generation,
                "segment_generation",
            ),
            (
                {PipelineStage.SCRIPT_GENERATION},
                self._execute_script_generation,
                "script_generation",
            ),
            (
                {PipelineStage.AUDIO_SYNTHESIS},
                self._execute_audio_synthesis,
                "audio_synthesis",
            ),
            (
                {PipelineStage.AUDIO_MIXING},
                self._execute_audio_mixing,
                "audio_mixing",
            ),
        ]

        # Find where the episode's current stage sits in the pipeline
        try:
            start_idx = next(
                i
                for i, (stages, _, _) in enumerate(post_approval_pipeline)
                if episode.current_stage in stages
            )
        except StopIteration:
            raise ValueError(
                f"Episode {episode_id} is not in a resumable stage "
                f"(current: {episode.current_stage.value})"
            )

        remaining = post_approval_pipeline[start_idx:]

        for _, runner, stage_name in remaining:
            service_name = STAGE_SERVICE_MAP.get(
                STAGE_NAME_TO_ENUM.get(stage_name, PipelineStage.PENDING), "llm"
            )
            episode = await self._execute_stage_with_error_handling(
                runner, episode, stage_name, service_name, show_blueprint
            )

        # Finalize — update Show Blueprint concepts
        await self._finalize_episode(episode, show_blueprint)

        return PipelineResult(
            status=PipelineResultStatus.COMPLETED,
            episode=episode,
            message=f"Episode {episode.episode_id} complete",
        )

    async def retry_failed_episode(
        self,
        show_id: str,
        episode_id: str,
    ) -> PipelineResult:
        """Reset a FAILED episode to PENDING and re-run from the start.

        Transitions FAILED → PENDING, then delegates to ``generate_episode``
        which will run IDEATION → OUTLINING → AWAITING_APPROVAL.

        Args:
            show_id: Show identifier
            episode_id: Episode identifier

        Returns:
            PipelineResult with APPROVAL_REQUIRED status on success.

        Raises:
            ValueError: If episode is not in FAILED stage
        """
        episode = self.storage.load_episode(show_id, episode_id)

        if episode.current_stage != PipelineStage.FAILED:
            raise ValueError(
                f"Episode {episode_id} is not in FAILED stage "
                f"(current: {episode.current_stage.value})"
            )

        episode = self._transition(episode, PipelineStage.PENDING)
        self.storage.save_episode(episode)
        logger.info("Reset FAILED episode %s to PENDING", episode_id)

        # Re-use generate_episode logic on the existing episode
        show_blueprint = self.show_manager.load_show(show_id)

        try:
            episode = await self._execute_ideation(episode, show_blueprint)
            episode = await self._execute_outlining(episode, show_blueprint)
        except Exception:
            if self.can_transition_to(episode.current_stage, PipelineStage.FAILED):
                self._transition(episode, PipelineStage.FAILED)
                self.storage.save_episode(episode)
            raise

        episode = self._transition(episode, PipelineStage.AWAITING_APPROVAL)
        episode.approval_status = "pending"
        self.storage.save_episode(episode)
        await self._emit_event(EventType.APPROVAL_REQUIRED, episode)

        return PipelineResult(
            status=PipelineResultStatus.APPROVAL_REQUIRED,
            episode=episode,
            message=f"Episode {episode.episode_id} awaiting approval (retry)",
        )

    async def retry_rejected_episode(
        self,
        show_id: str,
        episode_id: str,
    ) -> PipelineResult:
        """Re-run a REJECTED episode from IDEATION with fresh content.

        Transitions REJECTED → IDEATION and re-generates concept + outline,
        pausing again at AWAITING_APPROVAL.

        Args:
            show_id: Show identifier
            episode_id: Episode identifier

        Returns:
            PipelineResult with APPROVAL_REQUIRED status on success.

        Raises:
            ValueError: If episode is not in REJECTED stage
        """
        episode = self.storage.load_episode(show_id, episode_id)

        if episode.current_stage != PipelineStage.REJECTED:
            raise ValueError(
                f"Episode {episode_id} is not in REJECTED stage "
                f"(current: {episode.current_stage.value})"
            )

        show_blueprint = self.show_manager.load_show(show_id)

        try:
            episode = await self._execute_ideation(episode, show_blueprint)
            episode = await self._execute_outlining(episode, show_blueprint)
        except Exception:
            if self.can_transition_to(episode.current_stage, PipelineStage.FAILED):
                self._transition(episode, PipelineStage.FAILED)
                self.storage.save_episode(episode)
            raise

        episode = self._transition(episode, PipelineStage.AWAITING_APPROVAL)
        episode.approval_status = "pending"
        self.storage.save_episode(episode)
        await self._emit_event(EventType.APPROVAL_REQUIRED, episode)

        return PipelineResult(
            status=PipelineResultStatus.APPROVAL_REQUIRED,
            episode=episode,
            message=(
                f"Episode {episode.episode_id} awaiting approval"
                " (retry after rejection)"
            ),
        )

    async def execute_single_stage(
        self,
        show_id: str,
        episode_id: str,
        target_stage: PipelineStage,
    ) -> Episode:
        """Execute exactly one pipeline stage for debugging/re-running.

        Runs the runner associated with *target_stage* without advancing
        through subsequent stages.  Note that some runners (post-approval:
        SEGMENT_GENERATION, SCRIPT_GENERATION, AUDIO_SYNTHESIS, AUDIO_MIXING)
        include an exit transition to the *next* stage as part of their
        completion contract.  Pre-approval runners (IDEATION, OUTLINING)
        do NOT advance — the orchestrator loop handles that.

        Args:
            show_id: Show identifier
            episode_id: Episode identifier
            target_stage: The single stage to execute

        Returns:
            Episode after the stage completes

        Raises:
            ValueError: If *target_stage* has no associated runner
        """
        stage_runner_map = {
            PipelineStage.IDEATION: self._execute_ideation,
            PipelineStage.OUTLINING: self._execute_outlining,
            PipelineStage.SEGMENT_GENERATION: self._execute_segment_generation,
            PipelineStage.SCRIPT_GENERATION: self._execute_script_generation,
            PipelineStage.AUDIO_SYNTHESIS: self._execute_audio_synthesis,
            PipelineStage.AUDIO_MIXING: self._execute_audio_mixing,
        }

        runner = stage_runner_map.get(target_stage)
        if runner is None:
            raise ValueError(
                f"No runner for stage {target_stage.value}. "
                f"Executable stages: {[s.value for s in stage_runner_map]}"
            )

        episode = self.storage.load_episode(show_id, episode_id)
        show_blueprint = self.show_manager.load_show(show_id)

        episode = await runner(episode, show_blueprint)
        return episode

    @staticmethod
    def can_transition_to(
        current: PipelineStage,
        target: PipelineStage,
    ) -> bool:
        """Check whether a state transition is valid.

        Delegates to the canonical ``transitions.can_transition_to()``.

        Args:
            current: Current pipeline stage
            target: Desired target stage

        Returns:
            True if the transition is allowed
        """
        return can_transition_to(current, target)

    async def reset_to_stage(
        self,
        show_id: str,
        episode_id: str,
        target_stage: str,
    ) -> Episode:
        """Reset episode to a previous stage for manual recovery.

        Clears checkpoints after the target stage and sets the episode's
        current_stage to the corresponding PipelineStage.

        Args:
            show_id: Show identifier
            episode_id: Episode identifier
            target_stage: Stage name to reset to (e.g. "ideation", "outlining")

        Returns:
            Episode after reset

        Raises:
            ValueError: If target_stage is not a valid stage name
        """
        if target_stage not in STAGE_NAME_TO_ENUM:
            raise ValueError(
                f"Invalid stage name: {target_stage}. "
                f"Valid stages: {list(STAGE_NAME_TO_ENUM.keys())}"
            )

        episode = self.storage.load_episode(show_id, episode_id)

        # Clear checkpoints after target stage
        if episode.checkpoints:
            target_idx = STAGE_ORDER.index(target_stage)
            stages_to_clear = [
                s for s in STAGE_ORDER[target_idx + 1 :] if s in episode.checkpoints
            ]
            for stage in stages_to_clear:
                del episode.checkpoints[stage]

            # Recalculate total cost from remaining checkpoints
            episode.total_cost = sum(
                cp.get("cost", 0.0) for cp in episode.checkpoints.values()
            )

        # Clear error state
        episode.last_error = None
        episode.retry_count = 0

        # Update stage
        target_enum = STAGE_NAME_TO_ENUM[target_stage]
        episode.current_stage = target_enum
        episode.updated_at = datetime.now(UTC)
        self.storage.save_episode(episode)

        logger.info("Reset episode %s to stage %s", episode_id, target_stage)
        return episode

    # ------------------------------------------------------------------
    # Checkpoint & error handling helpers (WP6b)
    # ------------------------------------------------------------------

    def _save_checkpoint(
        self,
        episode: Episode,
        stage_name: str,
        output_summary: dict[str, Any],
        cost: float = 0.0,
    ) -> None:
        """Save a per-stage checkpoint to the episode.

        Writes timestamp, output summary, and cost into episode.checkpoints,
        accumulates total_cost, and persists via storage.

        Args:
            episode: Episode to update.
            stage_name: Stage key (e.g. "ideation", "audio_synthesis").
            output_summary: Summary of stage output for checkpoint inspection.
            cost: Estimated cost of this stage in USD.
        """
        episode.checkpoints[stage_name] = {
            "completed_at": datetime.now(UTC).isoformat(),
            "output": output_summary,
            "cost": cost,
        }
        episode.total_cost = sum(
            cp.get("cost", 0.0) for cp in episode.checkpoints.values()
        )
        self.storage.save_episode(episode)
        logger.info("Checkpoint saved: %s (cost: $%.4f)", stage_name, cost)

    async def _execute_stage_with_error_handling(
        self,
        stage_func: Any,
        episode: Episode,
        stage_name: str,
        service_name: str,
        *args: Any,
        **kwargs: Any,
    ) -> Episode:
        """Execute a stage with circuit breaker check and error context storage.

        The stage_func itself handles retries via tenacity at the service level.
        This wrapper provides circuit-breaker gating and stores structured error
        context on the episode when all retries are exhausted.

        Args:
            stage_func: Async stage runner method.
            episode: Episode to process.
            stage_name: Human-readable stage name.
            service_name: Logical service name for circuit breaker.
            *args: Additional positional args for stage_func.
            **kwargs: Additional keyword args for stage_func.

        Returns:
            Episode after stage completion.

        Raises:
            StageExecutionError: Wrapping the original exception on final failure.
        """
        # Check circuit breaker before calling
        self.circuit_breaker.check(service_name)

        try:
            result = await stage_func(episode, *args, **kwargs)
            self.circuit_breaker.record_success(service_name)
            return result
        except Exception as e:
            self.circuit_breaker.record_failure(service_name)

            # Store error context on episode
            episode.last_error = build_error_context(stage_name, e)
            episode.retry_count += 1

            if self.can_transition_to(episode.current_stage, PipelineStage.FAILED):
                self._transition(episode, PipelineStage.FAILED)
                self.storage.save_episode(episode)

            raise StageExecutionError(
                f"Stage '{stage_name}' failed: {e}",
                stage=stage_name,
                error_type=type(e).__name__,
            ) from e

    # ------------------------------------------------------------------
    # Stage execution (private)
    # ------------------------------------------------------------------

    @asynccontextmanager
    async def _stage_events(
        self,
        episode: Episode,
        display_name: str,
    ):
        """Context manager for unified stage event emission (D-6).

        Emits STAGE_STARTED on entry and STAGE_COMPLETED on normal exit.
        Also drives ProgressTracker start/complete lifecycle.

        Args:
            episode: Current episode (used in event payloads).
            display_name: Human-readable stage name (e.g. "Ideation").

        Yields:
            Control to the stage body.
        """
        stage_key = display_name.lower().replace(" ", "_")
        self.progress.start_stage(display_name)
        await self._emit_event(EventType.STAGE_STARTED, episode)
        yield
        self.progress.complete_stage(display_name)
        await self._emit_event(
            EventType.STAGE_COMPLETED, episode, data={"stage": stage_key}
        )

    async def _execute_ideation(
        self,
        episode: Episode,
        show_blueprint: ShowBlueprint,
    ) -> Episode:
        """Run IDEATION stage: generate story concept from topic."""
        if episode.current_stage != PipelineStage.IDEATION:
            episode = self._transition(episode, PipelineStage.IDEATION)
            self.storage.save_episode(episode)

        async with self._stage_events(episode, "Ideation"):
            concept = await self.ideation.generate_concept(
                topic=episode.topic,
                show_blueprint=show_blueprint,
            )
            episode.concept = concept
            self._save_checkpoint(episode, "ideation", {"concept_length": len(concept)})

        logger.info("Ideation complete for episode %s", episode.episode_id)
        return episode

    async def _execute_outlining(
        self,
        episode: Episode,
        show_blueprint: ShowBlueprint,
    ) -> Episode:
        """Run OUTLINING stage: generate story outline from concept."""
        if episode.current_stage != PipelineStage.OUTLINING:
            episode = self._transition(episode, PipelineStage.OUTLINING)
            self.storage.save_episode(episode)

        async with self._stage_events(episode, "Outlining"):
            if not episode.concept:
                raise ValueError(
                    f"Episode {episode.episode_id} has no concept for outlining"
                )
            outline = await self.outline.generate_outline(
                concept=episode.concept,
                show_blueprint=show_blueprint,
                episode_id=episode.episode_id,
            )
            episode.outline = outline
            self._save_checkpoint(
                episode, "outlining", {"beats": len(outline.story_beats)}
            )

        logger.info("Outlining complete for episode %s", episode.episode_id)
        return episode

    async def _execute_segment_generation(
        self,
        episode: Episode,
        show_blueprint: ShowBlueprint,
    ) -> Episode:
        """Run SEGMENT_GENERATION stage: expand outline into segments."""
        if episode.current_stage != PipelineStage.SEGMENT_GENERATION:
            episode = self._transition(episode, PipelineStage.SEGMENT_GENERATION)
            self.storage.save_episode(episode)

        async with self._stage_events(episode, "Segment Generation"):
            if not episode.outline:
                raise ValueError(
                    f"Episode {episode.episode_id} has no outline"
                    " for segment generation"
                )
            segments = await self.segment.generate_segments(
                outline=episode.outline,
                show_blueprint=show_blueprint,
            )
            episode.segments = segments
            episode = self._transition(episode, PipelineStage.SCRIPT_GENERATION)
            self._save_checkpoint(
                episode, "segment_generation", {"segment_count": len(segments)}
            )

        logger.info("Segment generation complete for episode %s", episode.episode_id)
        return episode

    async def _execute_script_generation(
        self,
        episode: Episode,
        show_blueprint: ShowBlueprint,
    ) -> Episode:
        """Run SCRIPT_GENERATION stage: generate scripts from segments."""
        # May already be in SCRIPT_GENERATION if resuming from that stage
        if episode.current_stage != PipelineStage.SCRIPT_GENERATION:
            episode = self._transition(episode, PipelineStage.SCRIPT_GENERATION)
            self.storage.save_episode(episode)

        async with self._stage_events(episode, "Script Generation"):
            if not episode.segments:
                raise ValueError(
                    f"Episode {episode.episode_id} has no segments"
                    " for script generation"
                )
            scripts = await self.script.generate_scripts(
                segments=episode.segments,
                show_blueprint=show_blueprint,
            )
            episode.scripts = scripts
            episode = self._transition(episode, PipelineStage.AUDIO_SYNTHESIS)
            total_blocks = sum(len(s.script_blocks) for s in scripts)
            self._save_checkpoint(
                episode,
                "script_generation",
                {"script_count": len(scripts), "total_blocks": total_blocks},
            )

        logger.info("Script generation complete for episode %s", episode.episode_id)
        return episode

    async def _execute_audio_synthesis(
        self,
        episode: Episode,
        show_blueprint: ShowBlueprint,
    ) -> Episode:
        """Run AUDIO_SYNTHESIS stage: convert scripts to audio via TTS.

        Maps each ScriptBlock to a character voice config from the
        ShowBlueprint, then synthesizes each block individually.
        """
        if episode.current_stage != PipelineStage.AUDIO_SYNTHESIS:
            episode = self._transition(episode, PipelineStage.AUDIO_SYNTHESIS)
            self.storage.save_episode(episode)

        async with self._stage_events(episode, "Audio Synthesis"):
            if not episode.scripts:
                raise ValueError(
                    f"Episode {episode.episode_id} has no scripts for audio synthesis"
                )

            # Build speaker → voice_config lookup from blueprint
            voice_map = self._build_voice_map(show_blueprint)

            # Count total blocks for substage progress
            total_blocks = sum(len(s.script_blocks) for s in episode.scripts)

            segment_audio_paths: list[str] = []
            block_counter = 0

            for script in episode.scripts:
                for block in script.script_blocks:
                    block_counter += 1
                    self.progress.report_substage_progress(
                        block_counter, total_blocks, "Synthesizing audio blocks"
                    )
                    voice_config = voice_map.get(
                        block.speaker.lower(),
                        voice_map.get("narrator", {"voice_id": "mock_narrator"}),
                    )

                    result = await asyncio.to_thread(
                        self.synthesis.synthesize_segment,
                        text=block.text,
                        character_id=block.speaker.lower(),
                        voice_config=voice_config,
                        segment_number=block_counter,
                    )
                    segment_audio_paths.append(str(result.audio_path))

            # Store paths for the mixing stage
            episode.audio_segment_paths = segment_audio_paths
            episode = self._transition(episode, PipelineStage.AUDIO_MIXING)
            self._save_checkpoint(
                episode,
                "audio_synthesis",
                {"audio_segment_count": len(segment_audio_paths)},
            )

        logger.info(
            "Audio synthesis complete for episode %s (%d blocks)",
            episode.episode_id,
            block_counter,
        )
        return episode

    async def _execute_audio_mixing(
        self,
        episode: Episode,
        show_blueprint: ShowBlueprint,
    ) -> Episode:
        """Run AUDIO_MIXING stage: mix segments into final audio file.

        Args:
            episode: Episode with audio_segment_paths populated
            show_blueprint: Unused; kept for runner signature consistency
        """
        if episode.current_stage != PipelineStage.AUDIO_MIXING:
            episode = self._transition(episode, PipelineStage.AUDIO_MIXING)
            self.storage.save_episode(episode)

        async with self._stage_events(episode, "Audio Mixing"):
            # Collect audio segment paths
            segment_paths: list[str] = episode.audio_segment_paths
            if not segment_paths:
                raise ValueError(
                    f"Episode {episode.episode_id} has no audio segments for mixing"
                )

            # Mix all segments (sync I/O — offload to thread)
            mixed_audio = await asyncio.to_thread(
                self.mixer.mix_segments, segment_paths
            )

            # Determine output path
            episode_dir = self.storage.get_episode_path(
                episode.show_id, episode.episode_id
            )
            output_path = episode_dir / "final_audio.mp3"
            await asyncio.to_thread(mixed_audio.export, str(output_path), format="mp3")

            episode.audio_path = str(output_path)
            episode = self._transition(episode, PipelineStage.COMPLETE)
            self._save_checkpoint(
                episode,
                "audio_mixing",
                {"audio_path": str(output_path)},
            )

        logger.info("Audio mixing complete for episode %s", episode.episode_id)
        return episode

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def _transition(
        self,
        episode: Episode,
        target: PipelineStage,
    ) -> Episode:
        """Transition episode to a new stage with validation.

        Args:
            episode: Episode to transition
            target: Target pipeline stage

        Returns:
            Episode with updated current_stage and updated_at

        Raises:
            ValueError: If the transition is not valid
        """
        if not self.can_transition_to(episode.current_stage, target):
            raise ValueError(
                f"Invalid transition: {episode.current_stage.value} → {target.value} "
                f"for episode {episode.episode_id}"
            )
        episode.current_stage = target
        episode.updated_at = datetime.now(UTC)
        return episode

    def _build_voice_map(
        self,
        show_blueprint: ShowBlueprint,
    ) -> dict[str, dict[str, Any]]:
        """Build speaker-name → voice_config mapping from blueprint.

        Includes narrator, protagonist, and all supporting characters.

        Returns:
            Mapping of lowercase speaker name to voice configuration dict.
        """
        voice_map: dict[str, dict[str, Any]] = {}

        # Narrator from show config
        voice_map["narrator"] = dict(show_blueprint.show.narrator_voice_config)

        # Protagonist
        prot_name = show_blueprint.protagonist.name.lower()
        voice_map[prot_name] = dict(show_blueprint.protagonist.voice_config)
        # Also store first-name shortcut (e.g. "Oliver the Inventor" → "oliver")
        first_name = prot_name.split()[0]
        voice_map[first_name] = dict(show_blueprint.protagonist.voice_config)

        # Supporting characters (skip first-name shortcut if it would
        # collide with an existing entry — protagonist takes priority)
        for char in show_blueprint.characters:
            char_name = char.name.lower()
            voice_map[char_name] = dict(char.voice_config)
            char_first = char_name.split()[0]
            if char_first not in voice_map:
                voice_map[char_first] = dict(char.voice_config)
            elif char_first != char_name:
                logger.debug(
                    "Skipping first-name shortcut '%s' for character '%s' "
                    "(already mapped to another speaker)",
                    char_first,
                    char.name,
                )

        return voice_map

    async def _finalize_episode(
        self,
        episode: Episode,
        show_blueprint: ShowBlueprint,
    ) -> None:
        """Update Show Blueprint after episode completion.

        Adds the episode's topic as a covered concept.
        """
        try:
            self.show_manager.add_concept(
                show_id=episode.show_id,
                concept=episode.topic,
                episode_id=episode.episode_id,
            )
            logger.info(
                "Added concept '%s' to show %s",
                episode.topic,
                episode.show_id,
            )
        except Exception:
            logger.warning(
                "Failed to update concepts for show %s after episode %s",
                episode.show_id,
                episode.episode_id,
                exc_info=True,
            )

        try:
            self.show_manager.link_episode(
                show_id=episode.show_id,
                episode_id=episode.episode_id,
            )
            logger.info(
                "Linked episode %s to show %s",
                episode.episode_id,
                episode.show_id,
            )
        except Exception:
            logger.warning(
                "Failed to link episode %s to show %s",
                episode.episode_id,
                episode.show_id,
                exc_info=True,
            )

    @staticmethod
    def _generate_episode_id(topic: str) -> str:
        """Generate a URL-safe episode ID from the topic."""
        slug = re.sub(r"[^a-z0-9]+", "_", topic.lower()).strip("_")[:40]
        ts = datetime.now(UTC).strftime("%Y%m%d%H%M%S")
        short_uid = uuid.uuid4().hex[:8]
        return f"ep_{slug}_{ts}_{short_uid}"

    @staticmethod
    def _generate_title(topic: str) -> str:
        """Generate a human-readable title from the topic."""
        return topic.strip().title()

    async def _emit_event(
        self,
        event_type: EventType,
        episode: Episode,
        data: dict[str, Any] | None = None,
    ) -> None:
        """Emit a pipeline event if a callback is registered."""
        if self.event_callback is None:
            return
        event = PipelineEvent(
            event_type=event_type,
            episode_id=episode.episode_id,
            show_id=episode.show_id,
            stage=episode.current_stage,
            data=data or {},
        )
        result = self.event_callback(event)
        if inspect.isawaitable(result):
            await result
