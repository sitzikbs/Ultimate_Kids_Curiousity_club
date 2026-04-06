"""VibeVoice TTS API server.

Wraps VibeVoice inference in a FastAPI application, exposing single-speaker
and multi-speaker synthesis endpoints for the podcast pipeline.
"""

from __future__ import annotations

import tempfile
from enum import Enum
from typing import Any

from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from pydantic import BaseModel

app = FastAPI(title="VibeVoice TTS Service", version="0.1.0")

# ---------------------------------------------------------------------------
# Models
# ---------------------------------------------------------------------------


class Speaker(str, Enum):
    """Known podcast characters."""

    NARRATOR = "narrator"
    OLIVER = "oliver the inventor"
    LILY = "lily"
    MAX = "max"
    AISHA = "aisha"
    MRS_CHEN = "mrs. chen"


SPEAKER_MAP: dict[Speaker, dict[str, str]] = {
    Speaker.NARRATOR: {
        "speaker_id": "S1",
        "description": "Warm, engaging narrator",
    },
    Speaker.OLIVER: {
        "speaker_id": "S2",
        "description": "Curious, enthusiastic boy",
    },
    Speaker.LILY: {
        "speaker_id": "S3",
        "description": "Thoughtful, creative girl",
    },
    Speaker.MAX: {
        "speaker_id": "S4",
        "description": "Energetic, adventurous boy",
    },
    Speaker.AISHA: {
        "speaker_id": "S1",
        "description": "Clever, observant girl",
    },
    Speaker.MRS_CHEN: {
        "speaker_id": "S2",
        "description": "Kind, knowledgeable teacher",
    },
}


class TTSRequest(BaseModel):
    """Single-speaker synthesis request."""

    text: str
    speaker: str = "narrator"
    emotion: str | None = None
    speed: float = 1.0


class DialogueSegment(BaseModel):
    """One segment of a multi-speaker dialogue."""

    speaker: str
    text: str
    emotion: str | None = None


class MultiSpeakerRequest(BaseModel):
    """Multi-speaker dialogue synthesis request."""

    segments: list[DialogueSegment]
    output_format: str = "mp3"


class SpeakerInfo(BaseModel):
    """Public speaker metadata returned by the listing endpoint."""

    name: str
    speaker_id: str
    description: str


# ---------------------------------------------------------------------------
# Global model reference (lazy-loaded)
# ---------------------------------------------------------------------------

_model: Any = None
_model_loading: bool = False


def get_model() -> Any:
    """Lazy-load the VibeVoice model.

    Returns:
        The loaded VibeVoice model instance.

    Raises:
        RuntimeError: If the model cannot be loaded.
    """
    global _model, _model_loading  # noqa: PLW0603
    if _model is not None:
        return _model
    if _model_loading:
        return None

    _model_loading = True
    try:
        from vibevoice import VibeVoiceTTS  # type: ignore[import-untyped]

        # Try HuggingFace Hub first, fall back to local path
        try:
            _model = VibeVoiceTTS.from_pretrained("microsoft/VibeVoice-1.5B")
        except Exception:
            _model = VibeVoiceTTS.from_pretrained("/app/models/vibevoice-1.5b")
        _model = _model.cuda()
    except Exception as exc:
        _model_loading = False
        raise RuntimeError(f"Failed to load VibeVoice model: {exc}") from exc

    _model_loading = False
    return _model


def _resolve_speaker(name: str) -> dict[str, str]:
    """Map a speaker name string to its SPEAKER_MAP entry."""
    try:
        return SPEAKER_MAP[Speaker(name)]
    except ValueError:
        return SPEAKER_MAP[Speaker.NARRATOR]


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------


@app.get("/health")
async def health() -> dict[str, Any]:
    """Return service health including GPU status."""
    import torch

    gpu_available = torch.cuda.is_available()
    gpu_name = torch.cuda.get_device_name(0) if gpu_available else None
    gpu_memory: dict[str, float] | None = None
    if gpu_available:
        mem = torch.cuda.mem_get_info(0)
        gpu_memory = {
            "free_gb": round(mem[0] / 1e9, 2),
            "total_gb": round(mem[1] / 1e9, 2),
        }

    return {
        "status": "ok",
        "service": "tts",
        "model": "vibevoice-1.5b",
        "model_loaded": _model is not None,
        "gpu_available": gpu_available,
        "gpu_name": gpu_name,
        "gpu_memory": gpu_memory,
    }


@app.post("/v1/tts/synthesize")
async def synthesize(request: TTSRequest) -> FileResponse:
    """Synthesize speech from text for a single speaker."""
    model = get_model()
    if model is None:
        raise HTTPException(status_code=503, detail="Model not loaded yet")

    try:
        speaker_info = _resolve_speaker(request.speaker)
        audio = model.synthesize(
            text=request.text,
            speaker=speaker_info["speaker_id"],
            speed=request.speed,
        )

        with tempfile.NamedTemporaryFile(suffix=".mp3", delete=False) as fh:
            audio.save(fh.name)
            return FileResponse(
                fh.name,
                media_type="audio/mpeg",
                filename="output.mp3",
            )
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Synthesis failed: {exc}") from exc


@app.post("/v1/tts/synthesize-multi")
async def synthesize_multi(
    request: MultiSpeakerRequest,
) -> FileResponse:
    """Synthesize multi-speaker dialogue."""
    model = get_model()
    if model is None:
        raise HTTPException(status_code=503, detail="Model not loaded yet")

    try:
        dialogue_parts = []
        for seg in request.segments:
            speaker_info = _resolve_speaker(seg.speaker)
            dialogue_parts.append(
                {
                    "speaker": speaker_info["speaker_id"],
                    "text": seg.text,
                }
            )

        audio = model.synthesize_dialogue(dialogue_parts)
        suffix = ".mp3" if request.output_format == "mp3" else ".wav"
        media_type = "audio/mpeg" if request.output_format == "mp3" else "audio/wav"

        with tempfile.NamedTemporaryFile(suffix=suffix, delete=False) as fh:
            audio.save(fh.name, format=request.output_format)
            return FileResponse(
                fh.name,
                media_type=media_type,
                filename=f"dialogue{suffix}",
            )
    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=f"Multi-speaker synthesis failed: {exc}",
        ) from exc


@app.get("/v1/tts/speakers")
async def list_speakers() -> list[SpeakerInfo]:
    """List all available speakers and their metadata."""
    return [
        SpeakerInfo(
            name=speaker.value,
            speaker_id=info["speaker_id"],
            description=info["description"],
        )
        for speaker, info in SPEAKER_MAP.items()
    ]
