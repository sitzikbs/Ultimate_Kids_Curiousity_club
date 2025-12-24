"""Pydantic models for episodes and pipeline stages."""

from datetime import datetime
from enum import Enum
from pathlib import Path

from pydantic import BaseModel, Field

from src.models.story import Script, StoryOutline, StorySegment
from src.utils.validators import EpisodeId


class PipelineStage(str, Enum):
    """Pipeline stages for episode generation."""

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


class ApprovalStatus(str, Enum):
    """Approval status for episode content."""

    PENDING = "PENDING"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"
    NOT_REQUIRED = "NOT_REQUIRED"


class Episode(BaseModel):
    """Complete episode with all generation stages."""

    episode_id: EpisodeId
    show_id: str
    topic: str
    title: str = ""
    outline: StoryOutline | None = None
    segments: list[StorySegment] = Field(default_factory=list)
    scripts: list[Script] = Field(default_factory=list)
    audio_path: Path | None = None
    current_stage: PipelineStage = PipelineStage.PENDING
    approval_status: ApprovalStatus = ApprovalStatus.NOT_REQUIRED
    approval_feedback: str = ""
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)
    cost_estimate: float = 0.0

    class Config:
        """Pydantic configuration."""

        json_schema_extra = {
            "example": {
                "episode_id": "ep_001_bike_chains",
                "show_id": "olivers_workshop",
                "topic": "How bike chains work",
                "title": "The Broken Bike",
                "current_stage": "OUTLINING",
                "approval_status": "NOT_REQUIRED",
            }
        }

    def update_stage(self, stage: PipelineStage) -> None:
        """Update the current pipeline stage.
        
        Args:
            stage: New pipeline stage
        """
        self.current_stage = stage
        self.updated_at = datetime.now()

    def set_approval_status(self, status: ApprovalStatus, feedback: str = "") -> None:
        """Set the approval status with optional feedback.
        
        Args:
            status: Approval status
            feedback: Optional feedback message
        """
        self.approval_status = status
        self.approval_feedback = feedback
        self.updated_at = datetime.now()

    def add_segment(self, segment: StorySegment) -> None:
        """Add a story segment to the episode.
        
        Args:
            segment: Story segment to add
        """
        self.segments.append(segment)
        self.updated_at = datetime.now()

    def add_script(self, script: Script) -> None:
        """Add a script to the episode.
        
        Args:
            script: Script to add
        """
        self.scripts.append(script)
        self.updated_at = datetime.now()

    def is_complete(self) -> bool:
        """Check if episode is complete.
        
        Returns:
            True if episode is complete
        """
        return self.current_stage == PipelineStage.COMPLETE

    def is_failed(self) -> bool:
        """Check if episode generation failed.
        
        Returns:
            True if episode failed
        """
        return self.current_stage in (PipelineStage.FAILED, PipelineStage.REJECTED)
