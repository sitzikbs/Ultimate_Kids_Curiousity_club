"""Pydantic models for Show Blueprint architecture."""

from datetime import datetime
from pathlib import Path

from pydantic import BaseModel, Field

from src.utils.validators import AgeRange, ImagePath, ShowId, VocabularyLevel


class VoiceConfig(BaseModel):
    """Voice configuration for text-to-speech."""

    provider: str | None = None
    voice_id: str | None = None
    stability: float = 0.5
    similarity_boost: float = 0.75
    style: float = 0.3


class Show(BaseModel):
    """Show metadata and configuration."""

    show_id: ShowId
    title: str
    description: str
    theme: str
    narrator_voice_config: VoiceConfig | None = None
    created_at: datetime = Field(default_factory=datetime.now)

    class Config:
        """Pydantic configuration."""

        json_schema_extra = {
            "example": {
                "show_id": "olivers_workshop",
                "title": "Oliver the Inventor",
                "description": "STEM adventures for curious kids",
                "theme": "Science and engineering through invention",
                "created_at": "2024-01-15T10:00:00Z",
            }
        }


class Protagonist(BaseModel):
    """Main character/protagonist of the show."""

    name: str
    age: AgeRange
    description: str
    values: list[str] = Field(default_factory=list)
    catchphrases: list[str] = Field(default_factory=list)
    backstory: str = ""
    image_path: ImagePath = None
    voice_config: VoiceConfig = Field(default_factory=VoiceConfig)

    class Config:
        """Pydantic configuration."""

        json_schema_extra = {
            "example": {
                "name": "Oliver the Inventor",
                "age": 8,
                "description": "Curious and inventive 8-year-old",
                "values": ["curiosity", "creativity", "helping others"],
                "catchphrases": ["Let's figure it out!", "Gizmos ready!"],
                "backstory": "Oliver loves building gadgets in his backyard workshop",
            }
        }


class Location(BaseModel):
    """A location in the show's world."""

    name: str
    description: str
    image_path: ImagePath = None


class WorldDescription(BaseModel):
    """Description of the show's world/setting."""

    setting: str
    rules: list[str] = Field(default_factory=list)
    atmosphere: str = ""
    locations: list[Location] = Field(default_factory=list)

    class Config:
        """Pydantic configuration."""

        json_schema_extra = {
            "example": {
                "setting": "Modern suburban town called Maplewood",
                "rules": [
                    "No magic - only science and creativity",
                    "Adults are supportive mentors",
                ],
                "atmosphere": "Friendly and encouraging",
                "locations": [
                    {
                        "name": "Oliver's Workshop",
                        "description": "A cozy shed filled with tools and gadgets",
                    }
                ],
            }
        }


class Character(BaseModel):
    """Supporting character in the show."""

    name: str
    role: str
    description: str
    personality: str
    image_path: ImagePath = None
    voice_config: VoiceConfig = Field(default_factory=VoiceConfig)

    class Config:
        """Pydantic configuration."""

        json_schema_extra = {
            "example": {
                "name": "Maya Rivera",
                "role": "Best Friend",
                "description": "Oliver's energetic and creative friend",
                "personality": "Warm, outgoing, sometimes scatterbrained",
            }
        }


class ConceptEntry(BaseModel):
    """A single educational concept that has been covered."""

    concept: str
    episode_id: str
    date: datetime = Field(default_factory=datetime.now)
    complexity_level: str = "introductory"


class ConceptsHistory(BaseModel):
    """History of educational concepts covered in the show."""

    concepts: list[ConceptEntry] = Field(default_factory=list)
    last_updated: datetime = Field(default_factory=datetime.now)

    def add_concept(
        self, concept: str, episode_id: str, complexity_level: str = "introductory"
    ) -> None:
        """Add a new concept to the history.
        
        Args:
            concept: The educational concept
            episode_id: ID of the episode covering this concept
            complexity_level: Complexity level of the concept
        """
        entry = ConceptEntry(
            concept=concept, episode_id=episode_id, complexity_level=complexity_level
        )
        self.concepts.append(entry)
        self.last_updated = datetime.now()

    def get_covered_concepts(self) -> list[str]:
        """Get list of all covered concept names.
        
        Returns:
            List of concept names
        """
        return [entry.concept for entry in self.concepts]


class ShowBlueprint(BaseModel):
    """Complete show blueprint aggregating all show components."""

    show: Show
    protagonist: Protagonist
    world: WorldDescription
    characters: list[Character] = Field(default_factory=list)
    concepts_history: ConceptsHistory = Field(default_factory=ConceptsHistory)
    episodes: list[str] = Field(default_factory=list)

    class Config:
        """Pydantic configuration."""

        json_schema_extra = {
            "example": {
                "show": {"show_id": "olivers_workshop", "title": "Oliver the Inventor"},
                "protagonist": {"name": "Oliver", "age": 8},
                "world": {"setting": "Maplewood"},
                "characters": [],
                "episodes": ["ep_001", "ep_002"],
            }
        }

    def add_episode(self, episode_id: str) -> None:
        """Add an episode to the show.
        
        Args:
            episode_id: ID of the episode to add
        """
        if episode_id not in self.episodes:
            self.episodes.append(episode_id)

    def add_character(self, character: Character) -> None:
        """Add a supporting character to the show.
        
        Args:
            character: Character to add
        """
        # Check if character already exists
        for existing in self.characters:
            if existing.name == character.name:
                return
        self.characters.append(character)

    def add_concept(
        self, concept: str, episode_id: str, complexity_level: str = "introductory"
    ) -> None:
        """Add a covered concept to the history.
        
        Args:
            concept: The educational concept
            episode_id: ID of the episode covering this concept
            complexity_level: Complexity level of the concept
        """
        self.concepts_history.add_concept(concept, episode_id, complexity_level)
