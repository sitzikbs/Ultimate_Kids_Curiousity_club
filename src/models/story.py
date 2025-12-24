"""Pydantic models for story generation stages."""

from datetime import datetime

from pydantic import BaseModel, Field

from src.utils.validators import EpisodeId


class StoryBeat(BaseModel):
    """A single story beat in the narrative structure."""

    beat_number: int
    title: str
    description: str
    educational_focus: str
    key_moments: list[str] = Field(default_factory=list)

    class Config:
        """Pydantic configuration."""

        json_schema_extra = {
            "example": {
                "beat_number": 1,
                "title": "The Problem",
                "description": "Oliver discovers his bike chain is broken",
                "educational_focus": "Introduction to simple machines",
                "key_moments": [
                    "Oliver tries to ride his bike",
                    "Chain falls off",
                    "Oliver examines the chain",
                ],
            }
        }


class StoryOutline(BaseModel):
    """Complete story outline for an episode."""

    episode_id: EpisodeId
    show_id: str
    topic: str
    title: str
    educational_concept: str
    story_beats: list[StoryBeat] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=datetime.now)

    class Config:
        """Pydantic configuration."""

        json_schema_extra = {
            "example": {
                "episode_id": "ep_001",
                "show_id": "olivers_workshop",
                "topic": "How chains and gears work",
                "title": "The Broken Bike",
                "educational_concept": "Simple machines: chains and sprockets",
                "story_beats": [],
            }
        }


class StorySegment(BaseModel):
    """A segment of the story for detailed script generation."""

    segment_number: int
    beat_number: int
    description: str
    characters_involved: list[str] = Field(default_factory=list)
    setting: str
    educational_content: str

    class Config:
        """Pydantic configuration."""

        json_schema_extra = {
            "example": {
                "segment_number": 1,
                "beat_number": 1,
                "description": "Oliver examines the bike chain",
                "characters_involved": ["Oliver", "Maya"],
                "setting": "Oliver's backyard workshop",
                "educational_content": "Explain how chain links connect",
            }
        }


class ScriptBlock(BaseModel):
    """A single block of dialogue or narration in the script."""

    speaker: str
    text: str
    speaker_voice_id: str | None = None
    duration_estimate: float = 0.0

    class Config:
        """Pydantic configuration."""

        json_schema_extra = {
            "example": {
                "speaker": "Oliver",
                "text": "Hmm, this chain has lots of little links...",
                "speaker_voice_id": "oliver_voice",
                "duration_estimate": 3.5,
            }
        }


class Script(BaseModel):
    """Complete script for a story segment."""

    segment_number: int
    script_blocks: list[ScriptBlock] = Field(default_factory=list)

    class Config:
        """Pydantic configuration."""

        json_schema_extra = {
            "example": {
                "segment_number": 1,
                "script_blocks": [
                    {"speaker": "Narrator", "text": "Oliver looked at his bike..."}
                ],
            }
        }
