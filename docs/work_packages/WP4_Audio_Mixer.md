# WP4: Audio Mixing & Final Production

**Status**: ⏳ Not Started  
**Dependencies**: WP3 (TTS Service)  
**Estimated Effort**: 2-3 days  
**Owner**: TBD  
**Subsystem:** Audio Production

## 📋 Overview

Audio Mixer combines individual TTS-generated audio segments (narrator + character voices) into a final podcast episode with background music, intro/outro, and professional audio effects. Handles loudness normalization, crossfading, and MP3 export with ID3 tags for podcast distribution.

**Key Deliverables**:
- Audio mixing engine using pydub
- Background music integration (optional)
- Intro/outro support
- Loudness normalization (LUFS)
- MP3 export with ID3 tags (title, artist, album art)
- Audio effects (crossfade, silence trimming)

**System Context**:
- **Subsystem:** Audio Production
- **Depends on:** WP3 (TTS Service), WP1 (Foundation - AudioSegment models)
- **Used by:** WP6 (Orchestrator)
- **Parallel Development:** ✅ Can develop in parallel with WP2, WP3, WP5 after WP1 complete

## 🎯 High-Level Tasks

### Task 4.1: Audio Mixing Engine
Core audio mixing functionality.

**Subtasks**:
- [ ] 4.1.1: Create `AudioMixer` class
- [ ] 4.1.2: Implement `mix_segments(segments: list[AudioSegment]) -> AudioSegment` method
- [ ] 4.1.3: Add silence padding between segments (configurable, default 0.5s)
- [ ] 4.1.4: Implement crossfade transitions (optional, 100-300ms)
- [ ] 4.1.5: Trim leading/trailing silence from segments
- [ ] 4.1.6: Support stereo and mono audio mixing

**Expected Outputs**:
- `src/services/audio/mixer.py`
- Mixing configuration options

### Task 4.2: Background Music
Add optional background music to episodes.

**Subtasks**:
- [ ] 4.2.1: Implement `add_background_music(audio: AudioSegment, music_path: Path, volume: float) -> AudioSegment` method
- [ ] 4.2.2: Loop music to match episode duration
- [ ] 4.2.3: Duck background music during speech (reduce volume by 15-20 dB)
- [ ] 4.2.4: Fade in music at start, fade out at end
- [ ] 4.2.5: Support multiple music tracks (intro, main, outro)

**Expected Outputs**:
- Background music integration logic
- Sample royalty-free music tracks in `data/audio/music/`

### Task 4.3: Intro/Outro Support
Add branded intro and outro segments.

**Subtasks**:
- [ ] 4.3.1: Implement `add_intro(audio: AudioSegment, intro_path: Path) -> AudioSegment` method
- [ ] 4.3.2: Implement `add_outro(audio: AudioSegment, outro_path: Path) -> AudioSegment` method
- [ ] 4.3.3: Support custom intro/outro per episode or use defaults
- [ ] 4.3.4: Crossfade intro into main content
- [ ] 4.3.5: Create sample intro/outro audio files

**Expected Outputs**:
- Intro/outro integration logic
- Sample intro/outro files in `data/audio/branding/`

### Task 4.4: Loudness Normalization
Ensure consistent volume across all episodes.

**Subtasks**:
- [ ] 4.4.1: Implement LUFS measurement using pyloudnorm
- [ ] 4.4.2: Normalize to -16 LUFS (podcast standard)
- [ ] 4.4.3: Apply limiting to prevent clipping
- [ ] 4.4.4: Log loudness statistics for quality monitoring
- [ ] 4.4.5: Add optional dynamic range compression

**Expected Outputs**:
- `src/services/audio/normalization.py`
- Loudness measurement and normalization logic

### Task 4.5: MP3 Export with ID3 Tags
Export final audio with podcast metadata.

**Subtasks**:
- [ ] 4.5.1: Implement `export_mp3(audio: AudioSegment, output_path: Path, metadata: dict) -> None` method
- [ ] 4.5.2: Add ID3 tags: title, artist, album, genre, year
- [ ] 4.5.3: Embed album art (episode-specific or default podcast logo)
- [ ] 4.5.4: Set MP3 quality (192 kbps VBR or 128 kbps CBR)
- [ ] 4.5.5: Add comment field with generation metadata (date, cost, models used)

**Expected Outputs**:
- `src/services/audio/exporter.py`
- ID3 tagging logic using mutagen

### Task 4.6: Audio Effects
Additional audio processing effects.

**Subtasks**:
- [ ] 4.6.1: Implement silence removal (trim >2s silence between segments)
- [ ] 4.6.2: Implement speed adjustment (1.0x, 1.1x, 1.2x playback speed)
- [ ] 4.6.3: Add optional reverb for specific characters
- [ ] 4.6.4: Implement audio ducking (automatic volume adjustment during speech)
- [ ] 4.6.5: Add audio waveform visualization (optional, for debugging)

**Expected Outputs**:
- `src/services/audio/effects.py`
- Effect application utilities

### Task 4.7: Integration Testing
Validate complete audio mixing pipeline.

**Subtasks**:
- [ ] 4.7.1: Test mixing 2-character dialogue (Oliver + Hannah)
- [ ] 4.7.2: Test background music integration
- [ ] 4.7.3: Test intro/outro addition
- [ ] 4.7.4: Test loudness normalization accuracy
- [ ] 4.7.5: Validate ID3 tags in exported MP3
- [ ] 4.7.6: Test edge cases (very short episodes, single character)

**Expected Outputs**:
- Integration test suite in `tests/test_audio_mixer_integration.py`

## 🔧 Technical Specifications

### AudioMixer Implementation
```python
from pydub import AudioSegment
from pathlib import Path

class AudioMixer:
    def __init__(
        self,
        silence_padding_ms: int = 500,
        crossfade_ms: int = 0,
        trim_silence: bool = True
    ):
        self.silence_padding = silence_padding_ms
        self.crossfade = crossfade_ms
        self.trim_silence = trim_silence
    
    def mix_segments(self, segments: list[AudioSegment]) -> AudioSegment:
        """Combine audio segments into a single track."""
        if not segments:
            raise ValueError("No segments to mix")
        
        mixed = AudioSegment.empty()
        
        for segment in segments:
            # Trim silence if enabled
            if self.trim_silence:
                segment_audio = self._trim_silence(segment.audio_path)
            else:
                segment_audio = AudioSegment.from_mp3(segment.audio_path)
            
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
    
    def _trim_silence(self, audio_path: Path, threshold_db: float = -40.0) -> AudioSegment:
        """Trim leading and trailing silence."""
        audio = AudioSegment.from_mp3(audio_path)
        
        def detect_leading_silence(sound, threshold, chunk_size=10):
            trim_ms = 0
            while sound[trim_ms:trim_ms+chunk_size].dBFS < threshold and trim_ms < len(sound):
                trim_ms += chunk_size
            return trim_ms
        
        start_trim = detect_leading_silence(audio, threshold_db)
        end_trim = detect_leading_silence(audio.reverse(), threshold_db)
        
        return audio[start_trim:len(audio)-end_trim]
```

### Background Music Integration
```python
def add_background_music(
    audio: AudioSegment,
    music_path: Path,
    volume_db: float = -20.0,
    fade_duration_ms: int = 2000
) -> AudioSegment:
    """Add background music with ducking."""
    music = AudioSegment.from_mp3(music_path)
    
    # Loop music to match audio duration
    while len(music) < len(audio):
        music += music
    music = music[:len(audio)]
    
    # Reduce volume
    music = music + volume_db
    
    # Fade in/out
    music = music.fade_in(fade_duration_ms).fade_out(fade_duration_ms)
    
    # Overlay on original audio
    return audio.overlay(music)
```

### Loudness Normalization
```python
import pyloudnorm as pyln
import numpy as np

class LoudnessNormalizer:
    def __init__(self, target_lufs: float = -16.0):
        self.target_lufs = target_lufs
        self.meter = pyln.Meter(44100)  # Sample rate
    
    def normalize(self, audio: AudioSegment) -> AudioSegment:
        """Normalize audio to target LUFS."""
        # Convert to numpy array
        samples = np.array(audio.get_array_of_samples(), dtype=np.float32)
        samples = samples / (2**15)  # Normalize to -1 to 1
        
        # Measure loudness
        loudness = self.meter.integrated_loudness(samples)
        
        # Calculate gain
        gain_db = self.target_lufs - loudness
        
        # Apply gain
        normalized = audio + gain_db
        
        # Apply limiter to prevent clipping
        return self._apply_limiter(normalized)
    
    def _apply_limiter(self, audio: AudioSegment, threshold_db: float = -1.0) -> AudioSegment:
        """Prevent audio clipping."""
        # Simple peak limiting
        if audio.max_dBFS > threshold_db:
            gain_reduction = threshold_db - audio.max_dBFS
            audio = audio + gain_reduction
        return audio
```

### ID3 Tag Export
```python
from mutagen.easyid3 import EasyID3
from mutagen.id3 import ID3, APIC
from pathlib import Path

class MP3Exporter:
    def export(
        self,
        audio: AudioSegment,
        output_path: Path,
        metadata: dict[str, Any],
        album_art_path: Path | None = None
    ) -> None:
        """Export audio as MP3 with ID3 tags."""
        # Export audio
        audio.export(
            output_path,
            format="mp3",
            bitrate="192k",
            parameters=["-q:a", "0"]  # VBR quality
        )
        
        # Add ID3 tags
        audio_file = EasyID3(output_path)
        audio_file["title"] = metadata.get("title", "Untitled Episode")
        audio_file["artist"] = metadata.get("artist", "Kids Curiosity Club")
        audio_file["album"] = metadata.get("album", "Kids Curiosity Club Podcast")
        audio_file["genre"] = "Educational"
        audio_file["date"] = metadata.get("year", "2024")
        audio_file.save()
        
        # Add album art
        if album_art_path and album_art_path.exists():
            audio_file = ID3(output_path)
            with open(album_art_path, "rb") as img:
                audio_file["APIC"] = APIC(
                    encoding=3,
                    mime="image/png",
                    type=3,  # Cover (front)
                    desc="Cover",
                    data=img.read()
                )
            audio_file.save()
```

## 🧪 Testing Requirements

### Unit Tests
- **Mixer Tests**:
  - Mix 2 segments with silence padding
  - Mix with crossfade transitions
  - Trim silence from segments
  - Handle empty segment list
  
- **Background Music Tests**:
  - Loop music to match audio duration
  - Volume reduction (ducking)
  - Fade in/out

- **Normalization Tests**:
  - Measure LUFS accurately
  - Normalize to -16 LUFS within ±1 dB
  - Apply limiter to prevent clipping

- **Export Tests**:
  - Export MP3 with correct bitrate
  - Verify ID3 tags are present
  - Check album art embedding

### Integration Tests
- **End-to-End Pipeline**:
  - Mix TTS segments → Add background music → Normalize → Export MP3
  - Verify final audio duration matches expected
  - Validate ID3 tags and album art
  
### Fixtures
```python
@pytest.fixture
def sample_audio_segments(tmp_path):
    segments = []
    for i in range(3):
        audio_path = tmp_path / f"segment_{i}.mp3"
        silence = AudioSegment.silent(duration=2000)  # 2 seconds
        silence.export(audio_path, format="mp3")
        segments.append(AudioSegment(
            character_id="oliver",
            text=f"Segment {i}",
            audio_path=audio_path,
            duration=2.0
        ))
    return segments
```

## 📝 Implementation Notes

### Dependencies
```toml
[project]
dependencies = [
    "pydub>=0.25.1",
    "pyloudnorm>=0.1.1",
    "mutagen>=1.47.0",
    "numpy>=1.24.0"
]
```

### Key Design Decisions
1. **Pydub for Mixing**: Simple API, good format support, FFmpeg backend
2. **LUFS Normalization**: Industry standard for podcast loudness
3. **File-Based Processing**: All audio stored as files, not in-memory (memory efficient)
4. **Optional Effects**: Background music and intro/outro are optional for MVP
5. **ID3 Tags**: Full podcast metadata for RSS feed compatibility

### Audio Quality Standards
- **Format**: MP3, 192 kbps VBR
- **Sample Rate**: 44.1 kHz
- **Channels**: Stereo (or mono if all TTS is mono)
- **Loudness**: -16 LUFS ±1 dB
- **Duration**: Match script duration ±5%

## 📂 File Structure
```
src/services/audio/
├── __init__.py
├── mixer.py
├── normalization.py
├── exporter.py
└── effects.py

data/audio/
├── music/
│   ├── background_loop_1.mp3
│   └── background_loop_2.mp3
├── branding/
│   ├── intro.mp3
│   ├── outro.mp3
│   └── album_art.png
└── .gitkeep

tests/services/audio/
├── test_mixer.py
├── test_normalization.py
├── test_exporter.py
└── test_audio_mixer_integration.py
```

## ✅ Definition of Done
- [ ] AudioMixer combines segments with silence padding and crossfade
- [ ] Background music integration with ducking and looping
- [ ] Intro/outro support with sample files created
- [ ] Loudness normalization to -16 LUFS using pyloudnorm
- [ ] MP3 export with ID3 tags (title, artist, album, genre, album art)
- [ ] Test coverage ≥ 80% for audio mixing modules
- [ ] Integration test validates full pipeline (segments → mixed MP3)
- [ ] Documentation includes audio quality standards and mixing options
