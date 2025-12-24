# WP2: LLM Services & Story Generation

**Status**: ⏳ Not Started  
**Dependencies**: WP0 (Prompt Enhancement), WP1 (Foundation)  
**Estimated Effort**: 4-5 days  
**Owner**: TBD  
**Subsystem:** Content Generation

## 📋 Overview

LLM Services provide **incremental story generation** through 4 distinct stages: Ideation (story concept), Outlining (story beats), Segment Generation (detailed scenes), and Script Generation (narration + dialogue). Each service integrates with the prompt enhancer to inject Show Blueprint context for story continuity.

**Key Deliverables**:
- Provider abstraction layer (OpenAI, Anthropic, Mock)
- **IdeationService**: Topic → Story concept
- **OutlineService**: Concept → Story beats (reviewable)
- **SegmentGenerationService**: Outline → Detailed segments
- **ScriptGenerationService**: Segments → Narration + dialogue
- Validation and error handling
- Cost tracking and token usage monitoring

**System Context**:
- **Subsystem:** Content Generation
- **Depends on:** WP0 (Prompt Enhancement), WP1 (Show Blueprint models)
- **Used by:** WP6 (Orchestrator)
- **Parallel Development:** ✅ Can develop in parallel with WP3, WP4, WP5 after WP1 complete

## 🎯 High-Level Tasks

### Task 2.1: Provider Abstraction
Implement base LLM provider interface and concrete implementations.

**Subtasks**:
- [ ] 2.1.1: Create `BaseLLMProvider` abstract base class with `generate()` method
- [ ] 2.1.2: Implement `OpenAIProvider` using openai>=1.0 SDK
- [ ] 2.1.3: Implement `AnthropicProvider` using anthropic SDK
- [ ] 2.1.4: Implement `MockLLMProvider` with fixture-based responses (story concepts, outlines, segments, scripts)
- [ ] 2.1.5: Create `LLMProviderFactory` for provider instantiation
- [ ] 2.1.6: Add retry logic with exponential backoff for API failures
- [ ] 2.1.7: Implement response streaming support for long generations

**Expected Outputs**:
- `src/services/llm/base.py`
- `src/services/llm/openai_provider.py`
- `src/services/llm/anthropic_provider.py`
- `src/services/llm/mock_provider.py`
- `src/services/llm/factory.py`

### Task 2.2: IdeationService
Generate story concept from user topic.

**Subtasks**:
- [ ] 2.2.1: Create `IdeationService` class
- [ ] 2.2.2: Implement `generate_concept(topic: str, show_blueprint: ShowBlueprint) -> str` method
- [ ] 2.2.3: Integrate with prompt enhancer to inject Show Blueprint context
- [ ] 2.2.4: Generate 2-3 paragraph story concept with protagonist adventure
- [ ] 2.2.5: Include educational concept tie-in
- [ ] 2.2.6: Check concepts_covered.json to avoid repetition
- [ ] 2.2.7: Add age-appropriateness validation
- [ ] 2.2.8: Implement content safety checks

**Expected Outputs**:
- `src/services/llm/ideation_service.py`
- Story concept validation
- Ideation prompt templates (via WP0)

### Task 2.3: OutlineService
Transform story concept into reviewable outline with story beats.

**Subtasks**:
- [ ] 2.3.1: Create `OutlineService` class
- [ ] 2.3.2: Implement `generate_outline(concept: str, show_blueprint: ShowBlueprint) -> StoryOutline` method
- [ ] 2.3.3: Integrate Show Blueprint context (world, characters) via prompt enhancement
- [ ] 2.3.4: Generate 3-5 story beats with titles, descriptions, key moments
- [ ] 2.3.5: Ensure each beat has educational focus
- [ ] 2.3.6: Include protagonist value demonstration
- [ ] 2.3.7: Add duration estimation (total ~10-15 minutes)
- [ ] 2.3.8: Output YAML format for human review

**Expected Outputs**:
- `src/services/llm/outline_service.py`
- `StoryOutline` Pydantic model validation
- Outline prompt templates

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

### Task 2.7: Cost Tracking & Monitoring
Track token usage and API costs across all 4 services.

**Subtasks**:
- [ ] 2.7.1: Implement token counting for each generation stage
- [ ] 2.7.2: Add cost calculation per provider (GPT-4, Claude)
- [ ] 2.7.3: Log all LLM calls with metadata (stage, tokens, cost, duration)
- [ ] 2.7.4: Create cost summary per episode
- [ ] 2.7.5: Add budget warnings when approaching limits

**Expected Outputs**:
- `src/services/llm/cost_tracker.py`
- Cost logging utilities
- [ ] 2.4.3: Add Pydantic validation for Script (verify all character IDs exist)
- [ ] 2.4.4: Implement retry logic for invalid responses (up to 3 attempts)
- [ ] 2.4.5: Add logging for validation failures with response examples

**Expected Outputs**:
- Validation utilities in `src/services/llm/validation.py`
- Tests for parsing edge cases

### Task 2.5: Mock Provider Fixtures
Create realistic mock responses for development and testing.

**Subtasks**:
- [ ] 2.5.1: Generate fixture for Oliver + Hannah space exploration episode
- [ ] 2.5.2: Generate fixture for Oliver + Hannah dinosaurs episode
- [ ] 2.5.3: Generate fixture for single-character (Oliver only) episode
- [ ] 2.5.4: Add fixture loading logic based on topic keywords
- [ ] 2.5.5: Implement fixture response timing simulation (artificial delay)

**Expected Outputs**:
- `data/fixtures/llm/ideation_space.json`
- `data/fixtures/llm/script_space_oliver_hannah.json`
- `data/fixtures/llm/ideation_dinosaurs.json`
- `data/fixtures/llm/script_dinosaurs_oliver_hannah.json`

### Task 2.6: Cost Tracking
Monitor API usage and costs for budget management.

**Subtasks**:
- [ ] 2.6.1: Create `CostTracker` class with token counting
- [ ] 2.6.2: Track input and output tokens per request
- [ ] 2.6.3: Calculate cost based on provider pricing (OpenAI: $0.01/1K input, $0.03/1K output)
- [ ] 2.6.4: Store cost data in episode checkpoints
- [ ] 2.6.5: Implement cost reporting (per episode, per stage)
- [ ] 2.6.6: Add budget threshold warnings

**Expected Outputs**:
- `src/services/llm/cost_tracker.py`
- Cost data in episode JSON checkpoints

### Task 2.7: Integration Testing
Validate end-to-end LLM service flow.

**Subtasks**:
- [ ] 2.7.1: Test ideation → scripting pipeline with mock provider
- [ ] 2.7.2: Test provider switching (mock → OpenAI → Anthropic)
- [ ] 2.7.3: Test error handling for API rate limits
- [ ] 2.7.4: Test cost tracking accuracy
- [ ] 2.7.5: Create gated real API test (pytest marker `@pytest.mark.real_api`)

**Expected Outputs**:
- Integration test suite in `tests/test_llm_integration.py`

## 🔧 Technical Specifications

### BaseLLMProvider Interface
```python
from abc import ABC, abstractmethod
from typing import Any

class BaseLLMProvider(ABC):
    """Abstract base class for LLM providers."""
    
    @abstractmethod
    def generate(
        self,
        prompt: str,
        system_prompt: str | None = None,
        temperature: float = 0.7,
        max_tokens: int = 2000,
        response_format: dict[str, Any] | None = None
    ) -> dict[str, Any]:
        """
        Generate text from the LLM.
        
        Args:
            prompt: User/assistant prompt
            system_prompt: System instructions
            temperature: Sampling temperature (0.0-1.0)
            max_tokens: Maximum tokens in response
            response_format: Optional format constraints (e.g., {"type": "json_object"})
            
        Returns:
            dict with keys: "content" (str), "tokens_used" (dict), "model" (str)
        """
        pass
    
    @abstractmethod
    def get_cost(self, tokens_used: dict[str, int]) -> float:
        """Calculate cost in USD for token usage."""
        pass
```

### OpenAI Implementation Example
```python
import openai
from src.services.llm.base import BaseLLMProvider

class OpenAIProvider(BaseLLMProvider):
    def __init__(self, api_key: str, model: str = "gpt-4"):
        self.client = openai.OpenAI(api_key=api_key)
        self.model = model
        
    def generate(
        self,
        prompt: str,
        system_prompt: str | None = None,
        temperature: float = 0.7,
        max_tokens: int = 2000,
        response_format: dict[str, Any] | None = None
    ) -> dict[str, Any]:
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})
        
        kwargs = {
            "model": self.model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens
        }
        if response_format:
            kwargs["response_format"] = response_format
            
        response = self.client.chat.completions.create(**kwargs)
        
        return {
            "content": response.choices[0].message.content,
            "tokens_used": {
                "input": response.usage.prompt_tokens,
                "output": response.usage.completion_tokens,
                "total": response.usage.total_tokens
            },
            "model": response.model
        }
    
    def get_cost(self, tokens_used: dict[str, int]) -> float:
        # GPT-4 pricing (as of 2024)
        input_cost = tokens_used["input"] * 0.03 / 1000
        output_cost = tokens_used["output"] * 0.06 / 1000
        return input_cost + output_cost
```

### Ideation Output Schema
```python
from pydantic import BaseModel, Field

class IdeationOutput(BaseModel):
    """Output from ideation stage."""
    
    refined_topic: str = Field(
        description="Enhanced episode topic with clear focus"
    )
    learning_objectives: list[str] = Field(
        min_length=3,
        max_length=5,
        description="Key educational takeaways"
    )
    key_points: list[str] = Field(
        min_length=5,
        max_length=10,
        description="Discussion points ordered by importance"
    )
    age_appropriate: bool = Field(
        description="Flag indicating content is suitable for 5-12 year olds"
    )
    estimated_duration: int = Field(
        description="Estimated duration in minutes based on content"
    )
```

### Script Generation Example
```python
# Simplified example of scripting service
class ScriptingService:
    def __init__(self, llm_provider: BaseLLMProvider, prompt_enhancer: PromptEnhancer):
        self.llm = llm_provider
        self.enhancer = prompt_enhancer
    
    def generate_script(
        self,
        ideation: IdeationOutput,
        characters: list[Character],
        duration: int
    ) -> Script:
        # Get enhanced prompt with character context
        prompt = self.enhancer.enhance_prompt(
            stage="scripting",
            user_input=ideation.refined_topic,
            characters=characters,
            context={
                "learning_objectives": ideation.learning_objectives,
                "key_points": ideation.key_points,
                "duration": duration
            }
        )
        
        # Generate dialogue
        response = self.llm.generate(
            prompt=prompt,
            temperature=0.8,  # Higher for creative dialogue
            response_format={"type": "json_object"}
        )
        
        # Parse and validate
        script_data = json.loads(response["content"])
        script = Script(**script_data)
        
        return script
```

## 🧪 Testing Requirements

### Unit Tests
- **Provider Tests**:
  - OpenAI provider with mocked API responses
  - Anthropic provider with mocked API responses
  - Mock provider returns fixture data correctly
  - Factory creates correct provider based on settings
  - Retry logic triggers on transient failures
  - Cost calculation accuracy for different models

- **Ideation Service Tests**:
  - Generates valid IdeationOutput for simple topics
  - Rejects inappropriate topics (violence, politics)
  - Scales key points based on duration (10 min vs 20 min)
  - Integrates with prompt enhancer correctly

- **Scripting Service Tests**:
  - Generates balanced dialogue (character participation roughly equal)
  - Respects character speaking styles
  - Estimates duration within ±2 minutes of target
  - Handles single-character episodes
  - Validates all character IDs exist

### Integration Tests
- **End-to-End Pipeline**:
  - User topic → Ideation → Scripting with mock provider
  - Cost tracking accumulates correctly across stages
  - Error recovery: invalid LLM response triggers retry
  
- **Real API Tests** (gated with `@pytest.mark.real_api`):
  - OpenAI provider generates valid ideation
  - Anthropic provider generates valid ideation
  - Full pipeline with real OpenAI API (budgeted at $1-2)

### Fixtures
```python
# tests/fixtures/llm_responses.py
@pytest.fixture
def mock_ideation_space():
    return {
        "content": json.dumps({
            "refined_topic": "How Rockets Work and Space Travel",
            "learning_objectives": [
                "Understand Newton's Third Law (action-reaction)",
                "Learn about rocket fuel and propulsion",
                "Discover how astronauts live in space"
            ],
            "key_points": [
                "Rockets need to push gas down to go up",
                "Fuel is stored in huge tanks",
                "Space has no air or gravity",
                "Astronauts wear special suits",
                "Rockets go really, really fast"
            ],
            "age_appropriate": true,
            "estimated_duration": 15
        }),
        "tokens_used": {"input": 150, "output": 120, "total": 270},
        "model": "gpt-4"
    }
```

## 📝 Implementation Notes

### Dependencies
```toml
[project]
dependencies = [
    "openai>=1.12.0",
    "anthropic>=0.18.0",
    "tenacity>=8.2.0"  # Retry logic
]
```

### Key Design Decisions
1. **Provider Abstraction**: Enables easy swapping between OpenAI, Anthropic, or mocks without changing business logic
2. **Prompt Enhancement Integration**: LLM service calls prompt enhancer rather than building prompts directly
3. **JSON Mode**: Use provider's structured output features (OpenAI `response_format`, Anthropic tool use) for reliable parsing
4. **Cost Tracking**: Store cost data in episode checkpoints for transparency and budget monitoring
5. **Mock Fixtures**: Use real examples generated during development to ensure realistic mock behavior

### Error Handling Strategy
```python
from tenacity import retry, stop_after_attempt, wait_exponential

class ScriptingService:
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10)
    )
    def _generate_with_retry(self, prompt: str) -> dict[str, Any]:
        """Generate with automatic retry on transient failures."""
        try:
            return self.llm.generate(prompt)
        except (APIError, ValidationError) as e:
            logger.warning(f"LLM generation failed, retrying: {e}")
            raise
```

## 📂 File Structure
```
src/services/llm/
├── __init__.py
├── base.py                # BaseLLMProvider
├── openai_provider.py
├── anthropic_provider.py
├── mock_provider.py
├── factory.py             # LLMProviderFactory
├── ideation_service.py
├── scripting_service.py
├── cost_tracker.py
└── validation.py

data/fixtures/llm/
├── ideation_space.json
├── script_space_oliver_hannah.json
├── ideation_dinosaurs.json
└── script_dinosaurs_oliver_hannah.json

tests/services/llm/
├── test_providers.py
├── test_ideation_service.py
├── test_scripting_service.py
├── test_cost_tracker.py
└── test_llm_integration.py
```

## ✅ Definition of Done
- [ ] All LLM providers implement BaseLLMProvider interface
- [ ] Ideation service generates valid IdeationOutput with learning objectives
- [ ] Scripting service generates balanced multi-character dialogues
- [ ] Mock provider uses realistic fixtures from data/fixtures/llm/
- [ ] Cost tracking records tokens and costs in episode checkpoints
- [ ] Test coverage ≥ 80% for LLM service modules
- [ ] At least 2 real API integration tests (gated with markers)
- [ ] Documentation includes provider setup instructions and API key requirements
