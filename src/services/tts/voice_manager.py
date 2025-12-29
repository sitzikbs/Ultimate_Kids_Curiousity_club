"""Voice management and configuration utilities."""

from pathlib import Path
from typing import Any

from services.tts.base import BaseTTSProvider


class VoiceManager:
    """Manager for voice configuration and validation."""

    # Default emotion mappings for providers that support them
    DEFAULT_EMOTION_MAPPINGS = {
        "excited": {"stability": 0.3, "style": 0.8},
        "calm": {"stability": 0.7, "style": 0.2},
        "curious": {"stability": 0.5, "style": 0.5},
        "surprised": {"stability": 0.4, "style": 0.7},
        "thoughtful": {"stability": 0.6, "style": 0.3},
        "happy": {"stability": 0.4, "style": 0.6},
        "serious": {"stability": 0.7, "style": 0.4},
    }

    def __init__(self, tts_provider: BaseTTSProvider, sample_dir: Path | None = None):
        """Initialize voice manager.

        Args:
            tts_provider: TTS provider instance
            sample_dir: Optional directory to store voice samples
        """
        self.tts_provider = tts_provider
        self.sample_dir = sample_dir
        if self.sample_dir:
            self.sample_dir.mkdir(parents=True, exist_ok=True)

    def validate_voice_id(self, voice_id: str) -> bool:
        """Validate that a voice ID exists for the current provider.

        Args:
            voice_id: Voice ID to validate

        Returns:
            True if voice exists, False otherwise
        """
        try:
            voices = self.tts_provider.list_voices()
            return any(voice["voice_id"] == voice_id for voice in voices)
        except Exception:
            # If we can't list voices, assume the voice is valid
            return True

    def get_voice_info(self, voice_id: str) -> dict[str, Any] | None:
        """Get information about a specific voice.

        Args:
            voice_id: Voice ID to look up

        Returns:
            Voice info dict or None if not found
        """
        try:
            voices = self.tts_provider.list_voices()
            for voice in voices:
                if voice["voice_id"] == voice_id:
                    return voice
            return None
        except Exception:
            return None

    def list_available_voices(
        self, filter_language: str | None = None
    ) -> list[dict[str, Any]]:
        """List all available voices, optionally filtered by language.

        Args:
            filter_language: Optional language code to filter by (e.g., 'en-US')

        Returns:
            List of voice info dicts
        """
        voices = self.tts_provider.list_voices()

        if not filter_language:
            return voices

        # Filter by language if specified
        filtered = []
        for voice in voices:
            labels = voice.get("labels", {})
            # Check if language code is in labels
            if isinstance(labels, dict):
                if "language_codes" in labels:
                    if filter_language in labels["language_codes"]:
                        filtered.append(voice)

        return filtered if filtered else voices

    def map_emotion_to_params(
        self, emotion: str, base_params: dict[str, Any] | None = None
    ) -> dict[str, Any]:
        """Map an emotion tag to provider-specific voice parameters.

        Args:
            emotion: Emotion tag (e.g., 'excited', 'calm')
            base_params: Optional base parameters to merge with

        Returns:
            Dictionary of voice parameters
        """
        params = base_params.copy() if base_params else {}

        # Get emotion mapping
        emotion_params = self.DEFAULT_EMOTION_MAPPINGS.get(emotion.lower(), {})

        # Merge with base params (emotion params override base)
        params.update(emotion_params)

        return params

    def preview_voice(
        self,
        voice_id: str,
        sample_text: str = "Hello! This is a sample of my voice.",
        output_filename: str | None = None,
        **kwargs: Any,
    ) -> Path:
        """Generate a preview audio sample for a voice.

        Args:
            voice_id: Voice ID to preview
            sample_text: Text to synthesize for the preview
            output_filename: Optional output filename (default: voice_id_preview.mp3)
            **kwargs: Additional voice parameters

        Returns:
            Path to the generated preview file

        Raises:
            ValueError: If sample_dir was not set during initialization
        """
        if not self.sample_dir:
            raise ValueError("sample_dir must be set to generate voice previews")

        # Determine output filename
        if not output_filename:
            output_filename = f"{voice_id}_preview.mp3"

        output_path = self.sample_dir / output_filename

        # Synthesize preview
        self.tts_provider.synthesize(
            text=sample_text,
            voice_id=voice_id,
            output_path=output_path,
            **kwargs,
        )

        return output_path

    def clone_voice(
        self,
        name: str,
        description: str,
        reference_audio_path: Path,
        **kwargs: Any,
    ) -> str:
        """Clone a voice from reference audio (ElevenLabs specific).

        Args:
            name: Name for the cloned voice
            description: Description of the voice
            reference_audio_path: Path to reference audio file
            **kwargs: Additional parameters for voice cloning

        Returns:
            Voice ID of the cloned voice

        Raises:
            NotImplementedError: If provider doesn't support voice cloning
        """
        # Check if provider supports voice cloning
        provider_name = type(self.tts_provider).__name__

        if "ElevenLabs" in provider_name:
            return self._clone_elevenlabs_voice(
                name, description, reference_audio_path, **kwargs
            )
        else:
            raise NotImplementedError(
                f"Voice cloning is not supported for {provider_name}"
            )

    def _clone_elevenlabs_voice(
        self,
        name: str,
        description: str,
        reference_audio_path: Path,
        **kwargs: Any,
    ) -> str:
        """Clone a voice using ElevenLabs API.

        Args:
            name: Name for the cloned voice
            description: Description of the voice
            reference_audio_path: Path to reference audio file
            **kwargs: Additional parameters

        Returns:
            Voice ID of the cloned voice

        Raises:
            ImportError: If elevenlabs package is not installed
        """
        try:
            from elevenlabs import clone
        except ImportError:
            raise ImportError(
                "elevenlabs package is required for voice cloning. "
                "Install with: pip install elevenlabs"
            )

        # Get API key from provider
        api_key = getattr(self.tts_provider, "api_key", None)
        if not api_key:
            raise ValueError("ElevenLabs API key is required for voice cloning")

        # Clone the voice
        voice = clone(
            name=name,
            description=description,
            files=[str(reference_audio_path)],
            api_key=api_key,
        )

        return voice.voice_id

    def validate_voice_config(self, voice_config: dict[str, Any]) -> tuple[bool, str]:
        """Validate a voice configuration dictionary.

        Args:
            voice_config: Voice configuration to validate

        Returns:
            Tuple of (is_valid, error_message)
        """
        # Check required fields
        if "voice_id" not in voice_config:
            return False, "Missing required field: voice_id"

        # Validate voice ID exists
        voice_id = voice_config["voice_id"]
        if not self.validate_voice_id(voice_id):
            return False, f"Voice ID '{voice_id}' not found in provider"

        # Validate parameter ranges if present
        if "stability" in voice_config:
            stability = voice_config["stability"]
            if not 0.0 <= stability <= 1.0:
                return False, "stability must be between 0.0 and 1.0"

        if "similarity_boost" in voice_config:
            similarity_boost = voice_config["similarity_boost"]
            if not 0.0 <= similarity_boost <= 1.0:
                return False, "similarity_boost must be between 0.0 and 1.0"

        if "style" in voice_config:
            style = voice_config["style"]
            if not 0.0 <= style <= 1.0:
                return False, "style must be between 0.0 and 1.0"

        return True, ""
