"""Pydantic models for API request/response validation."""

from datetime import datetime

from pydantic import BaseModel, Field


# Health check models
class HealthResponse(BaseModel):
    """Health check response."""

    status: str = Field(..., description="Service status")
    timestamp: datetime = Field(..., description="Current server timestamp")


# Show models
class ShowResponse(BaseModel):
    """Response model for show metadata."""

    show_id: str = Field(..., description="Unique identifier for the show")
    title: str = Field(..., description="Title of the show")
    description: str = Field(..., description="Description of the show")
    theme: str = Field(..., description="Overall theme of the show")
    created_at: datetime = Field(..., description="When the show was created")


class ShowBlueprintResponse(BaseModel):
    """Response model for complete show blueprint."""

    show: dict = Field(..., description="Core show information")
    protagonist: dict = Field(..., description="Main character")
    world: dict = Field(..., description="World description")
    characters: list[dict] = Field(..., description="Supporting characters")
    concepts_history: dict = Field(..., description="History of educational concepts")
    episodes: list[str] = Field(..., description="List of episode IDs")


class UpdateShowBlueprintRequest(BaseModel):
    """Request model for updating show blueprint."""

    protagonist: dict | None = Field(None, description="Updated protagonist data")
    world: dict | None = Field(None, description="Updated world description")


# Episode models
class EpisodeResponse(BaseModel):
    """Response model for episode data."""

    episode_id: str = Field(..., description="Unique identifier for the episode")
    show_id: str = Field(..., description="Show this episode belongs to")
    topic: str = Field(..., description="Topic of the episode")
    title: str = Field(..., description="Title of the episode")
    current_stage: str = Field(..., description="Current pipeline stage")
    approval_status: str | None = Field(None, description="Approval status")
    created_at: datetime = Field(..., description="When the episode was created")
    updated_at: datetime = Field(..., description="When the episode was last updated")


class EpisodeDetailResponse(EpisodeResponse):
    """Response model for detailed episode data including outline and scripts."""

    outline: dict | None = Field(None, description="Story outline for the episode")
    segments: list[dict] = Field(default_factory=list, description="Story segments")
    scripts: list[dict] = Field(default_factory=list, description="Scripts")
    audio_path: str | None = Field(None, description="Path to final audio file")
    approval_feedback: str | None = Field(
        None, description="Feedback from approval process"
    )


class UpdateOutlineRequest(BaseModel):
    """Request model for updating episode outline."""

    outline: dict = Field(..., description="Updated story outline")


class ApproveEpisodeRequest(BaseModel):
    """Request model for approving/rejecting episode outline."""

    approved: bool = Field(..., description="Whether to approve the outline")
    feedback: str | None = Field(None, description="Optional feedback message")


# WebSocket models
class WebSocketMessage(BaseModel):
    """WebSocket message model."""

    event_type: str = Field(..., description="Type of event")
    data: dict = Field(..., description="Event data")
    timestamp: datetime = Field(..., description="Event timestamp")


class EpisodeStatusChangeEvent(BaseModel):
    """Event for episode status changes."""

    episode_id: str = Field(..., description="Episode identifier")
    show_id: str = Field(..., description="Show identifier")
    old_stage: str = Field(..., description="Previous pipeline stage")
    new_stage: str = Field(..., description="New pipeline stage")


class ProgressUpdateEvent(BaseModel):
    """Event for progress updates."""

    episode_id: str = Field(..., description="Episode identifier")
    show_id: str = Field(..., description="Show identifier")
    stage: str = Field(..., description="Current pipeline stage")
    progress: float = Field(..., description="Progress percentage (0-100)")
    message: str | None = Field(None, description="Optional progress message")
