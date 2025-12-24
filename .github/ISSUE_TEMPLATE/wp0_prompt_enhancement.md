---
name: WP0 - Prompt Enhancement Service
about: Enrich topic inputs with Show Blueprint context for story generation
title: 'WP0: Prompt Enhancement Service'
labels: ['work-package', 'wp0', 'prompt-engineering', 'foundation']
assignees: []
---

## 📋 Work Package Overview

**Work Package**: WP0 - Prompt Enhancement Service  
**Full Specification**: [WP0_Prompt_Enhancement.md](../docs/work_packages/WP0_Prompt_Enhancement.md)  
**Status**: 🔴 Not Started  
**Estimated Effort**: 1-2 days  
**Dependencies**: None (foundation)  
**Blocks**: WP2 (LLM Service)

## 🎯 Objectives

Create a sophisticated prompt enhancement system using Jinja2 templates that automatically enriches topic inputs with Show Blueprint context (protagonist, world, characters, concepts covered) for consistent story generation across 4 stages: Ideation, Outline, Segment, Script.

## 📚 Key References

- **Primary Spec**: [WP0_Prompt_Enhancement.md](../docs/work_packages/WP0_Prompt_Enhancement.md)
- **Architecture**: [PLAN.md](../docs/PLAN.md) - Content Generation Subsystem
- **Data Models**: [INTERFACES.md](../docs/work_packages/INTERFACES.md) - ShowBlueprint, Protagonist, WorldDescription
- **Progress Tracking**: [PROGRESS.md](../docs/PROGRESS.md)
- **ADRs**: 
  - [ADR 003: Prompt Enhancement Layer](../docs/decisions/003-prompt-enhancement-layer.md)
  - [ADR 005: YAML/JSON Hybrid](../docs/decisions/005-yaml-json-hybrid.md)

## ✅ Key Deliverables

- [ ] **Task 0.1**: Template System
  - Jinja2 environment with custom filters
  - Template directory structure (`src/prompts/templates/`)
  - Template loading and caching
  
- [ ] **Task 0.2**: Show Blueprint Context Extraction
  - `extract_protagonist_context()`: personality, voice, constraints
  - `extract_world_context()`: setting, rules, atmosphere
  - `extract_concepts_context()`: covered topics, avoid repetition
  
- [ ] **Task 0.3**: Enhancement Methods (4 Stages)
  - `enhance_ideation_prompt()`: topic → story concept
  - `enhance_outline_prompt()`: concept → story beats
  - `enhance_segment_prompt()`: outline → detailed segments
  - `enhance_script_prompt()`: segments → narration + dialogue
  
- [ ] **Task 0.4**: Prompt Templates (Jinja2)
  - `ideation.j2`: Story concept generation
  - `outline.j2`: Story beat structure
  - `segment.j2`: Detailed segment expansion
  - `script.j2`: Narration + character dialogue
  
- [ ] **Task 0.5**: Versioning & Metadata
  - Prompt version tracking
  - A/B testing capability
  - Template changelog

## 🔄 Feedback Checkpoints

### Midway Checkpoint (After Task 0.2)
**Please request feedback with:**
- [ ] Template system working (loading, caching)
- [ ] Show Blueprint context extraction implemented
- [ ] Sample extraction from Oliver's Workshop blueprint
- [ ] Questions:
  - Is the context extraction capturing the right details?
  - Are the custom Jinja2 filters useful?
  - Any missing context from Show Blueprint?

### Final Checkpoint (After Task 0.5)
**Please request feedback with:**
- [ ] All 4 enhancement methods working
- [ ] All 4 Jinja2 templates created
- [ ] Versioning system implemented
- [ ] End-to-end demo: topic → enhanced prompts for all 4 stages
- [ ] Questions:
  - Are the prompts rich enough for LLM generation?
  - Is the protagonist personality coming through?
  - Any improvements to template structure?

## 📝 Implementation Notes

### Show Blueprint Structure (Reference)
```python
# data/shows/olivers_workshop/
protagonist.yaml  # Oliver's personality, voice, constraints
world.yaml        # Maplewood setting, locations, rules
concepts_covered.json  # Topics already covered
```

### Template Example Pattern
```jinja2
You are helping create a STEM podcast episode for {{ show.title }}.

**Protagonist**: {{ protagonist.name }} ({{ protagonist.age }} years old)
{{ protagonist.personality_traits | join('\n') }}

**World**: {{ world.world_name }}
{{ world.description }}

**Topic**: {{ topic }}

**Previously Covered**: {% for concept in concepts_covered %}{{ concept.concept }}{% if not loop.last %}, {% endif %}{% endfor %}

Generate a {{ stage_name }} that...
```

### Testing Strategy
- Unit tests with mock Show Blueprint data
- Fixture-based template rendering tests
- Verify all 4 stages produce distinct prompts
- Test with Oliver's Workshop real data

## 🚀 Getting Started

1. Review [WP0_Prompt_Enhancement.md](../docs/work_packages/WP0_Prompt_Enhancement.md) fully
2. Study [ADR 003: Prompt Enhancement Layer](../docs/decisions/003-prompt-enhancement-layer.md)
3. Examine `data/shows/olivers_workshop/` Show Blueprint structure
4. Set up Jinja2 environment and template directory
5. Start with Task 0.1 (Template System)

## ⚠️ Important Notes

- **Do NOT import old prompts**: Old repo prompts are empty/unpolished (see [MIGRATION_ASSESSMENT.md](../docs/MIGRATION_ASSESSMENT.md))
- **YAML format**: Show Blueprints use YAML (human-friendly), not JSON
- **4 stages**: Ensure templates are distinct for Ideation, Outline, Segment, Script
- **Image paths**: Templates should include protagonist/world image paths for context

## 📊 Success Criteria

- [ ] All 4 enhancement methods working
- [ ] Templates produce rich, context-aware prompts
- [ ] Show Blueprint context properly injected
- [ ] Protagonist personality evident in prompts
- [ ] ConceptsHistory prevents repetition
- [ ] Versioning system functional
- [ ] Tests passing with >80% coverage
- [ ] Documentation complete

---

**When complete**, this WP enables WP2 (LLM Service) to generate consistent, character-driven stories.
