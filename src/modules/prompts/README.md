# Prompt Enhancement Module

This module provides a system for enhancing prompts with Show Blueprint context for the Ultimate Kids Curiosity Club content generation pipeline.

## Overview

The Prompt Enhancement Service automatically enriches topic inputs with Show Blueprint context (protagonist values, world rules, covered concepts, supporting characters) before sending to LLM services. This ensures story continuity and consistency across episodes.

## Features

- **Template-based Enhancement**: Uses Jinja2 templates for flexible prompt generation
- **4-Stage Support**: Ideation, Outline, Segment Generation, Script Generation
- **Custom Filters**: Smart text formatting and manipulation
- **Version Tracking**: Templates include version metadata for reproducibility
- **Context Injection**: Automatically includes relevant Show Blueprint information

## Installation

The module is included with the main package:

```bash
pip install -e ".[dev]"
```

## Quick Start

```python
from models import ShowBlueprint, Protagonist, Show, WorldDescription
from modules.prompts import PromptEnhancer

# Create your show blueprint
show_blueprint = ShowBlueprint(
    show=Show(...),
    protagonist=Protagonist(...),
    world=WorldDescription(...),
    # ... other components
)

# Initialize the enhancer
enhancer = PromptEnhancer(version="1.0.0")

# Generate enhanced prompts for each stage
ideation_prompt = enhancer.enhance_ideation_prompt(
    topic="How gravity works",
    show_blueprint=show_blueprint
)

outline_prompt = enhancer.enhance_outline_prompt(
    concept="Oliver discovers gravity...",
    show_blueprint=show_blueprint
)

# ... and so on for segment and script stages
```

## Usage Example

See `examples/prompt_enhancer_demo.py` for a complete working example that demonstrates all 4 enhancement stages.

Run the demo:
```bash
python examples/prompt_enhancer_demo.py
```

## Module Structure

```
src/modules/prompts/
├── __init__.py          # Module exports
├── enhancer.py          # Main PromptEnhancer class
├── filters.py           # Custom Jinja2 filters
├── py.typed             # Type checking marker
└── templates/           # Jinja2 templates
    ├── ideation.j2      # Stage 1: Story concept generation
    ├── outline.j2       # Stage 2: Story outline with beats
    ├── segment.j2       # Stage 3: Detailed segment generation
    ├── script.j2        # Stage 4: Script with dialogue
    └── versions/        # Historical template versions
```

## API Reference

### PromptEnhancer

Main class for prompt enhancement.

#### `__init__(template_dir: Path | None = None, version: str = "1.0.0")`

Initialize the PromptEnhancer.

**Parameters:**
- `template_dir`: Directory containing templates (default: built-in templates)
- `version`: Version string for prompt versioning

#### `enhance_ideation_prompt(topic: str, show_blueprint: ShowBlueprint) -> str`

Enhance ideation prompt with Show Blueprint context.

**Returns:** Enhanced prompt for story concept generation

#### `enhance_outline_prompt(concept: str, show_blueprint: ShowBlueprint) -> str`

Enhance outline prompt with Show Blueprint context.

**Returns:** Enhanced prompt for story outline generation

#### `enhance_segment_prompt(outline: StoryOutline, show_blueprint: ShowBlueprint) -> str`

Enhance segment generation prompt.

**Returns:** Enhanced prompt for detailed segment generation

#### `enhance_script_prompt(segments: list[StorySegment], show_blueprint: ShowBlueprint) -> str`

Enhance script generation prompt.

**Returns:** Enhanced prompt for script with dialogue generation

## Custom Filters

The module provides custom Jinja2 filters for use in templates:

### `format_list(items, separator=", ")`
Format a list as a separated string.

```jinja2
{{ protagonist.values | format_list }}
→ "curiosity, creativity, persistence"

{{ items | format_list(separator=" and ") }}
→ "apple and orange and banana"
```

### `truncate_smart(text, max_length=100, suffix="...")`
Truncate text at word boundaries.

```jinja2
{{ long_text | truncate_smart(max_length=50) }}
→ "This is a long text that will be truncat..."
```

### `capitalize_speaker(speaker)`
Capitalize speaker name for script formatting.

```jinja2
{{ protagonist.name | capitalize_speaker }}
→ "OLIVER"
```

## Template Development

Templates are written in Jinja2 and have access to:

1. **Show Context**: `show.title`, `show.theme`, `show.description`
2. **Protagonist**: `protagonist.name`, `protagonist.values`, `protagonist.catchphrases`
3. **World**: `world.setting`, `world.rules`, `world.atmosphere`, `world.locations`
4. **Characters**: List of supporting characters
5. **Concepts History**: Previously covered educational concepts
6. **Version**: Template version for tracking

Example template snippet:

```jinja2
## Protagonist
Name: {{ protagonist.name }}
Age: {{ protagonist.age }}
{% if protagonist.values %}
Core Values: {{ protagonist.values | format_list }}
{% endif %}

## World Setting
Setting: {{ world.setting }}
{% if world.rules %}
World Rules:
{% for rule in world.rules %}
- {{ rule }}
{% endfor %}
{% endif %}
```

## Testing

Run the test suite:

```bash
# Test filters
pytest tests/unit/test_prompt_filters.py -v

# Test enhancer
pytest tests/unit/test_prompt_enhancer.py -v

# Run all prompt tests
pytest tests/unit/test_prompt_*.py -v
```

## Best Practices

1. **Context Selection**: Each stage includes only relevant Show Blueprint fields to optimize token usage
2. **Version Control**: Always specify a version when initializing the enhancer
3. **Template Updates**: Store old template versions in `templates/versions/` before making breaking changes
4. **Testing**: Test prompts with various Show Blueprints to ensure robustness
5. **Token Optimization**: Keep prompts concise while maintaining necessary context

## Token Optimization

The module is designed to minimize token usage:

- **Ideation**: Includes protagonist values, world rules, covered concepts (~500-800 tokens)
- **Outline**: Adds supporting characters and locations (~600-1000 tokens)
- **Segment**: Includes full story outline and character details (~800-1200 tokens)
- **Script**: Adds voice configuration and segment details (~1000-1500 tokens)

## Future Enhancements

Potential improvements (see WP0 work package):

- [ ] A/B testing support for template variants
- [ ] Template caching for improved performance
- [ ] Additional custom filters as needed
- [ ] Migration utilities for template version updates
- [ ] Validation prompt templates

## Related Documentation

- **WP0 Work Package**: `docs/work_packages/WP0_Prompt_Enhancement.md`
- **Show Blueprint Models**: `src/models/show.py`
- **Story Models**: `src/models/story.py`
- **Episode Models**: `src/models/episode.py`

## License

MIT License - See LICENSE file for details
