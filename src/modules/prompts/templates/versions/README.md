# Template Versions

This directory stores historical versions of prompt templates for version control and reproducibility.

## Purpose

- Track template changes over time
- Enable rollback to previous versions if needed
- Document breaking changes between versions
- Ensure episodes can reference the exact template version used

## Structure

```
versions/
├── 2024-12-26/
│   ├── ideation.j2
│   ├── outline.j2
│   ├── segment.j2
│   ├── script.j2
│   └── CHANGELOG.md
└── README.md (this file)
```

## Versioning Convention

Store template versions in date-based directories: `YYYY-MM-DD/`

When making significant template changes:

1. Copy current templates to a new date directory
2. Document changes in a CHANGELOG.md file
3. Update the version parameter in PromptEnhancer
4. Test thoroughly before deploying

## Version 1.0.0 (Initial Release)

**Date:** 2024-12-26  
**Location:** `src/modules/prompts/templates/` (main templates)

**Features:**
- Ideation template for story concept generation
- Outline template for story beat structuring
- Segment template for detailed scene generation
- Script template for dialogue and narration

**Template Sections:**
- Show context (title, theme, description)
- Protagonist details (name, age, values, catchphrases)
- World setting (setting, rules, atmosphere, locations)
- Supporting characters
- Previously covered concepts
- Custom Jinja2 filters (format_list, truncate_smart, capitalize_speaker)

## Best Practices

1. **Document Changes**: Always include a CHANGELOG.md with version snapshots
2. **Breaking Changes**: Clearly mark breaking changes that affect LLM output format
3. **Testing**: Test new templates with various Show Blueprints before deployment
4. **Naming**: Keep filenames consistent across versions
5. **Migration**: Provide migration guides for significant changes

## Example CHANGELOG.md

```markdown
# Version 1.1.0 - 2024-12-30

## Changes
- Added "educational objective" section to outline template
- Enhanced segment template to include character emotions
- Fixed formatting issue in script template

## Breaking Changes
None

## Migration Notes
No migration needed - templates are backward compatible
```

## Future Versions

As the system evolves, store template versions here to maintain a complete history.
