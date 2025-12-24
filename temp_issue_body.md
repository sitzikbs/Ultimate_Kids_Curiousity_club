**Work Package Document**: [docs/work_packages/WP1_Foundation.md](docs/work_packages/WP1_Foundation.md)

**✅ No Dependencies** - Can start immediately!

**🔢 Phase**: 0

---

## Overview
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

## Tasks

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

