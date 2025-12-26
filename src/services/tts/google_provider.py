"""Google Cloud TTS provider implementation."""

from pathlib import Path
from typing import Any

from pydub import AudioSegment

from services.tts.base import BaseTTSProvider


class GoogleTTSProvider(BaseTTSProvider):
    """Google Cloud Text-to-Speech provider."""

    # Pricing: $4.00 per 1 million characters for WaveNet voices
    COST_PER_1M_CHARS = 4.00

    def __init__(self, credentials_path: str | None = None) -> None:
        """Initialize Google TTS provider.

        Args:
            credentials_path: Path to Google Cloud credentials JSON file.
                            If None, will use default credentials.
        """
        self.credentials_path = credentials_path

    def synthesize(
        self,
        text: str,
        voice_id: str,
        output_path: Path,
        **kwargs: Any,
    ) -> dict[str, Any]:
        """Synthesize speech using Google Cloud TTS.

        Args:
            text: Text to convert to speech
            voice_id: Google Cloud voice name (e.g., 'en-US-Wavenet-A')
            output_path: Path to save audio file
            **kwargs: Additional parameters:
                - language_code: Language code (default 'en-US')
                - speaking_rate: Speaking rate (0.25-4.0, default 1.0)
                - pitch: Voice pitch (-20.0-20.0, default 0.0)
                - volume_gain_db: Volume adjustment (default 0.0)

        Returns:
            dict with keys: "duration" (float), "characters" (int), "audio_path" (Path)

        Raises:
            ImportError: If google-cloud-texttospeech package is not installed
        """
        try:
            from google.cloud import texttospeech
        except ImportError:
            raise ImportError(
                "google-cloud-texttospeech is required. "
                "Install with: pip install google-cloud-texttospeech"
            )

        # Initialize client
        if self.credentials_path:
            import os

            os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = self.credentials_path
        client = texttospeech.TextToSpeechClient()

        # Extract parameters
        language_code = kwargs.get("language_code", "en-US")
        speaking_rate = kwargs.get("speaking_rate", 1.0)
        pitch = kwargs.get("pitch", 0.0)
        volume_gain_db = kwargs.get("volume_gain_db", 0.0)

        # Set the text input to be synthesized
        synthesis_input = texttospeech.SynthesisInput(text=text)

        # Build the voice request
        voice = texttospeech.VoiceSelectionParams(
            language_code=language_code,
            name=voice_id,
        )

        # Select the type of audio file
        audio_config = texttospeech.AudioConfig(
            audio_encoding=texttospeech.AudioEncoding.MP3,
            speaking_rate=speaking_rate,
            pitch=pitch,
            volume_gain_db=volume_gain_db,
        )

        # Perform the text-to-speech request
        response = client.synthesize_speech(
            input=synthesis_input, voice=voice, audio_config=audio_config
        )

        # Create parent directory if it doesn't exist
        output_path.parent.mkdir(parents=True, exist_ok=True)

        # Write the response to the output file
        with open(output_path, "wb") as out:
            out.write(response.audio_content)

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
        """List available Google Cloud TTS voices.

        Returns:
            List of voice dictionaries

        Raises:
            ImportError: If google-cloud-texttospeech package is not installed
        """
        try:
            from google.cloud import texttospeech
        except ImportError:
            raise ImportError(
                "google-cloud-texttospeech is required. "
                "Install with: pip install google-cloud-texttospeech"
            )

        # Initialize client
        if self.credentials_path:
            import os

            os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = self.credentials_path
        client = texttospeech.TextToSpeechClient()

        # Performs the list voices request
        voices = client.list_voices()

        return [
            {
                "voice_id": voice.name,
                "name": voice.name,
                "labels": {
                    "language_codes": voice.language_codes,
                    "ssml_gender": voice.ssml_gender.name,
                },
            }
            for voice in voices.voices
        ]

    def get_cost(self, characters: int) -> float:
        """Calculate cost for Google TTS synthesis.

        Args:
            characters: Number of characters to synthesize

        Returns:
            Cost in USD
        """
        return characters * self.COST_PER_1M_CHARS / 1_000_000
