"""Show Blueprint Manager for loading, saving, and managing show data."""

import json
from datetime import UTC, datetime
from pathlib import Path

import yaml

from config import get_settings
from models.show import (
    Character,
    ConceptsHistory,
    Protagonist,
    Show,
    ShowBlueprint,
    WorldDescription,
)


class ShowBlueprintManager:
    """Manages Show Blueprint CRUD operations and concept tracking."""

    def __init__(self, shows_dir: Path | None = None):
        """Initialize manager with shows directory from settings.

        Args:
            shows_dir: Directory containing show data. Defaults to settings.SHOWS_DIR
        """
        self.shows_dir = shows_dir or get_settings().SHOWS_DIR

    def load_show(self, show_id: str) -> ShowBlueprint:
        """Load Show Blueprint from disk.

        Args:
            show_id: Unique identifier for the show

        Returns:
            Complete ShowBlueprint loaded from disk

        Raises:
            FileNotFoundError: If show directory or required files don't exist
            ValueError: If YAML/JSON files are invalid
        """
        show_dir = self.shows_dir / show_id
        if not show_dir.exists():
            raise FileNotFoundError(f"Show directory not found: {show_dir}")

        # Load show metadata
        show_path = show_dir / "show.yaml"
        if not show_path.exists():
            raise FileNotFoundError(f"Show file not found: {show_path}")

        with show_path.open("r") as f:
            show_data = yaml.safe_load(f)

        # Load protagonist
        protagonist_path = show_dir / "protagonist.yaml"
        if not protagonist_path.exists():
            raise FileNotFoundError(f"Protagonist file not found: {protagonist_path}")

        with protagonist_path.open("r") as f:
            protagonist_data = yaml.safe_load(f)

        # Load world
        world_path = show_dir / "world.yaml"
        if not world_path.exists():
            raise FileNotFoundError(f"World file not found: {world_path}")

        with world_path.open("r") as f:
            world_data = yaml.safe_load(f)

        # Load concepts history
        concepts_path = show_dir / "concepts_covered.json"
        if concepts_path.exists():
            with concepts_path.open("r") as f:
                concepts_data = json.load(f)
        else:
            concepts_data = {"concepts": [], "last_updated": None}

        # Load characters from characters directory
        characters = []
        characters_dir = show_dir / "characters"
        if characters_dir.exists():
            # Sort character files for consistent ordering
            for char_file in sorted(characters_dir.glob("*.yaml")):
                with char_file.open("r") as f:
                    char_data = yaml.safe_load(f)
                    characters.append(Character(**char_data))

        # Get episode list
        episodes = []
        episodes_dir = show_dir / "episodes"
        if episodes_dir.exists():
            episodes = sorted([ep.name for ep in episodes_dir.iterdir() if ep.is_dir()])

        # Create Show model
        show = Show(
            show_id=show_data.get("show_id", show_id),
            title=show_data.get("show_title", show_data.get("title", "")),
            description=show_data.get("description", show_data.get("tagline", "")),
            theme=show_data.get("theme", ""),
            narrator_voice_config=show_data.get("narrator_voice_config", {}),
            created_at=show_data.get("created_at", datetime.now(UTC)),
        )

        # Create Protagonist model
        voice_config = protagonist_data.get("voice_config", {})
        if voice_config is None:
            voice_config = {}
        # Filter out None values from voice_config
        voice_config = {k: v for k, v in voice_config.items() if v is not None}

        # Handle different field names between storage format and model
        # personality_traits is a list in YAML, we'll extract first values if present
        personality_traits = protagonist_data.get("personality_traits", [])
        values = []
        if isinstance(personality_traits, list) and personality_traits:
            # Extract key values from personality traits (before the colon)
            values = [
                trait.split(":")[0].strip().lower()
                for trait in personality_traits
                if isinstance(trait, str)
            ]

        protagonist = Protagonist(
            name=protagonist_data.get("name", ""),
            age=protagonist_data.get("age", 0),
            description=protagonist_data.get("physical_description", ""),
            values=values or protagonist_data.get("core_values", []),
            catchphrases=protagonist_data.get("catchphrases", []),
            backstory=protagonist_data.get(
                "core_motivation", protagonist_data.get("backstory", "")
            ),
            image_path=protagonist_data.get("image_path"),
            voice_config=voice_config,
        )

        # Create WorldDescription model
        world = WorldDescription(
            setting=world_data.get("description", ""),
            rules=world_data.get("world_rules", []),
            atmosphere=world_data.get("atmosphere", world_data.get("era_or_style", "")),
            locations=world_data.get("key_locations", []),
        )

        # Create ConceptsHistory model
        concepts_history = ConceptsHistory(
            concepts=concepts_data.get("concepts", []),
            last_updated=concepts_data.get("last_updated", datetime.now(UTC)),
        )

        return ShowBlueprint(
            show=show,
            protagonist=protagonist,
            world=world,
            characters=characters,
            concepts_history=concepts_history,
            episodes=episodes,
        )

    def save_show(self, blueprint: ShowBlueprint) -> None:
        """Save Show Blueprint to disk.

        Args:
            blueprint: ShowBlueprint to save

        Raises:
            OSError: If unable to create directories or write files
        """
        show_dir = self.shows_dir / blueprint.show.show_id
        show_dir.mkdir(parents=True, exist_ok=True)

        # Save show metadata
        show_data = {
            "show_id": blueprint.show.show_id,
            "show_title": blueprint.show.title,
            "tagline": blueprint.show.description,
            "theme": blueprint.show.theme,
            "narrator_voice_config": blueprint.show.narrator_voice_config,
            "created_at": blueprint.show.created_at.isoformat(),
        }
        show_path = show_dir / "show.yaml"
        with show_path.open("w") as f:
            yaml.safe_dump(show_data, f, default_flow_style=False, sort_keys=False)

        # Save protagonist
        protagonist_data = {
            "name": blueprint.protagonist.name,
            "age": blueprint.protagonist.age,
            "physical_description": blueprint.protagonist.description,
            "core_values": blueprint.protagonist.values,
            "catchphrases": blueprint.protagonist.catchphrases,
            "backstory": blueprint.protagonist.backstory,
            "image_path": blueprint.protagonist.image_path,
            "voice_config": blueprint.protagonist.voice_config,
        }
        protagonist_path = show_dir / "protagonist.yaml"
        with protagonist_path.open("w") as f:
            yaml.safe_dump(
                protagonist_data, f, default_flow_style=False, sort_keys=False
            )

        # Save world
        world_data = {
            "description": blueprint.world.setting,
            "world_rules": blueprint.world.rules,
            "era_or_style": blueprint.world.atmosphere,
            "key_locations": blueprint.world.locations,
        }
        world_path = show_dir / "world.yaml"
        with world_path.open("w") as f:
            yaml.safe_dump(world_data, f, default_flow_style=False, sort_keys=False)

        # Save concepts history
        concepts_data = {
            "show_id": blueprint.show.show_id,
            "concepts": blueprint.concepts_history.concepts,
            "last_updated": blueprint.concepts_history.last_updated.isoformat(),
        }
        concepts_path = show_dir / "concepts_covered.json"
        with concepts_path.open("w") as f:
            json.dump(concepts_data, f, indent=2)

        # Save characters
        if blueprint.characters:
            characters_dir = show_dir / "characters"
            characters_dir.mkdir(exist_ok=True)
            for character in blueprint.characters:
                char_data = {
                    "name": character.name,
                    "role": character.role,
                    "description": character.description,
                    "personality": character.personality,
                    "image_path": character.image_path,
                    "voice_config": character.voice_config,
                }
                char_filename = character.name.lower().replace(" ", "_") + ".yaml"
                char_path = characters_dir / char_filename
                with char_path.open("w") as f:
                    yaml.safe_dump(
                        char_data, f, default_flow_style=False, sort_keys=False
                    )

        # Create episodes directory if it doesn't exist
        episodes_dir = show_dir / "episodes"
        episodes_dir.mkdir(exist_ok=True)

    def list_shows(self) -> list[Show]:
        """Enumerate all available shows.

        Returns:
            List of Show objects for all available shows

        Raises:
            FileNotFoundError: If shows directory doesn't exist
        """
        if not self.shows_dir.exists():
            raise FileNotFoundError(f"Shows directory not found: {self.shows_dir}")

        shows = []
        for show_dir in sorted(self.shows_dir.iterdir()):
            if not show_dir.is_dir():
                continue

            show_path = show_dir / "show.yaml"
            if not show_path.exists():
                continue

            try:
                with show_path.open("r") as f:
                    show_data = yaml.safe_load(f)

                show = Show(
                    show_id=show_data.get("show_id", show_dir.name),
                    title=show_data.get("show_title", show_data.get("title", "")),
                    description=show_data.get(
                        "description", show_data.get("tagline", "")
                    ),
                    theme=show_data.get("theme", ""),
                    narrator_voice_config=show_data.get("narrator_voice_config", {}),
                    created_at=show_data.get("created_at", datetime.now(UTC)),
                )
                shows.append(show)
            except Exception:
                # Skip shows with invalid data
                continue

        return shows

    def update_protagonist(self, show_id: str, protagonist: Protagonist) -> None:
        """Update protagonist for a show.

        Args:
            show_id: Unique identifier for the show
            protagonist: New Protagonist data

        Raises:
            FileNotFoundError: If show directory doesn't exist
        """
        show_dir = self.shows_dir / show_id
        if not show_dir.exists():
            raise FileNotFoundError(f"Show directory not found: {show_dir}")

        protagonist_data = {
            "name": protagonist.name,
            "age": protagonist.age,
            "physical_description": protagonist.description,
            "core_values": protagonist.values,
            "catchphrases": protagonist.catchphrases,
            "backstory": protagonist.backstory,
            "image_path": protagonist.image_path,
            "voice_config": protagonist.voice_config,
        }

        protagonist_path = show_dir / "protagonist.yaml"
        with protagonist_path.open("w") as f:
            yaml.safe_dump(
                protagonist_data, f, default_flow_style=False, sort_keys=False
            )

    def update_world(self, show_id: str, world: WorldDescription) -> None:
        """Update world description for a show.

        Args:
            show_id: Unique identifier for the show
            world: New WorldDescription data

        Raises:
            FileNotFoundError: If show directory doesn't exist
        """
        show_dir = self.shows_dir / show_id
        if not show_dir.exists():
            raise FileNotFoundError(f"Show directory not found: {show_dir}")

        world_data = {
            "description": world.setting,
            "world_rules": world.rules,
            "era_or_style": world.atmosphere,
            "key_locations": world.locations,
        }

        world_path = show_dir / "world.yaml"
        with world_path.open("w") as f:
            yaml.safe_dump(world_data, f, default_flow_style=False, sort_keys=False)

    def add_character(self, show_id: str, character: Character) -> None:
        """Add supporting character to show.

        Args:
            show_id: Unique identifier for the show
            character: Character to add

        Raises:
            FileNotFoundError: If show directory doesn't exist
        """
        show_dir = self.shows_dir / show_id
        if not show_dir.exists():
            raise FileNotFoundError(f"Show directory not found: {show_dir}")

        characters_dir = show_dir / "characters"
        characters_dir.mkdir(exist_ok=True)

        char_data = {
            "name": character.name,
            "role": character.role,
            "description": character.description,
            "personality": character.personality,
            "image_path": character.image_path,
            "voice_config": character.voice_config,
        }

        char_filename = character.name.lower().replace(" ", "_") + ".yaml"
        char_path = characters_dir / char_filename
        with char_path.open("w") as f:
            yaml.safe_dump(char_data, f, default_flow_style=False, sort_keys=False)

    def add_concept(self, show_id: str, concept: str, episode_id: str) -> None:
        """Track new concept covered in episode.

        Args:
            show_id: Unique identifier for the show
            concept: Educational concept being covered
            episode_id: Episode where concept is covered

        Raises:
            FileNotFoundError: If show directory doesn't exist
        """
        show_dir = self.shows_dir / show_id
        if not show_dir.exists():
            raise FileNotFoundError(f"Show directory not found: {show_dir}")

        concepts_path = show_dir / "concepts_covered.json"

        # Load existing concepts or create new
        if concepts_path.exists():
            with concepts_path.open("r") as f:
                concepts_data = json.load(f)
        else:
            concepts_data = {"show_id": show_id, "concepts": [], "last_updated": None}

        # Add new concept
        new_concept = {
            "concept": concept,
            "episode_id": episode_id,
            "covered_at": datetime.now(UTC).isoformat(),
        }
        concepts_data["concepts"].append(new_concept)
        concepts_data["last_updated"] = datetime.now(UTC).isoformat()

        # Save updated concepts
        with concepts_path.open("w") as f:
            json.dump(concepts_data, f, indent=2)

    def link_episode(self, show_id: str, episode_id: str) -> None:
        """Register an episode in the show's episode list.

        Creates the ``episodes/<episode_id>/`` directory under the show.
        Directory presence is used as the metadata signal — subsequent
        ``load_show()`` calls discover episodes via directory listing.

        Args:
            show_id: Unique identifier for the show
            episode_id: Episode identifier to link

        Raises:
            FileNotFoundError: If show directory doesn't exist
        """
        show_dir = self.shows_dir / show_id
        if not show_dir.exists():
            raise FileNotFoundError(f"Show directory not found: {show_dir}")

        episodes_dir = show_dir / "episodes"
        episodes_dir.mkdir(exist_ok=True)

        episode_dir = episodes_dir / episode_id
        episode_dir.mkdir(exist_ok=True)

    def get_covered_concepts(self, show_id: str) -> list[str]:
        """Get all concepts covered across all episodes.

        Args:
            show_id: Unique identifier for the show

        Returns:
            List of concept strings

        Raises:
            FileNotFoundError: If show directory doesn't exist
        """
        show_dir = self.shows_dir / show_id
        if not show_dir.exists():
            raise FileNotFoundError(f"Show directory not found: {show_dir}")

        concepts_path = show_dir / "concepts_covered.json"
        if not concepts_path.exists():
            return []

        with concepts_path.open("r") as f:
            concepts_data = json.load(f)

        return [c["concept"] for c in concepts_data.get("concepts", [])]

    @classmethod
    def create_from_template(
        cls, template_name: str, show_id: str, shows_dir: Path | None = None
    ) -> ShowBlueprint:
        """Initialize new show from template.

        Args:
            template_name: Name of template (oliver_template, hannah_template)
            show_id: Unique identifier for new show
            shows_dir: Directory to save show. Defaults to settings.SHOWS_DIR

        Returns:
            ShowBlueprint created from template

        Raises:
            ValueError: If template_name is not recognized
        """
        if template_name == "oliver_template":
            return cls._create_oliver_template(show_id)
        elif template_name == "hannah_template":
            return cls._create_hannah_template(show_id)
        else:
            raise ValueError(
                f"Unknown template: {template_name}. "
                f"Available: oliver_template, hannah_template"
            )

    @staticmethod
    def _create_oliver_template(show_id: str) -> ShowBlueprint:
        """Create Oliver's STEM Adventures template.

        Args:
            show_id: Unique identifier for new show

        Returns:
            ShowBlueprint for Oliver template
        """
        show = Show(
            show_id=show_id,
            title="Oliver's STEM Adventures",
            description="Explore the amazing world of inventions and STEM!",
            theme="STEM education through hands-on invention and problem-solving",
            narrator_voice_config={"provider": "mock", "voice_id": "mock_narrator"},
        )

        protagonist = Protagonist(
            name="Oliver the Inventor",
            age=8,
            description=(
                "An energetic 8-year-old boy with messy brown hair and bright blue "
                "eyes. He wears a yellow shirt with blue overalls and always carries "
                "a well-worn backpack stuffed with gizmos."
            ),
            values=["curiosity", "creativity", "persistence"],
            catchphrases=["Let's figure it out!", "Gizmos ready!", "Time to tinker!"],
            backstory=(
                "To understand how things work and build simple inventions that "
                "solve problems, help friends, and make learning about STEM fun."
            ),
            image_path=None,
            voice_config={"provider": "mock", "voice_id": "mock_oliver"},
        )

        world = WorldDescription(
            setting=(
                "A friendly suburban town where kids ride bikes, teachers know your "
                "name, and neighborhood bakeries smell like cinnamon. The small twist: "
                "Maplewood celebrates hands-on curiosity through people and shared "
                "resources."
            ),
            rules=[
                "No magic — solutions come from curiosity and experimentation.",
                "Adults are generally supportive.",
                "Safety and learning matter: experiments should be tested.",
                "Every problem is an opportunity to learn a STEM concept.",
            ],
            atmosphere="Creative, experimental, and encouraging",
            locations=[
                {
                    "name": "Oliver's Backyard Workshop",
                    "description": (
                        "A cluttered but cozy shed behind Oliver's house filled "
                        "with spare parts, tools, and half-built gadgets."
                    ),
                }
            ],
        )

        return ShowBlueprint(
            show=show,
            protagonist=protagonist,
            world=world,
            characters=[],
            concepts_history=ConceptsHistory(
                concepts=[], last_updated=datetime.now(UTC)
            ),
            episodes=[],
        )

    @staticmethod
    def _create_hannah_template(show_id: str) -> ShowBlueprint:
        """Create Hannah's History Adventures template.

        Args:
            show_id: Unique identifier for new show

        Returns:
            ShowBlueprint for Hannah template
        """
        show = Show(
            show_id=show_id,
            title="Hannah's History Adventures",
            description="Discover fascinating stories from the past!",
            theme="History education through storytelling and exploration",
            narrator_voice_config={"provider": "mock", "voice_id": "mock_narrator"},
        )

        protagonist = Protagonist(
            name="Hannah the Historian",
            age=10,
            description=(
                "An enthusiastic 10-year-old girl with long dark hair often tied in "
                "a ponytail. She wears a green jacket with many pockets for carrying "
                "her history notes and a magnifying glass."
            ),
            values=["curiosity", "empathy", "critical thinking"],
            catchphrases=[
                "Did you know...?",
                "Let's explore the past!",
                "History is full of surprises!",
            ],
            backstory=(
                "To discover fascinating stories from history and help others "
                "understand how the past shapes our present."
            ),
            image_path=None,
            voice_config={"provider": "mock", "voice_id": "mock_hannah"},
        )

        world = WorldDescription(
            setting=(
                "A charming town with a rich history, featuring a well-preserved "
                "historical district, a local museum, and a library with extensive "
                "archives. Time seems to layer here, with stories from different "
                "eras waiting to be discovered."
            ),
            rules=[
                "History is about real people and real events.",
                "Every artifact has a story to tell.",
                "Understanding different perspectives is important.",
                "The past helps us understand the present.",
            ],
            atmosphere="Mysterious, educational, and inspiring",
            locations=[
                {
                    "name": "The History Corner",
                    "description": (
                        "Hannah's special spot in the town library where she keeps "
                        "her research materials and historical artifacts."
                    ),
                }
            ],
        )

        return ShowBlueprint(
            show=show,
            protagonist=protagonist,
            world=world,
            characters=[],
            concepts_history=ConceptsHistory(
                concepts=[], last_updated=datetime.now(UTC)
            ),
            episodes=[],
        )
