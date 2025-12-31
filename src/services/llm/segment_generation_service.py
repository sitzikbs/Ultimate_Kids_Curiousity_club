"""Segment generation service for expanding story beats into detailed segments."""

import logging
from time import time

from models import ShowBlueprint, StoryOutline, StorySegment
from modules.prompts.enhancer import PromptEnhancer
from services.llm.base import BaseLLMProvider
from services.llm.cost_tracker import CostTracker
from services.llm.parsing import LLMResponseParser

logger = logging.getLogger(__name__)


class SegmentGenerationService:
    """Service for generating detailed story segments from outline."""

    def __init__(
        self,
        provider: BaseLLMProvider,
        enhancer: PromptEnhancer | None = None,
        cost_tracker: CostTracker | None = None,
    ) -> None:
        """Initialize segment generation service.

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

    async def generate_segments(
        self,
        outline: StoryOutline,
        show_blueprint: ShowBlueprint,
        max_tokens: int = 3000,
        temperature: float = 0.7,
        max_retries: int = 3,
    ) -> list[StorySegment]:
        """Generate detailed story segments from outline.

        This method:
        1. Enhances the prompt with Show Blueprint context
        2. Generates detailed segments for each story beat
        3. Includes characters_involved, setting, educational_content
        4. Ensures world rules consistency
        5. Validates segment structure

        Args:
            outline: Story outline with beats
            show_blueprint: Complete show blueprint with context
            max_tokens: Maximum tokens for generation
            temperature: Sampling temperature
            max_retries: Maximum number of retries for validation failures

        Returns:
            List of StorySegment objects with detailed scene descriptions

        Raises:
            ValueError: If outline is invalid or generation fails
            Exception: If generation fails after retries
        """
        if not outline.story_beats:
            raise ValueError("Outline must have at least one story beat")

        # Enhance prompt with Show Blueprint context
        enhanced_prompt = self.enhancer.enhance_segment_prompt(outline, show_blueprint)

        # Track time
        start_time = time()

        # Generate segments with retry logic
        for attempt in range(max_retries):
            try:
                # Count tokens (may change if prompt is adjusted in retry)
                prompt_tokens = self.provider.count_tokens(enhanced_prompt)

                # Generate segments using LLM
                response = await self.provider.generate(
                    prompt=enhanced_prompt,
                    max_tokens=max_tokens,
                    temperature=temperature,
                )

                # Count completion tokens
                completion_tokens = self.provider.count_tokens(response)

                # Parse and validate response
                segments = self.parser.parse_and_validate(response, StorySegment)

                # Ensure we got a list
                if not isinstance(segments, list):
                    segments = [segments]

                # Validate segments
                self._validate_segments(segments, outline)

                # Log cost if tracker available
                if self.cost_tracker:
                    duration = time() - start_time
                    cost = self.provider.get_cost(prompt_tokens, completion_tokens)
                    self.cost_tracker.log_call(
                        stage="segment",
                        prompt_tokens=prompt_tokens,
                        completion_tokens=completion_tokens,
                        cost=cost,
                        duration=duration,
                        provider=self.provider.__class__.__name__,
                        model=getattr(self.provider, "model", "unknown"),
                    )

                logger.info(
                    f"Generated {len(segments)} segments for "
                    f"{len(outline.story_beats)} beats"
                )
                return segments

            except ValueError as e:
                if attempt < max_retries - 1:
                    logger.warning(
                        f"Segment generation attempt {attempt + 1} failed: "
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
                        f"Segment generation failed after {max_retries} attempts: {e}"
                    )
                    raise

        raise ValueError(f"Failed to generate segments after {max_retries} attempts")

    def _validate_segments(
        self, segments: list[StorySegment], outline: StoryOutline
    ) -> None:
        """Validate generated segments meet requirements.

        Args:
            segments: List of segments to validate
            outline: Original story outline

        Raises:
            ValueError: If segments don't meet requirements
        """
        if not segments:
            raise ValueError("No segments generated")

        # Check that all beats have at least one segment
        beat_numbers = {beat.beat_number for beat in outline.story_beats}
        segment_beats = {seg.beat_number for seg in segments}

        missing_beats = beat_numbers - segment_beats
        if missing_beats:
            raise ValueError(f"Missing segments for beats: {sorted(missing_beats)}")

        # Validate each segment has required fields
        for i, segment in enumerate(segments, 1):
            if not segment.description:
                raise ValueError(f"Segment {i} missing description")
            if not segment.setting:
                raise ValueError(f"Segment {i} missing setting")
            if not segment.educational_content:
                raise ValueError(f"Segment {i} missing educational content")
            if not segment.characters_involved:
                raise ValueError(f"Segment {i} missing characters")

        # Check segment numbering is sequential
        segment_numbers = [seg.segment_number for seg in segments]
        if segment_numbers != list(range(1, len(segments) + 1)):
            logger.warning("Segment numbers are not sequential, renumbering segments")
            for i, segment in enumerate(segments, 1):
                segment.segment_number = i
