# WP2b: Segment Generation, Script Generation & Cost Tracking

**Parent WP**: [WP2: LLM Services & Story Generation](WP2_LLM_Service.md)  
**Status**: ⏳ Not Started  
**Dependencies**: [WP2a: Provider, Ideation & Outline](WP2a_Provider_Ideation_Outline.md)  
**Estimated Effort**: 2 days  
**Owner**: TBD  
**Subsystem:** Content Generation

## 📋 Overview

This sub-work package implements the final two stages of story generation: **Segment Generation** (outline → detailed scenes) and **Script Generation** (segments → narration + dialogue). It also establishes **cost tracking** for token usage monitoring and **response validation** to ensure LLM outputs conform to expected schemas.

**Key Deliverables**:
- **SegmentGenerationService**: Outline → Detailed segments with scene descriptions
- **ScriptGenerationService**: Segments → Narration + dialogue scripts
- Response parsing and Pydantic validation
- Cost tracking and token usage monitoring
- Integration tests for end-to-end LLM pipeline

**Subsystem Context**:
- **Subsystem:** Content Generation
- **Depends on:** WP2a (Provider abstraction, Ideation, Outline)
- **Used by:** WP6 (Orchestrator), WP3 (TTS synthesis)

**This Sub-WP Covers**: Tasks 2.4 (Segment Generation), 2.5 (Script Generation), 2.6 (Response Parsing), and 2.7 (Cost Tracking + Testing).

## 🎯 High-Level Tasks

### Task 2.4: SegmentGenerationService
Expand story beats into detailed segments (what happens).

**Subtasks**:
- [ ] 2.4.1: Create `SegmentGenerationService` class
- [ ] 2.4.2: Implement `generate_segments(outline: StoryOutline, show_blueprint: ShowBlueprint) -> list[StorySegment]` method
- [ ] 2.4.3: Integrate Show Blueprint context via prompt enhancement
- [ ] 2.4.4: Generate detailed scene descriptions for each beat
- [ ] 2.4.5: Include characters_involved, setting, educational_content
- [ ] 2.4.6: Ensure world rules consistency
- [ ] 2.4.7: Add supporting character interactions
- [ ] 2.4.8: Validate segment count (3-7 per beat)

**Expected Outputs**:
- `src/services/llm/segment_generation_service.py`
- `StorySegment` model validation
- Segment prompt templates

### Task 2.5: ScriptGenerationService
Transform segments into narration + dialogue scripts.

**Subtasks**:
- [ ] 2.5.1: Create `ScriptGenerationService` class
- [ ] 2.5.2: Implement `generate_scripts(segments: list[StorySegment], show_blueprint: ShowBlueprint) -> list[Script]` method
- [ ] 2.5.3: Integrate narrator voice guidelines via prompt enhancement
- [ ] 2.5.4: Generate narration for scene setting and transitions
- [ ] 2.5.5: Generate character dialogue with speaker tags
- [ ] 2.5.6: Include protagonist catchphrases appropriately
- [ ] 2.5.7: Add emotion/tone hints for TTS
- [ ] 2.5.8: Implement duration estimation (150 words/minute)
- [ ] 2.5.9: Validate script completeness

**Expected Outputs**:
- `src/services/llm/script_generation_service.py`
- `Script` model with `ScriptBlock` list
- Script prompt templates

### Task 2.6: Response Parsing & Validation
Ensure LLM outputs conform to expected schemas.

**Subtasks**:
- [ ] 2.6.1: Implement JSON parsing with fallback for malformed responses
- [ ] 2.6.2: Add Pydantic validation for StoryOutline, StorySegment, Script models
- [ ] 2.6.3: Implement retry on validation failure with prompt adjustment
- [ ] 2.6.4: Add error logging for malformed responses
- [ ] 2.6.5: Create fallback strategies (simpler prompts, temperature adjustment)

**Expected Outputs**:
- Robust parsing utilities in `src/services/llm/parsing.py`
- Validation error handling

### Task 2.7: Cost Tracking & Integration Testing
Track token usage and API costs across all 4 services + validate end-to-end flow.

**Subtasks**:
- [ ] 2.7.1: Implement token counting for each generation stage
- [ ] 2.7.2: Add cost calculation per provider (GPT-4, Claude)
- [ ] 2.7.3: Log all LLM calls with metadata (stage, tokens, cost, duration)
- [ ] 2.7.4: Create cost summary per episode
- [ ] 2.7.5: Add budget warnings when approaching limits
- [ ] 2.7.6: Test ideation → scripting pipeline with mock provider
- [ ] 2.7.7: Test provider switching (mock → OpenAI → Anthropic)
- [ ] 2.7.8: Test error handling for API rate limits
- [ ] 2.7.9: Test cost tracking accuracy
- [ ] 2.7.10: Create gated real API test (pytest marker `@pytest.mark.real_api`)

**Expected Outputs**:
- `src/services/llm/cost_tracker.py`
- Cost logging utilities
- Integration test suite in `tests/test_llm_integration.py`

## 🔧 Technical Specifications

### SegmentGenerationService Usage
```python
from src.services.llm.segment_generation_service import SegmentGenerationService

# Initialize
segment_service = SegmentGenerationService(provider, enhancer)

# Generate segments from outline
segments = await segment_service.generate_segments(
    outline=story_outline,
    show_blueprint=show_blueprint
)

# Output: List of StorySegment models
"""
[
  StorySegment(
    segment_number=1,
    beat_number=1,
    description="Oliver stands in his cluttered workshop, staring at his model volcano...",
    characters_involved=["oliver"],
    setting="Oliver's Workshop - workbench area",
    educational_content="Volcanic eruptions can be explosive or gentle depending on magma composition"
  ),
  ...
]
"""
```

### ScriptGenerationService Output Format
```python
# Script model structure
Script(
    segment_number=1,
    script_blocks=[
        ScriptBlock(
            speaker="narrator",
            text="In Oliver's workshop, surrounded by tools and gadgets, a small model volcano sits on the workbench.",
            speaker_voice_id="narrator_calm",
            duration_estimate=4.5,
            emotion="neutral"
        ),
        ScriptBlock(
            speaker="oliver",
            text="I followed the instructions exactly! Why did it explode like that?",
            speaker_voice_id="oliver_curious",
            duration_estimate=3.2,
            emotion="curious"
        ),
        ScriptBlock(
            speaker="narrator",
            text="Oliver's curiosity was sparked. He needed to understand the science behind volcanoes.",
            speaker_voice_id="narrator_calm",
            duration_estimate=4.8,
            emotion="thoughtful"
        )
    ]
)
```

### Script Block Structure
```python
from pydantic import BaseModel, Field

class ScriptBlock(BaseModel):
    """Single block of narration or dialogue."""
    speaker: str = Field(..., description="Speaker ID (narrator, character name)")
    text: str = Field(..., description="Spoken text")
    speaker_voice_id: str = Field(..., description="Voice ID for TTS")
    duration_estimate: float = Field(..., description="Estimated duration in seconds")
    emotion: str | None = Field(None, description="Emotion/tone hint for TTS")
    
    @property
    def word_count(self) -> int:
        return len(self.text.split())

class Script(BaseModel):
    """Complete script for one segment."""
    segment_number: int
    script_blocks: list[ScriptBlock]
    
    @property
    def total_duration(self) -> float:
        return sum(block.duration_estimate for block in self.script_blocks)
```

### Cost Tracker Implementation
```python
from dataclasses import dataclass
from datetime import datetime

@dataclass
class LLMCallMetrics:
    """Metrics for a single LLM API call."""
    stage: str  # ideation, outline, segment, script
    prompt_tokens: int
    completion_tokens: int
    total_tokens: int
    cost: float
    duration_seconds: float
    timestamp: datetime
    provider: str
    model: str

class CostTracker:
    """Track LLM API costs and token usage."""
    
    def __init__(self):
        self.calls: list[LLMCallMetrics] = []
    
    def log_call(
        self,
        stage: str,
        prompt_tokens: int,
        completion_tokens: int,
        cost: float,
        duration: float,
        provider: str,
        model: str
    ) -> None:
        """Log a single LLM API call."""
        self.calls.append(LLMCallMetrics(
            stage=stage,
            prompt_tokens=prompt_tokens,
            completion_tokens=completion_tokens,
            total_tokens=prompt_tokens + completion_tokens,
            cost=cost,
            duration_seconds=duration,
            timestamp=datetime.now(),
            provider=provider,
            model=model
        ))
    
    def get_episode_cost(self) -> float:
        """Get total cost for all calls."""
        return sum(call.cost for call in self.calls)
    
    def get_stage_breakdown(self) -> dict[str, float]:
        """Get cost breakdown by stage."""
        breakdown = {}
        for call in self.calls:
            breakdown[call.stage] = breakdown.get(call.stage, 0.0) + call.cost
        return breakdown
    
    def export_report(self) -> dict:
        """Export cost report for episode checkpoint."""
        return {
            "total_cost": self.get_episode_cost(),
            "total_tokens": sum(call.total_tokens for call in self.calls),
            "stage_breakdown": self.get_stage_breakdown(),
            "call_count": len(self.calls),
            "calls": [
                {
                    "stage": call.stage,
                    "tokens": call.total_tokens,
                    "cost": call.cost,
                    "timestamp": call.timestamp.isoformat()
                }
                for call in self.calls
            ]
        }
```

### Response Parsing with Validation
```python
import json
from pydantic import ValidationError
from typing import TypeVar, Type

T = TypeVar('T')

class LLMResponseParser:
    """Parse and validate LLM responses."""
    
    async def parse_and_validate(
        self,
        response: str,
        model_class: Type[T],
        retry_callback: callable | None = None,
        max_retries: int = 3
    ) -> T:
        """Parse JSON response and validate against Pydantic model."""
        for attempt in range(max_retries):
            try:
                # Try to extract JSON from response
                json_str = self._extract_json(response)
                data = json.loads(json_str)
                
                # Validate with Pydantic
                return model_class.model_validate(data)
                
            except (json.JSONDecodeError, ValidationError) as e:
                if attempt < max_retries - 1 and retry_callback:
                    # Retry with adjusted prompt
                    response = await retry_callback(
                        error=str(e),
                        previous_response=response
                    )
                else:
                    raise ValueError(f"Failed to parse response after {max_retries} attempts: {e}")
    
    def _extract_json(self, response: str) -> str:
        """Extract JSON from response (handle markdown code blocks)."""
        # Remove markdown code blocks if present
        if "```json" in response:
            start = response.find("```json") + 7
            end = response.find("```", start)
            return response[start:end].strip()
        elif "```" in response:
            start = response.find("```") + 3
            end = response.find("```", start)
            return response[start:end].strip()
        return response.strip()
```

## 🧪 Testing Strategy

### Unit Tests
```python
# tests/services/llm/test_script_generation_service.py
@pytest.mark.asyncio
async def test_generate_script_includes_narrator():
    """Test that script includes narrator blocks."""
    provider = MockLLMProvider()
    service = ScriptGenerationService(provider, enhancer)
    
    scripts = await service.generate_scripts(segments, blueprint)
    
    assert len(scripts) == len(segments)
    for script in scripts:
        narrator_blocks = [b for b in script.script_blocks if b.speaker == "narrator"]
        assert len(narrator_blocks) > 0
```

### Integration Tests
```python
# tests/test_llm_integration.py
@pytest.mark.asyncio
async def test_complete_story_generation_pipeline():
    """Test complete flow: topic → concept → outline → segments → scripts."""
    # Initialize services
    ideation = IdeationService(provider, enhancer)
    outline_service = OutlineService(provider, enhancer)
    segment_service = SegmentGenerationService(provider, enhancer)
    script_service = ScriptGenerationService(provider, enhancer)
    tracker = CostTracker()
    
    # Run pipeline
    concept = await ideation.generate_concept(topic, blueprint)
    outline = await outline_service.generate_outline(concept, blueprint)
    segments = await segment_service.generate_segments(outline, blueprint)
    scripts = await script_service.generate_scripts(segments, blueprint)
    
    # Validate outputs
    assert len(outline.story_beats) >= 3
    assert len(segments) >= len(outline.story_beats)
    assert len(scripts) == len(segments)
    
    # Check cost tracking
    report = tracker.export_report()
    assert report["total_cost"] > 0
    assert len(report["stage_breakdown"]) == 4  # ideation, outline, segment, script
```

### Real API Test (Gated)
```python
@pytest.mark.real_api
@pytest.mark.asyncio
async def test_openai_provider_real_call():
    """Test real OpenAI API call (requires API key)."""
    settings = get_settings()
    if not settings.OPENAI_API_KEY:
        pytest.skip("OPENAI_API_KEY not set")
    
    provider = OpenAIProvider(settings.OPENAI_API_KEY)
    response = await provider.generate(
        prompt="Generate a one-sentence story concept about space.",
        max_tokens=100
    )
    
    assert len(response) > 10
    assert isinstance(response, str)
```

## 📦 Dependencies

### Python Packages
```toml
# pyproject.toml additions (inherited from WP2a)
pydantic = "^2.5.0"
openai = "^1.0.0"
anthropic = "^0.18.0"
tiktoken = "^0.6.0"
tenacity = "^8.2.0"
```

## 📋 Definition of Done

- [ ] SegmentGenerationService generates valid StorySegment lists
- [ ] ScriptGenerationService generates valid Script objects
- [ ] Response parsing handles malformed JSON gracefully
- [ ] Pydantic validation catches schema violations
- [ ] Retry logic works for validation failures
- [ ] CostTracker logs all LLM calls with accurate costs
- [ ] Cost summary export includes stage breakdown
- [ ] Integration test validates complete pipeline (topic → scripts)
- [ ] Provider switching test passes
- [ ] Real API test runs when gated marker used
- [ ] Documentation includes usage examples
- [ ] Code reviewed and merged to main branch

## 🔗 Related Work Packages

- **Depends on:**
  - [WP2a: Provider, Ideation & Outline](WP2a_Provider_Ideation_Outline.md) - Provider abstraction and first two generation stages
  
- **Enables:**
  - [WP3: TTS Service](WP3_TTS_Service.md) - Script → Audio synthesis
  - [WP6: Orchestrator](WP6_Orchestrator.md) - Complete story generation pipeline
  
- **Parallel Development:**
  - ✅ Can develop WP3 (TTS), WP4 (Audio), WP5 (Image) in parallel after provider abstraction complete
