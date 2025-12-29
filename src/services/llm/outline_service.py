"""Outline service for generating story outlines from concepts."""

import yaml

from models import ShowBlueprint, StoryBeat, StoryOutline
from modules.prompts.enhancer import PromptEnhancer
from services.llm.base import BaseLLMProvider


class OutlineService:
    """Service for generating story outlines from concepts."""

    def __init__(
        self, provider: BaseLLMProvider, enhancer: PromptEnhancer | None = None
    ) -> None:
        """Initialize outline service.

        Args:
            provider: LLM provider to use for generation
            enhancer: Prompt enhancer for injecting Show Blueprint context.
                     If None, creates a new instance.
        """
        self.provider = provider
        self.enhancer = enhancer or PromptEnhancer()

    async def generate_outline(
        self,
        concept: str,
        show_blueprint: ShowBlueprint,
        episode_id: str = "temp_episode",
        max_tokens: int = 2000,
        temperature: float = 0.7,
    ) -> StoryOutline:
        """Generate story outline from concept.

        This method:
        1. Enhances the prompt with Show Blueprint context
        2. Generates 3-5 story beats with titles, descriptions, key moments
        3. Ensures educational focus in each beat
        4. Includes protagonist value demonstration
        5. Adds duration estimation (total ~10-15 minutes)
        6. Returns structured StoryOutline model

        Args:
            concept: Story concept from ideation stage
            show_blueprint: Complete show blueprint with context
            episode_id: Episode identifier
            max_tokens: Maximum tokens for generation
            temperature: Sampling temperature

        Returns:
            StoryOutline with structured story beats

        Raises:
            ValueError: If concept is empty or invalid
            Exception: If generation or parsing fails
        """
        if not concept or not concept.strip():
            raise ValueError("Concept cannot be empty")

        # Enhance prompt with Show Blueprint context
        enhanced_prompt = self.enhancer.enhance_outline_prompt(concept, show_blueprint)

        # Generate outline using LLM
        outline_yaml = await self.provider.generate(
            prompt=enhanced_prompt,
            max_tokens=max_tokens,
            temperature=temperature,
        )

        # Parse YAML and create StoryOutline
        outline = self._parse_outline(outline_yaml, episode_id, show_blueprint)

        # Validate outline
        self._validate_outline(outline)

        return outline

    def _parse_outline(
        self, yaml_content: str, episode_id: str, show_blueprint: ShowBlueprint
    ) -> StoryOutline:
        """Parse YAML content into StoryOutline model.

        Args:
            yaml_content: YAML string from LLM
            episode_id: Episode identifier
            show_blueprint: Show blueprint for context

        Returns:
            Parsed StoryOutline

        Raises:
            ValueError: If YAML is invalid or missing required fields
        """
        try:
            # Try to extract YAML from markdown code blocks if present
            if "```yaml" in yaml_content:
                yaml_content = yaml_content.split("```yaml")[1].split("```")[0]
            elif "```" in yaml_content:
                yaml_content = yaml_content.split("```")[1].split("```")[0]

            data = yaml.safe_load(yaml_content)
        except Exception as e:
            raise ValueError(f"Failed to parse outline YAML: {e}") from e

        # Extract story beats
        story_beats = []
        beats_data = data.get("story_beats", [])

        if not beats_data:
            raise ValueError("No story beats found in outline")

        for beat_data in beats_data:
            beat = StoryBeat(
                beat_number=beat_data.get("beat_number", 0),
                title=beat_data.get("title", ""),
                description=beat_data.get("description", ""),
                educational_focus=beat_data.get("educational_focus", ""),
                key_moments=beat_data.get("key_moments", []),
            )
            story_beats.append(beat)

        # Create StoryOutline
        outline = StoryOutline(
            episode_id=data.get("episode_id", episode_id),
            show_id=data.get("show_id", show_blueprint.show.show_id),
            topic=data.get("topic", "Generated Topic"),
            title=data.get("title", "Generated Title"),
            educational_concept=data.get(
                "educational_concept", "Educational Content"
            ),
            story_beats=story_beats,
        )

        return outline

    def _validate_outline(self, outline: StoryOutline) -> None:
        """Validate story outline meets requirements.

        Args:
            outline: Story outline to validate

        Raises:
            ValueError: If outline doesn't meet requirements
        """
        # Check number of beats (should be 3-5)
        num_beats = len(outline.story_beats)
        if num_beats < 3 or num_beats > 5:
            raise ValueError(
                f"Outline should have 3-5 story beats, got {num_beats}"
            )

        # Validate each beat has required fields
        for beat in outline.story_beats:
            if not beat.title:
                raise ValueError(f"Beat {beat.beat_number} missing title")
            if not beat.description:
                raise ValueError(f"Beat {beat.beat_number} missing description")
            if not beat.educational_focus:
                raise ValueError(f"Beat {beat.beat_number} missing educational focus")

        # Check for educational content
        if not outline.educational_concept:
            raise ValueError("Outline missing educational concept")

    async def generate_outline_yaml(
        self,
        concept: str,
        show_blueprint: ShowBlueprint,
        episode_id: str = "temp_episode",
        max_tokens: int = 2000,
        temperature: float = 0.7,
    ) -> str:
        """Generate story outline and return as YAML string.

        This is a convenience method for human review.

        Args:
            concept: Story concept from ideation stage
            show_blueprint: Complete show blueprint with context
            episode_id: Episode identifier
            max_tokens: Maximum tokens for generation
            temperature: Sampling temperature

        Returns:
            YAML formatted outline string for human review
        """
        outline = await self.generate_outline(
            concept, show_blueprint, episode_id, max_tokens, temperature
        )

        # Convert to YAML
        outline_dict = {
            "episode_id": outline.episode_id,
            "show_id": outline.show_id,
            "topic": outline.topic,
            "title": outline.title,
            "educational_concept": outline.educational_concept,
            "created_at": outline.created_at.isoformat(),
            "story_beats": [
                {
                    "beat_number": beat.beat_number,
                    "title": beat.title,
                    "description": beat.description,
                    "educational_focus": beat.educational_focus,
                    "key_moments": beat.key_moments,
                }
                for beat in outline.story_beats
            ],
        }

        return yaml.dump(outline_dict, default_flow_style=False, sort_keys=False)
