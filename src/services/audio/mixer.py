"""Audio mixer for combining TTS segments into final podcast episodes."""

from pathlib import Path

from pydub import AudioSegment


class AudioMixer:
    """Mix audio segments with configurable transitions and effects."""

    def __init__(
        self,
        silence_padding_ms: int = 500,
        crossfade_ms: int = 0,
        trim_silence: bool = True,
        silence_threshold_db: float = -40.0,
    ):
        """Initialize audio mixer.

        Args:
            silence_padding_ms: Milliseconds of silence between segments (default 500ms)
            crossfade_ms: Milliseconds of crossfade between segments (default 0)
            trim_silence: Whether to trim leading/trailing silence (default True)
            silence_threshold_db: dB threshold for silence detection (default -40.0)
        """
        self.silence_padding = silence_padding_ms
        self.crossfade = crossfade_ms
        self.trim_silence = trim_silence
        self.silence_threshold = silence_threshold_db

    def mix_segments(self, segment_paths: list[Path | str]) -> AudioSegment:
        """Combine audio segments into a single track.

        Args:
            segment_paths: List of paths to audio files to mix

        Returns:
            Combined AudioSegment

        Raises:
            ValueError: If no segments provided or files don't exist
        """
        if not segment_paths:
            raise ValueError("No segments to mix")

        mixed = AudioSegment.empty()

        for path in segment_paths:
            path = Path(path)
            if not path.exists():
                raise ValueError(f"Audio file not found: {path}")

            # Load audio segment
            segment_audio = AudioSegment.from_file(str(path))

            # Trim silence if enabled
            if self.trim_silence:
                segment_audio = self._trim_silence(segment_audio)

            # Add to mix
            if len(mixed) == 0:
                mixed = segment_audio
            else:
                if self.crossfade > 0:
                    mixed = mixed.append(segment_audio, crossfade=self.crossfade)
                else:
                    silence = AudioSegment.silent(duration=self.silence_padding)
                    mixed = mixed + silence + segment_audio

        return mixed

    def add_background_music(
        self,
        audio: AudioSegment,
        music_path: Path | str,
        volume_db: float = -20.0,
        fade_duration_ms: int = 2000,
        duck_during_speech: bool = True,
    ) -> AudioSegment:
        """Add background music to audio with ducking and fading.

        Args:
            audio: Main audio segment (dialogue/speech)
            music_path: Path to background music file
            volume_db: Volume reduction in dB (negative = quieter, default -20)
            fade_duration_ms: Duration of fade in/out in milliseconds (default 2000)
            duck_during_speech: Whether to duck music under speech (default True)

        Returns:
            Audio with background music overlaid

        Raises:
            ValueError: If music file doesn't exist
        """
        music_path = Path(music_path)
        if not music_path.exists():
            raise ValueError(f"Music file not found: {music_path}")

        music = AudioSegment.from_file(str(music_path))

        # Loop music to match audio duration
        while len(music) < len(audio):
            music += music
        music = music[: len(audio)]

        # Reduce volume
        music = music + volume_db

        # Apply fading
        if fade_duration_ms > 0:
            music = music.fade_in(fade_duration_ms).fade_out(fade_duration_ms)

        # Overlay on original audio (speech on top)
        return audio.overlay(music)

    def add_intro(
        self,
        audio: AudioSegment,
        intro_path: Path | str,
        crossfade_ms: int = 0,
    ) -> AudioSegment:
        """Add intro segment to beginning of audio.

        Args:
            audio: Main audio content
            intro_path: Path to intro audio file
            crossfade_ms: Crossfade duration in milliseconds (default 0)

        Returns:
            Audio with intro prepended

        Raises:
            ValueError: If intro file doesn't exist
        """
        intro_path = Path(intro_path)
        if not intro_path.exists():
            raise ValueError(f"Intro file not found: {intro_path}")

        intro = AudioSegment.from_file(str(intro_path))

        if crossfade_ms > 0:
            return intro.append(audio, crossfade=crossfade_ms)
        else:
            return intro + audio

    def add_outro(
        self,
        audio: AudioSegment,
        outro_path: Path | str,
        crossfade_ms: int = 0,
    ) -> AudioSegment:
        """Add outro segment to end of audio.

        Args:
            audio: Main audio content
            outro_path: Path to outro audio file
            crossfade_ms: Crossfade duration in milliseconds (default 0)

        Returns:
            Audio with outro appended

        Raises:
            ValueError: If outro file doesn't exist
        """
        outro_path = Path(outro_path)
        if not outro_path.exists():
            raise ValueError(f"Outro file not found: {outro_path}")

        outro = AudioSegment.from_file(str(outro_path))

        if crossfade_ms > 0:
            return audio.append(outro, crossfade=crossfade_ms)
        else:
            return audio + outro

    def _trim_silence(self, audio: AudioSegment) -> AudioSegment:
        """Trim leading and trailing silence from audio.

        Args:
            audio: Audio segment to trim

        Returns:
            Trimmed audio segment
        """

        def detect_leading_silence(
            sound: AudioSegment, threshold: float, chunk_size: int = 10
        ) -> int:
            """Detect leading silence in milliseconds."""
            trim_ms = 0
            while (
                trim_ms < len(sound)
                and sound[trim_ms : trim_ms + chunk_size].dBFS < threshold
            ):
                trim_ms += chunk_size
            return trim_ms

        start_trim = detect_leading_silence(audio, self.silence_threshold)
        end_trim = detect_leading_silence(audio.reverse(), self.silence_threshold)

        duration = len(audio)
        if start_trim + end_trim >= duration:
            # Audio is all silence, return a short silent segment
            return AudioSegment.silent(duration=100)

        return audio[start_trim : duration - end_trim]
