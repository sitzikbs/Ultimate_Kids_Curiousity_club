"""Audio loudness normalization using LUFS standard."""

import logging

import numpy as np
import pyloudnorm as pyln
from pydub import AudioSegment

logger = logging.getLogger(__name__)


class LoudnessNormalizer:
    """Normalize audio loudness to podcast standards."""

    def __init__(self, target_lufs: float = -16.0, sample_rate: int = 44100):
        """Initialize loudness normalizer.

        Args:
            target_lufs: Target loudness in LUFS (default -16.0 for podcasts)
            sample_rate: Audio sample rate in Hz (default 44100)
        """
        self.target_lufs = target_lufs
        self.sample_rate = sample_rate
        self.meter = pyln.Meter(sample_rate)

    def normalize(self, audio: AudioSegment) -> AudioSegment:
        """Normalize audio to target LUFS.

        Args:
            audio: Audio segment to normalize

        Returns:
            Normalized audio segment

        Note:
            If the audio sample rate differs from the configured sample rate,
            it will be resampled before normalization and then restored.
        """
        # Check if sample rate matches
        original_sample_rate = audio.frame_rate
        if original_sample_rate != self.sample_rate:
            logger.info(
                f"Resampling audio from {original_sample_rate}Hz "
                f"to {self.sample_rate}Hz for loudness measurement"
            )
            # Resample to the meter's sample rate
            audio_for_measurement = audio.set_frame_rate(self.sample_rate)
        else:
            audio_for_measurement = audio

        # Convert to numpy array for loudness measurement
        samples = np.array(
            audio_for_measurement.get_array_of_samples(), dtype=np.float32
        )

        # Handle stereo audio
        if audio_for_measurement.channels == 2:
            samples = samples.reshape((-1, 2))

        # Normalize to -1 to 1 range
        samples = samples / (2 ** (audio_for_measurement.sample_width * 8 - 1))

        # Measure loudness
        try:
            loudness = self.meter.integrated_loudness(samples)
        except Exception as e:
            logger.warning(f"Error measuring loudness: {e}, skipping normalization")
            return audio

        # Calculate gain needed
        gain_db = self.target_lufs - loudness

        logger.info(
            f"Measured loudness: {loudness:.2f} LUFS, "
            f"applying gain: {gain_db:.2f} dB to reach {self.target_lufs} LUFS"
        )

        # Apply gain
        normalized = audio + gain_db

        # Apply limiter to prevent clipping
        normalized = self._apply_limiter(normalized)

        return normalized

    def measure_loudness(self, audio: AudioSegment) -> float:
        """Measure loudness of audio in LUFS.

        Args:
            audio: Audio segment to measure

        Returns:
            Loudness in LUFS

        Note:
            If the audio sample rate differs from the configured sample rate,
            it will be resampled before measurement.
        """
        # Check if sample rate matches
        if audio.frame_rate != self.sample_rate:
            logger.info(
                f"Resampling audio from {audio.frame_rate}Hz "
                f"to {self.sample_rate}Hz for loudness measurement"
            )
            audio = audio.set_frame_rate(self.sample_rate)

        samples = np.array(audio.get_array_of_samples(), dtype=np.float32)

        # Handle stereo audio
        if audio.channels == 2:
            samples = samples.reshape((-1, 2))

        # Normalize to -1 to 1 range
        samples = samples / (2 ** (audio.sample_width * 8 - 1))

        try:
            loudness = self.meter.integrated_loudness(samples)
            return loudness
        except Exception as e:
            logger.error(f"Error measuring loudness: {e}")
            return 0.0

    def _apply_limiter(
        self, audio: AudioSegment, threshold_db: float = -1.0
    ) -> AudioSegment:
        """Apply peak limiter to prevent clipping.

        Args:
            audio: Audio segment to limit
            threshold_db: Peak threshold in dB (default -1.0)

        Returns:
            Limited audio segment
        """
        # Simple peak limiting
        if audio.max_dBFS > threshold_db:
            gain_reduction = threshold_db - audio.max_dBFS
            audio = audio + gain_reduction
            logger.info(
                f"Applied limiting: {gain_reduction:.2f} dB "
                f"to keep peaks below {threshold_db} dB"
            )

        return audio

    def get_loudness_stats(self, audio: AudioSegment) -> dict[str, float]:
        """Get detailed loudness statistics.

        Args:
            audio: Audio segment to analyze

        Returns:
            Dictionary with loudness statistics
        """
        loudness = self.measure_loudness(audio)

        return {
            "integrated_lufs": loudness,
            "peak_db": audio.max_dBFS,
            "rms_db": audio.dBFS,
            "target_lufs": self.target_lufs,
            "gain_needed_db": self.target_lufs - loudness,
        }
