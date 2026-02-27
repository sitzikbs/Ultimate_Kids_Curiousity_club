"""Episode data models for the Ultimate Kids Curiosity Club."""

from datetime import UTC, datetime
from enum import Enum

from pydantic import BaseModel, Field

from models.story import Script, StoryOutline, StorySegment


class PipelineStage(str, Enum):
    """Episode pipeline stage enumeration."""

    PENDING = "PENDING"
    IDEATION = "IDEATION"
    OUTLINING = "OUTLINING"
    AWAITING_APPROVAL = "AWAITING_APPROVAL"
    APPROVED = "APPROVED"
    SEGMENT_GENERATION = "SEGMENT_GENERATION"
    SCRIPT_GENERATION = "SCRIPT_GENERATION"
    AUDIO_SYNTHESIS = "AUDIO_SYNTHESIS"
    AUDIO_MIXING = "AUDIO_MIXING"
    COMPLETE = "COMPLETE"
    FAILED = "FAILED"
    REJECTED = "REJECTED"


class Episode(BaseModel):
    """Complete episode with all generation stages."""

    episode_id: str = Field(..., description="Unique identifier for the episode")
    show_id: str = Field(..., description="Show this episode belongs to")
    topic: str = Field(..., description="Topic of the episode")
    title: str = Field(..., description="Title of the episode")
    outline: StoryOutline | None = Field(
        default=None, description="Story outline for the episode"
    )
    segments: list[StorySegment] = Field(
        default_factory=list, description="Story segments"
    )
    concept: str | None = Field(
        default=None, description="Generated story concept from ideation"
    )
    scripts: list[Script] = Field(
        default_factory=list, description="Scripts for each segment"
    )
    audio_segment_paths: list[str] = Field(
        default_factory=list,
        description="Paths to individual audio segments from TTS synthesis",
    )
    audio_path: str | None = Field(default=None, description="Path to final audio file")
    current_stage: PipelineStage = Field(
        default=PipelineStage.PENDING, description="Current pipeline stage"
    )
    approval_status: str | None = Field(
        default=None, description="Approval status (approved/rejected/pending)"
    )
    approval_feedback: str | None = Field(
        default=None, description="Feedback from approval process"
    )
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(UTC),
        description="When the episode was created",
    )
    updated_at: datetime = Field(
        default_factory=lambda: datetime.now(UTC),
        description="When the episode was last updated",
    )
