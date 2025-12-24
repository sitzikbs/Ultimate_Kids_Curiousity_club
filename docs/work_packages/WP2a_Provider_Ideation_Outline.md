# WP2a: Provider Abstraction, Ideation & Outline Generation

**Parent WP**: [WP2: LLM Services & Story Generation](WP2_LLM_Service.md)  
**Status**: ⏳ Not Started  
**Dependencies**: [WP0: Prompt Enhancement](WP0_Prompt_Enhancement.md), [WP1a: Core Models](WP1a_Core_Models.md), [WP1b: Configuration](WP1b_Configuration.md)  
**Estimated Effort**: 2-3 days  
**Owner**: TBD  
**Subsystem:** Content Generation

## 📋 Overview

This sub-work package establishes the **LLM Provider abstraction layer** and implements the first two stages of story generation: **Ideation** (topic → concept) and **Outlining** (concept → story beats). These stages integrate with the prompt enhancer to inject Show Blueprint context and produce reviewable story structures.

**Key Deliverables**:
- Provider abstraction layer (OpenAI, Anthropic, Mock)
- **IdeationService**: Topic → Story concept
- **OutlineService**: Concept → Story beats (reviewable)
- Provider factory and retry logic
- Mock provider with fixture-based responses

**Subsystem Context**:
- **Subsystem:** Content Generation
- **Depends on:** WP0 (Prompt Enhancement), WP1 (Show Blueprint models)
- **Used by:** WP2b (Segment & Script generation), WP6 (Orchestrator)

**This Sub-WP Covers**: Tasks 2.1 (Provider Abstraction), 2.2 (Ideation), and 2.3 (Outline Generation).

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

## 🔧 Technical Specifications

### BaseLLMProvider Interface
```python
from abc import ABC, abstractmethod
from typing import Any

class BaseLLMProvider(ABC):
    """Abstract base class for LLM providers."""
    
    @abstractmethod
    async def generate(
        self,
        prompt: str,
        max_tokens: int = 2000,
        temperature: float = 0.7,
        **kwargs: Any
    ) -> str:
        """Generate text from prompt."""
        pass
    
    @abstractmethod
    def count_tokens(self, text: str) -> int:
        """Count tokens in text."""
        pass
    
    @abstractmethod
    def get_cost(self, input_tokens: int, output_tokens: int) -> float:
        """Calculate cost for token usage."""
        pass
```

### OpenAI Provider Implementation
```python
from openai import AsyncOpenAI
from tenacity import retry, stop_after_attempt, wait_exponential

class OpenAIProvider(BaseLLMProvider):
    def __init__(self, api_key: str, model: str = "gpt-4-turbo-preview"):
        self.client = AsyncOpenAI(api_key=api_key)
        self.model = model
    
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10)
    )
    async def generate(
        self,
        prompt: str,
        max_tokens: int = 2000,
        temperature: float = 0.7,
        **kwargs: Any
    ) -> str:
        response = await self.client.chat.completions.create(
            model=self.model,
            messages=[{"role": "user", "content": prompt}],
            max_tokens=max_tokens,
            temperature=temperature,
            **kwargs
        )
        return response.choices[0].message.content
    
    def count_tokens(self, text: str) -> int:
        # Use tiktoken for accurate counting
        import tiktoken
        encoding = tiktoken.encoding_for_model(self.model)
        return len(encoding.encode(text))
    
    def get_cost(self, input_tokens: int, output_tokens: int) -> float:
        # GPT-4 Turbo pricing
        return (input_tokens * 0.01 / 1000) + (output_tokens * 0.03 / 1000)
```

### IdeationService Usage
```python
from src.services.llm.ideation_service import IdeationService
from src.services.llm.factory import LLMProviderFactory
from src.services.prompt_enhancer import PromptEnhancer

# Initialize
factory = LLMProviderFactory()
provider = factory.create_provider("openai")
enhancer = PromptEnhancer()
ideation = IdeationService(provider, enhancer)

# Generate concept
topic = "How do volcanoes form?"
show_blueprint = load_show_blueprint("olivers_workshop")

concept = await ideation.generate_concept(
    topic=topic,
    show_blueprint=show_blueprint
)

# Output: 2-3 paragraph story concept
"""
Oliver is building a model volcano for the science fair when it suddenly 
erupts with much more force than expected! Curious about why some volcanoes 
are explosive while others flow gently, Oliver and Hannah shrink down to 
explore the earth's crust...

[concept continues with educational tie-ins]
"""
```

### OutlineService Output Format
```yaml
episode_id: "ep042_volcano_adventure"
show_id: "olivers_workshop"
topic: "How do volcanoes form?"
title: "Oliver's Explosive Discovery"
educational_concept: "Plate tectonics, magma formation, volcanic eruptions"
created_at: "2024-12-24T10:30:00Z"

story_beats:
  - beat_number: 1
    title: "The Unexpected Eruption"
    description: "Oliver's model volcano erupts unexpectedly, sparking his curiosity about real volcanoes"
    educational_focus: "Introduction to volcanic activity"
    key_moments:
      - "Model volcano eruption surprises Oliver"
      - "Oliver wonders why some volcanoes explode"
      - "Decision to explore earth's interior"
    duration_minutes: 3
    
  - beat_number: 2
    title: "Journey to the Earth's Mantle"
    description: "Oliver and Hannah shrink down and travel through rock layers to discover magma"
    educational_focus: "Earth's layers and magma formation"
    key_moments:
      - "Shrinking and entering the earth"
      - "Discovering tectonic plates"
      - "Finding pockets of molten magma"
    duration_minutes: 4
    
  # ... more beats
```

## 🧪 Testing Strategy

### Unit Tests
```python
# tests/services/llm/test_ideation_service.py
import pytest
from src.services.llm.ideation_service import IdeationService
from src.services.llm.mock_provider import MockLLMProvider

@pytest.mark.asyncio
async def test_generate_concept_includes_protagonist():
    """Test that generated concept mentions protagonist."""
    provider = MockLLMProvider()
    service = IdeationService(provider, mock_enhancer)
    
    concept = await service.generate_concept(
        topic="space exploration",
        show_blueprint=oliver_blueprint
    )
    
    assert "Oliver" in concept
    assert len(concept.split()) >= 100  # At least 100 words
```

### Integration Tests
```python
# tests/test_ideation_to_outline_flow.py
@pytest.mark.asyncio
async def test_ideation_to_outline_pipeline():
    """Test complete flow from topic to outline."""
    # Generate concept
    concept = await ideation.generate_concept(topic, blueprint)
    
    # Generate outline
    outline = await outline_service.generate_outline(concept, blueprint)
    
    # Validate outline
    assert len(outline.story_beats) >= 3
    assert all(beat.educational_focus for beat in outline.story_beats)
    assert outline.show_id == blueprint.show.show_id
```

## 📦 Dependencies

### Python Packages
```toml
# pyproject.toml additions
openai = "^1.0.0"
anthropic = "^0.18.0"
tiktoken = "^0.6.0"
tenacity = "^8.2.0"
pydantic = "^2.5.0"
```

### Environment Variables
```bash
# .env requirements
OPENAI_API_KEY=sk-...
ANTHROPIC_API_KEY=sk-ant-...
LLM_PROVIDER=openai  # or anthropic, mock
```

## 📋 Definition of Done

- [ ] All provider implementations pass unit tests
- [ ] Mock provider returns fixture-based responses
- [ ] IdeationService generates valid story concepts
- [ ] OutlineService generates valid YAML outlines
- [ ] Retry logic handles API failures gracefully
- [ ] Token counting and cost estimation working
- [ ] Integration test validates ideation → outline flow
- [ ] Documentation includes usage examples
- [ ] Code reviewed and merged to main branch

## 🔗 Related Work Packages

- **Depends on:**
  - [WP0: Prompt Enhancement](WP0_Prompt_Enhancement.md) - Prompt enhancement layer
  - [WP1a: Core Models](WP1a_Core_Models.md) - ShowBlueprint, StoryOutline models
  - [WP1b: Configuration](WP1b_Configuration.md) - Settings and API key management
  
- **Enables:**
  - [WP2b: Segment & Script Generation](WP2b_Segment_Script_Cost.md) - Next generation stages
  - [WP6: Orchestrator](WP6_Orchestrator.md) - Story generation pipeline

- **Parallel Development:**
  - ✅ Can develop in parallel with WP3 (TTS), WP4 (Audio), WP5 (Image) after completing provider abstraction
