"""API routes for file uploads."""

import re
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
MAX_UPLOAD_SIZE = 5 * 1024 * 1024  # 5 MB
_VALID_SHOW_ID = re.compile(r"^[a-zA-Z0-9_-]+$")


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
    if not _VALID_SHOW_ID.match(show_id):
        raise HTTPException(
            status_code=400,
            detail="Invalid show_id: only alphanumeric, "
            "hyphens, and underscores allowed",
        )

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
        size = 0
        with dest.open("wb") as f:
            while chunk := await file.read(8192):
                size += len(chunk)
                if size > MAX_UPLOAD_SIZE:
                    f.close()
                    dest.unlink(missing_ok=True)
                    max_mb = MAX_UPLOAD_SIZE // (1024 * 1024)
                    raise HTTPException(
                        status_code=413,
                        detail=f"File too large. Max size: {max_mb} MB",
                    )
                f.write(chunk)
    finally:
        await file.close()

    return {"path": f"/admin/uploads/{show_id}/{filename}"}
