# WP6: Pipeline Orchestrator

**Status**: ⏳ Not Started  
**Dependencies**: WP0 (Prompt Enhancement), WP1 (Foundation), WP2 (LLM), WP3 (TTS), WP4 (Audio Mixer), WP5 (Image)  
**Estimated Effort**: 3-4 days  
**Owner**: TBD  
**Subsystem:** Orchestration

## 📋 Overview

Orchestrator coordinates the entire podcast generation pipeline, managing state transitions through the **8-stage workflow** (IDEATION → OUTLINING → **AWAITING_APPROVAL** → SEGMENT_GENERATION → SCRIPT_GENERATION → AUDIO_SYNTHESIS → AUDIO_MIXING → COMPLETE). Handles service integration, **human approval gate**, checkpointing for resume capability, Show Blueprint context injection, and progress tracking.

**Key Deliverables**:
- State machine for 8 pipeline stages with human approval gate
- Service integration via factory pattern
- Human approval workflow (pause, review, approve/reject)
- Checkpoint save/restore functionality
- Show Blueprint context injection at each stage
- Error handling and retry logic
- Progress tracking and logging
- Resume-from-any-stage capability

**System Context**:
- **Subsystem:** Orchestration
- **Depends on:** All service subsystems (WP0-5)
- **Used by:** WP7 (CLI), WP9 (Dashboard)
- **Parallel Development:** ❌ Must wait for all services (critical path)

## 🎯 High-Level Tasks

### Task 6.1: Pipeline State Machine
Implement core workflow orchestration with 8 stages.

**Subtasks**:
- [ ] 6.1.1: Create `PipelineOrchestrator` class
- [ ] 6.1.2: Define state transition rules (IDEATION → OUTLINING → AWAITING_APPROVAL → SEGMENT → SCRIPT → AUDIO → MIXING → COMPLETE)
- [ ] 6.1.3: Implement `execute_stage(episode: Episode) -> Episode` method
- [ ] 6.1.4: Add state validation (can't skip stages, must approve before continuing)
- [ ] 6.1.5: Implement automatic progression through stages (pauses at AWAITING_APPROVAL)
- [ ] 6.1.6: Add manual stage execution for debugging
- [ ] 6.1.7: Handle REJECTED status (requires restarting from IDEATION or editing outline)

**Expected Outputs**:
- `src/orchestrator/pipeline.py`
- State machine with 8 stages
- Approval gate logic

### Task 6.2: Human Approval Workflow
Implement approval gate after OUTLINING stage.

**Subtasks**:
- [ ] 6.2.1: Transition episode to AWAITING_APPROVAL after outline generation
- [ ] 6.2.2: Implement `submit_approval(episode_id: str, approved: bool, edited_outline: StoryOutline | None, feedback: str | None) -> None`
- [ ] 6.2.3: If approved: transition to SEGMENT_GENERATION, update outline if edited
- [ ] 6.2.4: If rejected: transition to REJECTED, store feedback
- [ ] 6.2.5: Add approval timeout warnings (e.g., pending > 7 days)
- [ ] 6.2.6: Support outline editing before approval (replace outline, regenerate segments)
- [ ] 6.2.7: Emit approval event for UI notifications (WebSocket)

**Expected Outputs**:
- `src/orchestrator/approval.py`
- Approval workflow methods
- Event emission for real-time updates

### Task 6.3: Show Blueprint Context Injection
Load and inject Show Blueprint at each stage.

**Subtasks**:
- [ ] 6.3.1: Load ShowBlueprint at pipeline start using ShowBlueprintManager
- [ ] 6.3.2: Pass show_blueprint to IdeationService
- [ ] 6.3.3: Pass show_blueprint to OutlineService
- [ ] 6.3.4: Pass show_blueprint to SegmentGenerationService
- [ ] 6.3.5: Pass show_blueprint to ScriptGenerationService
- [ ] 6.3.6: After COMPLETE, update concepts_covered.json via ShowBlueprintManager
- [ ] 6.3.7: Link episode to show's episodes list

**Expected Outputs**:
- Show Blueprint loading logic
- Context passing through all stages
- Concepts update after completion

### Task 6.4: Service Integration
Connect all services through orchestrator.

**Subtasks**:
- [ ] 6.4.1: Inject PromptEnhancer for all LLM stages
- [ ] 6.4.2: Inject IdeationService for IDEATION stage
- [ ] 6.4.3: Inject OutlineService for OUTLINING stage
- [ ] 6.4.4: Inject SegmentGenerationService for SEGMENT_GENERATION stage
- [ ] 6.4.5: Inject ScriptGenerationService for SCRIPT_GENERATION stage
- [ ] 6.4.6: Inject TTS service (via factory) for AUDIO_SYNTHESIS stage
- [ ] 6.4.7: Inject AudioMixer for AUDIO_MIXING stage
- [ ] 6.4.8: Use Settings for provider selection (mock vs real)

**Expected Outputs**:
- Service dependency injection in orchestrator
- Factory-based provider instantiation

### Task 6.5: Checkpointing System
Implement save/restore for pipeline resumption.

**Subtasks**:
- [ ] 6.5.1: Save checkpoint after each stage completes
- [ ] 6.5.2: Store intermediate outputs (concept, outline, segments, scripts, audio paths)
- [ ] 6.5.3: Implement `resume_episode(episode_id: str) -> None` method
- [ ] 6.5.4: Load last checkpoint and continue from next stage
- [ ] 6.5.5: Add checkpoint validation (detect corrupted state)
- [ ] 6.5.6: Store cost data in checkpoints for transparency
- [ ] 6.5.7: Handle resume from AWAITING_APPROVAL (wait for approval before continuing)

**Expected Outputs**:
- Checkpoint save/load logic
- Resume capability from any stage

### Task 6.6: Error Handling & Recovery
Handle failures gracefully with retries.

**Subtasks**:
- [ ] 6.6.1: Wrap each stage in try-except with logging
- [ ] 6.6.2: Set episode status to FAILED on unrecoverable failures
- [ ] 6.6.3: Implement retry logic for transient API errors (3 attempts)
- [ ] 6.6.4: Store error context in checkpoints (stage, timestamp, error message)
- [ ] 6.6.5: Add manual error recovery (reset to previous stage)
- [ ] 6.6.6: Implement circuit breaker for repeated API failures
- [ ] 6.6.7: Handle Show Blueprint loading errors gracefully

**Expected Outputs**:
- `src/orchestrator/error_handler.py`
- Retry and recovery logic

### Task 6.5: Progress Tracking
Provide visibility into pipeline execution.

**Subtasks**:
- [ ] 6.5.1: Implement `ProgressTracker` class
- [ ] 6.5.2: Report stage progress (e.g., "Audio synthesis: 3/10 segments")
- [ ] 6.5.3: Calculate estimated time remaining
- [ ] 6.5.4: Log to console and file
- [ ] 6.5.5: Add optional webhook notifications (future)

**Expected Outputs**:
- `src/orchestrator/progress_tracker.py`
- Progress logging utilities

### Task 6.6: Pipeline Configuration
Allow customization of pipeline behavior.

**Subtasks**:
- [ ] 6.6.1: Create `PipelineConfig` dataclass
- [ ] 6.6.2: Add toggles (skip_audio_mixing, skip_image_processing)
- [ ] 6.6.3: Add retry settings (max_retries, retry_delay)
- [ ] 6.6.4: Add timeout settings per stage
- [ ] 6.6.5: Support dry-run mode (validate without executing)

**Expected Outputs**:
- `src/orchestrator/config.py`
- Configuration options

### Task 6.7: Integration Testing
Validate end-to-end pipeline execution.

**Subtasks**:
- [ ] 6.7.1: Test full pipeline with mock services (IDEATION → COMPLETE)
- [ ] 6.7.2: Test checkpoint save/restore at each stage
- [ ] 6.7.3: Test error recovery (inject failure at each stage)
- [ ] 6.7.4: Test provider switching (mock → real)
- [ ] 6.7.5: Create gated real API test (full episode generation, budgeted at $5-10)

**Expected Outputs**:
- Integration test suite in `tests/test_pipeline_integration.py`

## 🔧 Technical Specifications

### PipelineOrchestrator Implementation
```python
from src.models.episode import Episode, EpisodeStatus
from src.orchestrator.config import PipelineConfig
from src.orchestrator.progress_tracker import ProgressTracker

class PipelineOrchestrator:
    def __init__(
        self,
        prompt_enhancer: PromptEnhancer,
        llm_service: IdeationService,
        scripting_service: ScriptingService,
        tts_service: AudioSynthesisService,
        audio_mixer: AudioMixer,
        image_manager: ImageManager,
        episode_storage: EpisodeStorage,
        config: PipelineConfig = PipelineConfig()
    ):
        self.prompt_enhancer = prompt_enhancer
        self.llm = llm_service
        self.scripting = scripting_service
        self.tts = tts_service
        self.mixer = audio_mixer
        self.images = image_manager
        self.storage = episode_storage
        self.config = config
        self.progress = ProgressTracker()
    
    def generate_episode(
        self,
        topic: str,
        characters: list[Character],
        duration: int = 15
    ) -> Episode:
        """Execute full pipeline for new episode."""
        # Create episode
        episode = Episode(
            id=self._generate_id(topic),
            title=self._generate_title(topic),
            topic=topic,
            duration_minutes=duration,
            characters=[c.id for c in characters],
            status=EpisodeStatus.IDEATION
        )
        
        # Save initial state
        self.storage.save_episode(episode)
        
        # Execute pipeline
        self._execute_ideation(episode, characters)
        self._execute_scripting(episode, characters)
        self._execute_audio_synthesis(episode, characters)
        self._execute_audio_mixing(episode)
        self._execute_image_processing(episode, characters)
        
        # Mark complete
        episode.status = EpisodeStatus.COMPLETE
        self.storage.save_episode(episode)
        
        return episode
    
    def resume_episode(self, episode_id: str) -> Episode:
        """Resume episode from last checkpoint."""
        episode = self.storage.load_episode(episode_id)
        
        if episode.status == EpisodeStatus.COMPLETE:
            logger.info(f"Episode {episode_id} already complete")
            return episode
        
        if episode.status == EpisodeStatus.ERROR:
            logger.warning(f"Episode {episode_id} in error state, retrying from last successful stage")
        
        # Resume from current status
        if episode.status == EpisodeStatus.IDEATION:
            self._execute_ideation(episode, self._load_characters(episode))
        if episode.status == EpisodeStatus.SCRIPTING:
            self._execute_scripting(episode, self._load_characters(episode))
        if episode.status == EpisodeStatus.AUDIO_SYNTHESIS:
            self._execute_audio_synthesis(episode, self._load_characters(episode))
        if episode.status == EpisodeStatus.AUDIO_MIXING:
            self._execute_audio_mixing(episode)
        if episode.status == EpisodeStatus.IMAGE_PROCESSING:
            self._execute_image_processing(episode, self._load_characters(episode))
        
        episode.status = EpisodeStatus.COMPLETE
        self.storage.save_episode(episode)
        
        return episode
    
    def _execute_ideation(self, episode: Episode, characters: list[Character]) -> None:
        """Execute ideation stage."""
        self.progress.start_stage("Ideation")
        
        try:
            ideation = self.llm.refine_topic(
                user_topic=episode.topic,
                duration=episode.duration_minutes
            )
            
            # Save checkpoint
            episode.checkpoints["ideation"] = {
                "completed_at": datetime.now().isoformat(),
                "output": ideation.model_dump()
            }
            episode.status = EpisodeStatus.SCRIPTING
            self.storage.save_episode(episode)
            
            self.progress.complete_stage("Ideation")
        except Exception as e:
            logger.error(f"Ideation failed: {e}")
            episode.status = EpisodeStatus.ERROR
            episode.checkpoints["ideation"] = {
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }
            self.storage.save_episode(episode)
            raise
    
    def _execute_scripting(self, episode: Episode, characters: list[Character]) -> None:
        """Execute scripting stage."""
        self.progress.start_stage("Scripting")
        
        # Load ideation output
        ideation_data = episode.checkpoints["ideation"]["output"]
        ideation = IdeationOutput(**ideation_data)
        
        try:
            script = self.scripting.generate_script(
                ideation=ideation,
                characters=characters,
                duration=episode.duration_minutes
            )
            
            # Save checkpoint
            episode.checkpoints["scripting"] = {
                "completed_at": datetime.now().isoformat(),
                "output": script.model_dump()
            }
            episode.status = EpisodeStatus.AUDIO_SYNTHESIS
            self.storage.save_episode(episode)
            
            self.progress.complete_stage("Scripting")
        except Exception as e:
            logger.error(f"Scripting failed: {e}")
            episode.status = EpisodeStatus.ERROR
            self.storage.save_episode(episode)
            raise
    
    # Additional stage methods: _execute_audio_synthesis, _execute_audio_mixing, _execute_image_processing
```

### Checkpoint Format
```json
{
  "id": "ep001_space",
  "status": "AUDIO_MIXING",
  "checkpoints": {
    "ideation": {
      "completed_at": "2024-01-15T10:05:00Z",
      "output": {
        "refined_topic": "How Rockets Work",
        "learning_objectives": ["..."],
        "key_points": ["..."]
      },
      "cost": 0.02
    },
    "scripting": {
      "completed_at": "2024-01-15T10:08:00Z",
      "output": {
        "segments": [
          {"character_id": "oliver", "text": "...", "emotion": "excited"},
          {"character_id": "hannah", "text": "...", "emotion": "curious"}
        ]
      },
      "cost": 0.05
    },
    "audio_synthesis": {
      "completed_at": "2024-01-15T10:15:00Z",
      "audio_segments": [
        {"path": "data/audio/ep001/segment_001_oliver.mp3", "duration": 3.2},
        {"path": "data/audio/ep001/segment_002_hannah.mp3", "duration": 2.8}
      ],
      "cost": 2.50
    }
  },
  "total_cost": 2.57
}
```

### Error Recovery Example
```python
from tenacity import retry, stop_after_attempt, wait_exponential

class PipelineOrchestrator:
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        reraise=True
    )
    def _execute_with_retry(self, stage_func, *args, **kwargs):
        """Execute stage with automatic retry."""
        return stage_func(*args, **kwargs)
    
    def _execute_ideation(self, episode: Episode, characters: list[Character]) -> None:
        try:
            self._execute_with_retry(self._ideation_impl, episode, characters)
        except Exception as e:
            logger.error(f"Ideation failed after retries: {e}")
            episode.status = EpisodeStatus.ERROR
            self.storage.save_episode(episode)
            raise
```

## 🧪 Testing Requirements

### Unit Tests
- **State Machine Tests**:
  - Valid state transitions (IDEATION → SCRIPTING → ...)
  - Invalid state transitions rejected
  - Resume from each stage
  - Error state handling
  
- **Checkpoint Tests**:
  - Save checkpoint after each stage
  - Load checkpoint and resume
  - Validate checkpoint integrity
  - Handle corrupted checkpoints

- **Progress Tracking Tests**:
  - Stage progress reporting
  - Time estimation accuracy
  - Log output format

### Integration Tests
- **End-to-End Pipeline**:
  - Full pipeline with mock services (free)
  - Checkpoint save/restore at each stage
  - Error injection and recovery
  - Cost tracking accumulation
  
- **Real API Tests** (gated with `@pytest.mark.real_api`):
  - Full episode generation with OpenAI + ElevenLabs (budgeted at $5-10)
  - Validate final MP3 output
  - Verify cost tracking accuracy

### Fixtures
```python
@pytest.fixture
def orchestrator_with_mocks(prompt_enhancer, mock_llm, mock_tts, mock_mixer):
    return PipelineOrchestrator(
        prompt_enhancer=prompt_enhancer,
        llm_service=mock_llm,
        scripting_service=mock_scripting,
        tts_service=mock_tts,
        audio_mixer=mock_mixer,
        image_manager=mock_images,
        episode_storage=EpisodeStorage()
    )
```

## 📝 Implementation Notes

### Dependencies
```toml
[project]
dependencies = [
    "tenacity>=8.2.0"  # Retry logic
]
```

### Key Design Decisions
1. **Sequential Pipeline**: Stages execute in strict order (no parallelization in MVP)
2. **Checkpointing**: Save after each stage for full resume capability
3. **Dependency Injection**: Services injected via constructor for testability
4. **Factory Pattern**: Providers instantiated via factories based on settings
5. **Error Boundaries**: Each stage wrapped in try-except to prevent cascade failures

### Performance Considerations
- **Stage Duration**: Ideation (5-10s), Scripting (10-20s), TTS (30-60s), Mixing (10-15s)
- **Total Time**: ~2-5 minutes per episode with real APIs (mock: ~10 seconds)
- **Memory**: Keep audio files on disk, not in memory
- **Parallelization**: Consider parallel TTS for multiple segments in future

## 📂 File Structure
```
src/orchestrator/
├── __init__.py
├── pipeline.py            # PipelineOrchestrator
├── config.py              # PipelineConfig
├── progress_tracker.py
└── error_handler.py

tests/orchestrator/
├── test_pipeline.py
├── test_checkpointing.py
├── test_error_handling.py
└── test_pipeline_integration.py
```

## ✅ Definition of Done
- [ ] PipelineOrchestrator executes all 6 stages in sequence
- [ ] Checkpointing saves intermediate state after each stage
- [ ] Resume capability works from any stage
- [ ] Error handling with retry logic (3 attempts)
- [ ] Progress tracking with stage completion reporting
- [ ] Service integration via dependency injection
- [ ] Test coverage ≥ 80% for orchestrator modules
- [ ] Full pipeline integration test with mock services
- [ ] At least 1 real API test generating complete episode (gated, budgeted)
- [ ] Documentation includes pipeline flow diagram and error recovery guide
