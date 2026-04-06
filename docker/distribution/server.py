"""Distribution API server for RSS feeds and R2 storage."""

import os
from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.responses import Response
from pydantic import BaseModel

app = FastAPI(title="Podcast Distribution Service", version="0.1.0")

# Lazy init
_publication_service = None


def get_service():
    """Get or create the singleton PublicationService instance."""
    global _publication_service
    if _publication_service is None:
        from services.distribution.publication_service import (
            PublicationService,
        )
        from services.distribution.r2_storage import R2StorageClient
        from services.distribution.rss_generator import PodcastFeedGenerator

        r2 = R2StorageClient(
            account_id=os.environ.get("R2_ACCOUNT_ID", ""),
            access_key_id=os.environ.get("R2_ACCESS_KEY_ID", ""),
            secret_access_key=os.environ.get("R2_SECRET_ACCESS_KEY", ""),
            bucket_name=os.environ.get(
                "R2_BUCKET_NAME", "kids-curiosity-club"
            ),
            cdn_base_url=os.environ.get(
                "CDN_BASE_URL", "https://cdn.kidscuriosityclub.com"
            ),
        )
        feed_gen = PodcastFeedGenerator(
            site_url=os.environ.get(
                "SITE_URL", "https://kidscuriosityclub.com"
            ),
            cdn_url=os.environ.get(
                "CDN_BASE_URL", "https://cdn.kidscuriosityclub.com"
            ),
        )
        _publication_service = PublicationService(
            r2_client=r2,
            feed_generator=feed_gen,
            data_dir=Path(os.environ.get("DATA_DIR", "/data")),
            feeds_dir=Path(os.environ.get("FEEDS_DIR", "/data/feeds")),
        )
    return _publication_service


class PublishRequest(BaseModel):
    """Request body for episode publication."""

    show_id: str
    episode_id: str
    audio_path: str
    title: str
    description: str = ""
    duration_seconds: float = 0.0
    episode_number: int = 1


@app.get("/health")
async def health():
    """Health check endpoint."""
    return {
        "status": "ok",
        "service": "distribution",
        "r2_configured": bool(os.environ.get("R2_ACCOUNT_ID")),
    }


@app.get("/feeds/{show_id}.xml")
async def get_feed(show_id: str):
    """Serve RSS feed for a show."""
    svc = get_service()
    feed_path = svc.feeds_dir / f"{show_id}.xml"
    if not feed_path.exists():
        # Generate on first request
        try:
            xml = svc.regenerate_feed(show_id)
        except Exception:
            raise HTTPException(404, f"Feed not found for show: {show_id}")
    else:
        xml = feed_path.read_text()
    return Response(content=xml, media_type="application/rss+xml")


@app.post("/feeds/{show_id}/regenerate")
async def regenerate_feed(show_id: str):
    """Regenerate RSS feed for a show."""
    svc = get_service()
    xml = svc.regenerate_feed(show_id)
    validation = svc.feed_gen.validate_feed(xml)
    return {
        "show_id": show_id,
        "regenerated": True,
        "validation": validation,
    }


@app.post("/feeds/{show_id}/validate")
async def validate_feed(show_id: str):
    """Validate the RSS feed for a show."""
    svc = get_service()
    feed_path = svc.feeds_dir / f"{show_id}.xml"
    if not feed_path.exists():
        raise HTTPException(404, "Feed not found")
    xml = feed_path.read_text()
    return svc.feed_gen.validate_feed(xml)


@app.post("/publish")
async def publish_episode(request: PublishRequest):
    """Publish an episode: upload to R2 and add to RSS feed."""
    svc = get_service()
    audio = Path(request.audio_path)
    if not audio.exists():
        raise HTTPException(
            400, f"Audio file not found: {request.audio_path}"
        )
    metadata = svc.publish_episode(
        show_id=request.show_id,
        episode_id=request.episode_id,
        audio_path=audio,
        title=request.title,
        description=request.description,
        duration_seconds=request.duration_seconds,
        episode_number=request.episode_number,
    )
    return metadata.model_dump()


@app.post("/unpublish/{show_id}/{episode_id}")
async def unpublish_episode(show_id: str, episode_id: str):
    """Unpublish an episode from the RSS feed."""
    svc = get_service()
    metadata = svc.unpublish_episode(show_id, episode_id)
    return metadata.model_dump()


@app.get("/status/{show_id}/{episode_id}")
async def get_status(show_id: str, episode_id: str):
    """Get publication status for an episode."""
    svc = get_service()
    metadata = svc.get_publication_status(show_id, episode_id)
    return metadata.model_dump()
