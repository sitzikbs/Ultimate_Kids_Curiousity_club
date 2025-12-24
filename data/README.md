# Data Directory Structure

This directory contains all show blueprints and generated episode content.

## Structure

```
data/
├── shows/                    # Show blueprints (one per show)
│   └── {show-id}/
│       ├── show.yaml         # Show metadata
│       ├── protagonist.yaml  # Main character profile (YAML)
│       ├── world.yaml        # World/setting description (YAML)
│       ├── characters/       # Supporting characters (YAML)
│       │   └── *.yaml
│       ├── concepts_covered.json  # Educational tracking (JSON)
│       ├── images/           # Show Blueprint images
│       │   ├── {protagonist}_portrait.png
│       │   ├── {world}_*.png
│       │   └── characters/*.png
│       └── episodes/         # Generated episodes
│           └── {episode-id}/
│               ├── concept.yaml      # Original concept (if authored)
│               ├── outline.json      # Story beats (JSON)
│               ├── segments.json     # Detailed segments (JSON)
│               ├── script.json       # Final script (JSON)
│               ├── audio/            # Audio files
│               │   ├── segment_*.mp3
│               │   └── final.mp3
│               └── state.json        # Pipeline state
└── assets/                   # Shared assets (music, sound effects)
    ├── music/
    └── sfx/
```

## Format Guidelines

### YAML Files (Human-Authored)
Used for creative content that humans edit:
- **`show.yaml`**: Show metadata, theme, narrator config
- **`protagonist.yaml`**: Main character personality, voice, constraints
- **`world.yaml`**: World description, locations, rules
- **`characters/*.yaml`**: Supporting character profiles

**Why YAML?**
- Comments for guidance
- Clean multi-line strings
- Easy to edit for writers/creators
- Version control friendly

### JSON Files (Machine-Generated)
Used for programmatic tracking and LLM outputs:
- **`concepts_covered.json`**: Tracking file (avoid repetition)
- **`outline.json`**, **`segments.json`**, **`script.json`**: LLM outputs
- **`state.json`**: Pipeline state machine

**Why JSON?**
- No ambiguity, strict typing
- Native Python support
- Fast parsing
- API-friendly (WP9 Dashboard)

## Current Shows

### Oliver's Workshop (`olivers_workshop`)
**Theme**: STEM education through invention and problem-solving  
**Target Age**: 6-9 years  
**Protagonist**: Oliver the Inventor (curious, energetic, hands-on learner)  
**World**: Maplewood (suburban town with maker culture)  
**Status**: ✅ Blueprint complete, ready for episode generation

### Hannah's History Adventures (`hannahs_adventures`)
**Status**: ⏳ To be created (port from old repo or create new)

## Show Blueprint Requirements

Each show MUST have:
1. **`show.yaml`** - Show metadata
2. **`protagonist.yaml`** - Main character with:
   - Personality traits
   - Voice profile
   - Safety constraints
   - Image path
3. **`world.yaml`** - Setting with:
   - World description
   - Key locations
   - World rules
   - Image paths
4. **`concepts_covered.json`** - Empty initially, populated by episodes
5. **`episodes/`** directory - For generated content

## Image Paths

All image paths are relative to the repository root:
```yaml
image_path: "data/shows/olivers_workshop/images/oliver_portrait.png"
```

Images can be:
- Pre-existing (manually created/sourced)
- Generated via WP5 (Image Service with Flux/DALL-E)
- Placeholders during development

## Adding a New Show

1. Create directory: `data/shows/{show-id}/`
2. Copy templates from `old_repo/content_creation/series_blueprints/_templates/`
3. Fill in show.yaml, protagonist.yaml, world.yaml
4. Add placeholder image paths
5. Create empty concepts_covered.json
6. Test with ShowBlueprintManager (WP1)

## Migration Notes

This structure is adapted from the old `kidscuriosityclub` repo with improvements:
- Added `image_path` fields to all character/world definitions
- Split supporting characters into separate files
- Added `show.yaml` for show-level metadata
- Changed `concepts/*.yaml` to single `concepts_covered.json` tracker
- Clearer separation of YAML (human) vs JSON (machine)

See `docs/MIGRATION_ASSESSMENT.md` for full migration details.
