"""Audio effects for podcast production."""

import logging

from pydub import AudioSegment

logger = logging.getLogger(__name__)


class AudioEffects:
    """Audio effects processor for podcast enhancement."""

    def __init__(self):
        """Initialize audio effects processor."""
        pass

    def remove_long_silence(
        self,
        audio: AudioSegment,
        silence_threshold_ms: int = 2000,
        silence_db: float = -40.0,
    ) -> AudioSegment:
        """Remove silence longer than threshold.

        Args:
            audio: Audio segment to process
            silence_threshold_ms: Maximum allowed silence duration in ms (default 2000)
            silence_db: Silence detection threshold in dB (default -40.0)

        Returns:
            Audio with long silences removed
        """
        chunk_size = 10  # ms
        chunks = []
        silence_duration = 0

        for i in range(0, len(audio), chunk_size):
            chunk = audio[i : i + chunk_size]

            # Check if chunk is silent
            if chunk.dBFS < silence_db:
                silence_duration += chunk_size
                # Keep some silence but not too much
                if silence_duration <= silence_threshold_ms:
                    chunks.append(chunk)
            else:
                silence_duration = 0
                chunks.append(chunk)

        if not chunks:
            return AudioSegment.silent(duration=100)

        result = chunks[0]
        for chunk in chunks[1:]:
            result += chunk

        logger.info(f"Removed long silences (>{silence_threshold_ms}ms)")
        return result

    def adjust_speed(
        self, audio: AudioSegment, speed_factor: float = 1.0
    ) -> AudioSegment:
        """Adjust playback speed of audio.

        Args:
            audio: Audio segment to adjust
            speed_factor: Speed multiplier (1.0=normal, 1.1=10% faster, etc.)

        Returns:
            Speed-adjusted audio

        Raises:
            ValueError: If speed factor is out of valid range
        """
        if speed_factor <= 0 or speed_factor > 2.0:
            raise ValueError("Speed factor must be between 0 and 2.0")

        if speed_factor == 1.0:
            return audio

        # Change frame rate to adjust speed
        # Higher frame rate = faster playback
        sound_with_altered_frame_rate = audio._spawn(
            audio.raw_data, overrides={"frame_rate": int(audio.frame_rate * speed_factor)}
        )

        # Convert back to original sample rate to maintain pitch
        adjusted_audio = sound_with_altered_frame_rate.set_frame_rate(audio.frame_rate)

        logger.info(f"Adjusted speed to {speed_factor}x")
        return adjusted_audio

    def apply_fade(
        self,
        audio: AudioSegment,
        fade_in_ms: int = 0,
        fade_out_ms: int = 0,
    ) -> AudioSegment:
        """Apply fade in/out to audio.

        Args:
            audio: Audio segment to fade
            fade_in_ms: Fade in duration in milliseconds (default 0)
            fade_out_ms: Fade out duration in milliseconds (default 0)

        Returns:
            Audio with fades applied
        """
        result = audio

        if fade_in_ms > 0:
            result = result.fade_in(fade_in_ms)
            logger.info(f"Applied {fade_in_ms}ms fade in")

        if fade_out_ms > 0:
            result = result.fade_out(fade_out_ms)
            logger.info(f"Applied {fade_out_ms}ms fade out")

        return result

    def duck_audio(
        self,
        background: AudioSegment,
        foreground: AudioSegment,
        duck_db: float = -15.0,
    ) -> AudioSegment:
        """Duck background audio when foreground is present (volume reduction).

        Args:
            background: Background audio (e.g., music)
            foreground: Foreground audio (e.g., speech)
            duck_db: Volume reduction in dB for background (default -15.0)

        Returns:
            Background audio with ducking applied
        """
        # Simple implementation: reduce background volume globally
        # A more sophisticated version would detect speech regions
        ducked = background + duck_db
        logger.info(f"Applied audio ducking: {duck_db} dB")
        return ducked

    def add_silence(
        self, audio: AudioSegment, duration_ms: int, position: str = "end"
    ) -> AudioSegment:
        """Add silence to audio.

        Args:
            audio: Audio segment
            duration_ms: Duration of silence in milliseconds
            position: Where to add silence ("start", "end", default "end")

        Returns:
            Audio with silence added

        Raises:
            ValueError: If position is invalid
        """
        silence = AudioSegment.silent(duration=duration_ms)

        if position == "start":
            return silence + audio
        elif position == "end":
            return audio + silence
        else:
            raise ValueError(f"Invalid position: {position}. Use 'start' or 'end'")

    def normalize_volume(
        self, audio: AudioSegment, target_db: float = -20.0
    ) -> AudioSegment:
        """Normalize audio to target dB level.

        Args:
            audio: Audio segment to normalize
            target_db: Target dB level (default -20.0)

        Returns:
            Normalized audio
        """
        change_in_db = target_db - audio.dBFS
        normalized = audio + change_in_db
        logger.info(f"Normalized volume to {target_db} dB (change: {change_in_db:.2f} dB)")
        return normalized
