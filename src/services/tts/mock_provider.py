"""Mock TTS provider for cost-free testing."""

from pathlib import Path
from typing import Any

from pydub import AudioSegment
from pydub.generators import WhiteNoise

from services.tts.base import BaseTTSProvider


class MockTTSProvider(BaseTTSProvider):
    """Mock TTS provider that generates silent audio files."""

    def __init__(self, fast_mode: bool = False, add_noise: bool = False) -> None:
        """Initialize mock TTS provider.

        Args:
            fast_mode: If True, skip actual audio generation and return metadata only
            add_noise: If True, add background noise for realism
        """
        self.fast_mode = fast_mode
        self.add_noise = add_noise

    def synthesize(
        self,
        text: str,
        voice_id: str,
        output_path: Path,
        **kwargs: Any,
    ) -> dict[str, Any]:
        """Synthesize mock speech by generating silent audio.

        Args:
            text: Text to convert to speech (used for duration calculation)
            voice_id: Voice identifier (ignored in mock mode)
            output_path: Path to save audio file
            **kwargs: Additional parameters (ignored in mock mode)

        Returns:
            dict with keys: "duration" (float), "characters" (int), "audio_path" (Path)
        """
        # Calculate duration based on text length (150 words per minute)
        words = len(text.split())
        duration_seconds = (words / 150) * 60

        # Minimum duration of 0.5 seconds
        duration_seconds = max(duration_seconds, 0.5)
        duration_ms = int(duration_seconds * 1000)

        if not self.fast_mode:
            # Create parent directory if it doesn't exist
            output_path.parent.mkdir(parents=True, exist_ok=True)

            # Generate audio
            if self.add_noise:
                # Create white noise for realism
                noise = WhiteNoise().to_audio_segment(duration=duration_ms)
                # Make it very quiet
                audio = noise - 40  # Reduce by 40 dB
            else:
                # Create silent audio
                audio = AudioSegment.silent(duration=duration_ms)

            # Export as MP3
            audio.export(str(output_path), format="mp3")
        else:
            # Fast mode: Just create an empty file
            output_path.parent.mkdir(parents=True, exist_ok=True)
            output_path.touch()

        return {
            "duration": duration_seconds,
            "characters": len(text),
            "audio_path": output_path,
            "voice_id": voice_id,
        }

    def list_voices(self) -> list[dict[str, Any]]:
        """List available mock voices.

        Returns:
            List of mock voice configurations
        """
        return [
            {
                "voice_id": "mock_narrator",
                "name": "Mock Narrator",
                "labels": {"gender": "neutral", "age": "adult"},
            },
            {
                "voice_id": "mock_oliver",
                "name": "Mock Oliver",
                "labels": {"gender": "male", "age": "child"},
            },
            {
                "voice_id": "mock_hannah",
                "name": "Mock Hannah",
                "labels": {"gender": "female", "age": "child"},
            },
            {
                "voice_id": "mock_test",
                "name": "Mock Test Character",
                "labels": {"gender": "neutral", "age": "child"},
            },
        ]

    def get_cost(self, characters: int) -> float:
        """Calculate cost for mock provider (always $0).

        Args:
            characters: Number of characters (ignored)

        Returns:
            Cost in USD (always 0.0)
        """
        return 0.0
