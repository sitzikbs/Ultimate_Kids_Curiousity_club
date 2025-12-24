"""Show Blueprint data models for the Ultimate Kids Curiosity Club."""

from datetime import datetime

from pydantic import BaseModel, Field, field_validator


class Show(BaseModel):
    """Core show information and metadata."""

    show_id: str = Field(..., description="Unique identifier for the show")
    title: str = Field(..., description="Title of the show")
    description: str = Field(..., description="Description of the show")
    theme: str = Field(..., description="Overall theme of the show")
    narrator_voice_config: dict[str, str | float] = Field(
        ..., description="Voice configuration for the narrator"
    )
    created_at: datetime = Field(
        default_factory=datetime.now, description="When the show was created"
    )

    @field_validator("show_id")
    @classmethod
    def validate_show_id(cls, v: str) -> str:
        """Validate show_id format (alphanumeric and underscores)."""
        if not v.replace("_", "").replace("-", "").isalnum():
            raise ValueError(
                "show_id must contain only alphanumeric characters, "
                "underscores, and hyphens"
            )
        return v


class Protagonist(BaseModel):
    """Main character of the show."""

    name: str = Field(..., description="Name of the protagonist")
    age: int = Field(..., description="Age of the protagonist")
    description: str = Field(..., description="Description of the protagonist")
    values: list[str] = Field(
        default_factory=list, description="Core values of the protagonist"
    )
    catchphrases: list[str] = Field(
        default_factory=list, description="Catchphrases of the protagonist"
    )
    backstory: str = Field(default="", description="Backstory of the protagonist")
    image_path: str | None = Field(
        default=None, description="Path to protagonist image"
    )
    voice_config: dict[str, str | float] = Field(
        ..., description="Voice configuration for the protagonist"
    )

    @field_validator("image_path")
    @classmethod
    def validate_image_path(cls, v: str | None) -> str | None:
        """Validate that image path is provided in valid format."""
        if v is not None and v.strip() == "":
            raise ValueError("Image path cannot be empty string")
        return v


class WorldDescription(BaseModel):
    """Description of the show's world and settings."""

    setting: str = Field(..., description="Primary setting of the show")
    rules: list[str] = Field(
        default_factory=list, description="Rules that govern the world"
    )
    atmosphere: str = Field(..., description="Atmosphere and mood of the world")
    locations: list[dict[str, str]] = Field(
        default_factory=list,
        description="List of locations with descriptions and image_paths",
    )

    @field_validator("locations")
    @classmethod
    def validate_locations(cls, v: list[dict[str, str]]) -> list[dict[str, str]]:
        """Validate that each location has required keys."""
        for loc in v:
            if "name" not in loc:
                raise ValueError("Each location must have a 'name' key")
        return v


class Character(BaseModel):
    """Supporting character in the show."""

    name: str = Field(..., description="Name of the character")
    role: str = Field(..., description="Role of the character in the show")
    description: str = Field(..., description="Description of the character")
    personality: str = Field(..., description="Personality traits of the character")
    image_path: str | None = Field(default=None, description="Path to character image")
    voice_config: dict[str, str | float] = Field(
        ..., description="Voice configuration for the character"
    )

    @field_validator("image_path")
    @classmethod
    def validate_image_path(cls, v: str | None) -> str | None:
        """Validate that image path is provided in valid format."""
        if v is not None and v.strip() == "":
            raise ValueError("Image path cannot be empty string")
        return v


class ConceptsHistory(BaseModel):
    """History of educational concepts covered in the show."""

    concepts: list[dict[str, str]] = Field(
        default_factory=list,
        description="List of concepts with metadata (episode_id, topic, date)",
    )
    last_updated: datetime = Field(
        default_factory=datetime.now,
        description="When the concepts history was last updated",
    )


class ShowBlueprint(BaseModel):
    """Complete show blueprint aggregating all show components."""

    show: Show = Field(..., description="Core show information")
    protagonist: Protagonist = Field(..., description="Main character")
    world: WorldDescription = Field(..., description="World description")
    characters: list[Character] = Field(
        default_factory=list, description="Supporting characters"
    )
    concepts_history: ConceptsHistory = Field(
        default_factory=ConceptsHistory,
        description="History of educational concepts",
    )
    episodes: list[str] = Field(
        default_factory=list, description="List of episode IDs"
    )
