# WP0: Prompt Enhancement Service

**Status:** 🔴 Not Started  
**Owner:** Unassigned  
**GitHub Issue:** TBD  
**Subsystem:** Content Generation

## Overview

### Purpose
Build a prompt enhancement system that automatically enriches topic inputs with **Show Blueprint context** (protagonist values, world rules, covered concepts, supporting characters) before sending to LLM services. This ensures story continuity and consistency across episodes.

### System Context
- **Subsystem:** Content Generation
- **Depends on:** WP1 (Show Blueprint models)
- **Used by:** WP2 (LLM Services - all 4 stages)
- **Parallel Development:** ✅ Can develop in parallel with WP3, WP4, WP5 after WP1 complete

### Goals
- Transform topics into rich prompts with Show Blueprint context
- Inject protagonist personality, values, and world rules automatically
- Include concepts already covered to avoid repetition
- Support 4 generation stages: Ideation, Outline, Segment, Script
- Ensure consistent prompt formatting across all LLM calls
- Support prompt versioning for reproducibility

### Success Criteria
- [x] Template system loads and renders Jinja2 templates for all 4 stages
- [x] Show Blueprint context injection works (protagonist, world, characters, concepts)
- [x] Enhanced prompts include all required sections
- [x] Prompt versioning tracks template changes
- [x] Unit tests cover all enhancement methods
- [x] Integration with WP2 (LLM Services) validated

---

## High-Level Tasks

### Task 1: Template System Setup
**Estimated Effort:** 4 hours  
**Dependencies:** None

#### Subtasks
- [ ] Create `src/modules/prompts/` directory structure
- [ ] Set up Jinja2 environment with custom filters
- [ ] Create template loader with versioning
- [ ] Implement template caching mechanism

**Acceptance Criteria:**
- Templates load from `src/modules/prompts/templates/`
- Version field tracks template changes
- Templates cached after first load
- Custom filters available (e.g., `format_list`, `truncate`)

---

### Task 2: Ideation Stage Prompt Template
**Estimated Effort:** 4 hours  
**Dependencies:** Task 1

#### Subtasks
- [ ] Design ideation template structure
- [ ] Create `templates/ideation.j2` with sections:
  - Show context (theme, protagonist, world)
  - Concepts already covered (from concepts_covered.json)
  - Educational guidelines for the topic
  - Output format (story concept, 2-3 paragraphs)
- [ ] Add Show Blueprint context injection
- [ ] Test with various shows and topics

**Acceptance Criteria:**
- Template injects protagonist values and personality
- World rules and setting included
- Covered concepts listed to avoid repetition
- Output format clearly specified
- Works with different shows (Oliver, Hannah)

---

### Task 3: Outline Stage Prompt Template
**Estimated Effort:** 4 hours  
**Dependencies:** Task 1

#### Subtasks
- [ ] Create `templates/outline.j2` with sections:
  - Story concept from ideation
  - Show Blueprint context (protagonist, world, characters)
  - Story structure guidelines (3-5 beats)
  - Output format (YAML with story beats)
- [ ] Add supporting character suggestions
- [ ] Include world locations if applicable

**Acceptance Criteria:**
- Template transforms concept into structured outline
- Story beats have clear educational tie-ins
- Supporting characters referenced appropriately
- Output format: YAML with beat structure

---

### Task 4: Segment Generation Stage Prompt Template
**Estimated Effort:** 4 hours  
**Dependencies:** Task 1

#### Subtasks
- [ ] Create `templates/segment.j2` with sections:
  - Approved story outline
  - Show Blueprint context
  - Detailed scene description guidelines
  - Output format (JSON segments with "what happens")
- [ ] Add character action guidelines
- [ ] Include world-building consistency checks

**Acceptance Criteria:**
- Template expands each beat into detailed segments
- Characters behave consistently with personality
- World rules maintained
- Output: Detailed segments (what happens, not dialogue yet)

---

### Task 5: Script Generation Stage Prompt Template
**Estimated Effort:** 4 hours  
**Dependencies:** Task 1

#### Subtasks
- [ ] Create `templates/script.j2` with sections:
  - Story segments (what happens)
  - Show Blueprint context
  - Narration + dialogue guidelines
  - Character speaking styles
  - Output format (JSON scripts with speaker tags)
- [ ] Add voice/tone guidelines for narrator
- [ ] Include protagonist catchphrase integration

**Acceptance Criteria:**
- Template converts segments into narration + dialogue
- Narrator voice distinct from character voices
- Character catchphrases used appropriately
- Output: Scripts with speaker tags ready for TTS

**Example Template Structure:**
```jinja2
You are helping create an educational podcast episode for kids.

## Character Context
Character Name: {{ character.name }}
Personality Traits: {{ character.personality.traits | join(", ") }}
Speaking Style: {{ character.speaking_style }}

## Episode Idea
{{ user_idea }}

## Your Task
Create an episode outline with:
1. Episode Title (engaging, kid-friendly)
2. Abstract (2-3 sentences)
3. Chapter Breakdown (4-6 chapters)

## Educational Guidelines
- Age appropriate for {{ character.target_age_range }}
- Scientifically accurate
- Encouraging and positive
- Promotes curiosity

## Output Format
```json
{
  "title": "...",
  "abstract": "...",
  "chapters": [
    {"number": 1, "title": "...", "summary": "..."}
  ]
}
```
```

---

### Task 3: Scripting Prompt Templates
**Estimated Effort:** 6 hours  
**Dependencies:** Task 1

#### Subtasks
- [ ] Design scripting template structure
- [ ] Create `templates/scripting.j2` with sections:
  - Character speaking style details
  - Chapter context
  - Dialogue format requirements
  - Audio cue instructions ([SFX:], [MUSIC:])
- [ ] Add side character support
- [ ] Add timing estimate requirements
- [ ] Test script generation quality

**Acceptance Criteria:**
- Template produces natural dialogue
- Speaker tags clearly defined (CHARACTER vs NARRATOR)
- Audio cues properly formatted
- Timing estimates included
- Side characters integrated naturally

**Example Template Structure:**
```jinja2
## Character Voice
Name: {{ character.name }}
Speaking Style: {{ character.speaking_style }}
Catchphrases: {{ character.personality.catchphrases | join(", ") }}

{% if character.side_characters %}
## Side Characters
{% for side_char in character.side_characters %}
- {{ side_char.name }}: {{ side_char.personality }}
{% endfor %}
{% endif %}

## Chapter to Script
Chapter: {{ chapter.title }}
Summary: {{ chapter.summary }}

## Instructions
Write a detailed script with:
- Natural dialogue in character's voice
- Narrator for scene descriptions
- Sound effects as [SFX: description]
- Music cues as [MUSIC: mood]
- Each line with speaker tag

## Format
NARRATOR: [Scene description]
{{ character.name | upper }}: [Dialogue with character voice]
[SFX: sound effect]
```

---

### Task 4: Validation Prompt Templates
**Estimated Effort:** 4 hours  
**Dependencies:** Task 1

#### Subtasks
- [ ] Create `templates/validation.j2`
- [ ] Add age-appropriateness check criteria
- [ ] Add educational value validation
- [ ] Add character consistency check
- [ ] Test validation accuracy

**Acceptance Criteria:**
- Template checks age-appropriateness
- Educational value assessed
- Character voice consistency verified
- Clear pass/fail criteria
- Specific feedback provided

---

### Task 5: Prompt Enhancer Implementation
**Estimated Effort:** 6 hours  
**Dependencies:** Tasks 2, 3, 4

#### Subtasks
- [ ] Create `src/modules/prompts/enhancer.py`
- [ ] Implement `PromptEnhancer` class
- [ ] Add `enhance_ideation_prompt()` method
- [ ] Add `enhance_scripting_prompt()` method
- [ ] Add `enhance_validation_prompt()` method
- [ ] Implement character context extraction
- [ ] Add prompt versioning metadata

**Acceptance Criteria:**
- All enhancement methods work
- Character context properly extracted
- Templates rendered correctly
- Version metadata attached
- Error handling for missing fields

**Interface (see INTERFACES.md):**
```python
class PromptEnhancer:
    """Enhance prompts with Show Blueprint context."""
    
    def __init__(self, template_dir: Path, version: str = "1.0.0"):
        self.template_dir = template_dir
        self.version = version
        self.env = self._setup_jinja_env()
    
    def enhance_ideation_prompt(
        self,
        topic: str,
        show_blueprint: ShowBlueprint
    ) -> str:
        """Enhance ideation prompt with Show Blueprint context."""
        template = self.env.get_template("ideation.j2")
        return template.render(
            topic=topic,
            show=show_blueprint.show,
            protagonist=show_blueprint.protagonist,
            world=show_blueprint.world,
            covered_concepts=show_blueprint.concepts_history.concepts,
            version=self.version
        )
    
    def enhance_outline_prompt(
        self,
        concept: str,
        show_blueprint: ShowBlueprint
    ) -> str:
        """Enhance outline prompt with Show Blueprint context."""
        template = self.env.get_template("outline.j2")
        return template.render(
            concept=concept,
            show=show_blueprint.show,
            protagonist=show_blueprint.protagonist,
            world=show_blueprint.world,
            characters=show_blueprint.characters,
            version=self.version
        )
    
    def enhance_segment_prompt(
        self,
        outline: StoryOutline,
        show_blueprint: ShowBlueprint
    ) -> str:
        """Enhance segment generation prompt."""
        template = self.env.get_template("segment.j2")
        return template.render(
            outline=outline,
            protagonist=show_blueprint.protagonist,
            world=show_blueprint.world,
            characters=show_blueprint.characters,
            version=self.version
        )
    
    def enhance_script_prompt(
        self,
        segments: list[StorySegment],
        show_blueprint: ShowBlueprint
    ) -> str:
        """Enhance script generation prompt."""
        template = self.env.get_template("script.j2")
        return template.render(
            segments=segments,
            protagonist=show_blueprint.protagonist,
            world=show_blueprint.world,
            characters=show_blueprint.characters,
            narrator_voice=show_blueprint.show.narrator_voice_config,
            version=self.version
        )
```

---

### Task 6: Show Blueprint Context Extraction
**Estimated Effort:** 4 hours  
**Dependencies:** Task 5

#### Subtasks
- [ ] Implement Show Blueprint field selection logic
- [ ] Create curated context for ideation (protagonist values, covered concepts)
- [ ] Create curated context for outline (world, characters)
- [ ] Create curated context for segments (detailed world, character personalities)
- [ ] Create curated context for scripts (speaking styles, catchphrases)
- [ ] Add field validation before injection
- [ ] Handle missing optional fields gracefully

**Acceptance Criteria:**
- Only relevant fields included per stage
- Token usage optimized (not entire Show Blueprint)
- Missing fields don't break prompts
- Clear error messages for required fields
- Covered concepts properly formatted to avoid repetition

---

### Task 7: Prompt Versioning
**Estimated Effort:** 3 hours  
**Dependencies:** Task 5

#### Subtasks
- [ ] Add version field to all templates
- [ ] Store template snapshots in `templates/versions/`
- [ ] Implement version comparison
- [ ] Add migration warnings for breaking changes

**Acceptance Criteria:**
- Version tracked in enhanced prompt metadata
- Old versions accessible from `versions/` directory
- Breaking changes documented
- Episodes can reference prompt version used

---

### Task 8: Custom Jinja Filters
**Estimated Effort:** 3 hours  
**Dependencies:** Task 1

#### Subtasks
- [ ] Create `format_list` filter (comma-separated)
- [ ] Create `truncate_smart` filter (word-aware truncation)
- [ ] Create `capitalize_speaker` filter
- [ ] Add filter documentation

**Acceptance Criteria:**
- All filters work in templates
- Filters handle edge cases (empty lists, None)
- Filter usage documented in templates

---

### Task 9: A/B Testing Support
**Estimated Effort:** 4 hours  
**Dependencies:** Task 5

#### Subtasks
- [ ] Add template variant system (ideation_v1.j2, ideation_v2.j2)
- [ ] Implement variant selection logic
- [ ] Add metadata tracking for which variant used
- [ ] Create comparison utilities

**Acceptance Criteria:**
- Multiple template variants supported
- Variant selection configurable
- Metadata tracks which variant used
- Easy to compare results across variants

---

### Task 10: Integration Testing
**Estimated Effort:** 4 hours  
**Dependencies:** All above tasks

#### Subtasks
- [ ] Test with mock Character objects
- [ ] Verify enhanced prompts have all sections
- [ ] Test with missing optional character fields
- [ ] Validate output format compliance
- [ ] Test version tracking

**Acceptance Criteria:**
- All enhancement methods tested
- Edge cases handled (missing fields, empty strings)
- Output format validated
- Version metadata correct

---

### Task 11: Documentation
**Estimated Effort:** 2 hours  
**Dependencies:** All above tasks

#### Subtasks
- [ ] Document template structure and conventions
- [ ] Add template authoring guide
- [ ] Document custom filters
- [ ] Add prompt engineering best practices
- [ ] Create examples for each enhancement type

**Acceptance Criteria:**
- Template authoring guide complete
- All filters documented with examples
- Best practices documented
- Examples clear and runnable

---

## Technical Specifications

### File Structure
```
src/
├── modules/
│   └── prompts/
│       ├── __init__.py
│       ├── enhancer.py
│       ├── filters.py
│       ├── templates/
│       │   ├── ideation.j2
│       │   ├── scripting.j2
│       │   ├── validation.j2
│       │   └── versions/
│       │       ├── 2025-12-01/
│       │       │   ├── ideation.j2
│       │       │   └── scripting.j2
│       │       └── README.md
│       └── tests/
│           ├── test_enhancer.py
│           ├── test_filters.py
│           └── fixtures/
│               └── test_character.json
```

### Dependencies
```python
# In pyproject.toml
dependencies = [
    "jinja2>=3.1.0",
    "pydantic>=2.5.0",
]
```

### Configuration
```python
# In src/config.py
class Settings(BaseSettings):
    prompt_template_dir: Path = Path("src/modules/prompts/templates")
    prompt_version: str = "1.0.0"
    prompt_cache_enabled: bool = True
```

---

## Testing Requirements

### Unit Tests
```python
# tests/test_wp0_enhancer.py

class TestPromptEnhancer:
    def test_enhance_ideation_basic(self, test_character):
        """Test ideation prompt enhancement."""
        enhancer = PromptEnhancer()
        result = enhancer.enhance_ideation_prompt(
            user_idea="Learn about gravity",
            character=test_character
        )
        
        assert "gravity" in result.lower()
        assert test_character.name in result
        assert test_character.speaking_style in result
    
    def test_enhance_with_missing_optional_fields(self, minimal_character):
        """Test enhancement handles missing optional fields."""
        enhancer = PromptEnhancer()
        result = enhancer.enhance_ideation_prompt(
            user_idea="Test idea",
            character=minimal_character
        )
        
        assert result  # Should not fail
        assert "Test idea" in result
```

### Integration Tests
```python
def test_full_prompt_pipeline(test_character):
    """Test prompt enhancement -> LLM -> validation."""
    enhancer = PromptEnhancer()
    llm = MockLLMProvider()
    
    # Enhance
    enhanced = enhancer.enhance_ideation_prompt(
        user_idea="Oliver learns physics",
        character=test_character
    )
    
    # Generate (mock)
    result = llm.generate(enhanced)
    
    # Validate format
    data = json.loads(result)
    assert "title" in data
    assert "chapters" in data
```

---

## Implementation Notes

### Prompt Engineering Best Practices
1. **Be specific:** Clear instructions produce better results
2. **Use examples:** Show desired output format
3. **Structure prompts:** Use headers and sections
4. **Limit scope:** Don't ask for too much in one prompt
5. **Version control:** Track prompt changes over time

### Token Optimization
- Include only relevant character fields per stage
- Ideation needs: personality, traits (not full appearance)
- Scripting needs: speaking_style, side_characters (not world_description)
- Estimate tokens: ~4 chars = 1 token

### Template Maintenance
- Review templates after LLM provider updates
- A/B test significant changes
- Keep versions of working templates
- Document why changes were made

### Gotchas
- Jinja2 auto-escaping can affect JSON output (use `| safe` filter)
- Missing character fields must have defaults in templates
- Long prompts = higher costs (optimize aggressively)
- Different LLMs may need different prompt styles

---

## Cost Estimates

**Development:** No API costs (template work only)

**Testing:** Minimal
- Testing enhanced prompts: FREE (no LLM calls)
- Integration with mock LLM: FREE
- Integration with real LLM: ~$0.10-0.50 (few test calls)

---

## References

- **Jinja2 Documentation:** https://jinja.palletsprojects.com/
- **ADR 003:** Prompt Enhancement Layer
- **WP2:** LLM Service (consumer of enhanced prompts)
- **INTERFACES.md:** PromptEnhancer interface specification

---

**Ready to start?** Pick Task 1 and begin implementing the template system!
