# Service Interfaces and Contracts

This document defines the interfaces and contracts between work packages, enabling parallel development with clear integration points.

## 🎯 Purpose

- Define service boundaries and responsibilities
- Specify input/output contracts
- Enable mock implementations
- Support parallel development
- Facilitate testing

## 📋 Table of Contents

- [Provider Base Classes](#provider-base-classes)
- [Core Models](#core-models)
- [Service Interfaces](#service-interfaces)
- [Integration Patterns](#integration-patterns)

---

## Provider Base Classes

### BaseLLMProvider (WP1 → WP2)

```python
from abc import ABC, abstractmethod
from typing import Any

class BaseLLMProvider(ABC):
    """Base class for LLM providers (OpenAI, Anthropic, Mock)."""
    
    @abstractmethod
    def generate(
        self,
        prompt: str,
        max_tokens: int = 2000,
        temperature: float = 0.7,
        **kwargs: Any
    ) -> str:
        """Generate text from prompt.
        
        Args:
            prompt: Enhanced prompt with character context
            max_tokens: Maximum tokens to generate
            temperature: Sampling temperature (0-1)
            **kwargs: Provider-specific parameters
            
        Returns:
            Generated text
            
        Raises:
            ProviderError: If API call fails
            ValidationError: If response invalid
        """
        pass
    
    @abstractmethod
    def estimate_cost(self, prompt: str, max_tokens: int) -> float:
        """Estimate cost in USD for this generation.
        
        Args:
            prompt: Input prompt
            max_tokens: Max tokens to generate
            
        Returns:
            Estimated cost in USD
        """
        pass
    
    @abstractmethod
    def validate_config(self) -> bool:
        """Validate provider configuration (API keys, etc).
        
        Returns:
            True if configuration is valid
            
        Raises:
            ConfigurationError: If config invalid
        """
        pass
```

**Implementations:**
- `OpenAIProvider` (WP2)
- `AnthropicProvider` (WP2)
- `MockLLMProvider` (WP2)

---

### BaseTTSProvider (WP1 → WP3)

```python
from abc import ABC, abstractmethod
from pathlib import Path

class BaseTTSProvider(ABC):
    """Base class for text-to-speech providers."""
    
    @abstractmethod
    def synthesize(
        self,
        text: str,
        voice_id: str,
        settings: dict[str, Any] | None = None
    ) -> bytes:
        """Synthesize speech from text.
        
        Args:
            text: Text to synthesize (max ~5000 chars)
            voice_id: Provider-specific voice identifier
            settings: Provider-specific voice settings
            
        Returns:
            Audio data in WAV format (bytes)
            
        Raises:
            ProviderError: If synthesis fails
            ValidationError: If text too long or voice_id invalid
        """
        pass
    
    @abstractmethod
    def list_voices(self) -> list[dict[str, str]]:
        """List available voices.
        
        Returns:
            List of dicts with keys: voice_id, name, language, gender
        """
        pass
    
    @abstractmethod
    def estimate_cost(self, text: str) -> float:
        """Estimate cost for synthesizing this text.
        
        Args:
            text: Text to synthesize
            
        Returns:
            Estimated cost in USD
        """
        pass
```

**Implementations:**
- `ElevenLabsProvider` (WP3)
- `GoogleTTSProvider` (WP3)
- `OpenAITTSProvider` (WP3)
- `MockTTSProvider` (WP3)

---

### BaseImageProvider (WP1 → WP5)

```python
from abc import ABC, abstractmethod
from pathlib import Path

class BaseImageProvider(ABC):
    """Base class for image generation providers."""
    
    @abstractmethod
    def generate(
        self,
        prompt: str,
        reference_image: Path | None = None,
        size: tuple[int, int] = (1024, 1024),
        **kwargs: Any
    ) -> bytes:
        """Generate image from prompt.
        
        Args:
            prompt: Image generation prompt
            reference_image: Optional reference for conditioning
            size: Output size (width, height)
            **kwargs: Provider-specific parameters
            
        Returns:
            Image data in PNG format (bytes)
            
        Raises:
            ProviderError: If generation fails
            ValidationError: If parameters invalid
        """
        pass
    
    @abstractmethod
    def estimate_cost(self, size: tuple[int, int]) -> float:
        """Estimate cost for image generation.
        
        Args:
            size: Image dimensions
            
        Returns:
            Estimated cost in USD
        """
        pass
```

**Implementations:**
- `FluxProvider` (WP5) - Local
- `ImagenProvider` (WP5) - Google Cloud
- `DALLEProvider` (WP5) - OpenAI
- `MockImageProvider` (WP5)

---

## Core Models

### Show & Show Blueprint (WP1)

```python
from pydantic import BaseModel, Field
from pathlib import Path
from datetime import datetime

class Show(BaseModel):
    """Top-level show configuration."""
    show_id: str = Field(..., regex=r"^[a-z0-9_-]+$")
    title: str  # "Oliver's STEM Adventures"
    description: str
    theme: str  # "STEM", "History", etc.
    narrator_voice_config: dict[str, Any]
    created_at: datetime = Field(default_factory=datetime.now)

class Protagonist(BaseModel):
    """Main character of a show."""
    name: str
    age: int | None = None
    description: str  # Physical appearance, personality
    values: list[str]  # Core values (curiosity, kindness, etc.)
    catchphrases: list[str] = Field(default_factory=list)
    backstory: str | None = None
    image_path: Path | None = None  # Local path to protagonist image
    voice_config: dict[str, Any]  # TTS configuration

class WorldDescription(BaseModel):
    """Setting and rules of the show's universe."""
    setting: str  # "A futuristic city", "Ancient civilizations"
    rules: list[str]  # Physics, magic rules, etc.
    atmosphere: str  # Tone, mood
    locations: list[dict[str, str]] = Field(default_factory=list)  # {"name": "Lab", "description": "...", "image_path": "..."}

class Character(BaseModel):
    """Supporting character in a show."""
    name: str
    role: str  # "Sidekick", "Mentor", "Antagonist"
    description: str
    personality: list[str]
    image_path: Path | None = None
    voice_config: dict[str, Any] | None = None  # If they speak

class ConceptsHistory(BaseModel):
    """Tracks educational concepts already covered."""
    concepts: list[dict[str, Any]]  # [{"concept": "gravity", "episode_id": "ep001", "date": "2025-12-23"}]
    last_updated: datetime = Field(default_factory=datetime.now)

class ShowBlueprint(BaseModel):
    """Centralized show data (formerly Show Bible)."""
    show: Show
    protagonist: Protagonist
    world: WorldDescription
    characters: list[Character] = Field(default_factory=list)
    concepts_history: ConceptsHistory
    episodes: list[str] = Field(default_factory=list)  # Episode IDs
```

---

### Story Models (WP1)

```python
class StoryBeat(BaseModel):
    """Individual story beat in an outline."""
    beat_number: int
    title: str
    description: str  # What happens in this beat
    educational_focus: str | None = None  # Concept taught
    key_moments: list[str] = Field(default_factory=list)

class StoryOutline(BaseModel):
    """Story outline for human review (after OUTLINING stage)."""
    episode_id: str
    show_id: str
    topic: str
    title: str
    educational_concept: str
    story_beats: list[StoryBeat]
    created_at: datetime = Field(default_factory=datetime.now)

class StorySegment(BaseModel):
    """Detailed segment (what happens) - after SEGMENT_GENERATION."""
    segment_number: int
    beat_number: int  # Links to story beat
    description: str  # Detailed description of what happens
    characters_involved: list[str]  # ["Oliver", "Robbie Robot"]
    setting: str
    educational_content: str | None = None

class ScriptBlock(BaseModel):
    """Individual narration or dialogue block."""
    speaker: str  # "NARRATOR", "Oliver", "Robbie Robot"
    text: str  # Actual narration or dialogue
    speaker_voice_id: str | None = None  # TTS voice ID
    duration_estimate: float | None = None

class Script(BaseModel):
    """Final script (how it's told) - after SCRIPT_GENERATION."""
    segment_number: int
    script_blocks: list[ScriptBlock]
```

---

### Legacy Character Model (Deprecated - Use ShowBlueprint Instead)

```python
class VoiceConfig(BaseModel):
    """Voice configuration for TTS."""
    provider: str = Field(..., regex="^(elevenlabs|google|openai|mock)$")
    voice_id: str
    settings: dict[str, Any] = Field(default_factory=dict)

class Character(BaseModel):
    """DEPRECATED: Legacy podcast character definition.
    
    Use ShowBlueprint with Protagonist and Character instead.
    """
    name: str = Field(..., min_length=1, max_length=100)
    character_id: str = Field(..., regex=r"^[a-z0-9_]+$")
    personality: dict[str, list[str] | str]
    speaking_style: str
    world_description: str
    visual_appearance: dict[str, Any]
    reference_image_path: Path | None = None
    voice_config: VoiceConfig
    narrator_voice_config: VoiceConfig | None = None
    side_characters: list[dict[str, Any]] = Field(default_factory=list)
```

---

### Episode (WP1)

```python
from enum import Enum
from datetime import datetime

class PipelineStage(str, Enum):
    """Pipeline processing stages."""
    PENDING = "pending"
    IDEATION = "ideation"
    OUTLINING = "outlining"
    AWAITING_APPROVAL = "awaiting_approval"
    APPROVED = "approved"
    SEGMENT_GENERATION = "segment_generation"
    SCRIPT_GENERATION = "script_generation"
    AUDIO_SYNTHESIS = "audio_synthesis"
    AUDIO_MIXING = "audio_mixing"
    COMPLETE = "complete"
    FAILED = "failed"
    REJECTED = "rejected"

class Episode(BaseModel):
    """Complete episode data."""
    episode_id: str
    show_id: str  # Which show this episode belongs to
    topic: str  # User-provided topic
    title: str | None = None
    outline: StoryOutline | None = None  # After OUTLINING stage
    segments: list[StorySegment] = Field(default_factory=list)  # After SEGMENT_GENERATION
    scripts: list[Script] = Field(default_factory=list)  # After SCRIPT_GENERATION
    audio_path: Path | None = None  # Final MP3 path
    current_stage: PipelineStage = PipelineStage.PENDING
    approval_status: str | None = None  # "approved", "rejected", "pending"
    approval_feedback: str | None = None
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)
```

---

## Service Interfaces

### PromptEnhancer (WP0 → WP2)

```python
class PromptEnhancer:
    """Enhance prompts with Show Blueprint context."""
    
    def enhance_ideation_prompt(
        self,
        topic: str,
        show_blueprint: ShowBlueprint
    ) -> str:
        """Enhance ideation prompt with show context.
        
        Args:
            topic: User topic (e.g., "How rockets work")
            show_blueprint: Complete show data (protagonist, world, concepts)
            
        Returns:
            Enhanced prompt with show context, protagonist values, covered concepts
        """
        pass
    
    def enhance_outline_prompt(
        self,
        story_concept: str,
        show_blueprint: ShowBlueprint
    ) -> str:
        """Enhance outline generation with show context.
        
        Args:
            story_concept: Story concept from ideation
            show_blueprint: Show data
            
        Returns:
            Enhanced prompt for generating story beats
        """
        pass
    
    def enhance_segment_prompt(
        self,
        outline: StoryOutline,
        show_blueprint: ShowBlueprint
    ) -> str:
        """Enhance segment generation with show context.
        
        Args:
            outline: Approved story outline
            show_blueprint: Show data
            
        Returns:
            Enhanced prompt for generating detailed segments
        """
        pass
    
    def enhance_script_prompt(
        self,
        segments: list[StorySegment],
        show_blueprint: ShowBlueprint
    ) -> str:
        """Enhance script generation with show context.
        
        Args:
            segments: Detailed story segments
            show_blueprint: Show data
            
        Returns:
            Enhanced prompt for generating narration + dialogue
        """
        pass
```

---

### ShowBlueprintManager (WP1)

```python
class ShowBlueprintManager:
    """Manage Show Blueprint data."""
    
    def load_show(self, show_id: str) -> ShowBlueprint:
        """Load complete Show Blueprint from disk.
        
        Args:
            show_id: Show identifier (e.g., "oliver")
            
        Returns:
            Complete Show Blueprint
            
        Raises:
            ShowNotFoundError: If show doesn't exist
        """
        pass
    
    def save_show(self, blueprint: ShowBlueprint) -> None:
        """Save Show Blueprint to disk."""
        pass
    
    def update_protagonist(
        self,
        show_id: str,
        protagonist: Protagonist
    ) -> None:
        """Update protagonist data."""
        pass
    
    def add_concept(
        self,
        show_id: str,
        concept: str,
        episode_id: str
    ) -> None:
        """Add concept to concepts_history.json."""
        pass
    
    def get_covered_concepts(self, show_id: str) -> list[str]:
        """Get list of concepts already covered."""
        pass
    
    def add_character(
        self,
        show_id: str,
        character: Character
    ) -> None:
        """Add supporting character."""
        pass
```

---

### LLM Services (WP2)

```python
class IdeationService:
    """Generate story concept from topic."""
    
    def generate_concept(
        self,
        topic: str,
        show_blueprint: ShowBlueprint
    ) -> str:
        """Generate story concept.
        
        Args:
            topic: User topic
            show_blueprint: Show data with context
            
        Returns:
            Story concept (2-3 paragraphs)
        """
        pass

class OutlineService:
    """Generate story outline from concept."""
    
    def generate_outline(
        self,
        concept: str,
        show_blueprint: ShowBlueprint
    ) -> StoryOutline:
        """Generate reviewable story outline.
        
        Args:
            concept: Story concept from ideation
            show_blueprint: Show data
            
        Returns:
            Story outline with beats
        """
        pass

class SegmentGenerationService:
    """Generate detailed segments from outline."""
    
    def generate_segments(
        self,
        outline: StoryOutline,
        show_blueprint: ShowBlueprint
    ) -> list[StorySegment]:
        """Generate detailed segments.
        
        Args:
            outline: Approved story outline
            show_blueprint: Show data
            
        Returns:
            Detailed segments (what happens)
        """
        pass

class ScriptGenerationService:
    """Generate final scripts from segments."""
    
    def generate_scripts(
        self,
        segments: list[StorySegment],
        show_blueprint: ShowBlueprint
    ) -> list[Script]:
        """Generate narration + dialogue scripts.
        
        Args:
            segments: Detailed story segments
            show_blueprint: Show data
            
        Returns:
            Scripts with speaker tags
        """
        pass
```

---

### Legacy ScriptingService (Deprecated)

```python
class ScriptingService:
    """DEPRECATED: Use OutlineService, SegmentGenerationService, ScriptGenerationService instead.
    
    Generate detailed script from ideation output."""
    
    def generate_script(
        self,
        ideation_output: str,
        character: Character
    ) -> str:
        """Enhance ideation prompt with character context.
        
        Args:
            user_idea: Short user input (e.g., "Oliver learns about gravity")
            character: Character definition
            
        Returns:
            Enhanced prompt with personality, educational guidelines, format
        """
        pass
    
    def enhance_scripting_prompt(
        self,
        chapter: Chapter,
        character: Character
    ) -> str:
        """Enhance scripting prompt with character details.
        
        Args:
            chapter: Chapter with summary to expand
            character: Character definition
            
        Returns:
            Enhanced prompt with speaking_style, side characters, format
        """
        pass
```

**Contract:**
- Input: Short user text + Character object
- Output: Rich prompt string with injected context
- Must include: personality, speaking style, format requirements
- Template versioning for reproducibility

---

### LLMService (WP2 → WP6)

```python
class LLMService:
    """Content generation using LLM providers."""
    
    def __init__(self, provider: BaseLLMProvider, enhancer: PromptEnhancer):
        self.provider = provider
        self.enhancer = enhancer
    
    def generate_ideation(
        self,
        user_idea: str,
        character: Character
    ) -> dict[str, Any]:
        """Generate episode outline from idea.
        
        Args:
            user_idea: User's episode idea
            character: Character definition
            
        Returns:
            Dict with keys: title, abstract, chapters (list of dicts)
        """
        pass
    
    def generate_script(
        self,
        chapter: Chapter,
        character: Character
    ) -> list[ScriptSegment]:
        """Generate detailed script for chapter.
        
        Args:
            chapter: Chapter with summary
            character: Character definition
            
        Returns:
            List of ScriptSegment objects with dialogue
        """
        pass
```

**Contract:**
- Input: User idea or Chapter + Character
- Output: Structured JSON (validated by Pydantic)
- Uses PromptEnhancer for all LLM calls
- Handles API retries and errors

---

### TTSService (WP3 → WP6)

```python
class TTSService:
    """Text-to-speech audio synthesis."""
    
    def __init__(self, provider: BaseTTSProvider):
        self.provider = provider
    
    def synthesize_segment(
        self,
        segment: ScriptSegment,
        voice_config: VoiceConfig
    ) -> Path:
        """Synthesize audio for script segment.
        
        Args:
            segment: Script segment with text
            voice_config: Voice configuration
            
        Returns:
            Path to generated WAV file
        """
        pass
    
    def synthesize_episode(
        self,
        segments: list[ScriptSegment],
        character: Character
    ) -> list[Path]:
        """Synthesize all segments for episode.
        
        Args:
            segments: All script segments
            character: Character for voice mapping
            
        Returns:
            List of paths to WAV files (in order)
        """
        pass
```

**Contract:**
- Input: ScriptSegment + VoiceConfig
- Output: WAV file path
- Maps speaker tag to voice_id
- Handles character vs narrator voices

---

### AudioMixerService (WP4 → WP6)

```python
class AudioMixerService:
    """Audio composition and mixing."""
    
    def mix_episode(
        self,
        segment_paths: list[Path],
        music_config: dict[str, Any] | None = None
    ) -> Path:
        """Mix audio segments into final episode.
        
        Args:
            segment_paths: Paths to WAV segment files (in order)
            music_config: Background music settings
            
        Returns:
            Path to mixed WAV file
        """
        pass
    
    def export_mp3(
        self,
        wav_path: Path,
        episode: Episode,
        character: Character
    ) -> Path:
        """Export WAV to MP3 with metadata.
        
        Args:
            wav_path: Path to mixed WAV
            episode: Episode metadata
            character: Character for cover art
            
        Returns:
            Path to final MP3 file
        """
        pass
```

**Contract:**
- Input: List of WAV paths + config
- Output: Mixed WAV, then MP3 with ID3 tags
- Handles timing, pauses, music, effects
- No dependency on TTS service

---

### ImageService (WP5 → WP6)

```python
class ImageService:
    """Character image management."""
    
    def __init__(self, provider: BaseImageProvider):
        self.provider = provider
    
    def load_reference_image(self, path: Path) -> bytes:
        """Load and validate reference image.
        
        Args:
            path: Path to reference image
            
        Returns:
            Image bytes (validated)
        """
        pass
    
    def generate_character_image(
        self,
        character: Character,
        prompt: str | None = None
    ) -> Path:
        """Generate character reference image.
        
        Args:
            character: Character definition
            prompt: Optional custom prompt
            
        Returns:
            Path to generated image
        """
        pass
```

**Contract:**
- Input: Path or Character
- Output: Validated image bytes or Path
- Supports PNG/JPG, min 512x512
- Optional generation capability

---

## Integration Patterns

### Factory Pattern for Providers

```python
class ProviderFactory:
    """Factory for creating providers based on config."""
    
    @staticmethod
    def create_llm_provider(config: Settings) -> BaseLLMProvider:
        """Create LLM provider based on configuration.
        
        Returns:
            MockLLMProvider if USE_MOCK_SERVICES=true
            Otherwise OpenAIProvider or AnthropicProvider
        """
        if config.use_mock_services:
            return MockLLMProvider()
        elif config.llm_provider == "openai":
            return OpenAIProvider(api_key=config.openai_api_key)
        elif config.llm_provider == "anthropic":
            return AnthropicProvider(api_key=config.anthropic_api_key)
        else:
            raise ValueError(f"Unknown provider: {config.llm_provider}")
```

### Error Handling Contract

All services must:
- Raise `ProviderError` for API failures
- Raise `ValidationError` for invalid inputs
- Raise `ConfigurationError` for setup issues
- Include original exception in error chain
- Log errors with context

```python
from tenacity import retry, stop_after_attempt, wait_exponential

class ProviderError(Exception):
    """Base exception for provider errors."""
    pass

@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=4, max=10)
)
def call_api_with_retry(self, *args, **kwargs):
    """Call API with automatic retry."""
    try:
        return self._api_call(*args, **kwargs)
    except Exception as e:
        raise ProviderError(f"API call failed: {e}") from e
```

### Cost Tracking Contract

All provider methods that call APIs must:
- Log call metadata (provider, model, tokens, cost)
- Use `@track_cost` decorator
- Estimate cost before calling
- Return actual cost after calling

```python
from functools import wraps

def track_cost(func):
    """Decorator to track API costs."""
    @wraps(func)
    def wrapper(self, *args, **kwargs):
        # Estimate cost
        estimated = self.estimate_cost(*args, **kwargs)
        
        # Call API
        result = func(self, *args, **kwargs)
        
        # Log actual cost
        log_cost(
            provider=self.__class__.__name__,
            function=func.__name__,
            estimated_cost=estimated,
            actual_cost=self.get_last_call_cost()
        )
        
        return result
    return wrapper
```

---

## Testing Contracts

### Mock Provider Requirements

All mock providers must:
- Return realistic data matching real provider format
- Have configurable latency (0-2s)
- Support error injection for testing
- Return deterministic results (same input → same output)
- Track call counts for verification

```python
class MockLLMProvider(BaseLLMProvider):
    """Mock LLM provider for testing."""
    
    def __init__(self, latency: float = 0.5, error_rate: float = 0.0):
        self.latency = latency
        self.error_rate = error_rate
        self.call_count = 0
        self.fixtures = load_fixtures("llm_responses")
    
    def generate(self, prompt: str, **kwargs) -> str:
        self.call_count += 1
        
        # Simulate latency
        time.sleep(self.latency)
        
        # Inject errors
        if random.random() < self.error_rate:
            raise ProviderError("Mock API error")
        
        # Return fixture
        return self.fixtures.get(hash(prompt), "Default response")
```

---

## Version Compatibility

All interfaces are versioned:
- Major version: Breaking changes to method signatures
- Minor version: New methods added (backwards compatible)
- Patch version: Bug fixes

Current versions:
- `BaseLLMProvider`: v1.0.0
- `BaseTTSProvider`: v1.0.0
- `BaseImageProvider`: v1.0.0

---

**See individual WP specifications for detailed implementation guidance.**
