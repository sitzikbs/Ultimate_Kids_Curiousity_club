"""API routes for show management."""

from fastapi import APIRouter, HTTPException

from api.models import ShowBlueprintResponse, ShowResponse, UpdateShowBlueprintRequest
from config import get_settings
from models.show import Protagonist, WorldDescription
from modules.show_blueprint_manager import ShowBlueprintManager

router = APIRouter(prefix="/api/shows", tags=["shows"])


def _get_manager() -> ShowBlueprintManager:
    """Get ShowBlueprintManager instance."""
    settings = get_settings()
    return ShowBlueprintManager(shows_dir=settings.SHOWS_DIR)


@router.get("", response_model=list[ShowResponse])
async def list_shows() -> list[ShowResponse]:
    """List all available shows.

    Returns:
        List of show metadata
    """
    try:
        manager = _get_manager()
        shows = manager.list_shows()

        return [
            ShowResponse(
                show_id=show.show_id,
                title=show.title,
                description=show.description,
                theme=show.theme,
                created_at=show.created_at,
            )
            for show in shows
        ]
    except FileNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@router.get("/{show_id}", response_model=ShowBlueprintResponse)
async def get_show(show_id: str) -> ShowBlueprintResponse:
    """Get complete show blueprint details.

    Args:
        show_id: Show identifier

    Returns:
        Complete show blueprint
    """
    try:
        manager = _get_manager()
        blueprint = manager.load_show(show_id)

        return ShowBlueprintResponse(
            show=blueprint.show.model_dump(),
            protagonist=blueprint.protagonist.model_dump(),
            world=blueprint.world.model_dump(),
            characters=[char.model_dump() for char in blueprint.characters],
            concepts_history=blueprint.concepts_history.model_dump(),
            episodes=blueprint.episodes,
        )
    except FileNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@router.put("/{show_id}", response_model=ShowBlueprintResponse)
async def update_show(
    show_id: str, request: UpdateShowBlueprintRequest
) -> ShowBlueprintResponse:
    """Update show blueprint (protagonist and/or world).

    Args:
        show_id: Show identifier
        request: Update request with protagonist and/or world data

    Returns:
        Updated show blueprint
    """
    try:
        manager = _get_manager()

        # Update protagonist if provided
        if request.protagonist is not None:
            protagonist = Protagonist(**request.protagonist)
            manager.update_protagonist(show_id, protagonist)

        # Update world if provided
        if request.world is not None:
            world = WorldDescription(**request.world)
            manager.update_world(show_id, world)

        # Load and return updated blueprint
        blueprint = manager.load_show(show_id)
        return ShowBlueprintResponse(
            show=blueprint.show.model_dump(),
            protagonist=blueprint.protagonist.model_dump(),
            world=blueprint.world.model_dump(),
            characters=[char.model_dump() for char in blueprint.characters],
            concepts_history=blueprint.concepts_history.model_dump(),
            episodes=blueprint.episodes,
        )
    except FileNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")
