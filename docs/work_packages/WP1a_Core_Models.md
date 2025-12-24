# WP1a: Core Models (Show Blueprint + Episode)

**Parent WP**: [WP1: Foundation & Data Models](WP1_Foundation.md)  
**Status**: ⏳ Not Started  
**Dependencies**: None  
**Estimated Effort**: 1-2 days  
**Owner**: TBD  
**Subsystems:** Storage + Show Management

## 📋 Overview

Foundation work package establishes the **Storage** and **Show Management subsystems**, providing core data structures and Show Blueprint management that all other components depend on. This is the **critical path** - all parallel development depends on completing this first.

**Key Deliverables**:
- Pydantic data models (Show, ShowBlueprint, Protagonist, WorldDescription, Character, Episode, StoryOutline, StorySegment, Script)
- Validation rules and custom types

**Subsystem Responsibilities**:
- **Storage Subsystem:** File I/O, data persistence, validation
- **Show Management Subsystem:** Show Blueprint CRUD, concepts tracking, episode linkage

**This Sub-WP Covers**: Show Blueprint and Episode data model definitions.

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
]
```

### Key Design Decisions
1. **Pydantic for Validation**: Ensures type safety and automatic validation at data boundaries
2. **Character JSON Format**: Human-editable for easy character creation and modification
3. **Checkpoint System**: Enables resume-from-any-stage capability without re-running expensive API calls

### Migration Path
- Start with v1 schema (current design)
- Add `schema_version` field to all JSON files
- Implement schema migration utilities in future WPs if format changes

## 📂 File Structure
```
src/
├── models/
│   ├── __init__.py
│   ├── show.py           # Show, ShowBlueprint, Protagonist, WorldDescription, Character
│   ├── episode.py        # Episode, PipelineStage
│   └── story.py          # StoryOutline, StoryBeat, StorySegment, Script, ScriptBlock
└── __init__.py

tests/
├── test_models.py
└── fixtures/
    ├── characters.py
    └── episodes.py
```

## ✅ Definition of Done
- [ ] All Pydantic models defined with type hints and validators
- [ ] JSON schema generation working for all models
- [ ] Test coverage ≥ 80% for all model classes
- [ ] Documentation includes example usage for all models
- [ ] Clear stage transitions documented for Episode pipeline

## 🔗 Related Sub-WPs
- **Next**: [WP1b: Configuration](WP1b_Configuration.md) - Settings system
- **Next**: [WP1c: Blueprint Manager](WP1c_Blueprint_Manager.md) - Show Blueprint CRUD operations
- **Next**: [WP1d: Storage](WP1d_Storage.md) - Episode persistence
- **Next**: [WP1e: Testing](WP1e_Testing.md) - Validation utilities
