"""ElevenLabs TTS provider implementation."""

from pathlib import Path
from typing import Any

from pydub import AudioSegment

from services.tts.base import BaseTTSProvider


class ElevenLabsProvider(BaseTTSProvider):
    """ElevenLabs TTS provider using the elevenlabs SDK."""

    # Pricing: $0.30 per 1K characters
    COST_PER_1K_CHARS = 0.30

    def __init__(self, api_key: str) -> None:
        """Initialize ElevenLabs provider.

        Args:
            api_key: ElevenLabs API key
        """
        self.api_key = api_key

    def synthesize(
        self,
        text: str,
        voice_id: str,
        output_path: Path,
        **kwargs: Any,
    ) -> dict[str, Any]:
        """Synthesize speech using ElevenLabs API.

        Args:
            text: Text to convert to speech
            voice_id: ElevenLabs voice ID
            output_path: Path to save audio file
            **kwargs: Additional parameters:
                - stability: Voice stability (0.0-1.0, default 0.5)
                - similarity_boost: Clarity/similarity (0.0-1.0, default 0.75)
                - style: Style exaggeration (0.0-1.0, default 0.0)
                - use_speaker_boost: Enable speaker boost (default True)

        Returns:
            dict with keys: "duration" (float), "characters" (int), "audio_path" (Path)

        Raises:
            ImportError: If elevenlabs package is not installed
        """
        try:
            from elevenlabs import VoiceSettings, generate, save
        except ImportError:
            raise ImportError(
                "elevenlabs package is required. Install with: pip install elevenlabs"
            )

        # Extract voice settings from kwargs
        stability = kwargs.get("stability", 0.5)
        similarity_boost = kwargs.get("similarity_boost", 0.75)
        style = kwargs.get("style", 0.0)
        use_speaker_boost = kwargs.get("use_speaker_boost", True)

        # Create parent directory if it doesn't exist
        output_path.parent.mkdir(parents=True, exist_ok=True)

        # Generate audio using ElevenLabs
        audio = generate(
            text=text,
            voice=voice_id,
            model="eleven_multilingual_v2",
            api_key=self.api_key,
            voice_settings=VoiceSettings(
                stability=stability,
                similarity_boost=similarity_boost,
                style=style,
                use_speaker_boost=use_speaker_boost,
            ),
        )

        # Save audio file
        save(audio, str(output_path))

        # Get audio duration using pydub
        audio_segment = AudioSegment.from_mp3(output_path)
        duration = len(audio_segment) / 1000.0  # Convert to seconds

        return {
            "duration": duration,
            "characters": len(text),
            "audio_path": output_path,
            "voice_id": voice_id,
        }

    def list_voices(self) -> list[dict[str, Any]]:
        """List available ElevenLabs voices.

        Returns:
            List of voice dictionaries

        Raises:
            ImportError: If elevenlabs package is not installed
        """
        try:
            from elevenlabs import voices
        except ImportError:
            raise ImportError(
                "elevenlabs package is required. Install with: pip install elevenlabs"
            )

        voice_list = voices(api_key=self.api_key)
        return [
            {
                "voice_id": v.voice_id,
                "name": v.name,
                "labels": v.labels if hasattr(v, "labels") else {},
            }
            for v in voice_list
        ]

    def get_cost(self, characters: int) -> float:
        """Calculate cost for ElevenLabs synthesis.

        Args:
            characters: Number of characters to synthesize

        Returns:
            Cost in USD
        """
        return characters * self.COST_PER_1K_CHARS / 1000
