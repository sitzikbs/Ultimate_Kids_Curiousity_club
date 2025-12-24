# ADR 004: Character JSON Schema Design

**Status**: ✅ Accepted  
**Date**: 2024-01-15  
**Deciders**: Team  
**Tags**: data-model, characters, extensibility

## Context

Characters are central to the podcast system, appearing in:
- **LLM prompts**: Personality and speaking style shape content generation
- **TTS synthesis**: Voice configuration determines audio output
- **Image generation**: Reference images for visual content
- **UI/CLI**: Display character information to users

Character data must:
1. **Support content generation**: Provide context for ideation and scripting
2. **Configure TTS**: Store provider-specific voice settings
3. **Be human-editable**: Non-developers should create/modify characters
4. **Be version-controlled**: Track changes in git
5. **Support validation**: Ensure data integrity
6. **Enable extensibility**: Add new fields without breaking existing code

We need a schema that balances:
- **Simplicity**: Easy for non-developers to edit
- **Completeness**: Captures all necessary information
- **Flexibility**: Supports multiple TTS providers
- **Validation**: Prevents invalid configurations

## Decision

We will use **JSON files with Pydantic validation** for character storage:

### 1. Character JSON Schema

```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "id": "oliver",
  "name": "Oliver the Inventor",
  "age": 10,
  "personality": "Curious, energetic inventor who loves building things. Always asking 'how does it work?' and explaining mechanisms with toy analogies.",
  "speaking_style": "Uses simple technical words, gets excited about mechanisms, often uses analogies with toys or everyday objects. Frequently says 'Wow!' and 'That's so cool!'",
  "vocabulary_level": "INTERMEDIATE",
  "voice_config": {
    "provider": "elevenlabs",
    "voice_id": "21m00Tcm4TlvDq8ikWAM",
    "stability": 0.5,
    "similarity_boost": 0.75,
    "style": 0.3,
    "emotion_mappings": {
      "excited": {
        "stability": 0.3,
        "style": 0.8
      },
      "calm": {
        "stability": 0.7,
        "style": 0.2
      },
      "curious": {
        "stability": 0.5,
        "style": 0.5
      }
    }
  },
  "reference_image_path": "data/characters/images/oliver.png",
  "created_at": "2024-01-15T10:00:00Z",
  "schema_version": "1.0"
}
```

### 2. Pydantic Models

```python
from pydantic import BaseModel, Field
from enum import Enum
from pathlib import Path

class VocabularyLevel(str, Enum):
    SIMPLE = "SIMPLE"         # Ages 5-7
    INTERMEDIATE = "INTERMEDIATE"  # Ages 8-10
    ADVANCED = "ADVANCED"     # Ages 11-12

class VoiceConfig(BaseModel):
    """TTS voice configuration."""
    provider: str = Field(description="TTS provider (elevenlabs, google, openai)")
    voice_id: str = Field(description="Provider-specific voice identifier")
    stability: float = Field(default=0.5, ge=0.0, le=1.0)
    similarity_boost: float = Field(default=0.75, ge=0.0, le=1.0)
    style: float = Field(default=0.0, ge=0.0, le=1.0)
    emotion_mappings: dict[str, dict[str, float]] = Field(default_factory=dict)

class Character(BaseModel):
    """Character definition for podcast."""
    id: str = Field(description="Unique character identifier (slug)")
    name: str = Field(description="Character display name")
    age: int = Field(ge=5, le=12, description="Character age (5-12)")
    personality: str = Field(description="Character personality and traits")
    speaking_style: str = Field(description="How the character speaks")
    vocabulary_level: VocabularyLevel
    voice_config: VoiceConfig
    reference_image_path: Path | None = Field(default=None)
    created_at: str = Field(description="ISO 8601 timestamp")
    schema_version: str = Field(default="1.0")
```

### 3. File Organization

```
data/characters/
├── oliver.json          # Character definition
├── hannah.json
├── images/
│   ├── oliver.png       # Reference images
│   └── hannah.png
└── templates/
    └── character_template.json  # Template for new characters
```

### 4. Character Manager

```python
class CharacterManager:
    def __init__(self, characters_dir: Path = Path("data/characters")):
        self.characters_dir = characters_dir
    
    def load_character(self, character_id: str) -> Character:
        """Load character from JSON file."""
        file_path = self.characters_dir / f"{character_id}.json"
        if not file_path.exists():
            raise CharacterNotFoundError(f"Character not found: {character_id}")
        
        data = json.loads(file_path.read_text())
        return Character(**data)
    
    def list_characters(self) -> list[Character]:
        """List all available characters."""
        characters = []
        for file_path in self.characters_dir.glob("*.json"):
            if file_path.stem not in ["template", "schema"]:
                characters.append(self.load_character(file_path.stem))
        return characters
    
    def validate_character(self, character: Character) -> list[str]:
        """Validate character configuration."""
        errors = []
        
        # Check reference image exists
        if character.reference_image_path:
            if not character.reference_image_path.exists():
                errors.append(f"Reference image not found: {character.reference_image_path}")
        
        # Validate voice ID for provider
        # (provider-specific validation logic)
        
        return errors
```

## Consequences

### Positive
1. **Human-Readable**: JSON is familiar to non-developers
2. **Version Control**: Plain text files work well with git
3. **Validation**: Pydantic ensures data integrity at runtime
4. **IDE Support**: JSON schema enables autocomplete in IDEs
5. **Extensibility**: Easy to add new fields (backward compatible with defaults)
6. **Simplicity**: No database needed for MVP
7. **Template Support**: Easy to create new characters from template

### Negative
1. **File-Based**: Not suitable for large-scale character management (100s of characters)
2. **No Transactions**: No atomic updates across multiple characters
3. **No Query Support**: Can't filter/search without loading all files
4. **Manual Sync**: Must manually update if character changes

### Mitigations
- **For File-Based**: Sufficient for MVP (<20 characters), can migrate to DB later
- **For No Transactions**: Rare to update multiple characters simultaneously
- **For No Query**: Small dataset makes in-memory filtering acceptable
- **For Manual Sync**: Schema versioning enables migration path

## Alternatives Considered

### Alternative 1: YAML Files
**Rejected because**:
- Less familiar to non-technical users
- More complex syntax (indentation errors)
- Smaller ecosystem than JSON
- YAML libraries have security issues (arbitrary code execution)

### Alternative 2: TOML Files
**Rejected because**:
- Poor support for nested structures (voice_config)
- Less common than JSON
- Fewer tools and IDE support

### Alternative 3: Database (SQLite, PostgreSQL)
**Rejected because**:
- Over-engineered for MVP (<20 characters)
- Harder for non-developers to edit
- Requires migration scripts
- Not version-controllable in same way as files

### Alternative 4: Python Dataclasses in Code
**Rejected because**:
- Not editable by non-developers
- Requires code changes to add characters
- No runtime validation
- Harder to version control

## Implementation Guidelines

### Creating a New Character

1. Copy template:
   ```bash
   cp data/characters/templates/character_template.json data/characters/newchar.json
   ```

2. Edit JSON:
   ```json
   {
     "id": "newchar",
     "name": "New Character",
     "age": 9,
     "personality": "...",
     "speaking_style": "...",
     "vocabulary_level": "INTERMEDIATE",
     "voice_config": {
       "provider": "mock",
       "voice_id": "mock_newchar"
     }
   }
   ```

3. Validate:
   ```bash
   kids-podcast characters validate newchar
   ```

4. Test:
   ```bash
   kids-podcast characters show newchar
   ```

### Schema Evolution

When adding new fields:

1. **Add with defaults** in Pydantic model:
   ```python
   class Character(BaseModel):
       ...
       new_field: str = Field(default="default_value")
   ```

2. **Update schema_version**: Increment to "1.1", "2.0", etc.

3. **Write migration script** (if needed):
   ```python
   def migrate_v1_to_v2(character_data: dict) -> dict:
       if character_data.get("schema_version") == "1.0":
           character_data["new_field"] = "default_value"
           character_data["schema_version"] = "2.0"
       return character_data
   ```

4. **Backward compatibility**: Old files still load (Pydantic uses defaults)

### Voice Configuration Guidelines

**ElevenLabs**:
- `stability`: 0.5 (balanced), lower = more expressive, higher = more consistent
- `similarity_boost`: 0.75 (default), higher = closer to reference voice
- `style`: 0.0-1.0 (style exaggeration)

**Google TTS**:
```json
"voice_config": {
  "provider": "google",
  "voice_id": "en-US-Wavenet-D",
  "speaking_rate": 1.0,
  "pitch": 0.0,
  "volume_gain_db": 0.0
}
```

**OpenAI TTS**:
```json
"voice_config": {
  "provider": "openai",
  "voice_id": "alloy",
  "speed": 1.0
}
```

## Future Considerations

### Database Migration Path
When character count exceeds ~50:
1. Create `Character` table in SQLite/PostgreSQL
2. Implement `CharacterRepository` with same interface
3. Migrate JSON files to database (one-time script)
4. Keep JSON export capability for version control

### Character Variants
Future enhancement: Multiple variants per character (different ages, moods):
```json
{
  "id": "oliver",
  "variants": {
    "excited": {"stability": 0.3, "style": 0.8},
    "calm": {"stability": 0.7, "style": 0.2}
  }
}
```

### Character Relationships
Future enhancement: Define relationships between characters:
```json
{
  "relationships": {
    "hannah": "best friend",
    "professor_nova": "mentor"
  }
}
```

## References

- [Pydantic Documentation](https://docs.pydantic.dev/)
- [JSON Schema](https://json-schema.org/)
- [Character Design for Kids Content](https://www.commonsensemedia.org/)
- [Voice Configuration Best Practices](https://elevenlabs.io/docs)
