# WP1d: Storage (Episode Storage + Error Handling)

**Parent WP**: [WP1: Foundation & Data Models](WP1_Foundation.md)  
**Status**: ⏳ Not Started  
**Dependencies**: [WP1a: Core Models](WP1a_Core_Models.md), [WP1b: Configuration](WP1b_Configuration.md)  
**Estimated Effort**: 1-2 days  
**Owner**: TBD  
**Subsystems:** Storage

## 📋 Overview

Foundation work package establishes the **Storage** and **Show Management subsystems**, providing core data structures and Show Blueprint management that all other components depend on. This is the **critical path** - all parallel development depends on completing this first.

**Key Deliverables**:
- File-based storage structure for shows and episodes
- Episode checkpoint system for pipeline resumption
- Error handling base classes
- Custom exception hierarchy

**Subsystem Responsibilities**:
- **Storage Subsystem:** File I/O, data persistence, validation, error handling

**This Sub-WP Covers**: File-based storage for episodes and error handling infrastructure.

## 🎯 High-Level Tasks

### Task 1.5: Storage & Episode Persistence
Implement file-based storage for episodes within show directories.

**Subtasks**:
- [ ] 1.5.1: Create `EpisodeStorage` class for save/load operations
- [ ] 1.5.2: Implement checkpoint saving (save intermediate state at each pipeline stage)
- [ ] 1.5.3: Implement checkpoint loading (resume from any stage)
- [ ] 1.5.4: Add episode metadata tracking (created_at, updated_at, cost_estimate)
- [ ] 1.5.5: Implement atomic writes with temporary files
- [ ] 1.5.6: Add file locking for concurrent access protection
- [ ] 1.5.7: Link episodes to Show Blueprint (update episodes list in show)

**Expected Outputs**:
- `src/modules/episode_storage.py`
- Episode save/load tests with fixtures

### Task 1.6: Error Handling
Define custom exception hierarchy and error handling utilities.

**Subtasks**:
- [ ] 1.6.1: Create base `PodcastError` exception class
- [ ] 1.6.2: Add domain-specific exceptions (ShowNotFoundError, CharacterNotFoundError, ValidationError, APIError, AudioProcessingError, ApprovalRequiredError)
- [ ] 1.6.3: Implement error context tracking (stage, episode_id, show_id, timestamp)
- [ ] 1.6.4: Add retry decorators for transient failures
- [ ] 1.6.5: Implement error logging with structured data

**Expected Outputs**:
- `src/utils/errors.py`
- Error handling tests

## 🔧 Technical Specifications

### EpisodeStorage API
```python
from pathlib import Path
from src.models.episode import Episode, PipelineStage
from src.config import get_settings

class EpisodeStorage:
    """Manages episode file persistence with checkpoint support."""
    
    def __init__(self, shows_dir: Path | None = None):
        """Initialize storage with shows directory from settings."""
        self.shows_dir = shows_dir or get_settings().SHOWS_DIR
        
    def save_episode(self, episode: Episode) -> None:
        """Save episode to disk with atomic write."""
        pass
        
    def load_episode(self, show_id: str, episode_id: str) -> Episode:
        """Load episode from disk."""
        pass
        
    def save_checkpoint(self, episode: Episode, stage: PipelineStage) -> None:
        """Save intermediate state at pipeline stage."""
        pass
        
    def list_episodes(self, show_id: str) -> list[str]:
        """List all episode IDs for a show."""
        pass
        
    def get_episode_path(self, show_id: str, episode_id: str) -> Path:
        """Get path to episode directory."""
        pass
        
    def delete_episode(self, show_id: str, episode_id: str) -> None:
        """Delete episode and all associated files."""
        pass
```

### Episode Directory Structure
```
data/shows/oliver/episodes/
├── ep001_rockets/
│   ├── episode.json          # Full Episode model
│   ├── outline.json          # StoryOutline checkpoint
│   ├── segments.json         # StorySegments checkpoint
│   ├── scripts.json          # Scripts checkpoint
│   ├── audio/
│   │   ├── segment_01.mp3
│   │   ├── segment_02.mp3
│   │   └── final_mix.mp3
│   └── metadata.json         # Timestamps, costs, etc.
└── ep002_magnets/
    └── ...
```

### Error Handling Hierarchy
```python
class PodcastError(Exception):
    """Base exception for all podcast generation errors."""
    
    def __init__(self, message: str, **context):
        super().__init__(message)
        self.context = context
        self.timestamp = datetime.now()
        
class ShowNotFoundError(PodcastError):
    """Show ID does not exist."""
    pass
    
class CharacterNotFoundError(PodcastError):
    """Character ID not found in show."""
    pass
    
class ValidationError(PodcastError):
    """Data validation failed."""
    pass
    
class APIError(PodcastError):
    """External API call failed."""
    pass
    
class AudioProcessingError(PodcastError):
    """Audio synthesis or mixing failed."""
    pass
    
class ApprovalRequiredError(PodcastError):
    """Content requires human approval before proceeding."""
    pass
```

### Retry Decorator
```python
import time
from functools import wraps
from typing import Type

def retry_on_failure(
    max_attempts: int = 3,
    delay: float = 1.0,
    exceptions: tuple[Type[Exception], ...] = (APIError,)
):
    """Retry function on transient failures."""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            for attempt in range(max_attempts):
                try:
                    return func(*args, **kwargs)
                except exceptions as e:
                    if attempt == max_attempts - 1:
                        raise
                    time.sleep(delay * (2 ** attempt))  # Exponential backoff
            return None
        return wrapper
    return decorator
```

## 🧪 Testing Requirements

### Unit Tests
- **Episode Storage Tests**:
  - Save episode to disk (creates directory and files)
  - Load episode from disk
  - Save checkpoint at each pipeline stage
  - Load checkpoint and resume
  - Atomic writes (verify .tmp file usage)
  - File locking (concurrent access protection)
  - Delete episode (removes all files)
  - List episodes for a show
  - Handle missing episode files gracefully
  
- **Error Handling Tests**:
  - Base exception with context tracking
  - Domain-specific exceptions raise correctly
  - Error logging captures structured data
  - Retry decorator attempts correct number of times
  - Exponential backoff timing
  - Context preservation through exception chain

### Integration Tests
- End-to-end episode checkpoint flow (save → load → resume)
- Episode storage integration with file system
- Error handling across module boundaries

### Fixtures
```python
# tests/fixtures/episodes.py
@pytest.fixture
def sample_episode():
    return Episode(
        episode_id="test_ep001",
        show_id="oliver",
        topic="How rockets work",
        title="Journey to the Stars",
        current_stage=PipelineStage.IDEATION,
        created_at=datetime.now(),
        updated_at=datetime.now()
    )

@pytest.fixture
def temp_storage(tmp_path):
    """Create temporary storage directory for tests."""
    shows_dir = tmp_path / "shows"
    shows_dir.mkdir()
    return EpisodeStorage(shows_dir=shows_dir)
```

## 📝 Implementation Notes

### Dependencies
```toml
[project]
dependencies = [
    "pydantic>=2.5.0",
]
```

### Key Design Decisions
1. **File-Based Storage**: Simple JSON files for episodes (no database needed for MVP)
2. **Checkpoint System**: Enables resume-from-any-stage capability without re-running expensive API calls
3. **Atomic Writes**: Write to .tmp file first, then rename to prevent corruption
4. **File Locking**: Prevent concurrent modifications to same episode
5. **Structured Error Context**: Track stage, IDs, and timestamps for debugging

### Atomic Write Pattern
```python
def atomic_write(path: Path, content: str) -> None:
    """Write file atomically to prevent corruption."""
    tmp_path = path.with_suffix(path.suffix + ".tmp")
    tmp_path.write_text(content)
    tmp_path.rename(path)  # Atomic on POSIX systems
```

### File Locking Strategy
- Use `fcntl.flock` on Linux/macOS
- Use `msvcrt.locking` on Windows
- Timeout after 5 seconds if lock unavailable
- Release lock in finally block

## 📂 File Structure
```
src/
├── modules/
│   ├── __init__.py
│   └── episode_storage.py
├── utils/
│   ├── __init__.py
│   └── errors.py
└── __init__.py

data/shows/oliver/episodes/
└── (episode directories created at runtime)

tests/
├── test_episode_storage.py
├── test_errors.py
└── fixtures/
    └── episodes.py
```

## ✅ Definition of Done
- [ ] Episode storage implements save/load with checkpointing
- [ ] Atomic writes prevent file corruption
- [ ] File locking protects concurrent access
- [ ] Custom exception hierarchy with context tracking
- [ ] Retry decorators handle transient failures
- [ ] Error logging captures structured data
- [ ] Test coverage ≥ 80% for storage and error modules
- [ ] Documentation includes checkpoint usage examples

## 🔗 Related Sub-WPs
- **Depends On**: [WP1a: Core Models](WP1a_Core_Models.md) - Episode model
- **Depends On**: [WP1b: Configuration](WP1b_Configuration.md) - Settings for paths
- **Related**: [WP1c: Blueprint Manager](WP1c_Blueprint_Manager.md) - Links episodes to shows
- **Next**: [WP1e: Testing](WP1e_Testing.md) - Validation utilities
