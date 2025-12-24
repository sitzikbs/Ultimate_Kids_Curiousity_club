# ADR 003: Prompt Enhancement Layer

**Status**: ✅ Accepted  
**Date**: 2024-01-15  
**Deciders**: Team  
**Tags**: architecture, prompts, optimization

## Context

The podcast generator uses LLMs for content generation (ideation and scripting). Effective prompts require:
- **Character-specific context**: Personality, speaking style, vocabulary level
- **Stage-specific instructions**: Different requirements for ideation vs scripting
- **Template management**: Reusable prompt structures
- **Version control**: Track prompt changes and A/B test variations
- **Token efficiency**: Inject only relevant context to minimize costs

Without proper prompt management:
1. **Prompts scattered across code**: Hard to maintain and iterate
2. **Duplicate context**: Repeating character descriptions wastes tokens ($0.01-0.06/1K tokens)
3. **No versioning**: Can't track what prompts work best
4. **Hard to customize**: Changing prompts requires code changes
5. **Poor testability**: Difficult to unit test prompt generation logic

We need a system that:
- Centralizes prompt templates
- Injects context dynamically based on stage and characters
- Supports prompt versioning and A/B testing
- Optimizes token usage
- Enables rapid iteration

## Decision

We will implement a **Prompt Enhancement Layer** with the following architecture:

### 1. Jinja2 Template System
Use Jinja2 for templating with clear separation:

```
data/prompts/
├── ideation/
│   ├── system.jinja2        # System instructions for ideation
│   └── user.jinja2           # User prompt template
├── scripting/
│   ├── system.jinja2        # System instructions for scripting
│   └── user.jinja2           # User prompt template
└── shared/
    ├── character.jinja2     # Character context template
    └── filters.jinja2       # Custom Jinja2 filters
```

### 2. PromptEnhancer Service
Central service for prompt enhancement:

```python
class PromptEnhancer:
    def enhance_prompt(
        self,
        stage: str,
        user_input: str,
        characters: list[Character],
        context: dict[str, Any] | None = None
    ) -> str:
        """Enhance user input with character context and stage instructions."""
        
        # Load stage-specific template
        template = self.templates[stage]["user"]
        
        # Extract relevant character context
        char_context = self._extract_character_context(stage, characters)
        
        # Render template
        return template.render(
            user_input=user_input,
            characters=char_context,
            **context or {}
        )
```

### 3. Context Extraction Strategy
Different stages need different character information:

| Stage | Character Context | Rationale |
|-------|------------------|-----------|
| **Ideation** | `personality`, `age`, `vocabulary_level` | Shape topic refinement |
| **Scripting** | `speaking_style`, `personality`, `vocabulary_level` | Generate authentic dialogue |
| **Validation** | `age`, `vocabulary_level` | Check age-appropriateness |

This reduces token usage by 30-50% vs. full character JSON.

### 4. Prompt Versioning
Version prompts using git and optional version tags:

```python
# Load specific version
enhancer = PromptEnhancer(prompt_version="v2.0")

# Compare versions (A/B testing)
results_v1 = enhancer_v1.enhance_prompt(...)
results_v2 = enhancer_v2.enhance_prompt(...)
```

### 5. Template Structure
**Ideation System Prompt**:
```jinja2
You are an expert educational content creator for kids aged 5-12.

Your task is to refine user topics into engaging podcast episode outlines.

Characters in this episode:
{% for char in characters %}
- {{ char.name }} (age {{ char.age }}): {{ char.personality }}
  Vocabulary: {{ char.vocabulary_level }}
{% endfor %}

Requirements:
- Create 3-5 clear learning objectives
- Generate 5-10 discussion points
- Ensure age-appropriate content (ages 5-12)
- Target duration: {{ duration }} minutes

Output format: JSON with keys "refined_topic", "learning_objectives", "key_points"
```

**Scripting User Prompt**:
```jinja2
Generate a {{ duration }}-minute podcast dialogue between:
{% for char in characters %}
- {{ char.name }}: {{ char.speaking_style }}
{% endfor %}

Topic: {{ refined_topic }}

Learning objectives:
{% for obj in learning_objectives %}
- {{ obj }}
{% endfor %}

Key points to cover:
{% for point in key_points %}
- {{ point }}
{% endfor %}

Requirements:
- Natural conversation flow
- Balanced character participation
- Age-appropriate vocabulary ({{ characters[0].vocabulary_level }})
- Include greetings and farewells
- Estimate 150 words per minute

Output format: JSON array of dialogue segments with keys "character_id", "text", "emotion"
```

## Consequences

### Positive
1. **Centralized Management**: All prompts in one location, easy to update
2. **Token Efficiency**: 30-50% reduction by injecting only relevant context
3. **Version Control**: Track prompt evolution, rollback if needed
4. **A/B Testing**: Easy to compare prompt variations
5. **Reusability**: Shared templates reduce duplication
6. **Testability**: Unit test prompt generation independently
7. **Non-Developer Friendly**: Copywriters can edit templates without touching code

### Negative
1. **Indirection**: Extra layer between service and LLM
2. **Template Complexity**: Jinja2 syntax learning curve
3. **Debugging**: Template rendering errors can be cryptic

### Mitigations
- **For Indirection**: Performance impact negligible (<1ms), clarity benefit outweighs
- **For Complexity**: Provide template examples and documentation
- **For Debugging**: Add verbose mode with rendered prompt logging

## Alternatives Considered

### Alternative 1: Inline Prompts
**Rejected because**:
- Prompts scattered across codebase
- Hard to iterate and A/B test
- No version control
- Difficult for non-developers to modify

### Alternative 2: External Prompt Management Service (PromptLayer, LangSmith)
**Rejected because**:
- Adds external dependency
- Requires API calls (cost, latency)
- Over-engineered for current needs
- Can migrate later if needed

### Alternative 3: F-strings or String Templates
**Rejected because**:
- Less powerful than Jinja2 (no loops, conditionals)
- Harder to maintain complex templates
- No built-in escaping or filters

### Alternative 4: LangChain Prompt Templates
**Rejected because**:
- Adds heavy dependency (entire LangChain framework)
- Overkill for our simple templating needs
- Jinja2 is more familiar and flexible

## Implementation Guidelines

### Adding a New Prompt Template
1. Create template file:
   ```bash
   data/prompts/new_stage/user.jinja2
   ```

2. Define template variables:
   ```jinja2
   Generate content for {{ topic }} with characters:
   {% for char in characters %}
   - {{ char.name }}
   {% endfor %}
   ```

3. Add enhancement method:
   ```python
   def enhance_new_stage_prompt(self, topic: str, characters: list[Character]) -> str:
       return self.enhance_prompt(
           stage="new_stage",
           user_input=topic,
           characters=characters
       )
   ```

4. Test:
   ```python
   def test_new_stage_prompt():
       enhancer = PromptEnhancer()
       prompt = enhancer.enhance_new_stage_prompt("test topic", [oliver, hannah])
       assert "test topic" in prompt
       assert "Oliver" in prompt
   ```

### Prompt Optimization Tips
1. **Token Budget**: Aim for <500 tokens in system prompt, <300 in user prompt
2. **Specificity**: Precise instructions reduce LLM confusion
3. **Examples**: Include 1-2 examples in system prompt for complex formats
4. **JSON Mode**: Use `response_format={"type": "json_object"}` for structured output
5. **Iteration**: Log prompts during development, refine based on LLM responses

### A/B Testing Workflow
```python
# Define two prompt versions
enhancer_v1 = PromptEnhancer(prompt_dir="data/prompts/v1")
enhancer_v2 = PromptEnhancer(prompt_dir="data/prompts/v2")

# Run experiment
for topic in test_topics:
    result_v1 = generate_with_prompt(enhancer_v1, topic)
    result_v2 = generate_with_prompt(enhancer_v2, topic)
    
    # Compare quality metrics
    score_v1 = evaluate_quality(result_v1)
    score_v2 = evaluate_quality(result_v2)
```

## Cost Impact

**Before Prompt Enhancement**:
- Full character JSON: ~200 tokens per character
- 2 characters × 200 tokens = 400 tokens
- 2 stages (ideation + scripting) × 400 tokens = 800 tokens
- Cost: 800 tokens × $0.03/1K = **$0.024 per episode**

**After Prompt Enhancement**:
- Selective context: ~80 tokens per character
- 2 characters × 80 tokens = 160 tokens
- 2 stages × 160 tokens = 320 tokens
- Cost: 320 tokens × $0.03/1K = **$0.0096 per episode**

**Savings**: 60% reduction in context token costs (400 tokens saved per episode)

At scale (1000 episodes): **$14.40 saved**

## References

- [Jinja2 Documentation](https://jinja.palletsprojects.com/)
- [OpenAI Prompt Engineering](https://platform.openai.com/docs/guides/prompt-engineering)
- [Anthropic Prompt Library](https://docs.anthropic.com/claude/prompt-library)
- [A/B Testing for LLM Prompts](https://www.promptingguide.ai/)
