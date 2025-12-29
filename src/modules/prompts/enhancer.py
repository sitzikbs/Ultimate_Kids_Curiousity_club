"""Prompt enhancer for enriching prompts with Show Blueprint context."""

from pathlib import Path

from jinja2 import Environment, FileSystemLoader

from models import ShowBlueprint, StoryOutline, StorySegment
from modules.prompts.filters import CUSTOM_FILTERS


class PromptEnhancer:
    """Enhance prompts with Show Blueprint context."""

    def __init__(
        self, template_dir: Path | None = None, version: str = "1.0.0"
    ) -> None:
        """Initialize the PromptEnhancer.

        Args:
            template_dir: Directory containing Jinja2 templates.
                         Defaults to src/modules/prompts/templates
            version: Version string for prompt versioning
        """
        if template_dir is None:
            # Default to the templates directory next to this file
            template_dir = Path(__file__).parent / "templates"

        self.template_dir = Path(template_dir)
        self.version = version
        self.env = self._setup_jinja_env()

    def _setup_jinja_env(self) -> Environment:
        """Set up Jinja2 environment with custom filters.

        Returns:
            Configured Jinja2 Environment
        """
        env = Environment(
            loader=FileSystemLoader(str(self.template_dir)),
            trim_blocks=True,
            lstrip_blocks=True,
            autoescape=False,  # We need to output text prompts, not HTML
        )

        # Register custom filters
        for filter_name, filter_func in CUSTOM_FILTERS.items():
            env.filters[filter_name] = filter_func

        return env

<<<<<<< HEAD
    def enhance_ideation_prompt(
        self, topic: str, show_blueprint: ShowBlueprint
    ) -> str:
=======
    def enhance_ideation_prompt(self, topic: str, show_blueprint: ShowBlueprint) -> str:
>>>>>>> 88d8b08e49146c77fb31ea4491b8fc32c256a29f
        """Enhance ideation prompt with Show Blueprint context.

        Args:
            topic: Topic for the episode
            show_blueprint: Complete show blueprint

        Returns:
            Enhanced prompt with show context injected

        Raises:
            FileNotFoundError: If ideation template not found
        """
        template = self.env.get_template("ideation.j2")
<<<<<<< HEAD
        
=======

>>>>>>> 88d8b08e49146c77fb31ea4491b8fc32c256a29f
        # Get covered concepts, handling None case defensively
        covered_concepts = []
        if show_blueprint.concepts_history is not None:
            covered_concepts = show_blueprint.concepts_history.concepts
<<<<<<< HEAD
        
=======

>>>>>>> 88d8b08e49146c77fb31ea4491b8fc32c256a29f
        return template.render(
            topic=topic,
            show=show_blueprint.show,
            protagonist=show_blueprint.protagonist,
            world=show_blueprint.world,
            covered_concepts=covered_concepts,
            version=self.version,
        )

    def enhance_outline_prompt(
        self, concept: str, show_blueprint: ShowBlueprint
    ) -> str:
        """Enhance outline prompt with Show Blueprint context.

        Args:
            concept: Story concept from ideation stage
            show_blueprint: Complete show blueprint

        Returns:
            Enhanced prompt with show context injected

        Raises:
            FileNotFoundError: If outline template not found
        """
        template = self.env.get_template("outline.j2")
        return template.render(
            concept=concept,
            show=show_blueprint.show,
            protagonist=show_blueprint.protagonist,
            world=show_blueprint.world,
            characters=show_blueprint.characters,
            version=self.version,
        )

    def enhance_segment_prompt(
        self, outline: StoryOutline, show_blueprint: ShowBlueprint
    ) -> str:
        """Enhance segment generation prompt.

        Args:
            outline: Story outline from outline stage
            show_blueprint: Complete show blueprint

        Returns:
            Enhanced prompt with show context injected

        Raises:
            FileNotFoundError: If segment template not found
        """
        template = self.env.get_template("segment.j2")
        return template.render(
            outline=outline,
            protagonist=show_blueprint.protagonist,
            world=show_blueprint.world,
            characters=show_blueprint.characters,
            version=self.version,
        )

    def enhance_script_prompt(
        self, segments: list[StorySegment], show_blueprint: ShowBlueprint
    ) -> str:
        """Enhance script generation prompt.

        Args:
            segments: List of story segments from segment generation stage
            show_blueprint: Complete show blueprint

        Returns:
            Enhanced prompt with show context injected

        Raises:
            FileNotFoundError: If script template not found
        """
        template = self.env.get_template("script.j2")
        return template.render(
            segments=segments,
            protagonist=show_blueprint.protagonist,
            world=show_blueprint.world,
            characters=show_blueprint.characters,
            narrator_voice=show_blueprint.show.narrator_voice_config,
            version=self.version,
        )
