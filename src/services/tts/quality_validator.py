"""Audio quality validation utilities."""

from pathlib import Path
from typing import Any

from pydantic import BaseModel, Field
from pydub import AudioSegment


class AudioQualityReport(BaseModel):
    """Report of audio quality validation."""

    file_path: Path = Field(..., description="Path to audio file")
    is_valid: bool = Field(..., description="Whether audio meets quality standards")
    format_valid: bool = Field(..., description="Whether format is valid (MP3)")
    duration_valid: bool = Field(..., description="Whether duration is within range")
    silence_valid: bool = Field(..., description="Whether audio is not silent/corrupt")
    actual_duration: float = Field(..., description="Actual audio duration in seconds")
    expected_duration: float | None = Field(
        None, description="Expected duration in seconds"
    )
    sample_rate: int = Field(..., description="Sample rate in Hz")
    channels: int = Field(..., description="Number of audio channels")
    frame_count: int = Field(..., description="Number of audio frames")
    issues: list[str] = Field(
        default_factory=list, description="List of quality issues found"
    )


class AudioQualityValidator:
    """Validator for audio quality standards."""

    # Quality standards
    TARGET_SAMPLE_RATE = 44100  # 44.1 kHz
    ACCEPTABLE_FORMATS = ["mp3", "wav"]
    DURATION_TOLERANCE = 0.10  # ±10%
    MIN_DURATION_SECONDS = 0.3  # Minimum 0.3 seconds
    SILENCE_THRESHOLD_DB = -50.0  # Consider silent if below this
    MAX_SILENCE_DURATION = 2.0  # Max 2 seconds of complete silence

    def __init__(
        self,
        target_sample_rate: int = TARGET_SAMPLE_RATE,
        duration_tolerance: float = DURATION_TOLERANCE,
    ):
        """Initialize quality validator.

        Args:
            target_sample_rate: Target sample rate in Hz
            duration_tolerance: Duration tolerance as percentage (0.1 = 10%)
        """
        self.target_sample_rate = target_sample_rate
        self.duration_tolerance = duration_tolerance

    def validate_format(self, audio_path: Path) -> tuple[bool, str]:
        """Validate audio file format.

        Args:
            audio_path: Path to audio file

        Returns:
            Tuple of (is_valid, error_message)
        """
        # Check file exists
        if not audio_path.exists():
            return False, "Audio file does not exist"

        # Check file extension
        extension = audio_path.suffix.lower().lstrip(".")
        if extension not in self.ACCEPTABLE_FORMATS:
            return (
                False,
                f"Invalid format: {extension}. "
                f"Must be one of {self.ACCEPTABLE_FORMATS}",
            )

        try:
            # Try to load the audio
            if extension == "mp3":
                AudioSegment.from_mp3(audio_path)
            elif extension == "wav":
                AudioSegment.from_wav(audio_path)
            return True, ""
        except Exception as e:
            return False, f"Failed to load audio file: {str(e)}"

    def validate_duration(
        self,
        audio_path: Path,
        expected_duration: float | None = None,
        text: str | None = None,
    ) -> tuple[bool, str, float]:
        """Validate audio duration matches expected length.

        Args:
            audio_path: Path to audio file
            expected_duration: Expected duration in seconds
            text: Optional text to estimate duration from (150 words/min)

        Returns:
            Tuple of (is_valid, error_message, actual_duration)
        """
        try:
            audio = AudioSegment.from_mp3(audio_path)
            actual_duration = len(audio) / 1000.0  # Convert to seconds

            # Check minimum duration
            if actual_duration < self.MIN_DURATION_SECONDS:
                return (
                    False,
                    f"Duration too short: {actual_duration:.2f}s "
                    f"(min: {self.MIN_DURATION_SECONDS}s)",
                    actual_duration,
                )

            # If expected duration provided, validate within tolerance
            if expected_duration is not None:
                tolerance = expected_duration * self.duration_tolerance
                if not (
                    expected_duration - tolerance
                    <= actual_duration
                    <= expected_duration + tolerance
                ):
                    return (
                        False,
                        f"Duration mismatch: {actual_duration:.2f}s vs "
                        f"expected {expected_duration:.2f}s "
                        f"(tolerance: ±{tolerance:.2f}s)",
                        actual_duration,
                    )

            # If text provided, estimate duration and validate
            if text is not None:
                words = len(text.split())
                estimated_duration = (words / 150) * 60  # 150 words per minute
                tolerance = estimated_duration * self.duration_tolerance
                if not (
                    estimated_duration - tolerance
                    <= actual_duration
                    <= estimated_duration + tolerance
                ):
                    return (
                        False,
                        f"Duration vs text mismatch: {actual_duration:.2f}s "
                        f"for {words} words "
                        f"(expected ~{estimated_duration:.2f}s)",
                        actual_duration,
                    )

            return True, "", actual_duration

        except Exception as e:
            return False, f"Failed to validate duration: {str(e)}", 0.0

    def detect_silence(self, audio_path: Path) -> tuple[bool, str]:
        """Detect if audio is silent or corrupt.

        Args:
            audio_path: Path to audio file

        Returns:
            Tuple of (is_valid, error_message)
        """
        try:
            audio = AudioSegment.from_mp3(audio_path)

            # Check if audio is completely silent
            if audio.dBFS == float("-inf"):
                return False, "Audio is completely silent"

            # Check if audio is too quiet
            if audio.dBFS < self.SILENCE_THRESHOLD_DB:
                return (
                    False,
                    f"Audio is too quiet: {audio.dBFS:.1f} dBFS "
                    f"(threshold: {self.SILENCE_THRESHOLD_DB} dBFS)",
                )

            # Check for long silence periods
            # Split audio into 100ms chunks and check each
            chunk_size = 100  # ms
            silent_chunks = 0
            max_silent_chunks = int(self.MAX_SILENCE_DURATION * 1000 / chunk_size)

            for i in range(0, len(audio), chunk_size):
                chunk = audio[i : i + chunk_size]
                if chunk.dBFS < self.SILENCE_THRESHOLD_DB:
                    silent_chunks += 1
                    if silent_chunks >= max_silent_chunks:
                        return (
                            False,
                            f"Audio contains prolonged silence "
                            f"(>{self.MAX_SILENCE_DURATION}s)",
                        )
                else:
                    silent_chunks = 0

            return True, ""

        except Exception as e:
            return False, f"Failed to detect silence: {str(e)}"

    def get_audio_info(self, audio_path: Path) -> dict[str, Any]:
        """Get technical information about audio file.

        Args:
            audio_path: Path to audio file

        Returns:
            Dictionary with audio information
        """
        try:
            audio = AudioSegment.from_mp3(audio_path)
            return {
                "duration": len(audio) / 1000.0,
                "sample_rate": audio.frame_rate,
                "channels": audio.channels,
                "frame_count": audio.frame_count(),
                "frame_width": audio.frame_width,
                "loudness": audio.dBFS,
            }
        except Exception as e:
            return {"error": str(e)}

    def measure_loudness(self, audio_path: Path) -> float:
        """Measure audio loudness in dBFS.

        Args:
            audio_path: Path to audio file

        Returns:
            Loudness in dBFS
        """
        try:
            audio = AudioSegment.from_mp3(audio_path)
            return audio.dBFS
        except Exception:
            return float("-inf")

    def validate_audio(
        self,
        audio_path: Path,
        expected_duration: float | None = None,
        text: str | None = None,
    ) -> AudioQualityReport:
        """Perform comprehensive audio quality validation.

        Args:
            audio_path: Path to audio file
            expected_duration: Optional expected duration in seconds
            text: Optional text for duration estimation

        Returns:
            AudioQualityReport with validation results
        """
        issues = []
        format_valid = True
        duration_valid = True
        silence_valid = True
        actual_duration = 0.0
        sample_rate = 0
        channels = 0
        frame_count = 0

        # Validate format
        format_ok, format_msg = self.validate_format(audio_path)
        if not format_ok:
            format_valid = False
            issues.append(format_msg)

        # Get audio info
        if format_valid:
            info = self.get_audio_info(audio_path)
            if "error" not in info:
                actual_duration = info["duration"]
                sample_rate = info["sample_rate"]
                channels = info["channels"]
                frame_count = info["frame_count"]

                # Validate duration
                duration_ok, duration_msg, actual_duration = self.validate_duration(
                    audio_path, expected_duration, text
                )
                if not duration_ok:
                    duration_valid = False
                    issues.append(duration_msg)

                # Detect silence
                silence_ok, silence_msg = self.detect_silence(audio_path)
                if not silence_ok:
                    silence_valid = False
                    issues.append(silence_msg)

        # Overall validity
        is_valid = format_valid and duration_valid and silence_valid

        return AudioQualityReport(
            file_path=audio_path,
            is_valid=is_valid,
            format_valid=format_valid,
            duration_valid=duration_valid,
            silence_valid=silence_valid,
            actual_duration=actual_duration,
            expected_duration=expected_duration,
            sample_rate=sample_rate,
            channels=channels,
            frame_count=frame_count,
            issues=issues,
        )

    def generate_quality_report(
        self, audio_files: list[Path], text_map: dict[Path, str] | None = None
    ) -> list[AudioQualityReport]:
        """Generate quality reports for multiple audio files.

        Args:
            audio_files: List of audio file paths
            text_map: Optional mapping of file paths to text for duration validation

        Returns:
            List of AudioQualityReport objects
        """
        reports = []
        for audio_path in audio_files:
            text = text_map.get(audio_path) if text_map else None
            report = self.validate_audio(audio_path, text=text)
            reports.append(report)
        return reports
