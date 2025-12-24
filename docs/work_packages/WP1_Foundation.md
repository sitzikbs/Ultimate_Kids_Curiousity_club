# WP1: Foundation & Data Models

**Status**: ⏳ Not Started  
**Dependencies**: None  
**Estimated Effort**: 4-5 days  
**Owner**: TBD  
**Subsystems:** Storage + Show Management

## 📋 Overview

Foundation work package establishes the **Storage** and **Show Management subsystems**, providing core data structures and Show Blueprint management that all other components depend on. This is the **critical path** - all parallel development depends on completing this first.

**Key Deliverables**:
- Pydantic data models (Show, ShowBlueprint, Protagonist, WorldDescription, Character, Episode, StoryOutline, StorySegment, Script)
- ShowBlueprintManager for loading/saving show data
- Settings system with environment-based configuration
- File-based storage structure for shows and episodes
- Validation rules and custom types
- Error handling base classes

**Subsystem Responsibilities**:
- **Storage Subsystem:** File I/O, data persistence, validation
- **Show Management Subsystem:** Show Blueprint CRUD, concepts tracking, episode linkage

## 🎯 High-Level Tasks

### Task 1.1: Show Blueprint Data Models
Define Pydantic models for Show Blueprint architecture.

**Subtasks**:
- [ ] 1.1.1: Create `Show` model with fields: show_id, title, description, theme, narrator_voice_config, created_at
- [ ] 1.1.2: Create `Protagonist` model with fields: name, age, description, values (list), catchphrases, backstory, image_path, voice_config
- [ ] 1.1.3: Create `WorldDescription` model with fields: setting, rules (list), atmosphere, locations (list of dicts with image_paths)
- [ ] 1.1.4: Create `Character` model (supporting) with fields: name, role, description, personality, image_path, voice_config
- [ ] 1.1.5: Create `ConceptsHistory` model with fields: concepts (list of dicts), last_updated
- [ ] 1.1.6: Create `ShowBlueprint` model aggregating: show, protagonist, world, characters (list), concepts_history, episodes (list of IDs)
- [ ] 1.1.7: Add validation for image_path existence, show_id format

**Expected Outputs**:
- `src/models/show.py` with Show, Protagonist, WorldDescription, Character, ConceptsHistory, ShowBlueprint
- Validators for file paths and IDs
- JSON schema generation for all models

### Task 1.2: Story & Episode Data Models
Define models for story generation stages.

**Subtasks**:
- [ ] 1.2.1: Create `StoryBeat` model with fields: beat_number, title, description, educational_focus, key_moments
- [ ] 1.2.2: Create `StoryOutline` model with fields: episode_id, show_id, topic, title, educational_concept, story_beats (list), created_at
- [ ] 1.2.3: Create `StorySegment` model with fields: segment_number, beat_number, description, characters_involved, setting, educational_content
- [ ] 1.2.4: Create `ScriptBlock` model with fields: speaker, text, speaker_voice_id, duration_estimate
- [ ] 1.2.5: Create `Script` model with fields: segment_number, script_blocks (list)
- [ ] 1.2.6: Create `Episode` model with fields: episode_id, show_id, topic, title, outline, segments, scripts, audio_path, current_stage, approval_status, approval_feedback, created_at, updated_at
- [ ] 1.2.7: Add `PipelineStage` enum (PENDING, IDEATION, OUTLINING, AWAITING_APPROVAL, APPROVED, SEGMENT_GENERATION, SCRIPT_GENERATION, AUDIO_SYNTHESIS, AUDIO_MIXING, COMPLETE, FAILED, REJECTED)

**Expected Outputs**:
- `src/models/episode.py` with Episode, PipelineStage
- `src/models/story.py` with StoryOutline, StoryBeat, StorySegment, Script, ScriptBlock
- Clear stage transitions documented
### Task 1.3: Settings & Configuration
Implement centralized configuration with Show Blueprint paths.

**Subtasks**:
- [ ] 1.3.1: Create `Settings` class inheriting from `BaseSettings`
- [ ] 1.3.2: Add `USE_MOCK_SERVICES` boolean flag (default: True)
- [ ] 1.3.3: Add API keys section (OPENAI_API_KEY, ANTHROPIC_API_KEY, ELEVENLABS_API_KEY, etc.)
- [ ] 1.3.4: Add storage paths (SHOWS_DIR, EPISODES_DIR, ASSETS_DIR)
- [ ] 1.3.5: Add provider preferences (LLM_PROVIDER, TTS_PROVIDER, IMAGE_PROVIDER)
- [ ] 1.3.6: Implement `.env` loading with `python-dotenv`
- [ ] 1.3.7: Add settings validation (require API keys only when USE_MOCK_SERVICES=False)
- [ ] 1.3.8: Create singleton accessor `get_settings()`

**Expected Outputs**:
- `src/config.py` with Settings class
- `.env.example` template file
- Settings validation tests

### Task 1.4: ShowBlueprintManager
Build Show Blueprint loading, saving, and management system.

**Subtasks**:
- [ ] 1.4.1: Create `ShowBlueprintManager` class with CRUD operations
- [ ] 1.4.2: Implement `load_show(show_id: str) -> ShowBlueprint` from disk
- [ ] 1.4.3: Implement `save_show(blueprint: ShowBlueprint)` to disk
- [ ] 1.4.4: Implement `list_shows() -> list[Show]` to enumerate available shows
- [ ] 1.4.5: Implement `update_protagonist(show_id, protagonist: Protagonist)`
- [ ] 1.4.6: Implement `update_world(show_id, world: WorldDescription)`
- [ ] 1.4.7: Implement `add_character(show_id, character: Character)` for supporting characters
- [ ] 1.4.8: Implement `add_concept(show_id, concept: str, episode_id: str)` to update concepts_covered.json
- [ ] 1.4.9: Implement `get_covered_concepts(show_id) -> list[str]`
- [ ] 1.4.10: Add image path validation and handling
- [ ] 1.4.11: Create show initialization from template (oliver_template, hannah_template)

**Expected Outputs**:
- `src/modules/show_blueprint_manager.py`
- `data/shows/oliver/` (Oliver's STEM Adventures template)
- `data/shows/hannah/` (Hannah's History Adventures template)
- Show Blueprint validation tests

### Task 1.5: Storage & Episode Persistence
Implement file-based storage for episodes within show directories.

**Subtasks**:
- [ ] 1.5.1: Create `EpisodeStorage` class for save/load operations
- [ ] 1.5.2: Implement checkpoint saving (save intermediate state at each pipeline stage)
- [ ] 1.5.3: Implement checkpoint loading (resume from any stage)
- [ ] 1.5.4: Add episode metadata tracking (created_at, updated_at, cost_estimate)
- [ ] 1.5.5: Implement atomic writes with temporary files
- [ ] 1.5.6: Add file locking for concurrent access protection
- [ ] 1.5.7: Link episodes to Show Blueprint (update episodes list in show)

**Expected Outputs**:
- `src/modules/episode_storage.py`
- Episode save/load tests with fixtures

### Task 1.6: Error Handling
Define custom exception hierarchy and error handling utilities.

**Subtasks**:
- [ ] 1.6.1: Create base `PodcastError` exception class
- [ ] 1.6.2: Add domain-specific exceptions (ShowNotFoundError, CharacterNotFoundError, ValidationError, APIError, AudioProcessingError, ApprovalRequiredError)
- [ ] 1.6.3: Implement error context tracking (stage, episode_id, show_id, timestamp)
- [ ] 1.6.4: Add retry decorators for transient failures
- [ ] 1.6.5: Implement error logging with structured data

**Expected Outputs**:
- `src/utils/errors.py`
- Error handling tests

### Task 1.6: Validation Utilities
Create reusable validation functions and custom Pydantic types.

**Subtasks**:
- [ ] 1.6.1: Create `DurationMinutes` custom type (5-20 minute range)
- [ ] 1.6.2: Create `AgeRange` custom type (5-12 years)
- [ ] 1.6.3: Create `VocabularyLevel` enum (SIMPLE, INTERMEDIATE, ADVANCED)
- [ ] 1.6.4: Implement file path validators (exists, readable, correct extension)
- [ ] 1.6.5: Add URL validators for image references
- [ ] 1.6.6: Create text content validators (profanity filtering, age-appropriate check)

**Expected Outputs**:
- `src/utils/validators.py`
- Validation utility tests

## 🔧 Technical Specifications

### Character JSON Schema
```json
{
  "id": "oliver",
  "name": "Oliver the Inventor",
  "age": 10,
  "personality": "Curious, energetic, loves building things. Always asking 'how does it work?'",
  "speaking_style": "Uses simple technical words, gets excited about mechanisms, often uses analogies with toys or everyday objects.",
  "vocabulary_level": "INTERMEDIATE",
  "voice_config": {
    "provider": "elevenlabs",
    "voice_id": "21m00Tcm4TlvDq8ikWAM",
    "stability": 0.5,
    "similarity_boost": 0.75,
    "style": 0.3
  },
  "reference_image_path": "data/characters/images/oliver.png",
  "created_at": "2024-01-15T10:00:00Z",
  "schema_version": "1.0"
}
```

### Episode Checkpoint Format
```json
{
  "id": "ep001_space_exploration",
  "title": "Journey to the Stars",
  "topic": "How rockets work and space travel",
  "duration_minutes": 15,
  "characters": ["oliver", "hannah"],
  "status": "SCRIPTING",
  "checkpoints": {
    "ideation": {
      "completed_at": "2024-01-15T10:05:23Z",
      "output": {
        "refined_topic": "...",
        "learning_objectives": ["..."],
        "key_points": ["..."]
      }
    },
    "scripting": {
      "started_at": "2024-01-15T10:05:25Z",
      "status": "IN_PROGRESS"
    }
  },
  "created_at": "2024-01-15T10:00:00Z",
  "updated_at": "2024-01-15T10:05:25Z"
}
```

### Settings Configuration
```python
from pydantic_settings import BaseSettings
from pathlib import Path

class Settings(BaseSettings):
    # Mock toggle
    USE_MOCK_SERVICES: bool = True
    
    # API Keys (required only when USE_MOCK_SERVICES=False)
    OPENAI_API_KEY: str | None = None
    ANTHROPIC_API_KEY: str | None = None
    ELEVENLABS_API_KEY: str | None = None
    
    # Provider selection
    LLM_PROVIDER: str = "openai"  # openai, anthropic, mock
    TTS_PROVIDER: str = "elevenlabs"  # elevenlabs, google, openai, mock
    IMAGE_PROVIDER: str = "flux"  # flux, dalle, mock
    
    # Storage paths
    DATA_DIR: Path = Path("data")
    CHARACTERS_DIR: Path = DATA_DIR / "characters"
    EPISODES_DIR: Path = DATA_DIR / "episodes"
    AUDIO_OUTPUT_DIR: Path = DATA_DIR / "audio"
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"

_settings: Settings | None = None

def get_settings() -> Settings:
    global _settings
    if _settings is None:
        _settings = Settings()
    return _settings
```

## 🧪 Testing Requirements

### Unit Tests
- **Character Model Tests**:
  - Valid character creation with all fields
  - Validation errors for invalid ages (< 5 or > 12)
  - Voice config nested validation
  - Reference image path validation
  
- **Episode Model Tests**:
  - Episode creation with checkpoint history
  - Status transitions (IDEATION → SCRIPTING → ...)
  - Duration constraints (5-20 minutes)
  - Character reference validation
  
- **Settings Tests**:
  - Environment variable loading from .env
  - Mock mode with no API keys required
  - Real mode validation (require API keys when USE_MOCK_SERVICES=False)
  - Path creation for storage directories
  
- **Character Manager Tests**:
  - Load character from JSON file
  - List all available characters
  - Handle missing character files gracefully
  - Validate character schema versions

### Integration Tests
- End-to-end episode checkpoint flow (save → load → resume)
- Character manager integration with file system
- Settings singleton behavior across modules

### Fixtures
```python
# tests/fixtures/characters.py
@pytest.fixture
def oliver_character():
    return Character(
        id="oliver",
        name="Oliver the Inventor",
        age=10,
        personality="Curious inventor",
        speaking_style="Technical but simple",
        vocabulary_level="INTERMEDIATE",
        voice_config=VoiceConfig(
            provider="mock",
            voice_id="mock_oliver_voice"
        ),
        reference_image_path=None
    )

@pytest.fixture
def sample_episode(oliver_character):
    return Episode(
        id="test_ep001",
        title="Test Episode",
        topic="How airplanes fly",
        duration_minutes=10,
        characters=[oliver_character.id],
        status=EpisodeStatus.IDEATION
    )
```

## 📝 Implementation Notes

### Dependencies
```toml
[project]
dependencies = [
    "pydantic>=2.5.0",
    "pydantic-settings>=2.1.0",
    "python-dotenv>=1.0.0"
]
```

### Key Design Decisions
1. **Pydantic for Validation**: Ensures type safety and automatic validation at data boundaries
2. **File-Based Storage**: Simple JSON files for episodes and characters (no database needed for MVP)
3. **Checkpoint System**: Enables resume-from-any-stage capability without re-running expensive API calls
4. **Singleton Settings**: Centralized configuration accessible from any module
5. **Character JSON Format**: Human-editable for easy character creation and modification

### Migration Path
- Start with v1 schema (current design)
- Add `schema_version` field to all JSON files
- Implement schema migration utilities in future WPs if format changes

## 📂 File Structure
```
src/
├── models/
│   ├── __init__.py
│   ├── character.py       # Character, VoiceConfig
│   ├── episode.py         # Episode, EpisodeStatus
│   └── script.py          # Script, AudioSegment
├── modules/
│   ├── character_manager.py
│   └── episode_storage.py
├── utils/
│   ├── errors.py
│   └── validators.py
├── config.py
└── __init__.py

data/
├── characters/
│   ├── oliver.json
│   ├── hannah.json
│   └── images/
│       ├── oliver.png
│       └── hannah.png
└── episodes/
    └── .gitkeep

tests/
├── test_models.py
├── test_character_manager.py
├── test_episode_storage.py
├── test_config.py
└── fixtures/
    ├── characters.py
    └── episodes.py
```

## ✅ Definition of Done
- [ ] All Pydantic models defined with type hints and validators
- [ ] Settings system loads from .env and validates based on USE_MOCK_SERVICES
- [ ] Character manager can load/list/validate characters from JSON
- [ ] Episode storage implements save/load with checkpointing
- [ ] Custom exception hierarchy with context tracking
- [ ] Test coverage ≥ 80% for all foundation modules
- [ ] Character templates (Oliver, Hannah) created and validated
- [ ] Documentation includes example usage for all public APIs
