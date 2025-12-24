# WP3: Text-to-Speech Service

**Status**: ⏳ Not Started  
**Dependencies**: WP1 (Foundation)  
**Estimated Effort**: 2-3 days  
**Owner**: TBD  
**Subsystem:** Audio Production

## 📋 Overview

TTS Service converts script text (narration + dialogue) into synthesized audio files using **narrator + protagonist + supporting character voices** from Show Blueprint. Supports multiple TTS providers (ElevenLabs, Google Cloud TTS, OpenAI TTS, Mock) with provider-specific voice management and audio quality settings.

**Key Deliverables**:
- Provider abstraction layer (ElevenLabs, Google, OpenAI, Mock)
- Audio synthesis for script blocks (narrator + character dialogue)
- Voice configuration management from Show Blueprint
- Audio quality validation
- Mock audio generation for cost-free testing

**System Context**:
- **Subsystem:** Audio Production
- **Depends on:** WP1 (Foundation - Script models with ScriptBlock)
- **Used by:** WP6 (Orchestrator)
- **Parallel Development:** ✅ Can develop in parallel with WP2, WP4, WP5 after WP1 complete

## 🎯 High-Level Tasks

### Task 3.1: Provider Abstraction
Implement base TTS provider interface and concrete implementations.

**Subtasks**:
- [ ] 3.1.1: Create `BaseTTSProvider` abstract base class with `synthesize()` method
- [ ] 3.1.2: Implement `ElevenLabsProvider` using elevenlabs SDK
- [ ] 3.1.3: Implement `GoogleTTSProvider` using google-cloud-texttospeech
- [ ] 3.1.4: Implement `OpenAITTSProvider` using openai TTS API
- [ ] 3.1.5: Implement `MockTTSProvider` with silent audio file generation
- [ ] 3.1.6: Create `TTSProviderFactory` for provider instantiation
- [ ] 3.1.7: Add retry logic for transient API failures

**Expected Outputs**:
- `src/services/tts/base.py`
- `src/services/tts/elevenlabs_provider.py`
- `src/services/tts/google_provider.py`
- `src/services/tts/openai_provider.py`
- `src/services/tts/mock_provider.py`
- `src/services/tts/factory.py`

### Task 3.2: Audio Synthesis Service
Convert script segments to audio files.

**Subtasks**:
- [ ] 3.2.1: Create `AudioSynthesisService` class
- [ ] 3.2.2: Implement `synthesize_segment(text: str, character: Character) -> AudioSegment` method
- [ ] 3.2.3: Map character voice_config to provider-specific parameters
- [ ] 3.2.4: Handle long text by chunking (providers have character limits)
- [ ] 3.2.5: Add silence padding between segments (0.5-1.0 seconds)
- [ ] 3.2.6: Implement batch synthesis for multiple segments
- [ ] 3.2.7: Store audio files with consistent naming (segment_001_oliver.mp3, segment_002_hannah.mp3)

**Expected Outputs**:
- `src/services/tts/synthesis_service.py`
- Audio file naming and storage logic

### Task 3.3: Voice Management
Handle voice configuration and provider-specific settings.

**Subtasks**:
- [ ] 3.3.1: Create `VoiceManager` class
- [ ] 3.3.2: Validate voice IDs exist for selected provider
- [ ] 3.3.3: Map generic emotion tags to provider-specific parameters (e.g., "excited" → stability=0.3)
- [ ] 3.3.4: Implement voice preview functionality (synthesize sample text)
- [ ] 3.3.5: Add voice cloning support for ElevenLabs (upload reference audio)
- [ ] 3.3.6: Store voice samples for quality comparison

**Expected Outputs**:
- `src/services/tts/voice_manager.py`
- Voice validation and preview utilities

### Task 3.4: Audio Quality Validation
Ensure synthesized audio meets quality standards.

**Subtasks**:
- [ ] 3.4.1: Validate audio format (MP3, 44.1kHz, mono or stereo)
- [ ] 3.4.2: Check audio duration matches expected length (±10%)
- [ ] 3.4.3: Detect silent or corrupt audio files
- [ ] 3.4.4: Measure audio loudness (LUFS) for normalization
- [ ] 3.4.5: Add automated quality reports

**Expected Outputs**:
- `src/services/tts/quality_validator.py`
- Audio validation tests

### Task 3.5: Mock Audio Generation
Generate silent audio files for mock testing.

**Subtasks**:
- [ ] 3.5.1: Implement silent audio generation using pydub
- [ ] 3.5.2: Calculate duration based on text length (150 words/minute)
- [ ] 3.5.3: Add optional background noise for realism
- [ ] 3.5.4: Store mock audio in temporary directory
- [ ] 3.5.5: Implement fast mode (skip actual audio generation, return metadata only)

**Expected Outputs**:
- Mock provider with silent audio generation
- Fast mock mode for rapid testing

### Task 3.6: Cost Tracking
Monitor TTS API usage and costs.

**Subtasks**:
- [ ] 3.6.1: Track character count per TTS request
- [ ] 3.6.2: Calculate cost based on provider pricing (ElevenLabs: $0.30/1K chars)
- [ ] 3.6.3: Store cost data in episode checkpoints
- [ ] 3.6.4: Implement cost reporting per episode
- [ ] 3.6.5: Add budget threshold warnings

**Expected Outputs**:
- `src/services/tts/cost_tracker.py`
- Cost data in episode JSON checkpoints

### Task 3.7: Integration Testing
Validate end-to-end TTS pipeline.

**Subtasks**:
- [ ] 3.7.1: Test synthesis for all characters with mock provider
- [ ] 3.7.2: Test provider switching (mock → ElevenLabs → Google → OpenAI)
- [ ] 3.7.3: Test error handling for invalid voice IDs
- [ ] 3.7.4: Test audio quality validation
- [ ] 3.7.5: Create gated real API tests (pytest marker `@pytest.mark.real_api`)

**Expected Outputs**:
- Integration test suite in `tests/test_tts_integration.py`

## 🔧 Technical Specifications

### BaseTTSProvider Interface
```python
from abc import ABC, abstractmethod
from pathlib import Path

class BaseTTSProvider(ABC):
    """Abstract base class for TTS providers."""
    
    @abstractmethod
    def synthesize(
        self,
        text: str,
        voice_id: str,
        output_path: Path,
        **kwargs
    ) -> dict[str, Any]:
        """
        Synthesize speech from text.
        
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
        """List available voices for this provider."""
        pass
    
    @abstractmethod
    def get_cost(self, characters: int) -> float:
        """Calculate cost in USD for character count."""
        pass
```

### ElevenLabs Implementation Example
```python
from elevenlabs import generate, save, voices
from src.services.tts.base import BaseTTSProvider

class ElevenLabsProvider(BaseTTSProvider):
    def __init__(self, api_key: str):
        self.api_key = api_key
        
    def synthesize(
        self,
        text: str,
        voice_id: str,
        output_path: Path,
        **kwargs
    ) -> dict[str, Any]:
        stability = kwargs.get("stability", 0.5)
        similarity_boost = kwargs.get("similarity_boost", 0.75)
        style = kwargs.get("style", 0.0)
        
        audio = generate(
            text=text,
            voice=voice_id,
            model="eleven_multilingual_v2",
            api_key=self.api_key,
            voice_settings={
                "stability": stability,
                "similarity_boost": similarity_boost,
                "style": style
            }
        )
        
        save(audio, str(output_path))
        
        # Get audio duration
        from pydub import AudioSegment
        audio_seg = AudioSegment.from_mp3(output_path)
        duration = len(audio_seg) / 1000.0  # Convert to seconds
        
        return {
            "duration": duration,
            "characters": len(text),
            "audio_path": output_path
        }
    
    def list_voices(self) -> list[dict[str, Any]]:
        voice_list = voices(api_key=self.api_key)
        return [
            {"voice_id": v.voice_id, "name": v.name, "labels": v.labels}
            for v in voice_list
        ]
    
    def get_cost(self, characters: int) -> float:
        # ElevenLabs pricing: $0.30 per 1K characters
        return characters * 0.30 / 1000
```

### Voice Configuration Mapping
```python
# Character JSON voice_config
{
  "provider": "elevenlabs",
  "voice_id": "21m00Tcm4TlvDq8ikWAM",
  "stability": 0.5,
  "similarity_boost": 0.75,
  "style": 0.3,
  "emotion_mappings": {
    "excited": {"stability": 0.3, "style": 0.8},
    "calm": {"stability": 0.7, "style": 0.2},
    "curious": {"stability": 0.5, "style": 0.5}
  }
}
```

### Audio Synthesis Flow
```python
class AudioSynthesisService:
    def __init__(self, tts_provider: BaseTTSProvider, output_dir: Path):
        self.tts = tts_provider
        self.output_dir = output_dir
    
    def synthesize_script(self, script: Script, characters: dict[str, Character]) -> list[AudioSegment]:
        """Synthesize all segments in a script."""
        audio_segments = []
        
        for idx, segment in enumerate(script.segments):
            character = characters[segment.character_id]
            output_path = self.output_dir / f"segment_{idx:03d}_{character.id}.mp3"
            
            # Get voice config
            voice_config = character.voice_config
            
            # Map emotion to voice parameters if specified
            if segment.emotion and segment.emotion in voice_config.get("emotion_mappings", {}):
                params = voice_config["emotion_mappings"][segment.emotion]
            else:
                params = {
                    "stability": voice_config.get("stability", 0.5),
                    "similarity_boost": voice_config.get("similarity_boost", 0.75)
                }
            
            # Synthesize
            result = self.tts.synthesize(
                text=segment.text,
                voice_id=voice_config["voice_id"],
                output_path=output_path,
                **params
            )
            
            audio_segments.append(AudioSegment(
                character_id=character.id,
                text=segment.text,
                audio_path=result["audio_path"],
                duration=result["duration"]
            ))
        
        return audio_segments
```

## 🧪 Testing Requirements

### Unit Tests
- **Provider Tests**:
  - ElevenLabs provider with mocked API
  - Google TTS provider with mocked API
  - OpenAI TTS provider with mocked API
  - Mock provider generates silent audio
  - Factory creates correct provider based on settings
  - Cost calculation accuracy

- **Synthesis Service Tests**:
  - Synthesizes single segment correctly
  - Batch synthesis for multiple segments
  - Handles long text chunking (>5000 chars)
  - Maps emotion tags to voice parameters
  - Creates consistent output file naming

- **Quality Validation Tests**:
  - Detects silent audio files
  - Validates audio format (MP3, 44.1kHz)
  - Checks duration within expected range

### Integration Tests
- **End-to-End Pipeline**:
  - Full script synthesis with mock provider
  - Provider switching test
  - Cost tracking accumulation
  
- **Real API Tests** (gated with `@pytest.mark.real_api`):
  - ElevenLabs synthesis for 2-3 segments (budgeted at $0.50)
  - Google TTS synthesis
  - OpenAI TTS synthesis

### Fixtures
```python
@pytest.fixture
def sample_script_segment():
    return ScriptSegment(
        character_id="oliver",
        text="Wow! Did you know rockets use Newton's Third Law?",
        emotion="excited"
    )

@pytest.fixture
def mock_audio_path(tmp_path):
    audio_path = tmp_path / "test_audio.mp3"
    # Create 3-second silent audio
    silence = AudioSegment.silent(duration=3000)
    silence.export(audio_path, format="mp3")
    return audio_path
```

## 📝 Implementation Notes

### Dependencies
```toml
[project]
dependencies = [
    "elevenlabs>=0.2.0",
    "google-cloud-texttospeech>=2.16.0",
    "pydub>=0.25.1",
    "openai>=1.12.0"
]
```

### Key Design Decisions
1. **Provider Abstraction**: Unified interface for all TTS providers
2. **File-Based Output**: Audio stored as MP3 files for simplicity and compatibility
3. **Mock Silent Audio**: Enables cost-free testing with realistic duration
4. **Emotion Mapping**: Character-specific emotion → voice parameter mappings
5. **Segment Naming**: Consistent pattern (segment_XXX_character.mp3) for audio mixer

### Audio Quality Standards
- **Format**: MP3, 192 kbps, 44.1 kHz
- **Loudness**: Target -16 LUFS for podcast standard
- **Duration**: Within ±10% of expected duration (150 words/min)
- **No Silence**: No segments with >2 seconds of complete silence

## 📂 File Structure
```
src/services/tts/
├── __init__.py
├── base.py                # BaseTTSProvider
├── elevenlabs_provider.py
├── google_provider.py
├── openai_provider.py
├── mock_provider.py
├── factory.py             # TTSProviderFactory
├── synthesis_service.py
├── voice_manager.py
├── quality_validator.py
└── cost_tracker.py

data/audio/
└── .gitkeep  # Temp audio files, not committed

tests/services/tts/
├── test_providers.py
├── test_synthesis_service.py
├── test_voice_manager.py
├── test_quality_validator.py
└── test_tts_integration.py
```

## ✅ Definition of Done
- [ ] All TTS providers implement BaseTTSProvider interface
- [ ] Audio synthesis service generates MP3 files for all script segments
- [ ] Mock provider generates silent audio with correct duration
- [ ] Voice manager validates voice IDs and maps emotion tags
- [ ] Quality validator checks format, duration, and silence detection
- [ ] Cost tracking records character counts and costs
- [ ] Test coverage ≥ 80% for TTS service modules
- [ ] At least 2 real API integration tests (ElevenLabs, Google, or OpenAI)
- [ ] Documentation includes voice setup guide and provider comparison
