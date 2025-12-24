# WP6a: State Machine & Workflow

**Status**: ⏳ Not Started  
**Parent WP**: WP6 (Orchestrator)  
**Dependencies**: WP0 (Prompt Enhancement), WP1 (Foundation), WP2 (LLM)  
**Estimated Effort**: 1.5-2 days  
**Owner**: TBD  
**Subsystem:** Orchestration

## 📋 Overview

Implement the core pipeline state machine with 8 stages (IDEATION → OUTLINING → AWAITING_APPROVAL → SEGMENT_GENERATION → SCRIPT_GENERATION → AUDIO_SYNTHESIS → AUDIO_MIXING → COMPLETE), including human approval workflow and Show Blueprint integration. This work package focuses on the orchestration logic and approval gate, without implementing reliability features like checkpointing.

**Key Deliverables**:
- State machine for 8 pipeline stages with approval gate
- Human approval workflow (pause, review, approve/reject)
- Show Blueprint context injection at each stage
- State transition validation and progression logic
- Event emission for UI notifications

**System Context**:
- **Subsystem:** Orchestration
- **Depends on:** WP0 (Prompt Enhancement), WP1 (Foundation), WP2 (LLM)
- **Used by:** WP6b (Reliability), WP7 (CLI), WP9 (Dashboard)
- **Parallel Development:** ❌ Must wait for dependencies

## 🎯 High-Level Tasks

### Task 6.1: Pipeline State Machine
Implement core workflow orchestration with 8 stages.

**Subtasks**:
- [ ] 6.1.1: Create `PipelineOrchestrator` class with service dependency injection
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

**Technical Notes**:
```python
from src.models.episode import Episode, EpisodeStatus
from enum import Enum

class PipelineStage(str, Enum):
    IDEATION = "ideation"
    OUTLINING = "outlining"
    AWAITING_APPROVAL = "awaiting_approval"
    SEGMENT_GENERATION = "segment_generation"
    SCRIPT_GENERATION = "script_generation"
    AUDIO_SYNTHESIS = "audio_synthesis"
    AUDIO_MIXING = "audio_mixing"
    COMPLETE = "complete"
    REJECTED = "rejected"
    FAILED = "failed"

class PipelineOrchestrator:
    def __init__(
        self,
        prompt_enhancer: PromptEnhancer,
        ideation_service: IdeationService,
        outline_service: OutlineService,
        segment_service: SegmentGenerationService,
        script_service: ScriptGenerationService,
        show_blueprint_manager: ShowBlueprintManager,
        episode_storage: EpisodeStorage
    ):
        self.prompt_enhancer = prompt_enhancer
        self.ideation = ideation_service
        self.outline = outline_service
        self.segment = segment_service
        self.script = script_service
        self.show_manager = show_blueprint_manager
        self.storage = episode_storage
    
    def execute_stage(self, episode: Episode) -> Episode:
        """Execute current stage and transition to next."""
        if episode.status == EpisodeStatus.IDEATION:
            return self._execute_ideation(episode)
        elif episode.status == EpisodeStatus.OUTLINING:
            return self._execute_outlining(episode)
        elif episode.status == EpisodeStatus.AWAITING_APPROVAL:
            raise ValueError("Episode awaiting approval - call submit_approval() first")
        elif episode.status == EpisodeStatus.SEGMENT_GENERATION:
            return self._execute_segment_generation(episode)
        # ... additional stages
    
    def can_transition_to(self, episode: Episode, target_status: EpisodeStatus) -> bool:
        """Validate if state transition is allowed."""
        valid_transitions = {
            EpisodeStatus.IDEATION: [EpisodeStatus.OUTLINING],
            EpisodeStatus.OUTLINING: [EpisodeStatus.AWAITING_APPROVAL],
            EpisodeStatus.AWAITING_APPROVAL: [EpisodeStatus.SEGMENT_GENERATION, EpisodeStatus.REJECTED],
            EpisodeStatus.SEGMENT_GENERATION: [EpisodeStatus.SCRIPT_GENERATION],
            EpisodeStatus.SCRIPT_GENERATION: [EpisodeStatus.AUDIO_SYNTHESIS],
            EpisodeStatus.AUDIO_SYNTHESIS: [EpisodeStatus.AUDIO_MIXING],
            EpisodeStatus.AUDIO_MIXING: [EpisodeStatus.COMPLETE],
            EpisodeStatus.REJECTED: [EpisodeStatus.IDEATION],
        }
        return target_status in valid_transitions.get(episode.status, [])
```

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

**Technical Notes**:
```python
from datetime import datetime, timedelta
from src.models.outline import StoryOutline

class ApprovalWorkflow:
    def __init__(self, episode_storage: EpisodeStorage):
        self.storage = episode_storage
    
    def submit_approval(
        self,
        episode_id: str,
        approved: bool,
        edited_outline: StoryOutline | None = None,
        feedback: str | None = None
    ) -> Episode:
        """Submit approval decision for episode outline."""
        episode = self.storage.load_episode(episode_id)
        
        if episode.status != EpisodeStatus.AWAITING_APPROVAL:
            raise ValueError(f"Episode {episode_id} is not awaiting approval (status: {episode.status})")
        
        if approved:
            # Update outline if edited
            if edited_outline:
                episode.outline = edited_outline
                logger.info(f"Updated outline for episode {episode_id}")
            
            # Transition to next stage
            episode.status = EpisodeStatus.SEGMENT_GENERATION
            episode.approval_date = datetime.now()
            logger.info(f"Episode {episode_id} approved, proceeding to segment generation")
        else:
            # Reject and store feedback
            episode.status = EpisodeStatus.REJECTED
            episode.rejection_feedback = feedback
            episode.rejection_date = datetime.now()
            logger.warning(f"Episode {episode_id} rejected: {feedback}")
        
        self.storage.save_episode(episode)
        self._emit_approval_event(episode, approved)
        
        return episode
    
    def check_approval_timeout(self, episode: Episode) -> bool:
        """Check if episode has been awaiting approval for too long."""
        if episode.status != EpisodeStatus.AWAITING_APPROVAL:
            return False
        
        if not episode.outline_created_at:
            return False
        
        timeout_days = 7
        time_waiting = datetime.now() - episode.outline_created_at
        return time_waiting > timedelta(days=timeout_days)
    
    def _emit_approval_event(self, episode: Episode, approved: bool) -> None:
        """Emit event for UI notifications (WebSocket)."""
        # Future: Implement WebSocket/SSE notification
        logger.debug(f"Approval event: episode={episode.id}, approved={approved}")
```

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
- Show Blueprint loading logic in orchestrator
- Context passing through all stages
- Concepts update after completion

**Technical Notes**:
```python
class PipelineOrchestrator:
    def generate_episode(
        self,
        show_id: str,
        topic: str,
        duration: int = 15
    ) -> Episode:
        """Execute full pipeline for new episode."""
        # Load Show Blueprint
        show_blueprint = self.show_manager.load_show(show_id)
        
        # Create episode
        episode = Episode(
            id=self._generate_id(topic),
            show_id=show_id,
            title=self._generate_title(topic),
            topic=topic,
            duration_minutes=duration,
            status=EpisodeStatus.IDEATION
        )
        
        # Save initial state
        self.storage.save_episode(episode)
        
        # Execute pipeline stages with Show Blueprint context
        episode = self._execute_ideation(episode, show_blueprint)
        episode = self._execute_outlining(episode, show_blueprint)
        # ... continues at approval gate
        
        return episode
    
    def _execute_ideation(self, episode: Episode, show_blueprint: ShowBlueprint) -> Episode:
        """Execute ideation stage with Show Blueprint context."""
        concept = self.ideation.generate_concept(
            topic=episode.topic,
            show_blueprint=show_blueprint,
            duration=episode.duration_minutes
        )
        
        episode.concept = concept
        episode.status = EpisodeStatus.OUTLINING
        self.storage.save_episode(episode)
        
        return episode
    
    def _finalize_episode(self, episode: Episode) -> Episode:
        """Update Show Blueprint with completed episode."""
        show_blueprint = self.show_manager.load_show(episode.show_id)
        
        # Update concepts covered
        self.show_manager.add_concepts_covered(
            show_id=episode.show_id,
            episode_id=episode.id,
            concepts=episode.concept.educational_objectives
        )
        
        # Link episode to show
        self.show_manager.link_episode(episode.show_id, episode.id)
        
        return episode
```

## 🧪 Testing Requirements

### Unit Tests
- **State Machine Tests**:
  - Valid state transitions (IDEATION → OUTLINING → AWAITING_APPROVAL → ...)
  - Invalid state transitions rejected
  - Can't skip approval gate
  - REJECTED state requires restart from IDEATION
  
- **Approval Workflow Tests**:
  - Submit approval with approval=True
  - Submit approval with approval=False and feedback
  - Submit approval with edited outline
  - Approval timeout detection (> 7 days)
  - Cannot approve episode in wrong state
  
- **Show Blueprint Integration Tests**:
  - Show Blueprint loaded at pipeline start
  - Show Blueprint passed to all stages
  - Concepts updated after COMPLETE
  - Episode linked to show

### Integration Tests
- **End-to-End Workflow** (mock services):
  - IDEATION → OUTLINING → AWAITING_APPROVAL
  - Approve → SEGMENT_GENERATION (continue in WP6b)
  - Reject → REJECTED → restart from IDEATION
  - Edit outline → approve → continue

### Fixtures
```python
@pytest.fixture
def orchestrator_for_state_machine(
    prompt_enhancer,
    mock_ideation,
    mock_outline,
    mock_show_manager,
    episode_storage
):
    return PipelineOrchestrator(
        prompt_enhancer=prompt_enhancer,
        ideation_service=mock_ideation,
        outline_service=mock_outline,
        segment_service=Mock(),
        script_service=Mock(),
        show_blueprint_manager=mock_show_manager,
        episode_storage=episode_storage
    )

@pytest.fixture
def approval_workflow(episode_storage):
    return ApprovalWorkflow(episode_storage=episode_storage)
```

## 📝 Implementation Notes

### Key Design Decisions
1. **Sequential Pipeline**: Stages execute in strict order (no parallelization in MVP)
2. **Approval Gate**: Pipeline pauses at AWAITING_APPROVAL until human decision
3. **State Validation**: Enforce valid state transitions to prevent inconsistencies
4. **Show Blueprint Context**: Loaded once at start, passed to all stages
5. **Event Emission**: Prepare for future WebSocket/SSE notifications

### Performance Considerations
- **Stage Duration**: Ideation (5-10s), Outlining (10-20s) with real APIs
- **Memory**: Keep intermediate outputs in Episode model
- **Show Blueprint Loading**: Cache in orchestrator to avoid repeated disk reads

## 📂 File Structure
```
src/orchestrator/
├── __init__.py
├── pipeline.py            # PipelineOrchestrator
└── approval.py            # ApprovalWorkflow

tests/orchestrator/
├── test_pipeline_states.py
├── test_approval_workflow.py
└── test_show_blueprint_integration.py
```

## ✅ Definition of Done
- [ ] PipelineOrchestrator executes IDEATION → OUTLINING → AWAITING_APPROVAL stages
- [ ] State transition validation prevents invalid state changes
- [ ] Approval workflow supports approve/reject/edit outline
- [ ] Approval timeout warnings for episodes pending > 7 days
- [ ] Show Blueprint loaded and passed to all LLM stages
- [ ] Concepts updated after episode COMPLETE
- [ ] Test coverage ≥ 80% for state machine and approval modules
- [ ] Integration test validates approval gate workflow
- [ ] Documentation includes state machine diagram and approval workflow guide
