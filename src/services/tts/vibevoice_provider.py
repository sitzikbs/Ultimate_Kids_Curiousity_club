"""VibeVoice TTS provider -- calls the containerized VibeVoice API server."""

from __future__ import annotations

import logging
import tempfile
from pathlib import Path
from typing import Any

import httpx

from services.tts.base import BaseTTSProvider

logger = logging.getLogger(__name__)

# Speaker names recognised by the VibeVoice API server.
VIBEVOICE_SPEAKERS: list[dict[str, Any]] = [
    {
        "voice_id": "narrator",
        "name": "Narrator",
        "labels": {
            "description": "Warm, engaging narrator",
        },
    },
    {
        "voice_id": "oliver the inventor",
        "name": "Oliver the Inventor",
        "labels": {
            "description": "Curious, enthusiastic boy",
        },
    },
    {
        "voice_id": "lily",
        "name": "Lily",
        "labels": {
            "description": "Thoughtful, creative girl",
        },
    },
    {
        "voice_id": "max",
        "name": "Max",
        "labels": {
            "description": "Energetic, adventurous boy",
        },
    },
    {
        "voice_id": "aisha",
        "name": "Aisha",
        "labels": {
            "description": "Clever, observant girl",
        },
    },
    {
        "voice_id": "mrs. chen",
        "name": "Mrs. Chen",
        "labels": {
            "description": "Kind, knowledgeable teacher",
        },
    },
]


class VibeVoiceProvider(BaseTTSProvider):
    """TTS provider using a local VibeVoice server via HTTP API.

    The server is expected to be running inside the ``docker/tts``
    container and exposes single- and multi-speaker synthesis endpoints.
    """

    def __init__(
        self,
        base_url: str = "http://tts:8100",
        timeout: float = 300.0,
    ) -> None:
        """Initialise the VibeVoice provider.

        Args:
            base_url: Root URL of the VibeVoice API server.
            timeout: HTTP request timeout in seconds.
        """
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout

    def synthesize(
        self,
        text: str,
        voice_id: str,
        output_path: Path,
        **kwargs: Any,
    ) -> dict[str, Any]:
        """Synthesize speech from text via the VibeVoice API.

        Args:
            text: Text to convert to speech.
            voice_id: Character / speaker name recognised by the server
                (e.g. ``"narrator"``, ``"oliver the inventor"``).
            output_path: Path to save the resulting audio file.
            **kwargs: Additional parameters forwarded to the API:
                - speed (float): Speech speed multiplier (default 1.0).
                - emotion (str | None): Emotion hint for synthesis.

        Returns:
            Dict with keys ``duration``, ``characters``, ``audio_path``,
            and ``voice_id``.

        Raises:
            httpx.HTTPStatusError: On non-2xx responses from the server.
            httpx.ConnectError: When the server is unreachable.
        """
        speed: float = kwargs.get("speed", 1.0)
        emotion: str | None = kwargs.get("emotion")

        response = httpx.post(
            f"{self.base_url}/v1/tts/synthesize",
            json={
                "text": text,
                "speaker": voice_id,
                "emotion": emotion,
                "speed": speed,
            },
            timeout=self.timeout,
        )
        response.raise_for_status()

        # Persist received audio bytes
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_bytes(response.content)

        logger.info(
            "Synthesized %d chars for '%s' -> %s (%d bytes)",
            len(text),
            voice_id,
            output_path,
            len(response.content),
        )

        # Estimate duration (~150 words/min, ~5 chars/word)
        estimated_duration = len(text) / (150 * 5 / 60)

        return {
            "duration": estimated_duration,
            "characters": len(text),
            "audio_path": output_path,
            "voice_id": voice_id,
        }

    async def synthesize_dialogue(
        self,
        segments: list[dict[str, str]],
        output_format: str = "mp3",
    ) -> Path:
        """Synthesize multi-speaker dialogue via the API.

        Args:
            segments: List of dicts with ``speaker`` and ``text`` keys.
            output_format: Audio format (``mp3`` or ``wav``).

        Returns:
            Path to the generated audio file.

        Raises:
            httpx.HTTPStatusError: On non-2xx responses.
        """
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            response = await client.post(
                f"{self.base_url}/v1/tts/synthesize-multi",
                json={
                    "segments": segments,
                    "output_format": output_format,
                },
            )
            response.raise_for_status()

        with tempfile.NamedTemporaryFile(
            delete=False, suffix=f".{output_format}", prefix="dialogue_"
        ) as fh:
            output_path = Path(fh.name)
        output_path.write_bytes(response.content)
        return output_path

    def list_voices(self) -> list[dict[str, Any]]:
        """List available VibeVoice speakers.

        Returns:
            List of voice dictionaries with ``voice_id``, ``name``,
            and ``labels`` keys.
        """
        return VIBEVOICE_SPEAKERS

    def get_cost(self, characters: int) -> float:
        """Calculate cost for VibeVoice synthesis.

        VibeVoice runs locally so there is no per-character cost.

        Args:
            characters: Number of characters (unused).

        Returns:
            Always ``0.0``.
        """
        return 0.0
