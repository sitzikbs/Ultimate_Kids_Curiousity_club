"""API routes for episode management."""

import asyncio
import logging
from datetime import UTC, datetime

from fastapi import APIRouter, BackgroundTasks, HTTPException

from api.models import (
    ApproveEpisodeRequest,
    CreateEpisodeRequest,
    EpisodeDetailResponse,
    EpisodeResponse,
    UpdateOutlineRequest,
)
from api.websocket import manager as ws_manager
from config import get_settings
from models.episode import Episode, PipelineStage
from models.story import StoryOutline
from modules.episode_storage import EpisodeStorage
from modules.show_blueprint_manager import ShowBlueprintManager
from utils.errors import StorageError

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api", tags=["episodes"])


def _get_storage() -> EpisodeStorage:
    """Get EpisodeStorage instance."""
    settings = get_settings()
    return EpisodeStorage(shows_dir=settings.SHOWS_DIR)


def _get_manager() -> ShowBlueprintManager:
    """Get ShowBlueprintManager instance."""
    settings = get_settings()
    return ShowBlueprintManager(shows_dir=settings.SHOWS_DIR)


def _find_episode(episode_id: str) -> Episode:
    """Find episode across all shows.

    Args:
        episode_id: Episode identifier

    Returns:
        Episode instance

    Raises:
        HTTPException: If episode is not found
    """
    storage = _get_storage()
    manager = _get_manager()
    shows = manager.list_shows()

    for show in shows:
        try:
            return storage.load_episode(show.show_id, episode_id)
        except (FileNotFoundError, StorageError):
            continue

    raise HTTPException(status_code=404, detail=f"Episode {episode_id} not found")


def _to_web_audio_path(audio_path: str | None) -> str | None:
    """Convert absolute audio path to a URL path servable by /data mount."""
    if not audio_path:
        return None
    settings = get_settings()
    data_dir = str(settings.DATA_DIR)
    if audio_path.startswith(data_dir):
        return "/data" + audio_path[len(data_dir):]
    return audio_path


def _episode_to_detail_response(episode: Episode) -> EpisodeDetailResponse:
    """Convert Episode to EpisodeDetailResponse.

    Args:
        episode: Episode instance

    Returns:
        EpisodeDetailResponse with all episode data
    """
    return EpisodeDetailResponse(
        episode_id=episode.episode_id,
        show_id=episode.show_id,
        topic=episode.topic,
        title=episode.title,
        current_stage=episode.current_stage.value,
        approval_status=episode.approval_status,
        approval_feedback=episode.approval_feedback,
        created_at=episode.created_at,
        updated_at=episode.updated_at,
        outline=episode.outline.model_dump() if episode.outline else None,
        segments=[seg.model_dump() for seg in episode.segments],
        scripts=[script.model_dump() for script in episode.scripts],
        audio_path=_to_web_audio_path(episode.audio_path),
    )


@router.get("/episodes", response_model=list[EpisodeResponse])
async def list_all_episodes(
    stage: str | None = None,
    show_id: str | None = None,
) -> list[EpisodeResponse]:
    """List all episodes across all shows with optional filtering.

    Args:
        stage: Optional pipeline stage filter (e.g. AWAITING_APPROVAL)
        show_id: Optional show filter

    Returns:
        List of episode metadata sorted by updated_at descending
    """
    try:
        storage = _get_storage()
        manager = _get_manager()
        shows = manager.list_shows()

        all_episodes = []
        for show in shows:
            if show_id and show.show_id != show_id:
                continue
            blueprint = manager.load_show(show.show_id)
            for ep_id in blueprint.episodes:
                try:
                    episode = storage.load_episode(show.show_id, ep_id)
                    if stage and episode.current_stage.value != stage:
                        continue
                    all_episodes.append(
                        EpisodeResponse(
                            episode_id=episode.episode_id,
                            show_id=episode.show_id,
                            topic=episode.topic,
                            title=episode.title,
                            current_stage=episode.current_stage.value,
                            approval_status=episode.approval_status,
                            created_at=episode.created_at,
                            updated_at=episode.updated_at,
                        )
                    )
                except (FileNotFoundError, StorageError):
                    continue

        all_episodes.sort(key=lambda e: e.updated_at, reverse=True)
        return all_episodes
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@router.get("/shows/{show_id}/episodes", response_model=list[EpisodeResponse])
async def list_episodes(show_id: str) -> list[EpisodeResponse]:
    """List all episodes for a show.

    Args:
        show_id: Show identifier

    Returns:
        List of episode metadata
    """
    try:
        storage = _get_storage()
        manager = _get_manager()

        # Verify show exists
        blueprint = manager.load_show(show_id)

        episodes = []
        for episode_id in blueprint.episodes:
            try:
                episode = storage.load_episode(show_id, episode_id)
                episodes.append(
                    EpisodeResponse(
                        episode_id=episode.episode_id,
                        show_id=episode.show_id,
                        topic=episode.topic,
                        title=episode.title,
                        current_stage=episode.current_stage.value,
                        approval_status=episode.approval_status,
                        created_at=episode.created_at,
                        updated_at=episode.updated_at,
                    )
                )
            except FileNotFoundError:
                continue

        return episodes
    except FileNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@router.post("/shows/{show_id}/episodes", response_model=dict)
async def create_episode(
    show_id: str,
    request: CreateEpisodeRequest,
    background_tasks: BackgroundTasks,
) -> dict:
    """Create a new episode and start the generation pipeline.

    Runs IDEATION and OUTLINING in the background, then pauses at
    AWAITING_APPROVAL for human review.

    Args:
        show_id: Show identifier
        request: Episode topic and optional title
        background_tasks: FastAPI background tasks runner

    Returns:
        Acknowledgement with topic and title
    """
    try:
        manager = _get_manager()
        manager.load_show(show_id)  # validate show exists

        title = request.title or request.topic

        # Run the full initial pipeline in background
        # (the orchestrator creates the episode internally)
        background_tasks.add_task(
            _run_initial_pipeline, show_id, request.topic, title
        )

        return {
            "status": "started",
            "show_id": show_id,
            "topic": request.topic,
            "title": title,
        }
    except FileNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Internal server error: {str(e)}"
        )


def _run_initial_pipeline(
    show_id: str, topic: str, title: str
) -> None:
    """Run ideation + outlining in a background thread."""
    from cli.factory import create_pipeline

    async def _run() -> None:
        pipeline = create_pipeline()
        await pipeline.generate_episode(show_id, topic, title)

    asyncio.run(_run())


@router.get("/episodes/{episode_id}", response_model=EpisodeDetailResponse)
async def get_episode(episode_id: str) -> EpisodeDetailResponse:
    """Get detailed episode information.

    Args:
        episode_id: Episode identifier

    Returns:
        Complete episode data including outline and scripts
    """
    try:
        episode = _find_episode(episode_id)
        return _episode_to_detail_response(episode)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@router.put("/episodes/{episode_id}/outline", response_model=EpisodeDetailResponse)
async def update_outline(
    episode_id: str, request: UpdateOutlineRequest
) -> EpisodeDetailResponse:
    """Update episode outline.

    Args:
        episode_id: Episode identifier
        request: Update request with outline data

    Returns:
        Updated episode data
    """
    try:
        storage = _get_storage()
        episode = _find_episode(episode_id)

        # Update outline
        old_stage = episode.current_stage
        episode.outline = StoryOutline(**request.outline)
        episode.updated_at = datetime.now(UTC)

        # Save updated episode
        storage.save_episode(episode)

        # Broadcast status change if stage changed
        if episode.current_stage != old_stage:
            await ws_manager.broadcast_episode_status_change(
                episode_id=episode.episode_id,
                show_id=episode.show_id,
                old_stage=old_stage.value,
                new_stage=episode.current_stage.value,
            )

        return _episode_to_detail_response(episode)
    except HTTPException:
        raise
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@router.post("/episodes/{episode_id}/approve", response_model=EpisodeDetailResponse)
async def approve_episode(
    episode_id: str,
    request: ApproveEpisodeRequest,
    background_tasks: BackgroundTasks,
) -> EpisodeDetailResponse:
    """Approve or reject episode outline.

    On approval the remaining pipeline stages (segment generation through
    audio mixing) are automatically kicked off in the background.

    Args:
        episode_id: Episode identifier
        request: Approval request with approved flag and optional feedback
        background_tasks: FastAPI background tasks runner

    Returns:
        Updated episode data
    """
    try:
        storage = _get_storage()
        episode = _find_episode(episode_id)

        # Update approval status
        old_stage = episode.current_stage
        episode.approval_status = "approved" if request.approved else "rejected"
        episode.approval_feedback = request.feedback
        episode.updated_at = datetime.now(UTC)

        # Update pipeline stage
        if request.approved:
            episode.current_stage = PipelineStage.APPROVED
        else:
            episode.current_stage = PipelineStage.REJECTED

        # Save updated episode
        storage.save_episode(episode)

        # Broadcast status change
        await ws_manager.broadcast_episode_status_change(
            episode_id=episode.episode_id,
            show_id=episode.show_id,
            old_stage=old_stage.value,
            new_stage=episode.current_stage.value,
        )

        # Auto-resume pipeline in background on approval
        if request.approved:
            background_tasks.add_task(
                _resume_pipeline, episode.show_id, episode.episode_id
            )

        return _episode_to_detail_response(episode)
    except HTTPException:
        raise
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Internal server error: {str(e)}"
        )


def _resume_pipeline(show_id: str, episode_id: str) -> None:
    """Resume the pipeline in a background thread after approval."""
    from cli.factory import create_pipeline

    async def _run() -> None:
        pipeline = create_pipeline()
        result = await pipeline.resume_episode(show_id, episode_id)
        logger.info(
            "Pipeline resumed for %s/%s — status: %s",
            show_id,
            episode_id,
            result.status,
        )

    asyncio.run(_run())
