"""Ideation service for generating story concepts from topics."""

from models import ShowBlueprint
from modules.prompts.enhancer import PromptEnhancer
from services.llm.base import BaseLLMProvider


class IdeationService:
    """Service for generating story concepts from user topics."""

    def __init__(
        self, provider: BaseLLMProvider, enhancer: PromptEnhancer | None = None
    ) -> None:
        """Initialize ideation service.

        Args:
            provider: LLM provider to use for generation
            enhancer: Prompt enhancer for injecting Show Blueprint context.
                     If None, creates a new instance.
        """
        self.provider = provider
        self.enhancer = enhancer or PromptEnhancer()

    async def generate_concept(
        self,
        topic: str,
        show_blueprint: ShowBlueprint,
        max_tokens: int = 1000,
        temperature: float = 0.7,
    ) -> str:
        """Generate story concept from user topic.

        This method:
        1. Enhances the prompt with Show Blueprint context
        2. Checks concepts_covered to avoid repetition
        3. Generates a 2-3 paragraph story concept
        4. Validates age-appropriateness and content safety

        Args:
            topic: User's topic for the episode
            show_blueprint: Complete show blueprint with context
            max_tokens: Maximum tokens for generation
            temperature: Sampling temperature

        Returns:
            2-3 paragraph story concept with protagonist adventure
            and educational tie-in

        Raises:
            ValueError: If topic is empty or invalid
            Exception: If generation fails
        """
        if not topic or not topic.strip():
            raise ValueError("Topic cannot be empty")

        # Enhance prompt with Show Blueprint context
        enhanced_prompt = self.enhancer.enhance_ideation_prompt(topic, show_blueprint)

        # Generate concept using LLM
        concept = await self.provider.generate(
            prompt=enhanced_prompt,
            max_tokens=max_tokens,
            temperature=temperature,
        )

        # Basic validation
        if not concept or len(concept.strip()) < 50:
            raise ValueError("Generated concept is too short or empty")

        # Validate protagonist mention
        protagonist_name = show_blueprint.protagonist.name
        if protagonist_name.lower() not in concept.lower():
            # Add protagonist mention if missing
            concept = (
                f"In this adventure, {protagonist_name} explores {topic}. {concept}"
            )

        # Content safety check (basic)
        self._validate_content_safety(concept)

        return concept.strip()

    def _validate_content_safety(self, concept: str) -> None:
        """Validate that concept is age-appropriate and safe.

        Args:
            concept: Story concept to validate

        Raises:
            ValueError: If content contains inappropriate material
        """
        # Basic content safety checks
        unsafe_keywords = [
            "violent",
            "scary",
            "dangerous",
            "inappropriate",
        ]

        concept_lower = concept.lower()
        for keyword in unsafe_keywords:
            if keyword in concept_lower:
                raise ValueError(
                    f"Content safety check failed: potentially inappropriate content detected"
                )

    def _check_concept_repetition(
        self, topic: str, show_blueprint: ShowBlueprint
    ) -> bool:
        """Check if concept has been covered before.

        Args:
            topic: Topic to check
            show_blueprint: Show blueprint with concepts history

        Returns:
            True if concept is new, False if already covered
        """
        if not show_blueprint.concepts_history:
            return True

        covered_topics = [
            c.get("topic", "").lower()
            for c in show_blueprint.concepts_history.concepts
        ]
        return topic.lower() not in covered_topics
