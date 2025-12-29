"""Base TTS provider interface."""

from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any


class BaseTTSProvider(ABC):
    """Abstract base class for TTS providers."""

    @abstractmethod
    def synthesize(
        self,
        text: str,
        voice_id: str,
        output_path: Path,
        **kwargs: Any,
    ) -> dict[str, Any]:
        """Synthesize speech from text.

        Args:
            text: Text to convert to speech
            voice_id: Provider-specific voice identifier
            output_path: Path to save audio file
            **kwargs: Provider-specific parameters (stability, speed, etc.)

        Returns:
            dict with keys: "duration" (float), "characters" (int), "audio_path" (Path)
        """
        pass

    @abstractmethod
    def list_voices(self) -> list[dict[str, Any]]:
        """List available voices for this provider.

        Returns:
            List of voice dictionaries with keys: voice_id, name, labels
        """
        pass

    @abstractmethod
    def get_cost(self, characters: int) -> float:
        """Calculate cost in USD for character count.

        Args:
            characters: Number of characters to synthesize

        Returns:
            Cost in USD
        """
        pass
