"""VibeVoice TTS API server.

Wraps VibeVoice 1.5B inference in a FastAPI application, exposing
single-speaker and multi-speaker synthesis endpoints.
"""

from __future__ import annotations

import logging
import os
import tempfile
from contextlib import asynccontextmanager
from enum import Enum
from typing import Any

import torch
from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from pydantic import BaseModel
from starlette.background import BackgroundTask

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Schemas
# ---------------------------------------------------------------------------


class Speaker(str, Enum):
    NARRATOR = "narrator"
    OLIVER = "oliver the inventor"
    LILY = "lily"
    MAX = "max"
    AISHA = "aisha"
    MRS_CHEN = "mrs. chen"


# VibeVoice expects "Speaker N:" format. Map characters to speaker numbers.
# Max 4 simultaneous speakers per synthesis call.
SPEAKER_MAP: dict[Speaker, dict[str, str]] = {
    Speaker.NARRATOR: {"id": "1", "description": "Warm, engaging narrator"},
    Speaker.OLIVER: {"id": "2", "description": "Curious, enthusiastic boy"},
    Speaker.LILY: {"id": "3", "description": "Thoughtful, creative girl"},
    Speaker.MAX: {"id": "4", "description": "Energetic, adventurous boy"},
    Speaker.AISHA: {"id": "1", "description": "Clever, observant girl"},
    Speaker.MRS_CHEN: {"id": "2", "description": "Kind, knowledgeable teacher"},
}


class TTSRequest(BaseModel):
    text: str
    speaker: str = "narrator"
    emotion: str | None = None
    speed: float = 1.0


class DialogueSegment(BaseModel):
    speaker: str
    text: str
    emotion: str | None = None


class MultiSpeakerRequest(BaseModel):
    segments: list[DialogueSegment]
    output_format: str = "wav"


class SpeakerInfo(BaseModel):
    name: str
    speaker_name: str
    description: str


# ---------------------------------------------------------------------------
# Global model + processor
# ---------------------------------------------------------------------------

_model: Any = None
_processor: Any = None
_tokenizer: Any = None


def get_model():
    """Load VibeVoice model and processor."""
    global _model, _processor, _tokenizer  # noqa: PLW0603

    if _model is not None:
        return _model, _processor, _tokenizer

    model_path = os.environ.get("VIBEVOICE_MODEL", "microsoft/VibeVoice-1.5B")
    device = "cuda" if torch.cuda.is_available() else "cpu"
    dtype = torch.bfloat16 if device == "cuda" else torch.float32

    logger.info("Loading VibeVoice from %s on %s (%s)", model_path, device, dtype)

    from vibevoice.modular.modeling_vibevoice_inference import (
        VibeVoiceForConditionalGenerationInference,
    )
    from vibevoice.processor.vibevoice_processor import VibeVoiceProcessor

    _processor = VibeVoiceProcessor.from_pretrained(model_path)
    _tokenizer = _processor.tokenizer
    _model = VibeVoiceForConditionalGenerationInference.from_pretrained(
        model_path,
        torch_dtype=dtype,
        attn_implementation="sdpa",
    ).to(device)
    _model.eval()
    logger.info("VibeVoice model loaded on %s", device)

    return _model, _processor, _tokenizer


def _resolve_speaker(name: str) -> dict[str, str]:
    try:
        return SPEAKER_MAP[Speaker(name)]
    except ValueError:
        return SPEAKER_MAP[Speaker.NARRATOR]


# ---------------------------------------------------------------------------
# Lifespan
# ---------------------------------------------------------------------------


@asynccontextmanager
async def lifespan(app: FastAPI):
    try:
        get_model()
    except Exception as e:
        logger.warning("Model not available at startup: %s", e)
    yield


app = FastAPI(title="VibeVoice TTS Service", version="0.1.0", lifespan=lifespan)

# Allow browser access from the test dashboard (different port)
from starlette.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------


@app.get("/health")
async def health() -> dict[str, Any]:
    gpu_available = torch.cuda.is_available()
    gpu_name = torch.cuda.get_device_name(0) if gpu_available else None
    gpu_memory = None
    if gpu_available:
        mem = torch.cuda.mem_get_info(0)
        gpu_memory = {
            "free_gb": round(mem[0] / 1e9, 2),
            "total_gb": round(mem[1] / 1e9, 2),
        }
    return {
        "status": "ok",
        "service": "tts",
        "model": os.environ.get("VIBEVOICE_MODEL", "microsoft/VibeVoice-1.5B"),
        "model_loaded": _model is not None,
        "gpu_available": gpu_available,
        "gpu_name": gpu_name,
        "gpu_memory": gpu_memory,
    }


@app.post("/v1/tts/synthesize")
async def synthesize(request: TTSRequest) -> FileResponse:
    """Synthesize speech for a single speaker."""
    model, processor, tokenizer = get_model()

    try:
        speaker_info = _resolve_speaker(request.speaker)
        # VibeVoice expects "Speaker N: text" format
        script = f"Speaker {speaker_info['id']}: {request.text}"

        inputs = processor(
            text=[script],
            voice_samples=None,
            padding=True,
            return_tensors="pt",
            return_attention_mask=True,
        )
        inputs = {k: v.to(model.device) for k, v in inputs.items() if hasattr(v, "to")}

        with torch.no_grad():
            output = model.generate(
                **inputs,
                cfg_scale=1.3,
                tokenizer=tokenizer,
                generation_config={"do_sample": False},
            )

        audio = output.speech_outputs if hasattr(output, "speech_outputs") else output
        out_dir = tempfile.mkdtemp()
        saved_paths = processor.save_audio(audio, os.path.join(out_dir, "out.wav"))

        # save_audio returns a list of paths; serve the first one
        if saved_paths and os.path.isfile(saved_paths[0]):
            wav_path = saved_paths[0]
        else:
            # Fallback: look for any .wav in the output dir
            wavs = [
                os.path.join(out_dir, f)
                for f in os.listdir(out_dir) if f.endswith(".wav")
            ]
            wav_path = wavs[0] if wavs else os.path.join(out_dir, "out.wav")

        return FileResponse(
                wav_path,
                media_type="audio/wav",
                filename="output.wav",
                background=BackgroundTask(lambda p: __import__('shutil').rmtree(os.path.dirname(p), ignore_errors=True), wav_path),
            )
    except torch.cuda.OutOfMemoryError:
        torch.cuda.empty_cache()
        raise HTTPException(
            503, "GPU out of memory — try shorter text or restart container"
        )
    except Exception as exc:
        raise HTTPException(500, f"Synthesis failed: {exc}") from exc


@app.post("/v1/tts/synthesize-multi")
async def synthesize_multi(request: MultiSpeakerRequest) -> FileResponse:
    """Synthesize multi-speaker dialogue."""
    model, processor, tokenizer = get_model()

    try:
        # Build script in VibeVoice format: "Speaker N: text"
        lines = []
        for seg in request.segments:
            info = _resolve_speaker(seg.speaker)
            lines.append(f"Speaker {info['id']}: {seg.text}")
        script = "\n".join(lines)

        inputs = processor(
            text=[script],
            voice_samples=None,
            padding=True,
            return_tensors="pt",
            return_attention_mask=True,
        )
        inputs = {k: v.to(model.device) for k, v in inputs.items() if hasattr(v, "to")}

        with torch.no_grad():
            output = model.generate(
                **inputs,
                cfg_scale=1.3,
                tokenizer=tokenizer,
                generation_config={"do_sample": False},
            )

        audio = output.speech_outputs if hasattr(output, "speech_outputs") else output
        out_dir = tempfile.mkdtemp()
        saved_paths = processor.save_audio(audio, os.path.join(out_dir, "out.wav"))

        if saved_paths and os.path.isfile(saved_paths[0]):
            wav_path = saved_paths[0]
        else:
            wavs = [
                os.path.join(out_dir, f)
                for f in os.listdir(out_dir) if f.endswith(".wav")
            ]
            wav_path = wavs[0] if wavs else os.path.join(out_dir, "out.wav")

        return FileResponse(
                wav_path,
                media_type="audio/wav",
                filename="dialogue.wav",
                background=BackgroundTask(lambda p: __import__('shutil').rmtree(os.path.dirname(p), ignore_errors=True), wav_path),
            )
    except torch.cuda.OutOfMemoryError:
        torch.cuda.empty_cache()
        raise HTTPException(
            503, "GPU out of memory — try shorter text or restart container"
        )
    except Exception as exc:
        raise HTTPException(500, f"Multi-speaker synthesis failed: {exc}") from exc


@app.get("/v1/tts/speakers")
async def list_speakers() -> list[SpeakerInfo]:
    return [
        SpeakerInfo(
            name=speaker.value,
            speaker_name=f"Speaker {info['id']}",
            description=info["description"],
        )
        for speaker, info in SPEAKER_MAP.items()
    ]
