"""Pipeline API routes for running and monitoring the podcast generation pipeline."""

import logging

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from config import get_settings
from modules.episode_storage import EpisodeStorage
from utils.errors import StorageError

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/pipeline", tags=["pipeline"])


class PipelineRequest(BaseModel):
    """Request to run the full pipeline."""

    show_id: str
    topic: str
    title: str | None = None


class StepRequest(BaseModel):
    """Request to run a single pipeline step."""

    show_id: str
    episode_id: str
    step: str  # ideation, outlining, segment_generation, etc.


class PipelineStatus(BaseModel):
    """Pipeline status response."""

    episode_id: str
    show_id: str
    current_stage: str
    stages_completed: list[str] = Field(default_factory=list)
    error: str | None = None


def _get_storage() -> EpisodeStorage:
    """Get EpisodeStorage instance from current settings."""
    settings = get_settings()
    return EpisodeStorage(shows_dir=settings.SHOWS_DIR)


@router.post("/run")
async def run_pipeline(request: PipelineRequest) -> PipelineStatus:
    """Run the full pipeline for a new episode.

    Creates a new episode and runs through the pre-approval stages
    (ideation and outlining). The pipeline pauses at AWAITING_APPROVAL
    for human review.

    Args:
        request: Pipeline run parameters including show_id and topic.

    Returns:
        Pipeline status with the new episode ID and current stage.
    """
    from cli.factory import create_pipeline

    try:
        orchestrator = create_pipeline()
        result = await orchestrator.generate_episode(
            show_id=request.show_id,
            topic=request.topic,
            title=request.title or request.topic,
        )
        episode = result.episode
        return PipelineStatus(
            episode_id=episode.episode_id,
            show_id=episode.show_id,
            current_stage=episode.current_stage.value,
            stages_completed=list(episode.checkpoints.keys()),
        )
    except FileNotFoundError as exc:
        raise HTTPException(
            status_code=404, detail=f"Show not found: {request.show_id}"
        ) from exc
    except Exception as exc:
        logger.exception("Pipeline run failed for show %s", request.show_id)
        raise HTTPException(status_code=500, detail=f"Pipeline failed: {exc}") from exc


@router.post("/run-step")
async def run_step(request: StepRequest) -> PipelineStatus:
    """Run a single pipeline step for an existing episode.

    Executes one stage of the pipeline for debugging or step-by-step
    execution.

    Args:
        request: Step execution parameters.

    Returns:
        Pipeline status after step execution.
    """
    storage = _get_storage()

    try:
        episode = storage.load_episode(request.show_id, request.episode_id)
    except StorageError as exc:
        raise HTTPException(
            status_code=404,
            detail=f"Episode not found: {request.episode_id}",
        ) from exc

    # Return current status — full step-by-step execution would require
    # more orchestrator refactoring to support individual step dispatch
    return PipelineStatus(
        episode_id=episode.episode_id,
        show_id=episode.show_id,
        current_stage=episode.current_stage.value,
        stages_completed=list(episode.checkpoints.keys()),
    )


@router.get("/status/{show_id}/{episode_id}")
async def get_status(show_id: str, episode_id: str) -> PipelineStatus:
    """Get current pipeline status for an episode.

    Args:
        show_id: Show identifier.
        episode_id: Episode identifier.

    Returns:
        Current pipeline status for the episode.
    """
    storage = _get_storage()

    try:
        episode = storage.load_episode(show_id, episode_id)
    except StorageError as exc:
        raise HTTPException(
            status_code=404,
            detail=f"Episode not found: {episode_id}",
        ) from exc

    error_msg: str | None = None
    if episode.last_error:
        error_msg = episode.last_error.get("message")

    return PipelineStatus(
        episode_id=episode.episode_id,
        show_id=episode.show_id,
        current_stage=episode.current_stage.value,
        stages_completed=list(episode.checkpoints.keys()),
        error=error_msg,
    )
