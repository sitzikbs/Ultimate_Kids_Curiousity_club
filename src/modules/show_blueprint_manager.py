"""Show Blueprint loading, saving, and management system."""

import json
from pathlib import Path

import yaml

from src.config import get_settings
from src.models.show import (
    Character,
    ConceptEntry,
    ConceptsHistory,
    Location,
    Protagonist,
    Show,
    ShowBlueprint,
    VoiceConfig,
    WorldDescription,
)
from src.utils.errors import ShowNotFoundError, StorageError, ValidationError


class ShowBlueprintManager:
    """Manager for Show Blueprint CRUD operations."""

    def __init__(self, shows_dir: Path | None = None):
        """Initialize the manager.
        
        Args:
            shows_dir: Directory containing show data (default: from settings)
        """
        self.shows_dir = shows_dir or get_settings().SHOWS_DIR

    def load_show(self, show_id: str) -> ShowBlueprint:
        """Load a show blueprint from disk.
        
        Args:
            show_id: Show identifier
            
        Returns:
            ShowBlueprint instance
            
        Raises:
            ShowNotFoundError: If show doesn't exist
            StorageError: If loading fails
        """
        show_dir = self.shows_dir / show_id

        if not show_dir.exists():
            raise ShowNotFoundError(
                f"Show '{show_id}' not found", show_id=show_id
            )

        try:
            # Load show metadata
            show_path = show_dir / "show.yaml"
            if not show_path.exists():
                raise StorageError(
                    f"show.yaml not found for show '{show_id}'", show_id=show_id
                )

            with open(show_path) as f:
                show_data = yaml.safe_load(f)

            show = Show(
                show_id=show_data.get("show_id", show_id),
                title=show_data.get("show_title", ""),
                description=show_data.get("tagline", ""),
                theme=show_data.get("theme", ""),
                narrator_voice_config=VoiceConfig(
                    voice_id=show_data.get("narrator_voice_id")
                ),
                created_at=show_data.get("created_at"),
            )

            # Load protagonist
            protagonist_path = show_dir / "protagonist.yaml"
            if not protagonist_path.exists():
                raise StorageError(
                    f"protagonist.yaml not found for show '{show_id}'",
                    show_id=show_id,
                )

            with open(protagonist_path) as f:
                protag_data = yaml.safe_load(f)

            protagonist = Protagonist(
                name=protag_data.get("name", ""),
                age=protag_data.get("age", 8),
                description=protag_data.get("physical_description", ""),
                values=protag_data.get("personality_traits", []),
                catchphrases=protag_data.get("catchphrases", []),
                backstory=protag_data.get("core_motivation", ""),
                image_path=protag_data.get("image_path"),
                voice_config=self._load_voice_config(
                    protag_data.get("voice_config", {})
                ),
            )

            # Load world description
            world_path = show_dir / "world.yaml"
            if not world_path.exists():
                raise StorageError(
                    f"world.yaml not found for show '{show_id}'", show_id=show_id
                )

            with open(world_path) as f:
                world_data = yaml.safe_load(f)

            locations = []
            for loc_data in world_data.get("key_locations", []):
                locations.append(
                    Location(
                        name=loc_data.get("name", ""),
                        description=loc_data.get("description", ""),
                    )
                )

            world = WorldDescription(
                setting=world_data.get("description", ""),
                rules=world_data.get("world_rules", []),
                atmosphere=world_data.get("era_or_style", ""),
                locations=locations,
            )

            # Load concepts history
            concepts_path = show_dir / "concepts_covered.json"
            concepts_history = ConceptsHistory()

            if concepts_path.exists():
                with open(concepts_path) as f:
                    concepts_data = json.load(f)

                if isinstance(concepts_data, dict):
                    concepts_list = concepts_data.get("concepts", [])
                elif isinstance(concepts_data, list):
                    concepts_list = concepts_data
                else:
                    concepts_list = []

                for concept_data in concepts_list:
                    if isinstance(concept_data, dict):
                        concepts_history.concepts.append(
                            ConceptEntry(**concept_data)
                        )

            # Load characters (if directory exists)
            characters = []
            characters_dir = show_dir / "characters"
            if characters_dir.exists():
                for char_file in characters_dir.glob("*.yaml"):
                    with open(char_file) as f:
                        char_data = yaml.safe_load(f)

                    characters.append(
                        Character(
                            name=char_data.get("name", ""),
                            role=char_data.get("role", ""),
                            description=char_data.get("personality_snippet", ""),
                            personality=char_data.get("personality_snippet", ""),
                            image_path=char_data.get("image_path"),
                            voice_config=self._load_voice_config(
                                char_data.get("voice_config", {})
                            ),
                        )
                    )

            # Load episode list
            episodes = []
            episodes_dir = show_dir / "episodes"
            if episodes_dir.exists():
                for ep_file in episodes_dir.glob("*.json"):
                    episodes.append(ep_file.stem)

            return ShowBlueprint(
                show=show,
                protagonist=protagonist,
                world=world,
                characters=characters,
                concepts_history=concepts_history,
                episodes=episodes,
            )

        except (OSError, yaml.YAMLError, json.JSONDecodeError) as e:
            raise StorageError(
                f"Failed to load show '{show_id}': {e}",
                show_id=show_id,
            ) from e

    def save_show(self, blueprint: ShowBlueprint) -> None:
        """Save a show blueprint to disk.
        
        Args:
            blueprint: ShowBlueprint to save
            
        Raises:
            StorageError: If saving fails
        """
        show_id = blueprint.show.show_id
        show_dir = self.shows_dir / show_id

        try:
            show_dir.mkdir(parents=True, exist_ok=True)

            # Save show metadata
            show_data = {
                "show_id": blueprint.show.show_id,
                "show_title": blueprint.show.title,
                "tagline": blueprint.show.description,
                "theme": blueprint.show.theme,
                "narrator_voice_id": (
                    blueprint.show.narrator_voice_config.voice_id
                    if blueprint.show.narrator_voice_config
                    else None
                ),
                "created_at": blueprint.show.created_at.isoformat(),
            }

            with open(show_dir / "show.yaml", "w") as f:
                yaml.dump(show_data, f, default_flow_style=False)

            # Save protagonist
            protag_data = {
                "name": blueprint.protagonist.name,
                "age": blueprint.protagonist.age,
                "physical_description": blueprint.protagonist.description,
                "personality_traits": blueprint.protagonist.values,
                "catchphrases": blueprint.protagonist.catchphrases,
                "core_motivation": blueprint.protagonist.backstory,
                "image_path": (
                    str(blueprint.protagonist.image_path)
                    if blueprint.protagonist.image_path
                    else None
                ),
                "voice_config": self._voice_config_to_dict(
                    blueprint.protagonist.voice_config
                ),
            }

            with open(show_dir / "protagonist.yaml", "w") as f:
                yaml.dump(protag_data, f, default_flow_style=False)

            # Save world description
            world_data = {
                "world_name": show_id,
                "description": blueprint.world.setting,
                "world_rules": blueprint.world.rules,
                "era_or_style": blueprint.world.atmosphere,
                "key_locations": [
                    {"name": loc.name, "description": loc.description}
                    for loc in blueprint.world.locations
                ],
            }

            with open(show_dir / "world.yaml", "w") as f:
                yaml.dump(world_data, f, default_flow_style=False)

            # Save concepts history
            concepts_data = {
                "show_id": show_id,
                "concepts": [
                    {
                        "concept": entry.concept,
                        "episode_id": entry.episode_id,
                        "date": entry.date.isoformat(),
                        "complexity_level": entry.complexity_level,
                    }
                    for entry in blueprint.concepts_history.concepts
                ],
                "last_updated": blueprint.concepts_history.last_updated.isoformat(),
            }

            with open(show_dir / "concepts_covered.json", "w") as f:
                json.dump(concepts_data, f, indent=2)

            # Save characters
            if blueprint.characters:
                characters_dir = show_dir / "characters"
                characters_dir.mkdir(exist_ok=True)

                for character in blueprint.characters:
                    char_data = {
                        "name": character.name,
                        "role": character.role,
                        "personality_snippet": character.personality,
                        "image_path": (
                            str(character.image_path)
                            if character.image_path
                            else None
                        ),
                        "voice_config": self._voice_config_to_dict(
                            character.voice_config
                        ),
                    }

                    char_filename = character.name.lower().replace(" ", "_") + ".yaml"
                    with open(characters_dir / char_filename, "w") as f:
                        yaml.dump(char_data, f, default_flow_style=False)

        except (OSError, yaml.YAMLError, json.JSONDecodeError) as e:
            raise StorageError(
                f"Failed to save show '{show_id}': {e}",
                show_id=show_id,
            ) from e

    def list_shows(self) -> list[Show]:
        """List all available shows.
        
        Returns:
            List of Show instances
        """
        shows = []

        if not self.shows_dir.exists():
            return shows

        for show_dir in self.shows_dir.iterdir():
            if not show_dir.is_dir():
                continue

            show_yaml = show_dir / "show.yaml"
            if not show_yaml.exists():
                continue

            try:
                with open(show_yaml) as f:
                    show_data = yaml.safe_load(f)

                shows.append(
                    Show(
                        show_id=show_data.get("show_id", show_dir.name),
                        title=show_data.get("show_title", ""),
                        description=show_data.get("tagline", ""),
                        theme=show_data.get("theme", ""),
                        created_at=show_data.get("created_at"),
                    )
                )
            except (OSError, yaml.YAMLError) as e:
                # Skip shows with invalid metadata
                continue

        return shows

    def update_protagonist(self, show_id: str, protagonist: Protagonist) -> None:
        """Update protagonist for a show.
        
        Args:
            show_id: Show identifier
            protagonist: New protagonist data
            
        Raises:
            ShowNotFoundError: If show doesn't exist
        """
        blueprint = self.load_show(show_id)
        blueprint.protagonist = protagonist
        self.save_show(blueprint)

    def update_world(self, show_id: str, world: WorldDescription) -> None:
        """Update world description for a show.
        
        Args:
            show_id: Show identifier
            world: New world description
            
        Raises:
            ShowNotFoundError: If show doesn't exist
        """
        blueprint = self.load_show(show_id)
        blueprint.world = world
        self.save_show(blueprint)

    def add_character(self, show_id: str, character: Character) -> None:
        """Add a supporting character to a show.
        
        Args:
            show_id: Show identifier
            character: Character to add
            
        Raises:
            ShowNotFoundError: If show doesn't exist
        """
        blueprint = self.load_show(show_id)
        blueprint.add_character(character)
        self.save_show(blueprint)

    def add_concept(
        self, show_id: str, concept: str, episode_id: str, complexity_level: str = "introductory"
    ) -> None:
        """Add a covered concept to the show's history.
        
        Args:
            show_id: Show identifier
            concept: Educational concept covered
            episode_id: Episode where concept was covered
            complexity_level: Complexity level of the concept
            
        Raises:
            ShowNotFoundError: If show doesn't exist
        """
        blueprint = self.load_show(show_id)
        blueprint.add_concept(concept, episode_id, complexity_level)
        self.save_show(blueprint)

    def get_covered_concepts(self, show_id: str) -> list[str]:
        """Get list of all covered concepts for a show.
        
        Args:
            show_id: Show identifier
            
        Returns:
            List of concept names
            
        Raises:
            ShowNotFoundError: If show doesn't exist
        """
        blueprint = self.load_show(show_id)
        return blueprint.concepts_history.get_covered_concepts()

    def _load_voice_config(self, data: dict) -> VoiceConfig:
        """Load VoiceConfig from dict.
        
        Args:
            data: Voice config data
            
        Returns:
            VoiceConfig instance
        """
        return VoiceConfig(
            provider=data.get("provider"),
            voice_id=data.get("voice_id"),
            stability=data.get("stability", 0.5),
            similarity_boost=data.get("similarity_boost", 0.75),
            style=data.get("style", 0.3),
        )

    def _voice_config_to_dict(self, config: VoiceConfig) -> dict:
        """Convert VoiceConfig to dict.
        
        Args:
            config: VoiceConfig instance
            
        Returns:
            Dictionary representation
        """
        return {
            "provider": config.provider,
            "voice_id": config.voice_id,
            "stability": config.stability,
            "similarity_boost": config.similarity_boost,
            "style": config.style,
        }
