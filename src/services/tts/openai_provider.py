"""OpenAI TTS provider implementation."""

from pathlib import Path
from typing import Any

from pydub import AudioSegment

from services.tts.base import BaseTTSProvider


class OpenAITTSProvider(BaseTTSProvider):
    """OpenAI Text-to-Speech provider."""

    # Pricing: $15.00 per 1M characters for standard voices
    COST_PER_1M_CHARS = 15.00

    def __init__(self, api_key: str) -> None:
        """Initialize OpenAI TTS provider.

        Args:
            api_key: OpenAI API key
        """
        self.api_key = api_key

    def synthesize(
        self,
        text: str,
        voice_id: str,
        output_path: Path,
        **kwargs: Any,
    ) -> dict[str, Any]:
        """Synthesize speech using OpenAI TTS.

        Args:
            text: Text to convert to speech
            voice_id: OpenAI voice name (alloy, echo, fable, onyx, nova, shimmer)
            output_path: Path to save audio file
            **kwargs: Additional parameters:
                - model: TTS model (default 'tts-1', options: 'tts-1', 'tts-1-hd')
                - speed: Speed of speech (0.25-4.0, default 1.0)

        Returns:
            dict with keys: "duration" (float), "characters" (int), "audio_path" (Path)

        Raises:
            ImportError: If openai package is not installed
        """
        try:
            from openai import OpenAI
        except ImportError:
            raise ImportError(
                "openai package is required. Install with: pip install openai"
            )

        # Initialize client
        client = OpenAI(api_key=self.api_key)

        # Extract parameters
        model = kwargs.get("model", "tts-1")
        speed = kwargs.get("speed", 1.0)

        # Create parent directory if it doesn't exist
        output_path.parent.mkdir(parents=True, exist_ok=True)

        # Perform TTS request
        response = client.audio.speech.create(
            model=model,
            voice=voice_id,
            input=text,
            speed=speed,
        )

        # Write the response to the output file
        response.stream_to_file(str(output_path))

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
        """List available OpenAI TTS voices.

        Returns:
            List of voice dictionaries
        """
        # OpenAI TTS has a fixed set of voices
        return [
            {
                "voice_id": "alloy",
                "name": "Alloy",
                "labels": {"gender": "neutral", "description": "Balanced and neutral"},
            },
            {
                "voice_id": "echo",
                "name": "Echo",
                "labels": {"gender": "male", "description": "Warm and engaging"},
            },
            {
                "voice_id": "fable",
                "name": "Fable",
                "labels": {
                    "gender": "male",
                    "description": "Expressive and storytelling",
                },
            },
            {
                "voice_id": "onyx",
                "name": "Onyx",
                "labels": {"gender": "male", "description": "Deep and authoritative"},
            },
            {
                "voice_id": "nova",
                "name": "Nova",
                "labels": {"gender": "female", "description": "Bright and energetic"},
            },
            {
                "voice_id": "shimmer",
                "name": "Shimmer",
                "labels": {"gender": "female", "description": "Soft and calm"},
            },
        ]

    def get_cost(self, characters: int) -> float:
        """Calculate cost for OpenAI TTS synthesis.

        Args:
            characters: Number of characters to synthesize

        Returns:
            Cost in USD
        """
        return characters * self.COST_PER_1M_CHARS / 1_000_000
