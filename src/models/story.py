"""Story generation data models for the Ultimate Kids Curiosity Club."""

from datetime import UTC, datetime

from pydantic import BaseModel, Field


class StoryBeat(BaseModel):
    """A single beat in the story outline."""

    beat_number: int = Field(..., description="Sequential number of the beat")
    title: str = Field(..., description="Title of the beat")
    description: str = Field(..., description="Description of what happens in the beat")
    educational_focus: str = Field(
        ..., description="Educational focus of this beat"
    )
    key_moments: list[str] = Field(
        default_factory=list, description="Key moments in the beat"
    )


class StoryOutline(BaseModel):
    """High-level story outline for an episode."""

    episode_id: str = Field(..., description="Episode this outline belongs to")
    show_id: str = Field(..., description="Show this outline belongs to")
    topic: str = Field(..., description="Topic of the episode")
    title: str = Field(..., description="Title of the episode")
    educational_concept: str = Field(
        ..., description="Primary educational concept"
    )
    story_beats: list[StoryBeat] = Field(
        default_factory=list, description="List of story beats"
    )
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(UTC),
        description="When the outline was created",
    )


class StorySegment(BaseModel):
    """Detailed segment of the story."""

    segment_number: int = Field(..., description="Sequential number of the segment")
    beat_number: int = Field(..., description="Which beat this segment belongs to")
    description: str = Field(..., description="Description of the segment")
    characters_involved: list[str] = Field(
        default_factory=list, description="Characters involved in this segment"
    )
    setting: str = Field(..., description="Setting for this segment")
    educational_content: str = Field(
        ..., description="Educational content covered in this segment"
    )


class ScriptBlock(BaseModel):
    """A single block of dialogue in the script."""

    speaker: str = Field(..., description="Name of the speaker")
    text: str = Field(..., description="The dialogue text")
    speaker_voice_id: str = Field(..., description="Voice ID for the speaker")
    duration_estimate: float | None = Field(
        default=None, description="Estimated duration in seconds"
    )


class Script(BaseModel):
    """Complete script for a story segment."""

    segment_number: int = Field(..., description="Which segment this script is for")
    script_blocks: list[ScriptBlock] = Field(
        default_factory=list, description="List of dialogue blocks"
    )
