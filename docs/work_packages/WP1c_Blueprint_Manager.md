# WP1c: Blueprint Manager (ShowBlueprintManager)

**Parent WP**: [WP1: Foundation & Data Models](WP1_Foundation.md)  
**Status**: ⏳ Not Started  
**Dependencies**: [WP1a: Core Models](WP1a_Core_Models.md), [WP1b: Configuration](WP1b_Configuration.md)  
**Estimated Effort**: 2 days  
**Owner**: TBD  
**Subsystems:** Show Management

## 📋 Overview

Foundation work package establishes the **Storage** and **Show Management subsystems**, providing core data structures and Show Blueprint management that all other components depend on. This is the **critical path** - all parallel development depends on completing this first.

**Key Deliverables**:
- ShowBlueprintManager for loading/saving show data
- Show Blueprint CRUD operations
- Concepts tracking and management
- Show templates (Oliver, Hannah)

**Subsystem Responsibilities**:
- **Show Management Subsystem:** Show Blueprint CRUD, concepts tracking, episode linkage

**This Sub-WP Covers**: Building the Show Blueprint loading, saving, and management system.

## 🎯 High-Level Tasks

### Task 1.4: ShowBlueprintManager
Build Show Blueprint loading, saving, and management system.

**Subtasks**:
- [ ] 1.4.1: Create `ShowBlueprintManager` class with CRUD operations
- [ ] 1.4.2: Implement `load_show(show_id: str) -> ShowBlueprint` from disk
- [ ] 1.4.3: Implement `save_show(blueprint: ShowBlueprint)` to disk
- [ ] 1.4.4: Implement `list_shows() -> list[Show]` to enumerate available shows
- [ ] 1.4.5: Implement `update_protagonist(show_id, protagonist: Protagonist)`
- [ ] 1.4.6: Implement `update_world(show_id, world: WorldDescription)`
- [ ] 1.4.7: Implement `add_character(show_id, character: Character)` for supporting characters
- [ ] 1.4.8: Implement `add_concept(show_id, concept: str, episode_id: str)` to update concepts_covered.json
- [ ] 1.4.9: Implement `get_covered_concepts(show_id) -> list[str]`
- [ ] 1.4.10: Add image path validation and handling
- [ ] 1.4.11: Create show initialization from template (oliver_template, hannah_template)

**Expected Outputs**:
- `src/modules/show_blueprint_manager.py`
- `data/shows/oliver/` (Oliver's STEM Adventures template)
- `data/shows/hannah/` (Hannah's History Adventures template)
- Show Blueprint validation tests

## 🔧 Technical Specifications

### ShowBlueprintManager API
```python
from pathlib import Path
from src.models.show import ShowBlueprint, Protagonist, WorldDescription, Character
from src.config import get_settings

class ShowBlueprintManager:
    """Manages Show Blueprint CRUD operations and concept tracking."""
    
    def __init__(self, shows_dir: Path | None = None):
        """Initialize manager with shows directory from settings."""
        self.shows_dir = shows_dir or get_settings().SHOWS_DIR
        
    def load_show(self, show_id: str) -> ShowBlueprint:
        """Load Show Blueprint from disk."""
        pass
        
    def save_show(self, blueprint: ShowBlueprint) -> None:
        """Save Show Blueprint to disk."""
        pass
        
    def list_shows(self) -> list[Show]:
        """Enumerate all available shows."""
        pass
        
    def update_protagonist(self, show_id: str, protagonist: Protagonist) -> None:
        """Update protagonist for a show."""
        pass
        
    def update_world(self, show_id: str, world: WorldDescription) -> None:
        """Update world description for a show."""
        pass
        
    def add_character(self, show_id: str, character: Character) -> None:
        """Add supporting character to show."""
        pass
        
    def add_concept(self, show_id: str, concept: str, episode_id: str) -> None:
        """Track new concept covered in episode."""
        pass
        
    def get_covered_concepts(self, show_id: str) -> list[str]:
        """Get all concepts covered across all episodes."""
        pass
        
    @classmethod
    def create_from_template(cls, template_name: str, show_id: str) -> ShowBlueprint:
        """Initialize new show from template (oliver_template, hannah_template)."""
        pass
```

### Show Directory Structure
```
data/shows/
├── oliver/
│   ├── show.yaml           # Show metadata
│   ├── protagonist.yaml    # Oliver's character
│   ├── world.yaml          # STEM lab world
│   ├── concepts_covered.json
│   ├── characters/
│   │   └── helper_bot.yaml
│   └── episodes/
│       ├── ep001_rockets/
│       └── ep002_magnets/
└── hannah/
    ├── show.yaml
    ├── protagonist.yaml
    ├── world.yaml
    ├── concepts_covered.json
    ├── characters/
    └── episodes/
```

### concepts_covered.json Format
```json
{
  "concepts": [
    {
      "concept": "How rockets work",
      "episode_id": "ep001_rockets",
      "covered_at": "2024-01-15T10:00:00Z"
    },
    {
      "concept": "Magnetism basics",
      "episode_id": "ep002_magnets",
      "covered_at": "2024-01-20T14:30:00Z"
    }
  ],
  "last_updated": "2024-01-20T14:30:00Z"
}
```

## 🧪 Testing Requirements

### Unit Tests
- **Show Blueprint Manager Tests**:
  - Load show from directory structure
  - Save show to directory (create files)
  - List all available shows
  - Update protagonist (modify protagonist.yaml)
  - Update world (modify world.yaml)
  - Add character (create new character file)
  - Add concept (update concepts_covered.json)
  - Get covered concepts (parse concepts_covered.json)
  - Handle missing show files gracefully
  - Validate show schema versions
  - Image path validation and resolution

### Integration Tests
- End-to-end show creation from template
- Concept tracking across multiple episodes
- Show Blueprint manager with real file system

### Fixtures
```python
# tests/fixtures/shows.py
@pytest.fixture
def oliver_show_template():
    return ShowBlueprint(
        show=Show(
            show_id="oliver",
            title="Oliver's STEM Adventures",
            description="Exploring science through invention",
            theme="STEM",
            narrator_voice_config=VoiceConfig(provider="mock")
        ),
        protagonist=Protagonist(
            name="Oliver the Inventor",
            age=10,
            description="Curious inventor",
            values=["curiosity", "creativity", "persistence"]
        ),
        world=WorldDescription(
            setting="Workshop laboratory",
            rules=["Physics apply", "Everything can be built"],
            atmosphere="Creative and experimental"
        ),
        characters=[],
        concepts_history=ConceptsHistory(concepts=[], last_updated=None),
        episodes=[]
    )
```

## 📝 Implementation Notes

### Dependencies
```toml
[project]
dependencies = [
    "pydantic>=2.5.0",
    "pyyaml>=6.0",  # For YAML file parsing
]
```

### Key Design Decisions
1. **YAML for Human Editing**: Show metadata stored in YAML for easy manual editing
2. **JSON for Machine Data**: Concepts history in JSON for structured tracking
3. **Directory-Based Shows**: Each show is a self-contained directory
4. **Template System**: Pre-built templates for quick show creation

### File I/O Patterns
- Use `pathlib.Path` for all file operations
- Atomic writes with temporary files (write to .tmp, then rename)
- Validate file existence before loading
- Create directories automatically when saving

## 📂 File Structure
```
src/
├── modules/
│   ├── __init__.py
│   └── show_blueprint_manager.py
└── __init__.py

data/shows/
├── oliver/               # Oliver template
│   ├── show.yaml
│   ├── protagonist.yaml
│   ├── world.yaml
│   ├── concepts_covered.json
│   ├── characters/
│   └── episodes/
└── hannah/              # Hannah template
    ├── show.yaml
    ├── protagonist.yaml
    ├── world.yaml
    ├── concepts_covered.json
    ├── characters/
    └── episodes/

tests/
├── test_show_blueprint_manager.py
└── fixtures/
    └── shows.py
```

## ✅ Definition of Done
- [ ] ShowBlueprintManager implements all CRUD operations
- [ ] Character templates (Oliver, Hannah) created and validated
- [ ] Concept tracking functional (add_concept, get_covered_concepts)
- [ ] Image path validation working
- [ ] Template system allows quick show creation
- [ ] Test coverage ≥ 80% for show blueprint manager
- [ ] Documentation includes example usage for all public APIs
- [ ] All file operations use atomic writes

## 🔗 Related Sub-WPs
- **Depends On**: [WP1a: Core Models](WP1a_Core_Models.md) - Show and Episode models
- **Depends On**: [WP1b: Configuration](WP1b_Configuration.md) - Settings for paths
- **Next**: [WP1d: Storage](WP1d_Storage.md) - Episode persistence within show directories
- **Related**: [WP1e: Testing](WP1e_Testing.md) - Error handling integration
