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
from datetime import UTC, datetime
from typing import Any, NoReturn

from models.episode import Episode, PipelineStage
from models.show import ShowBlueprint
from modules.episode_storage import EpisodeStorage
from modules.prompts.enhancer import PromptEnhancer
from modules.show_blueprint_manager import ShowBlueprintManager
from orchestrator.events import EventCallback, EventType, PipelineEvent
from services.audio.mixer import AudioMixer
from services.llm.ideation_service import IdeationService
from services.llm.outline_service import OutlineService
from services.llm.script_generation_service import ScriptGenerationService
from services.llm.segment_generation_service import SegmentGenerationService
from services.tts.synthesis_service import AudioSynthesisService
from utils.errors import ApprovalRequiredError

logger = logging.getLogger(__name__)

# Valid state transitions map
VALID_TRANSITIONS: dict[PipelineStage, set[PipelineStage]] = {
    PipelineStage.PENDING: {PipelineStage.IDEATION},
    PipelineStage.IDEATION: {PipelineStage.OUTLINING, PipelineStage.FAILED},
    PipelineStage.OUTLINING: {PipelineStage.AWAITING_APPROVAL, PipelineStage.FAILED},
    PipelineStage.AWAITING_APPROVAL: {
        PipelineStage.APPROVED,
        PipelineStage.REJECTED,
        PipelineStage.FAILED,
    },
    PipelineStage.APPROVED: {
        PipelineStage.SEGMENT_GENERATION,
        PipelineStage.FAILED,
    },
    PipelineStage.SEGMENT_GENERATION: {
        PipelineStage.SCRIPT_GENERATION,
        PipelineStage.FAILED,
    },
    PipelineStage.SCRIPT_GENERATION: {
        PipelineStage.AUDIO_SYNTHESIS,
        PipelineStage.FAILED,
    },
    PipelineStage.AUDIO_SYNTHESIS: {
        PipelineStage.AUDIO_MIXING,
        PipelineStage.FAILED,
    },
    PipelineStage.AUDIO_MIXING: {PipelineStage.COMPLETE, PipelineStage.FAILED},
    PipelineStage.REJECTED: {PipelineStage.IDEATION},
    PipelineStage.COMPLETE: set(),
    PipelineStage.FAILED: {PipelineStage.PENDING},
}


class PipelineOrchestrator:
    """Orchestrates the episode generation pipeline through 8 stages.

    Coordinates all generation services (LLM, TTS, audio mixing) with
    Show Blueprint context injection and a human approval gate.
    """

    def __init__(
        self,
        prompt_enhancer: PromptEnhancer,
        ideation_service: IdeationService,
        outline_service: OutlineService,
        segment_service: SegmentGenerationService,
        script_service: ScriptGenerationService,
        synthesis_service: AudioSynthesisService,
        audio_mixer: AudioMixer,
        show_blueprint_manager: ShowBlueprintManager,
        episode_storage: EpisodeStorage,
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
        # NOTE: prompt_enhancer stored for future use
        # (WP6b: prompt enhancement integration)
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

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    async def generate_episode(
        self,
        show_id: str,
        topic: str,
        title: str | None = None,
    ) -> NoReturn:
        """Start generating a new episode.

        Creates the episode, runs IDEATION → OUTLINING, then pauses at
        AWAITING_APPROVAL for human review.

        Args:
            show_id: Identifier of the show
            topic: Topic / educational concept for the episode
            title: Optional explicit title; auto-generated if omitted

        Raises:
            FileNotFoundError: If show_id does not exist
            ApprovalRequiredError: Always raised when the pipeline reaches
                the approval gate. Use episode_id/show_id from the exception
                to present the approval UI and later call resume_episode().
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

        raise ApprovalRequiredError(
            f"Episode {episode.episode_id} awaiting approval",
            episode_id=episode.episode_id,
            show_id=show_id,
        )

    async def resume_episode(
        self,
        show_id: str,
        episode_id: str,
    ) -> Episode:
        """Resume an approved episode through remaining stages.

        Continues the pipeline from the episode's current stage to COMPLETE.

        Args:
            show_id: Show identifier
            episode_id: Episode identifier

        Returns:
            Completed Episode

        Raises:
            ValueError: If episode is not in a resumable stage
        """
        episode = self.storage.load_episode(show_id, episode_id)
        show_blueprint = self.show_manager.load_show(show_id)

        # Ordered post-approval stage pipeline — runners are sliced from
        # the episode's current position so adding a stage requires only
        # one entry here.  Multiple stages can share a runner (e.g.
        # APPROVED and SEGMENT_GENERATION both enter segment generation).
        post_approval_pipeline: list[
            tuple[set[PipelineStage], Any]
        ] = [
            (
                {PipelineStage.APPROVED, PipelineStage.SEGMENT_GENERATION},
                self._execute_segment_generation,
            ),
            (
                {PipelineStage.SCRIPT_GENERATION},
                self._execute_script_generation,
            ),
            (
                {PipelineStage.AUDIO_SYNTHESIS},
                self._execute_audio_synthesis,
            ),
            (
                {PipelineStage.AUDIO_MIXING},
                self._execute_audio_mixing,
            ),
        ]

        # Find where the episode's current stage sits in the pipeline
        try:
            start_idx = next(
                i
                for i, (stages, _) in enumerate(post_approval_pipeline)
                if episode.current_stage in stages
            )
        except StopIteration:
            raise ValueError(
                f"Episode {episode_id} is not in a resumable stage "
                f"(current: {episode.current_stage.value})"
            )

        runners = [runner for _, runner in post_approval_pipeline[start_idx:]]

        try:
            for runner in runners:
                episode = await runner(episode, show_blueprint)
        except Exception:
            if self.can_transition_to(episode.current_stage, PipelineStage.FAILED):
                self._transition(episode, PipelineStage.FAILED)
                self.storage.save_episode(episode)
            raise

        # Finalize — update Show Blueprint concepts
        self._finalize_episode(episode, show_blueprint)

        return episode

    async def retry_failed_episode(
        self,
        show_id: str,
        episode_id: str,
    ) -> NoReturn:
        """Reset a FAILED episode to PENDING and re-run from the start.

        Transitions FAILED → PENDING, then delegates to ``generate_episode``
        which will run IDEATION → OUTLINING → AWAITING_APPROVAL.

        Args:
            show_id: Show identifier
            episode_id: Episode identifier

        Raises:
            ValueError: If episode is not in FAILED stage
            ApprovalRequiredError: Always raised at the approval gate
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

        raise ApprovalRequiredError(
            f"Episode {episode.episode_id} awaiting approval (retry)",
            episode_id=episode.episode_id,
            show_id=show_id,
        )

    async def retry_rejected_episode(
        self,
        show_id: str,
        episode_id: str,
    ) -> NoReturn:
        """Re-run a REJECTED episode from IDEATION with fresh content.

        Transitions REJECTED → IDEATION and re-generates concept + outline,
        pausing again at AWAITING_APPROVAL.

        Args:
            show_id: Show identifier
            episode_id: Episode identifier

        Raises:
            ValueError: If episode is not in REJECTED stage
            ApprovalRequiredError: Always raised at the approval gate
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

        raise ApprovalRequiredError(
            f"Episode {episode.episode_id} awaiting approval (retry after rejection)",
            episode_id=episode.episode_id,
            show_id=show_id,
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

        Args:
            current: Current pipeline stage
            target: Desired target stage

        Returns:
            True if the transition is allowed
        """
        return target in VALID_TRANSITIONS.get(current, set())

    # ------------------------------------------------------------------
    # Stage execution (private)
    # ------------------------------------------------------------------

    async def _execute_ideation(
        self,
        episode: Episode,
        show_blueprint: ShowBlueprint,
    ) -> Episode:
        """Run IDEATION stage: generate story concept from topic."""
        if episode.current_stage != PipelineStage.IDEATION:
            episode = self._transition(episode, PipelineStage.IDEATION)
            self.storage.save_episode(episode)
        await self._emit_event(EventType.STAGE_STARTED, episode)

        concept = await self.ideation.generate_concept(
            topic=episode.topic,
            show_blueprint=show_blueprint,
        )

        episode.concept = concept
        self.storage.save_episode(episode)
        await self._emit_event(
            EventType.STAGE_COMPLETED, episode, data={"stage": "ideation"}
        )

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
        await self._emit_event(EventType.STAGE_STARTED, episode)

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
        self.storage.save_episode(episode)
        await self._emit_event(
            EventType.STAGE_COMPLETED, episode, data={"stage": "outlining"}
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
        await self._emit_event(EventType.STAGE_STARTED, episode)

        if not episode.outline:
            raise ValueError(
                f"Episode {episode.episode_id} has no outline for segment generation"
            )

        segments = await self.segment.generate_segments(
            outline=episode.outline,
            show_blueprint=show_blueprint,
        )

        episode.segments = segments
        episode = self._transition(episode, PipelineStage.SCRIPT_GENERATION)
        self.storage.save_episode(episode)
        await self._emit_event(
            EventType.STAGE_COMPLETED, episode, data={"stage": "segment_generation"}
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
        await self._emit_event(EventType.STAGE_STARTED, episode)

        if not episode.segments:
            raise ValueError(
                f"Episode {episode.episode_id} has no segments for script generation"
            )

        scripts = await self.script.generate_scripts(
            segments=episode.segments,
            show_blueprint=show_blueprint,
        )

        episode.scripts = scripts
        episode = self._transition(episode, PipelineStage.AUDIO_SYNTHESIS)
        self.storage.save_episode(episode)
        await self._emit_event(
            EventType.STAGE_COMPLETED, episode, data={"stage": "script_generation"}
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
        await self._emit_event(EventType.STAGE_STARTED, episode)

        if not episode.scripts:
            raise ValueError(
                f"Episode {episode.episode_id} has no scripts for audio synthesis"
            )

        # Build speaker → voice_config lookup from blueprint
        voice_map = self._build_voice_map(show_blueprint)

        segment_audio_paths: list[str] = []
        block_counter = 0

        for script in episode.scripts:
            for block in script.script_blocks:
                block_counter += 1
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

        # Store paths for the mixing stage (proper model field for persistence)
        episode.audio_segment_paths = segment_audio_paths
        episode = self._transition(episode, PipelineStage.AUDIO_MIXING)
        self.storage.save_episode(episode)
        await self._emit_event(
            EventType.STAGE_COMPLETED, episode, data={"stage": "audio_synthesis"}
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
        await self._emit_event(EventType.STAGE_STARTED, episode)

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
        episode_dir = self.storage.get_episode_path(episode.show_id, episode.episode_id)
        output_path = episode_dir / "final_audio.mp3"
        await asyncio.to_thread(
            mixed_audio.export, str(output_path), format="mp3"
        )

        episode.audio_path = str(output_path)
        episode = self._transition(episode, PipelineStage.COMPLETE)
        self.storage.save_episode(episode)
        await self._emit_event(
            EventType.STAGE_COMPLETED, episode, data={"stage": "audio_mixing"}
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

    def _finalize_episode(
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
