# WP6b: Reliability & Recovery

**Status**: ⏳ Not Started  
**Parent WP**: WP6 (Orchestrator)  
**Dependencies**: WP6a (State Machine), WP3 (TTS), WP4 (Audio Mixer), WP5 (Image)  
**Estimated Effort**: 1.5-2 days  
**Owner**: TBD  
**Subsystem:** Orchestration

## 📋 Overview

Implement reliability features for the pipeline orchestrator, including checkpointing for resume capability, error handling with retry logic, progress tracking, and service integration with TTS/Audio/Image services. This work package builds on WP6a's state machine to make the pipeline production-ready.

**Key Deliverables**:
- Checkpoint save/restore functionality
- Error handling and retry logic
- Progress tracking and logging
- Service integration (TTS, Audio Mixer, Image Manager)
- Resume-from-any-stage capability
- Integration testing with mock and real services

**System Context**:
- **Subsystem:** Orchestration
- **Depends on:** WP6a (State Machine), WP3 (TTS), WP4 (Audio), WP5 (Image)
- **Used by:** WP7 (CLI), WP9 (Dashboard)
- **Parallel Development:** ❌ Must wait for WP6a

## 🎯 High-Level Tasks

### Task 6.4: Service Integration
Connect all services through orchestrator.

**Subtasks**:
- [ ] 6.4.1: Inject PromptEnhancer for all LLM stages (from WP6a)
- [ ] 6.4.2: Inject IdeationService for IDEATION stage (from WP6a)
- [ ] 6.4.3: Inject OutlineService for OUTLINING stage (from WP6a)
- [ ] 6.4.4: Inject SegmentGenerationService for SEGMENT_GENERATION stage
- [ ] 6.4.5: Inject ScriptGenerationService for SCRIPT_GENERATION stage
- [ ] 6.4.6: Inject TTS service (via factory) for AUDIO_SYNTHESIS stage
- [ ] 6.4.7: Inject AudioMixer for AUDIO_MIXING stage
- [ ] 6.4.8: Use Settings for provider selection (mock vs real)

**Expected Outputs**:
- Service dependency injection in orchestrator
- Factory-based provider instantiation
- Stage execution methods for SEGMENT_GENERATION through COMPLETE

**Technical Notes**:
```python
from src.orchestrator.pipeline import PipelineOrchestrator
from src.services.tts.factory import TTSServiceFactory
from src.services.audio.mixer import AudioMixer

class PipelineOrchestrator:
    def __init__(
        self,
        # WP6a services
        prompt_enhancer: PromptEnhancer,
        ideation_service: IdeationService,
        outline_service: OutlineService,
        show_blueprint_manager: ShowBlueprintManager,
        # WP6b services
        segment_service: SegmentGenerationService,
        script_service: ScriptGenerationService,
        tts_factory: TTSServiceFactory,
        audio_mixer: AudioMixer,
        image_manager: ImageManager,
        episode_storage: EpisodeStorage,
        settings: Settings
    ):
        # Store services
        self.tts = tts_factory.create(settings.tts_provider)
        self.mixer = audio_mixer
        self.images = image_manager
        # ... other services
    
    def _execute_audio_synthesis(self, episode: Episode, show_blueprint: ShowBlueprint) -> Episode:
        """Execute audio synthesis stage."""
        audio_segments = []
        
        for i, script_line in enumerate(episode.script.lines):
            audio_path = self.tts.synthesize(
                text=script_line.text,
                character_id=script_line.character_id,
                emotion=script_line.emotion
            )
            audio_segments.append({
                "path": audio_path,
                "character_id": script_line.character_id,
                "index": i
            })
        
        episode.audio_segments = audio_segments
        episode.status = EpisodeStatus.AUDIO_MIXING
        self.storage.save_episode(episode)
        
        return episode
    
    def _execute_audio_mixing(self, episode: Episode) -> Episode:
        """Execute audio mixing stage."""
        final_audio_path = self.mixer.mix_episode(
            episode_id=episode.id,
            audio_segments=episode.audio_segments,
            music_track=episode.music_track
        )
        
        episode.final_audio_path = final_audio_path
        episode.status = EpisodeStatus.COMPLETE
        self.storage.save_episode(episode)
        
        return episode
```

### Task 6.5: Checkpointing System
Implement save/restore for pipeline resumption.

**Subtasks**:
- [ ] 6.5.1: Save checkpoint after each stage completes
- [ ] 6.5.2: Store intermediate outputs (concept, outline, segments, scripts, audio paths)
- [ ] 6.5.3: Implement `resume_episode(episode_id: str) -> Episode` method
- [ ] 6.5.4: Load last checkpoint and continue from next stage
- [ ] 6.5.5: Add checkpoint validation (detect corrupted state)
- [ ] 6.5.6: Store cost data in checkpoints for transparency
- [ ] 6.5.7: Handle resume from AWAITING_APPROVAL (wait for approval before continuing)

**Expected Outputs**:
- Checkpoint save/load logic
- Resume capability from any stage
- Cost tracking in checkpoints

**Technical Notes**:
```python
from datetime import datetime

class PipelineOrchestrator:
    def _save_checkpoint(
        self,
        episode: Episode,
        stage: str,
        output: dict,
        cost: float = 0.0
    ) -> None:
        """Save checkpoint after stage completion."""
        if not episode.checkpoints:
            episode.checkpoints = {}
        
        episode.checkpoints[stage] = {
            "completed_at": datetime.now().isoformat(),
            "output": output,
            "cost": cost
        }
        
        # Update total cost
        episode.total_cost = sum(
            cp.get("cost", 0.0) for cp in episode.checkpoints.values()
        )
        
        self.storage.save_episode(episode)
        logger.info(f"Checkpoint saved: {stage} (cost: ${cost:.2f})")
    
    def resume_episode(self, episode_id: str) -> Episode:
        """Resume episode from last checkpoint."""
        episode = self.storage.load_episode(episode_id)
        
        if episode.status == EpisodeStatus.COMPLETE:
            logger.info(f"Episode {episode_id} already complete")
            return episode
        
        if episode.status == EpisodeStatus.AWAITING_APPROVAL:
            logger.warning(f"Episode {episode_id} awaiting approval - submit approval first")
            return episode
        
        if episode.status == EpisodeStatus.FAILED:
            logger.warning(f"Episode {episode_id} in failed state, retrying from last successful stage")
        
        # Load Show Blueprint
        show_blueprint = self.show_manager.load_show(episode.show_id)
        
        # Resume from current status
        while episode.status != EpisodeStatus.COMPLETE:
            if episode.status == EpisodeStatus.SEGMENT_GENERATION:
                episode = self._execute_segment_generation(episode, show_blueprint)
            elif episode.status == EpisodeStatus.SCRIPT_GENERATION:
                episode = self._execute_script_generation(episode, show_blueprint)
            elif episode.status == EpisodeStatus.AUDIO_SYNTHESIS:
                episode = self._execute_audio_synthesis(episode, show_blueprint)
            elif episode.status == EpisodeStatus.AUDIO_MIXING:
                episode = self._execute_audio_mixing(episode)
            else:
                raise ValueError(f"Cannot resume from status: {episode.status}")
        
        self._finalize_episode(episode)
        return episode
    
    def validate_checkpoint(self, episode: Episode, stage: str) -> bool:
        """Validate checkpoint integrity."""
        if stage not in episode.checkpoints:
            return False
        
        checkpoint = episode.checkpoints[stage]
        required_keys = ["completed_at", "output"]
        
        return all(key in checkpoint for key in required_keys)
```

**Checkpoint Format**:
```json
{
  "id": "ep001_space",
  "show_id": "olivers_workshop",
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
    "outlining": {
      "completed_at": "2024-01-15T10:07:00Z",
      "output": {
        "title": "...",
        "story_beats": [...]
      },
      "cost": 0.03
    },
    "segment_generation": {
      "completed_at": "2024-01-15T10:10:00Z",
      "output": {
        "segments": [...]
      },
      "cost": 0.05
    },
    "script_generation": {
      "completed_at": "2024-01-15T10:12:00Z",
      "output": {
        "lines": [...]
      },
      "cost": 0.08
    },
    "audio_synthesis": {
      "completed_at": "2024-01-15T10:15:00Z",
      "output": {
        "audio_segments": [
          {"path": "data/audio/ep001/segment_001_oliver.mp3", "duration": 3.2},
          {"path": "data/audio/ep001/segment_002_hannah.mp3", "duration": 2.8}
        ]
      },
      "cost": 2.50
    }
  },
  "total_cost": 2.68
}
```

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
- Circuit breaker implementation

**Technical Notes**:
```python
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type
import logging

logger = logging.getLogger(__name__)

class PipelineOrchestrator:
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        retry=retry_if_exception_type((APIError, TimeoutError)),
        reraise=True
    )
    def _execute_with_retry(self, stage_func, episode: Episode, *args, **kwargs):
        """Execute stage with automatic retry for transient errors."""
        return stage_func(episode, *args, **kwargs)
    
    def _execute_stage_with_error_handling(
        self,
        stage_func,
        episode: Episode,
        stage_name: str,
        *args,
        **kwargs
    ) -> Episode:
        """Execute stage with comprehensive error handling."""
        try:
            return self._execute_with_retry(stage_func, episode, *args, **kwargs)
        except Exception as e:
            logger.error(f"{stage_name} failed after retries: {e}", exc_info=True)
            
            # Save error state
            episode.status = EpisodeStatus.FAILED
            episode.last_error = {
                "stage": stage_name,
                "timestamp": datetime.now().isoformat(),
                "error": str(e),
                "error_type": type(e).__name__
            }
            self.storage.save_episode(episode)
            
            raise
    
    def reset_to_stage(self, episode_id: str, target_stage: str) -> Episode:
        """Reset episode to previous stage for manual recovery."""
        episode = self.storage.load_episode(episode_id)
        
        # Clear checkpoints after target stage
        if episode.checkpoints:
            stages_to_clear = []
            stage_order = ["ideation", "outlining", "segment_generation", 
                          "script_generation", "audio_synthesis", "audio_mixing"]
            
            target_idx = stage_order.index(target_stage)
            for stage in stage_order[target_idx + 1:]:
                if stage in episode.checkpoints:
                    stages_to_clear.append(stage)
            
            for stage in stages_to_clear:
                del episode.checkpoints[stage]
        
        # Update status
        stage_status_map = {
            "ideation": EpisodeStatus.IDEATION,
            "outlining": EpisodeStatus.OUTLINING,
            "segment_generation": EpisodeStatus.SEGMENT_GENERATION,
            "script_generation": EpisodeStatus.SCRIPT_GENERATION,
            "audio_synthesis": EpisodeStatus.AUDIO_SYNTHESIS,
            "audio_mixing": EpisodeStatus.AUDIO_MIXING,
        }
        episode.status = stage_status_map[target_stage]
        
        self.storage.save_episode(episode)
        logger.info(f"Reset episode {episode_id} to {target_stage}")
        
        return episode
```

### Task 6.7: Progress Tracking & Testing
Provide visibility into pipeline execution and validate reliability.

**Subtasks**:
- [ ] 6.7.1: Implement `ProgressTracker` class
- [ ] 6.7.2: Report stage progress (e.g., "Audio synthesis: 3/10 segments")
- [ ] 6.7.3: Calculate estimated time remaining
- [ ] 6.7.4: Log to console and file
- [ ] 6.7.5: Add optional webhook notifications (future)
- [ ] 6.7.6: Test checkpoint save/restore at each stage
- [ ] 6.7.7: Test error recovery (inject failure at each stage)
- [ ] 6.7.8: Create gated real API test (full episode generation, budgeted at $5-10)

**Expected Outputs**:
- `src/orchestrator/progress_tracker.py`
- Progress logging utilities
- Integration test suite in `tests/test_pipeline_integration.py`

**Technical Notes**:
```python
from datetime import datetime
from typing import Optional

class ProgressTracker:
    def __init__(self):
        self.current_stage: Optional[str] = None
        self.stage_start_time: Optional[datetime] = None
        self.total_stages = 8
        self.completed_stages = 0
    
    def start_stage(self, stage_name: str) -> None:
        """Mark stage as started."""
        self.current_stage = stage_name
        self.stage_start_time = datetime.now()
        logger.info(f"▶ Starting stage: {stage_name} ({self.completed_stages + 1}/{self.total_stages})")
    
    def complete_stage(self, stage_name: str) -> None:
        """Mark stage as completed."""
        if self.stage_start_time:
            duration = (datetime.now() - self.stage_start_time).total_seconds()
            logger.info(f"✓ Completed stage: {stage_name} ({duration:.1f}s)")
        
        self.completed_stages += 1
        self.current_stage = None
        self.stage_start_time = None
    
    def report_substage_progress(self, current: int, total: int, description: str) -> None:
        """Report progress within a stage."""
        percentage = (current / total) * 100
        logger.info(f"  ⌛ {description}: {current}/{total} ({percentage:.0f}%)")
    
    def estimate_time_remaining(self, avg_stage_duration: float) -> float:
        """Estimate time remaining based on average stage duration."""
        remaining_stages = self.total_stages - self.completed_stages
        return remaining_stages * avg_stage_duration

# Usage in orchestrator
class PipelineOrchestrator:
    def __init__(self, ...):
        self.progress = ProgressTracker()
    
    def _execute_audio_synthesis(self, episode: Episode, show_blueprint: ShowBlueprint) -> Episode:
        self.progress.start_stage("Audio Synthesis")
        
        total_lines = len(episode.script.lines)
        audio_segments = []
        
        for i, script_line in enumerate(episode.script.lines, 1):
            self.progress.report_substage_progress(i, total_lines, "Synthesizing segments")
            # ... synthesis logic
        
        self.progress.complete_stage("Audio Synthesis")
        return episode
```

## 🧪 Testing Requirements

### Unit Tests
- **Checkpoint Tests**:
  - Save checkpoint after each stage
  - Load checkpoint and resume
  - Validate checkpoint integrity
  - Handle corrupted checkpoints
  - Cost tracking accumulation

- **Error Handling Tests**:
  - Retry logic for transient errors
  - Failure after max retries
  - Error state saved to episode
  - Reset to previous stage
  - Circuit breaker triggers after repeated failures

- **Progress Tracking Tests**:
  - Stage progress reporting
  - Substage progress (e.g., audio synthesis)
  - Time estimation accuracy
  - Log output format

### Integration Tests
- **End-to-End Pipeline** (mock services):
  - Full pipeline from SEGMENT_GENERATION → COMPLETE
  - Checkpoint save/restore at each stage
  - Error injection and recovery
  - Cost tracking accumulation
  - Resume from each stage
  
- **Real API Tests** (gated with `@pytest.mark.real_api`):
  - Full episode generation with OpenAI + ElevenLabs (budgeted at $5-10)
  - Validate final MP3 output
  - Verify cost tracking accuracy
  - Test checkpoint resume with real data

### Fixtures
```python
@pytest.fixture
def orchestrator_with_all_services(
    prompt_enhancer,
    mock_ideation,
    mock_outline,
    mock_segment,
    mock_script,
    mock_tts,
    mock_mixer,
    mock_images,
    mock_show_manager,
    episode_storage
):
    return PipelineOrchestrator(
        prompt_enhancer=prompt_enhancer,
        ideation_service=mock_ideation,
        outline_service=mock_outline,
        segment_service=mock_segment,
        script_service=mock_script,
        tts_factory=Mock(return_value=mock_tts),
        audio_mixer=mock_mixer,
        image_manager=mock_images,
        show_blueprint_manager=mock_show_manager,
        episode_storage=episode_storage,
        settings=Settings()
    )

@pytest.mark.real_api
def test_full_pipeline_real_api(orchestrator_real_services):
    """Full episode generation with real APIs (budgeted at $5-10)."""
    episode = orchestrator_real_services.generate_episode(
        show_id="olivers_workshop",
        topic="How rainbows form",
        duration=10  # Shorter duration to reduce cost
    )
    
    assert episode.status == EpisodeStatus.COMPLETE
    assert episode.final_audio_path.exists()
    assert episode.total_cost < 10.0  # Budget check
    assert len(episode.checkpoints) == 6  # All stages completed
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
1. **Checkpointing**: Save after each stage for full resume capability
2. **Retry Logic**: 3 attempts with exponential backoff for transient errors
3. **Error Boundaries**: Each stage wrapped in try-except to prevent cascade failures
4. **Cost Tracking**: Accumulate cost in checkpoints for transparency
5. **Progress Reporting**: Real-time logging with substage progress

### Performance Considerations
- **Stage Duration**: Segment (10-20s), Script (10-20s), TTS (30-60s), Mixing (10-15s)
- **Total Time**: ~2-5 minutes per episode with real APIs (mock: ~10 seconds)
- **Memory**: Keep audio files on disk, not in memory
- **Parallelization**: Consider parallel TTS for multiple segments in future (out of scope for MVP)

## 📂 File Structure
```
src/orchestrator/
├── __init__.py
├── pipeline.py            # Extended with service integration
├── approval.py            # From WP6a
├── error_handler.py       # New: error handling utilities
└── progress_tracker.py    # New: progress tracking

tests/orchestrator/
├── test_pipeline_states.py      # From WP6a
├── test_approval_workflow.py    # From WP6a
├── test_checkpointing.py        # New
├── test_error_handling.py       # New
├── test_progress_tracking.py    # New
└── test_pipeline_integration.py # New: end-to-end tests
```

## ✅ Definition of Done
- [ ] PipelineOrchestrator executes all 8 stages in sequence
- [ ] Service integration for TTS, Audio Mixer, Image Manager
- [ ] Checkpointing saves intermediate state after each stage
- [ ] Resume capability works from any stage (including AWAITING_APPROVAL)
- [ ] Error handling with retry logic (3 attempts, exponential backoff)
- [ ] Manual error recovery (reset to previous stage)
- [ ] Progress tracking with stage and substage reporting
- [ ] Cost tracking accumulation in checkpoints
- [ ] Test coverage ≥ 80% for all orchestrator modules
- [ ] Full pipeline integration test with mock services
- [ ] At least 1 real API test generating complete episode (gated, budgeted at $5-10)
- [ ] Documentation includes checkpoint format, error recovery guide, and resume workflow
