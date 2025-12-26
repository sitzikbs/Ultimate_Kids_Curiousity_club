"""Audio synthesis service for converting script segments to audio."""

from pathlib import Path
from typing import Any

from pydantic import BaseModel, Field
from pydub import AudioSegment

from services.tts.base import BaseTTSProvider


class AudioSegmentResult(BaseModel):
    """Result of synthesizing an audio segment."""

    segment_number: int = Field(..., description="Segment sequence number")
    character_id: str = Field(..., description="Character ID")
    text: str = Field(..., description="Text that was synthesized")
    audio_path: Path = Field(..., description="Path to generated audio file")
    duration: float = Field(..., description="Duration in seconds")
    characters: int = Field(..., description="Number of characters synthesized")


class AudioSynthesisService:
    """Service for converting script segments to audio files."""

    # Maximum characters per chunk to avoid provider limits
    MAX_CHARS_PER_CHUNK = 5000

    # Silence padding between segments in seconds
    DEFAULT_PADDING_SECONDS = 0.75

    def __init__(
        self,
        tts_provider: BaseTTSProvider,
        output_dir: Path,
        padding_seconds: float = DEFAULT_PADDING_SECONDS,
    ) -> None:
        """Initialize audio synthesis service.

        Args:
            tts_provider: TTS provider instance to use for synthesis
            output_dir: Directory to save generated audio files
            padding_seconds: Silence padding between segments (default 0.75)
        """
        self.tts_provider = tts_provider
        self.output_dir = output_dir
        self.padding_seconds = padding_seconds

        # Create output directory if it doesn't exist
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def _chunk_text(self, text: str, max_chars: int = MAX_CHARS_PER_CHUNK) -> list[str]:
        """Split long text into chunks at sentence boundaries.

        Args:
            text: Text to split
            max_chars: Maximum characters per chunk

        Returns:
            List of text chunks
        """
        if len(text) <= max_chars:
            return [text]

        # Split on sentence boundaries
        sentences = text.replace("! ", "!|").replace("? ", "?|").replace(". ", ".|")
        sentences = [s.strip() for s in sentences.split("|") if s.strip()]

        chunks = []
        current_chunk = ""

        for sentence in sentences:
            # If adding this sentence would exceed max, start a new chunk
            if current_chunk and len(current_chunk) + len(sentence) + 1 > max_chars:
                chunks.append(current_chunk.strip())
                current_chunk = sentence
            else:
                # Add sentence to current chunk
                if current_chunk:
                    current_chunk += " " + sentence
                else:
                    current_chunk = sentence

        # Add the last chunk
        if current_chunk:
            chunks.append(current_chunk.strip())

        return chunks

    def synthesize_segment(
        self,
        text: str,
        character_id: str,
        voice_config: dict[str, Any],
        segment_number: int,
        emotion: str | None = None,
    ) -> AudioSegmentResult:
        """Synthesize a single script segment to audio.

        Args:
            text: Text to synthesize
            character_id: Character ID for file naming
            voice_config: Voice configuration dict with provider, voice_id, etc.
            segment_number: Segment sequence number for file naming
            emotion: Optional emotion tag to map to voice parameters

        Returns:
            AudioSegmentResult with audio path and metadata
        """
        # Determine output file name
        output_filename = f"segment_{segment_number:03d}_{character_id}.mp3"
        output_path = self.output_dir / output_filename

        # Extract voice parameters
        voice_id = voice_config.get("voice_id", "mock_narrator")
        voice_params = {
            "stability": voice_config.get("stability", 0.5),
            "similarity_boost": voice_config.get("similarity_boost", 0.75),
        }

        # Apply emotion mapping if emotion is specified
        if emotion and "emotion_mappings" in voice_config:
            emotion_params = voice_config["emotion_mappings"].get(emotion, {})
            voice_params.update(emotion_params)

        # Handle long text by chunking
        text_chunks = self._chunk_text(text)

        if len(text_chunks) == 1:
            # Single chunk - synthesize directly
            result = self.tts_provider.synthesize(
                text=text,
                voice_id=voice_id,
                output_path=output_path,
                **voice_params,
            )
        else:
            # Multiple chunks - synthesize and concatenate
            chunk_segments = []
            for idx, chunk in enumerate(text_chunks):
                chunk_path = self.output_dir / f"chunk_{segment_number}_{idx}.mp3"
                self.tts_provider.synthesize(
                    text=chunk,
                    voice_id=voice_id,
                    output_path=chunk_path,
                    **voice_params,
                )
                chunk_segments.append(AudioSegment.from_mp3(chunk_path))
                # Clean up chunk file
                chunk_path.unlink()

            # Concatenate chunks
            combined = sum(chunk_segments)
            combined.export(str(output_path), format="mp3")

            result = {
                "duration": len(combined) / 1000.0,
                "characters": len(text),
                "audio_path": output_path,
            }

        return AudioSegmentResult(
            segment_number=segment_number,
            character_id=character_id,
            text=text,
            audio_path=result["audio_path"],
            duration=result["duration"],
            characters=result["characters"],
        )

    def synthesize_batch(
        self,
        segments: list[dict[str, Any]],
        add_padding: bool = True,
    ) -> list[AudioSegmentResult]:
        """Synthesize multiple segments in batch.

        Args:
            segments: List of segment dicts with keys:
                - text: Text to synthesize
                - character_id: Character ID
                - voice_config: Voice configuration dict
                - segment_number: Segment number
                - emotion: Optional emotion tag
            add_padding: If True, add silence padding between segments

        Returns:
            List of AudioSegmentResult objects
        """
        results = []

        for segment in segments:
            result = self.synthesize_segment(
                text=segment["text"],
                character_id=segment["character_id"],
                voice_config=segment["voice_config"],
                segment_number=segment["segment_number"],
                emotion=segment.get("emotion"),
            )
            results.append(result)

            # Add padding if requested
            if add_padding and len(results) < len(segments):
                padding_path = (
                    self.output_dir
                    / f"padding_{segment['segment_number']:03d}.mp3"
                )
                padding_ms = int(self.padding_seconds * 1000)
                silence = AudioSegment.silent(duration=padding_ms)
                silence.export(str(padding_path), format="mp3")

                # Create padding result
                padding_result = AudioSegmentResult(
                    segment_number=segment["segment_number"],
                    character_id="_padding",
                    text="",
                    audio_path=padding_path,
                    duration=self.padding_seconds,
                    characters=0,
                )
                results.append(padding_result)

        return results

    def get_total_duration(self, results: list[AudioSegmentResult]) -> float:
        """Calculate total duration of all synthesized segments.

        Args:
            results: List of AudioSegmentResult objects

        Returns:
            Total duration in seconds
        """
        return sum(result.duration for result in results)

    def get_total_cost(self, results: list[AudioSegmentResult]) -> float:
        """Calculate total cost of all synthesized segments.

        Args:
            results: List of AudioSegmentResult objects

        Returns:
            Total cost in USD
        """
        total_chars = sum(result.characters for result in results)
        return self.tts_provider.get_cost(total_chars)
