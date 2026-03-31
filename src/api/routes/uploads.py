"""API routes for file uploads."""

import shutil
import uuid
from pathlib import Path

from fastapi import APIRouter, File, HTTPException, UploadFile

from api.config import get_api_settings

router = APIRouter(prefix="/api/uploads", tags=["uploads"])

ALLOWED_IMAGE_TYPES = {"image/jpeg", "image/png", "image/gif", "image/webp"}
EXTENSION_MAP = {
    "image/jpeg": ".jpg",
    "image/png": ".png",
    "image/gif": ".gif",
    "image/webp": ".webp",
}


@router.post("/images/{show_id}")
async def upload_image(show_id: str, file: UploadFile = File(...)) -> dict:
    """Upload an image for a show (protagonist, world, or character).

    Stores the file under website/admin/uploads/{show_id}/ so it is served
    by the existing StaticFiles mount at /.

    Args:
        show_id: Show identifier (used to namespace uploads)
        file: Image file to upload

    Returns:
        dict with 'path' key containing the URL path to the uploaded file
    """
    if file.content_type not in ALLOWED_IMAGE_TYPES:
        allowed = ", ".join(ALLOWED_IMAGE_TYPES)
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported image type: {file.content_type}. Allowed: {allowed}",
        )

    ext = EXTENSION_MAP.get(file.content_type, ".jpg")
    filename = f"{uuid.uuid4().hex}{ext}"

    settings = get_api_settings()
    website_dir = Path(settings.WEBSITE_DIR)
    dest = website_dir / "admin" / "uploads" / show_id / filename
    dest.parent.mkdir(parents=True, exist_ok=True)

    try:
        with dest.open("wb") as f:
            shutil.copyfileobj(file.file, f)
    finally:
        await file.close()

    return {"path": f"/admin/uploads/{show_id}/{filename}"}
