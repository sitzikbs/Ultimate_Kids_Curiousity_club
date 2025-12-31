"""Pipeline orchestrator for episode production workflow."""

import logging
from datetime import UTC, datetime

from models import Episode, PipelineStage, ShowBlueprint, StoryOutline
from modules.episode_storage import EpisodeStorage
from modules.prompts.enhancer import PromptEnhancer
from modules.show_blueprint_manager import ShowBlueprintManager
from services.llm.ideation_service import IdeationService
from services.llm.outline_service import OutlineService
from services.llm.script_generation_service import ScriptGenerationService
from services.llm.segment_generation_service import SegmentGenerationService

logger = logging.getLogger(__name__)


class PipelineOrchestrator:
    """Orchestrates episode production pipeline through multiple stages.

    The pipeline follows these stages:
    PENDING → IDEATION → OUTLINING → AWAITING_APPROVAL →
    SEGMENT_GENERATION → SCRIPT_GENERATION → AUDIO_SYNTHESIS →
    AUDIO_MIXING → COMPLETE

    The pipeline pauses at AWAITING_APPROVAL for human review.
    """

    def __init__(
        self,
        prompt_enhancer: PromptEnhancer,
        ideation_service: IdeationService,
        outline_service: OutlineService,
        segment_service: SegmentGenerationService,
        script_service: ScriptGenerationService,
        show_blueprint_manager: ShowBlueprintManager,
        episode_storage: EpisodeStorage,
    ):
        """Initialize pipeline orchestrator with required services.

        Args:
            prompt_enhancer: Service for enhancing prompts with context
            ideation_service: Service for generating story concepts
            outline_service: Service for generating story outlines
            segment_service: Service for generating story segments
            script_service: Service for generating scripts
            show_blueprint_manager: Manager for Show Blueprint operations
            episode_storage: Storage for episode persistence
        """
        self.prompt_enhancer = prompt_enhancer
        self.ideation = ideation_service
        self.outline = outline_service
        self.segment = segment_service
        self.script = script_service
        self.show_manager = show_blueprint_manager
        self.storage = episode_storage

    def can_transition_to(
        self, episode: Episode, target_stage: PipelineStage
    ) -> bool:
        """Validate if state transition is allowed.

        Args:
            episode: Episode to check
            target_stage: Target pipeline stage

        Returns:
            True if transition is valid, False otherwise
        """
        valid_transitions = {
            PipelineStage.PENDING: [PipelineStage.IDEATION],
            PipelineStage.IDEATION: [PipelineStage.OUTLINING],
            PipelineStage.OUTLINING: [PipelineStage.AWAITING_APPROVAL],
            PipelineStage.AWAITING_APPROVAL: [
                PipelineStage.SEGMENT_GENERATION,
                PipelineStage.REJECTED,
            ],
            PipelineStage.SEGMENT_GENERATION: [PipelineStage.SCRIPT_GENERATION],
            PipelineStage.SCRIPT_GENERATION: [PipelineStage.AUDIO_SYNTHESIS],
            PipelineStage.AUDIO_SYNTHESIS: [PipelineStage.AUDIO_MIXING],
            PipelineStage.AUDIO_MIXING: [PipelineStage.COMPLETE],
            PipelineStage.REJECTED: [PipelineStage.IDEATION],
            PipelineStage.FAILED: [],
            PipelineStage.COMPLETE: [],
        }
        return target_stage in valid_transitions.get(episode.current_stage, [])

    async def execute_stage(self, episode: Episode) -> Episode:
        """Execute current stage and transition to next.

        Args:
            episode: Episode at current stage

        Returns:
            Updated episode at next stage

        Raises:
            ValueError: If episode is in invalid state or awaiting approval
        """
        if episode.current_stage == PipelineStage.PENDING:
            return await self._execute_ideation(episode)
        elif episode.current_stage == PipelineStage.IDEATION:
            return await self._execute_outlining(episode)
        elif episode.current_stage == PipelineStage.AWAITING_APPROVAL:
            raise ValueError(
                "Episode awaiting approval - call submit_approval() first"
            )
        elif episode.current_stage == PipelineStage.SEGMENT_GENERATION:
            return await self._execute_segment_generation(episode)
        elif episode.current_stage == PipelineStage.SCRIPT_GENERATION:
            return await self._execute_script_generation(episode)
        elif episode.current_stage == PipelineStage.AUDIO_SYNTHESIS:
            raise ValueError(
                "AUDIO_SYNTHESIS stage not yet implemented (WP3/WP4)"
            )
        elif episode.current_stage == PipelineStage.AUDIO_MIXING:
            raise ValueError("AUDIO_MIXING stage not yet implemented (WP5)")
        elif episode.current_stage == PipelineStage.COMPLETE:
            raise ValueError("Episode already complete")
        elif episode.current_stage == PipelineStage.REJECTED:
            raise ValueError(
                "Episode rejected - restart from IDEATION or edit outline"
            )
        elif episode.current_stage == PipelineStage.FAILED:
            raise ValueError("Episode in failed state - cannot continue")
        else:
            raise ValueError(f"Unknown stage: {episode.current_stage}")

    async def generate_episode(
        self,
        show_id: str,
        topic: str,
        duration_minutes: int = 15,
    ) -> Episode:
        """Execute full pipeline for new episode up to approval gate.

        Creates a new episode and executes stages until AWAITING_APPROVAL.

        Args:
            show_id: Show identifier
            topic: Episode topic
            duration_minutes: Target duration in minutes

        Returns:
            Episode at AWAITING_APPROVAL stage

        Raises:
            FileNotFoundError: If show not found
            ValueError: If generation fails
        """
        # Load Show Blueprint
        show_blueprint = self.show_manager.load_show(show_id)

        # Create episode with generated ID
        episode_id = self._generate_episode_id(topic)
        episode = Episode(
            episode_id=episode_id,
            show_id=show_id,
            title=self._generate_title(topic),
            topic=topic,
            current_stage=PipelineStage.PENDING,
        )

        # Save initial state
        self.storage.save_episode(episode)

        logger.info(
            f"Starting episode generation: {episode_id} for show {show_id}"
        )

        # Execute pipeline stages up to approval gate
        episode = await self._execute_ideation(episode, show_blueprint)
        episode = await self._execute_outlining(episode, show_blueprint)

        logger.info(f"Episode {episode_id} awaiting approval")

        return episode

    async def continue_after_approval(self, episode: Episode) -> Episode:
        """Continue pipeline after approval through remaining stages.

        Executes stages from SEGMENT_GENERATION onwards. This is for
        future use when audio stages are implemented.

        Args:
            episode: Episode at SEGMENT_GENERATION or later stage

        Returns:
            Updated episode

        Raises:
            ValueError: If episode not in correct stage
        """
        if episode.current_stage not in [
            PipelineStage.SEGMENT_GENERATION,
            PipelineStage.SCRIPT_GENERATION,
        ]:
            raise ValueError(
                f"Cannot continue from stage {episode.current_stage}"
            )

        show_blueprint = self.show_manager.load_show(episode.show_id)

        # Execute remaining stages
        if episode.current_stage == PipelineStage.SEGMENT_GENERATION:
            episode = await self._execute_segment_generation(
                episode, show_blueprint
            )

        if episode.current_stage == PipelineStage.SCRIPT_GENERATION:
            episode = await self._execute_script_generation(
                episode, show_blueprint
            )

        # Audio stages would go here when implemented
        # For now, we stop after script generation

        return episode

    async def _execute_ideation(
        self, episode: Episode, show_blueprint: ShowBlueprint | None = None
    ) -> Episode:
        """Execute ideation stage with Show Blueprint context.

        Args:
            episode: Episode in PENDING stage
            show_blueprint: Show blueprint (loaded if not provided)

        Returns:
            Episode at IDEATION stage with concept generated
        """
        if episode.current_stage != PipelineStage.PENDING:
            raise ValueError(
                f"Cannot execute ideation from stage {episode.current_stage}"
            )

        if show_blueprint is None:
            show_blueprint = self.show_manager.load_show(episode.show_id)

        logger.info(f"Executing ideation for episode {episode.episode_id}")

        # Generate concept
        concept = await self.ideation.generate_concept(
            topic=episode.topic,
            show_blueprint=show_blueprint,
        )

        # Update episode
        episode.current_stage = PipelineStage.IDEATION
        episode.updated_at = datetime.now(UTC)

        # Store concept in approval_feedback field temporarily
        # (until we add a proper concept field to Episode model)
        if not episode.approval_feedback:
            episode.approval_feedback = concept

        self.storage.save_episode(episode)

        logger.info(f"Ideation complete for episode {episode.episode_id}")

        return episode

    async def _execute_outlining(
        self, episode: Episode, show_blueprint: ShowBlueprint | None = None
    ) -> Episode:
        """Execute outlining stage with Show Blueprint context.

        Args:
            episode: Episode in IDEATION stage
            show_blueprint: Show blueprint (loaded if not provided)

        Returns:
            Episode at AWAITING_APPROVAL stage with outline generated
        """
        if episode.current_stage != PipelineStage.IDEATION:
            raise ValueError(
                f"Cannot execute outlining from stage {episode.current_stage}"
            )

        if show_blueprint is None:
            show_blueprint = self.show_manager.load_show(episode.show_id)

        logger.info(f"Executing outlining for episode {episode.episode_id}")

        # Get concept from approval_feedback field
        concept = episode.approval_feedback or episode.topic

        # Generate outline
        outline = await self.outline.generate_outline(
            concept=concept,
            show_blueprint=show_blueprint,
            episode_id=episode.episode_id,
        )

        # Update episode
        episode.outline = outline
        episode.current_stage = PipelineStage.AWAITING_APPROVAL
        episode.approval_status = "pending"
        episode.updated_at = datetime.now(UTC)

        self.storage.save_episode(episode)
        self.storage.save_checkpoint(episode, PipelineStage.OUTLINING)

        logger.info(
            f"Outlining complete for episode {episode.episode_id}, "
            f"awaiting approval"
        )

        return episode

    async def _execute_segment_generation(
        self, episode: Episode, show_blueprint: ShowBlueprint | None = None
    ) -> Episode:
        """Execute segment generation stage with Show Blueprint context.

        Args:
            episode: Episode in SEGMENT_GENERATION stage
            show_blueprint: Show blueprint (loaded if not provided)

        Returns:
            Episode at SCRIPT_GENERATION stage with segments generated
        """
        if episode.current_stage != PipelineStage.SEGMENT_GENERATION:
            raise ValueError(
                f"Cannot execute segment generation from stage "
                f"{episode.current_stage}"
            )

        if show_blueprint is None:
            show_blueprint = self.show_manager.load_show(episode.show_id)

        if not episode.outline:
            raise ValueError("Episode has no outline for segment generation")

        logger.info(
            f"Executing segment generation for episode {episode.episode_id}"
        )

        # Generate segments
        segments = await self.segment.generate_segments(
            outline=episode.outline,
            show_blueprint=show_blueprint,
        )

        # Update episode
        episode.segments = segments
        episode.current_stage = PipelineStage.SCRIPT_GENERATION
        episode.updated_at = datetime.now(UTC)

        self.storage.save_episode(episode)
        self.storage.save_checkpoint(episode, PipelineStage.SEGMENT_GENERATION)

        logger.info(
            f"Segment generation complete for episode {episode.episode_id}"
        )

        return episode

    async def _execute_script_generation(
        self, episode: Episode, show_blueprint: ShowBlueprint | None = None
    ) -> Episode:
        """Execute script generation stage with Show Blueprint context.

        Args:
            episode: Episode in SCRIPT_GENERATION stage
            show_blueprint: Show blueprint (loaded if not provided)

        Returns:
            Episode at AUDIO_SYNTHESIS stage with scripts generated
        """
        if episode.current_stage != PipelineStage.SCRIPT_GENERATION:
            raise ValueError(
                f"Cannot execute script generation from stage "
                f"{episode.current_stage}"
            )

        if show_blueprint is None:
            show_blueprint = self.show_manager.load_show(episode.show_id)

        if not episode.segments:
            raise ValueError("Episode has no segments for script generation")

        logger.info(
            f"Executing script generation for episode {episode.episode_id}"
        )

        # Generate scripts
        scripts = await self.script.generate_scripts(
            segments=episode.segments,
            show_blueprint=show_blueprint,
        )

        # Update episode
        episode.scripts = scripts
        episode.current_stage = PipelineStage.AUDIO_SYNTHESIS
        episode.updated_at = datetime.now(UTC)

        self.storage.save_episode(episode)
        self.storage.save_checkpoint(episode, PipelineStage.SCRIPT_GENERATION)

        logger.info(
            f"Script generation complete for episode {episode.episode_id}"
        )

        return episode

    async def _finalize_episode(self, episode: Episode) -> Episode:
        """Update Show Blueprint with completed episode.

        This should be called when the episode reaches COMPLETE stage.

        Args:
            episode: Completed episode

        Returns:
            Updated episode
        """
        show_blueprint = self.show_manager.load_show(episode.show_id)

        # Extract educational objectives from outline
        if episode.outline:
            concept = episode.outline.educational_concept
            self.show_manager.add_concept(
                show_id=episode.show_id,
                concept=concept,
                episode_id=episode.episode_id,
            )

        logger.info(f"Episode {episode.episode_id} finalized and linked to show")

        return episode

    def _generate_episode_id(self, topic: str) -> str:
        """Generate episode ID from topic.

        Args:
            topic: Episode topic

        Returns:
            Episode ID (sanitized topic + timestamp)
        """
        # Sanitize topic for use in ID
        sanitized = "".join(
            c if c.isalnum() or c in "-_" else "_" for c in topic.lower()
        )
        # Truncate and add timestamp
        truncated = sanitized[:30]
        timestamp = datetime.now(UTC).strftime("%Y%m%d_%H%M%S")
        return f"{truncated}_{timestamp}"

    def _generate_title(self, topic: str) -> str:
        """Generate episode title from topic.

        Args:
            topic: Episode topic

        Returns:
            Episode title
        """
        # Capitalize first letter of each word
        return " ".join(word.capitalize() for word in topic.split())
