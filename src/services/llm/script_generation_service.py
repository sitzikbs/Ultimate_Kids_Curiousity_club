"""Script generation service for converting segments into narration and dialogue."""

import logging
from time import time

from models import Script, ScriptBlock, ShowBlueprint, StorySegment
from modules.prompts.enhancer import PromptEnhancer
from services.llm.base import BaseLLMProvider
from services.llm.cost_tracker import CostTracker
from services.llm.parsing import LLMResponseParser

logger = logging.getLogger(__name__)


class ScriptGenerationService:
    """Service for generating scripts with narration and dialogue from segments."""

    # Words per minute for duration estimation
    WORDS_PER_MINUTE = 150

    def __init__(
        self,
        provider: BaseLLMProvider,
        enhancer: PromptEnhancer | None = None,
        cost_tracker: CostTracker | None = None,
    ) -> None:
        """Initialize script generation service.

        Args:
            provider: LLM provider to use for generation
            enhancer: Prompt enhancer for injecting Show Blueprint context.
                     If None, creates a new instance.
            cost_tracker: Cost tracker for logging API calls.
                         If None, no cost tracking is performed.
        """
        self.provider = provider
        self.enhancer = enhancer or PromptEnhancer()
        self.cost_tracker = cost_tracker
        self.parser = LLMResponseParser()

    async def generate_scripts(
        self,
        segments: list[StorySegment],
        show_blueprint: ShowBlueprint,
        max_tokens: int = 4000,
        temperature: float = 0.7,
        max_retries: int = 3,
    ) -> list[Script]:
        """Generate scripts with narration and dialogue from segments.

        This method:
        1. Enhances the prompt with Show Blueprint context
        2. Generates narration for scene setting and transitions
        3. Generates character dialogue with speaker tags
        4. Includes protagonist catchphrases appropriately
        5. Adds emotion/tone hints for TTS
        6. Estimates duration for each script block

        Args:
            segments: List of story segments
            show_blueprint: Complete show blueprint with context
            max_tokens: Maximum tokens for generation
            temperature: Sampling temperature
            max_retries: Maximum number of retries for validation failures

        Returns:
            List of Script objects with narration and dialogue

        Raises:
            ValueError: If segments are invalid or generation fails
            Exception: If generation fails after retries
        """
        if not segments:
            raise ValueError("Segments list cannot be empty")

        # Enhance prompt with Show Blueprint context
        enhanced_prompt = self.enhancer.enhance_script_prompt(segments, show_blueprint)

        # Track time and tokens
        start_time = time()

        # Generate scripts with retry logic
        for attempt in range(max_retries):
            try:
                # Count prompt tokens
                prompt_tokens = self.provider.count_tokens(enhanced_prompt)

                # Generate scripts using LLM
                response = await self.provider.generate(
                    prompt=enhanced_prompt,
                    max_tokens=max_tokens,
                    temperature=temperature,
                )

                # Count completion tokens
                completion_tokens = self.provider.count_tokens(response)

                # Parse and validate response as ScriptBlock list
                script_blocks = self.parser.parse_and_validate(response, ScriptBlock)

                # Ensure we got a list
                if not isinstance(script_blocks, list):
                    script_blocks = [script_blocks]

                # Estimate duration for blocks that don't have it
                script_blocks = self._estimate_durations(script_blocks)

                # Organize blocks into scripts by segment
                scripts = self._organize_into_scripts(script_blocks, segments)

                # Validate scripts
                self._validate_scripts(scripts, segments)

                # Log cost if tracker available
                if self.cost_tracker:
                    duration = time() - start_time
                    cost = self.provider.get_cost(prompt_tokens, completion_tokens)
                    self.cost_tracker.log_call(
                        stage="script",
                        prompt_tokens=prompt_tokens,
                        completion_tokens=completion_tokens,
                        cost=cost,
                        duration=duration,
                        provider=self.provider.__class__.__name__,
                        model=getattr(self.provider, "model", "unknown"),
                    )

                logger.info(
                    f"Generated {len(scripts)} scripts from {len(segments)} segments"
                )
                return scripts

            except ValueError as e:
                if attempt < max_retries - 1:
                    logger.warning(
                        f"Script generation attempt {attempt + 1} failed: "
                        f"{e}. Retrying..."
                    )
                    # Adjust prompt for retry with error feedback
                    prev_response = response if "response" in locals() else ""
                    enhanced_prompt = self.parser.create_retry_prompt(
                        enhanced_prompt, str(e), prev_response
                    )
                    # Reduce temperature for more deterministic output
                    temperature = max(0.3, temperature - 0.2)
                else:
                    logger.error(
                        f"Script generation failed after {max_retries} "
                        f"attempts: {e}"
                    )
                    raise

        raise ValueError(f"Failed to generate scripts after {max_retries} attempts")

    def _estimate_durations(
        self, script_blocks: list[ScriptBlock]
    ) -> list[ScriptBlock]:
        """Estimate duration for script blocks that don't have it.

        Args:
            script_blocks: List of script blocks

        Returns:
            List of script blocks with duration estimates
        """
        for block in script_blocks:
            if block.duration_estimate is None or block.duration_estimate <= 0:
                # Estimate based on word count and words per minute
                word_count = len(block.text.split())
                # Convert to seconds
                block.duration_estimate = (word_count / self.WORDS_PER_MINUTE) * 60

        return script_blocks

    def _organize_into_scripts(
        self, script_blocks: list[ScriptBlock], segments: list[StorySegment]
    ) -> list[Script]:
        """Organize script blocks into scripts by segment.

        Args:
            script_blocks: List of all script blocks
            segments: List of story segments

        Returns:
            List of Script objects, one per segment
        """
        # Create one script per segment
        scripts = []
        blocks_per_segment = len(script_blocks) // len(segments)

        # If blocks don't divide evenly, distribute extras to early segments
        remaining_blocks = len(script_blocks) % len(segments)

        current_index = 0
        for i, segment in enumerate(segments, 1):
            # Calculate how many blocks for this segment
            num_blocks = blocks_per_segment + (1 if i <= remaining_blocks else 0)

            # Extract blocks for this segment
            segment_blocks = script_blocks[current_index : current_index + num_blocks]
            current_index += num_blocks

            # Create script
            script = Script(
                segment_number=segment.segment_number,
                script_blocks=segment_blocks,
            )
            scripts.append(script)

        return scripts

    def _validate_scripts(
        self, scripts: list[Script], segments: list[StorySegment]
    ) -> None:
        """Validate generated scripts meet requirements.

        Args:
            scripts: List of scripts to validate
            segments: Original segments

        Raises:
            ValueError: If scripts don't meet requirements
        """
        if not scripts:
            raise ValueError("No scripts generated")

        if len(scripts) != len(segments):
            raise ValueError(
                f"Expected {len(segments)} scripts, got {len(scripts)}"
            )

        # Validate each script
        for i, script in enumerate(scripts, 1):
            if not script.script_blocks:
                raise ValueError(f"Script {i} has no script blocks")

            # Check that at least one narrator block exists
            narrator_blocks = [
                b for b in script.script_blocks
                if b.speaker.upper() in ("NARRATOR", "NARRATION")
            ]

            if not narrator_blocks:
                logger.warning(f"Script {i} has no narrator blocks")

            # Validate each block
            for j, block in enumerate(script.script_blocks, 1):
                if not block.speaker:
                    raise ValueError(f"Script {i}, block {j} missing speaker")
                if not block.text:
                    raise ValueError(f"Script {i}, block {j} missing text")
                if not block.speaker_voice_id:
                    raise ValueError(f"Script {i}, block {j} missing speaker_voice_id")
                if block.duration_estimate is None or block.duration_estimate <= 0:
                    raise ValueError(
                        f"Script {i}, block {j} has invalid duration estimate"
                    )
