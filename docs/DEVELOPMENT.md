# Kids Curiosity Club - Development Guide

**Version:** 1.0  
**Last Updated:** December 23, 2025

This guide explains the development workflow, standards, and best practices for contributing to the Kids Curiosity Club podcast generation system.

## 🚀 Getting Started

### Prerequisites
- Python 3.12+
- Git
- uv (Python package manager)
- Basic understanding of async Python, Pydantic, pytest

### Initial Setup

```bash
# Clone repository
git clone <repo-url>
cd Ultimate_Kids_Curiousity_club

# Create virtual environment
uv venv
source .venv/bin/activate  # or .venv\Scripts\activate on Windows

# Install dependencies (when available)
uv pip install -e ".[dev]"

# Copy environment template
cp .env.example .env
# Edit .env with your settings (USE_MOCK_SERVICES=true for development)

# Run tests
pytest
```

## 📋 Picking Work

### 1. Review Available Work
- Check [PROGRESS.md](PROGRESS.md) for unassigned work packages
- Look at [work_packages/README.md](work_packages/README.md) for details
- Check GitHub issues for open tasks

### 2. Choose a Work Package
**Guidelines:**
- Start with WP0 or WP1 if you're new (foundation)
- WP2-5 can be done in parallel after WP1 is complete
- WP6-7 require most WPs complete
- Check dependencies in WP specification

### 3. Assign Yourself
- Comment on GitHub issue or update WP doc with your name
- Update PROGRESS.md with status change to 🟡 In Progress

## 🌿 Branching Strategy

### Branch Naming Convention

```
feature/wp{N}-{short-description}
```

**Examples:**
- `feature/wp0-template-system`
- `feature/wp1-data-models`
- `feature/wp2-openai-provider`
- `feature/wp3-elevenlabs-integration`

### Workflow

```bash
# Always start from main
git checkout main
git pull origin main

# Create feature branch
git checkout -b feature/wp1-data-models

# Make changes, commit frequently
git add .
git commit -m "feat(wp1): implement Character model with validation"

# Push to remote
git push origin feature/wp1-data-models

# Create PR when ready
```

## 💻 Development Workflow

### 1. Read the WP Specification
- Open the relevant `docs/work_packages/WP{N}_{Name}.md`
- Understand goals, tasks, and acceptance criteria
- Review interface specifications and code examples
- Check dependencies and integration points

### 2. Set Up Mock Services
```python
# In .env
USE_MOCK_SERVICES=true  # Start with mocks
```

### 3. Implement with TDD (Test-Driven Development)

```bash
# 1. Write test first
touch tests/test_wp1_models.py
# Write failing test

# 2. Run test (should fail)
pytest tests/test_wp1_models.py -v

# 3. Implement feature
touch src/models.py
# Implement code

# 4. Run test again (should pass)
pytest tests/test_wp1_models.py -v

# 5. Refactor if needed
```

### 4. Test Thoroughly

**Unit Tests (Free):**
```bash
pytest tests/test_wp1_models.py
```

**Integration Tests (Free with mocks):**
```bash
pytest -m integration tests/test_wp2_llm.py
```

**Service Tests (Costs money):**
```bash
# Requires --real flag and confirmation
pytest -m llm_service --real tests/test_wp2_llm.py
```

### 5. Update Documentation
- Check task boxes in WP document
- Update PROGRESS.md if completing major task
- Add docstrings to all public functions/classes
- Update INTERFACES.md if changing contracts

### 6. Create Pull Request

**PR Checklist:**
- [ ] All tests pass (`pytest`)
- [ ] Code formatted (`ruff format src/ tests/`)
- [ ] Linting passes (`ruff check src/ tests/`)
- [ ] Docstrings added to public APIs
- [ ] WP task checkboxes updated
- [ ] No secrets in code
- [ ] PR description references GitHub issue

## 📝 Code Standards

### Python Style
- **Formatter:** ruff (88 char line length)
- **Type hints:** Required for all function signatures
- **Docstrings:** Google style for all public functions/classes
- **Imports:** Organized by ruff (stdlib, third-party, local)

### Design Patterns & Best Practices

**Use design patterns to make code modular, maintainable, and testable:**

#### 1. Factory Pattern (WP1, WP2, WP3, WP5)
Use factories for creating providers with different implementations:

```python
class LLMProviderFactory:
    @staticmethod
    def create(settings: Settings) -> BaseLLMProvider:
        """Create LLM provider based on configuration."""
        if settings.USE_MOCK_SERVICES:
            return MockLLMProvider()
        elif settings.LLM_PROVIDER == "openai":
            return OpenAIProvider(api_key=settings.OPENAI_API_KEY)
        elif settings.LLM_PROVIDER == "anthropic":
            return AnthropicProvider(api_key=settings.ANTHROPIC_API_KEY)
        raise ValueError(f"Unknown provider: {settings.LLM_PROVIDER}")
```

**When to use:** Creating objects with different implementations based on configuration

#### 2. Strategy Pattern (WP0, WP2, WP3)
Encapsulate algorithms/behaviors that can be swapped at runtime:

```python
class BaseLLMProvider(ABC):
    """Strategy interface for LLM providers."""
    
    @abstractmethod
    def generate(self, prompt: str, **kwargs) -> dict[str, Any]:
        """Generate text using this strategy."""
        pass

# Context uses strategy
class IdeationService:
    def __init__(self, llm_provider: BaseLLMProvider):
        self.llm = llm_provider  # Can swap strategies
```

**When to use:** Multiple implementations of same behavior (providers, processors)

#### 3. Repository Pattern (WP1)
Separate data access logic from business logic:

```python
class EpisodeRepository:
    """Manages episode persistence."""
    
    def save(self, episode: Episode) -> None:
        """Save episode to storage."""
        pass
    
    def load(self, episode_id: str) -> Episode:
        """Load episode from storage."""
        pass
    
    def list_all(self) -> list[Episode]:
        """List all episodes."""
        pass

# Business logic doesn't know about JSON files
service = EpisodeService(repository=EpisodeRepository())
```

**When to use:** Data access operations (file I/O, database, API calls)

#### 4. Builder Pattern (WP1, WP4)
Construct complex objects step-by-step:

```python
class EpisodeBuilder:
    """Build episodes with fluent interface."""
    
    def __init__(self):
        self._episode = Episode()
    
    def with_topic(self, topic: str) -> "EpisodeBuilder":
        self._episode.topic = topic
        return self
    
    def with_characters(self, chars: list[Character]) -> "EpisodeBuilder":
        self._episode.characters = chars
        return self
    
    def build(self) -> Episode:
        return self._episode

# Usage
episode = (EpisodeBuilder()
    .with_topic("How rockets work")
    .with_characters([oliver, hannah])
    .with_duration(15)
    .build())
```

**When to use:** Objects with many optional parameters or complex construction

#### 5. Dependency Injection (All WPs)
Inject dependencies rather than creating them internally:

```python
# ❌ Bad: Hard to test, tightly coupled
class ScriptingService:
    def __init__(self):
        self.llm = OpenAIProvider()  # Can't swap or mock
        self.enhancer = PromptEnhancer()

# ✅ Good: Easy to test, loosely coupled
class ScriptingService:
    def __init__(
        self,
        llm_provider: BaseLLMProvider,
        prompt_enhancer: PromptEnhancer
    ):
        self.llm = llm_provider  # Can inject mock for testing
        self.enhancer = prompt_enhancer
```

**When to use:** Always! Makes testing and flexibility much easier

#### 6. Command Pattern (WP6, WP7)
Encapsulate requests as objects:

```python
class PipelineCommand(ABC):
    """Command for pipeline stage."""
    
    @abstractmethod
    def execute(self, episode: Episode) -> None:
        pass
    
    @abstractmethod
    def undo(self, episode: Episode) -> None:
        """Rollback if execution fails."""
        pass

class IdeationCommand(PipelineCommand):
    def execute(self, episode: Episode) -> None:
        # Run ideation
        pass
    
    def undo(self, episode: Episode) -> None:
        # Rollback to previous checkpoint
        pass
```

**When to use:** Operations that need undo/redo, transaction-like behavior

#### 7. Observer Pattern (WP6, WP7)
Notify subscribers when state changes:

```python
class ProgressTracker:
    """Observable progress tracker."""
    
    def __init__(self):
        self._observers: list[ProgressObserver] = []
    
    def attach(self, observer: ProgressObserver) -> None:
        self._observers.append(observer)
    
    def notify(self, stage: str, progress: float) -> None:
        for observer in self._observers:
            observer.update(stage, progress)

# CLI subscribes to progress updates
class CLIProgressDisplay(ProgressObserver):
    def update(self, stage: str, progress: float) -> None:
        print(f"{stage}: {progress:.0%}")
```

**When to use:** Progress tracking, event notifications, pub/sub patterns

#### 8. Template Method Pattern (WP0, WP4)
Define algorithm skeleton, let subclasses override steps:

```python
class BaseAudioProcessor(ABC):
    """Template for audio processing."""
    
    def process(self, audio: AudioSegment) -> AudioSegment:
        """Template method defines the algorithm."""
        audio = self.pre_process(audio)
        audio = self.apply_effect(audio)  # Subclass implements
        audio = self.post_process(audio)
        return audio
    
    def pre_process(self, audio: AudioSegment) -> AudioSegment:
        """Common pre-processing."""
        return audio.normalize()
    
    @abstractmethod
    def apply_effect(self, audio: AudioSegment) -> AudioSegment:
        """Subclass provides specific effect."""
        pass
    
    def post_process(self, audio: AudioSegment) -> AudioSegment:
        """Common post-processing."""
        return audio.trim_silence()

class ReverbProcessor(BaseAudioProcessor):
    def apply_effect(self, audio: AudioSegment) -> AudioSegment:
        return audio.apply_reverb()
```

**When to use:** Common algorithm with customizable steps

#### 9. Singleton Pattern (WP1)
Ensure only one instance exists:

```python
class Settings:
    """Singleton settings instance."""
    _instance: "Settings | None" = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            # Initialize
        return cls._instance

def get_settings() -> Settings:
    """Get global settings instance."""
    return Settings()
```

**When to use:** Configuration, shared state (use sparingly!)

#### 10. Adapter Pattern (WP2, WP3, WP5)
Convert one interface to another:

```python
class ElevenLabsAdapter(BaseTTSProvider):
    """Adapt ElevenLabs SDK to our interface."""
    
    def __init__(self, api_key: str):
        self.client = ElevenLabsSDK(api_key)  # External SDK
    
    def synthesize(self, text: str, voice_id: str, **kwargs) -> dict:
        """Adapt SDK call to our interface."""
        # Translate our interface to SDK interface
        audio = self.client.generate(
            text=text,
            voice=voice_id,
            model="eleven_multilingual_v2"
        )
        # Translate SDK response to our format
        return {
            "audio_data": audio,
            "duration": len(audio) / 1000,
            "provider": "elevenlabs"
        }
```

**When to use:** Integrating third-party libraries with different interfaces

### SOLID Principles

Follow SOLID for maintainable code:

1. **Single Responsibility**: Each class has one reason to change
   ```python
   # ❌ Bad: Multiple responsibilities
   class Episode:
       def save(self): pass
       def generate_audio(self): pass
       def send_email(self): pass
   
   # ✅ Good: Single responsibility each
   class Episode: pass  # Data model only
   class EpisodeRepository:
       def save(self, episode): pass
   class AudioGenerator:
       def generate(self, episode): pass
   class NotificationService:
       def notify(self, episode): pass
   ```

2. **Open/Closed**: Open for extension, closed for modification
   ```python
   # Use abstract base classes to extend without modifying
   class BaseLLMProvider(ABC):
       @abstractmethod
       def generate(self, prompt: str) -> str: pass
   
   # Add new providers without changing existing code
   class NewLLMProvider(BaseLLMProvider):
       def generate(self, prompt: str) -> str:
           # New implementation
           pass
   ```

3. **Liskov Substitution**: Subclasses should be substitutable for base classes
   ```python
   # Any BaseLLMProvider should work the same way
   def generate_content(provider: BaseLLMProvider, prompt: str) -> str:
       return provider.generate(prompt)  # Works for any provider
   ```

4. **Interface Segregation**: Many specific interfaces better than one general
   ```python
   # ❌ Bad: Fat interface
   class Provider(ABC):
       @abstractmethod
       def generate_text(self): pass
       @abstractmethod
       def generate_audio(self): pass
       @abstractmethod
       def generate_image(self): pass
   
   # ✅ Good: Segregated interfaces
   class TextProvider(ABC):
       @abstractmethod
       def generate(self): pass
   
   class AudioProvider(ABC):
       @abstractmethod
       def synthesize(self): pass
   ```

5. **Dependency Inversion**: Depend on abstractions, not concretions
   ```python
   # ❌ Bad: Depends on concrete class
   class Service:
       def __init__(self):
           self.provider = OpenAIProvider()  # Concrete dependency
   
   # ✅ Good: Depends on abstraction
   class Service:
       def __init__(self, provider: BaseLLMProvider):  # Abstract dependency
           self.provider = provider
   ```

### Code Modularity Guidelines

1. **Keep functions small** (< 50 lines, ideally < 20)
2. **Limit class size** (< 300 lines, split if larger)
3. **Use type hints** for all function signatures
4. **Avoid deep nesting** (max 3 levels of indentation)
5. **Extract magic numbers** into constants
6. **Use early returns** to reduce nesting
7. **Prefer composition over inheritance**
8. **Write self-documenting code** (clear names > comments)

### Example

```python
from pathlib import Path

from pydantic import BaseModel, Field


class Character(BaseModel):
    """Represents a podcast character with personality and voice config.
    
    Args:
        name: Character's display name
        character_id: Unique identifier (slug format)
        personality: Dict of personality traits and speaking style
        voice_config: TTS provider and voice settings
        
    Example:
        >>> char = Character(
        ...     name="Oliver the Inventor",
        ...     character_id="oliver_inventor",
        ...     personality={"traits": ["curious", "energetic"]},
        ...     voice_config={"provider": "elevenlabs", "voice_id": "abc123"}
        ... )
    """
    
    name: str = Field(..., min_length=1, max_length=100)
    character_id: str = Field(..., regex=r"^[a-z0-9_]+$")
    personality: dict[str, list[str] | str]
    voice_config: dict[str, str]
```

### File Organization

```
src/
├── models.py              # Pydantic models
├── config.py              # Configuration
├── modules/
│   ├── __init__.py
│   ├── character_manager.py
│   ├── content/
│   │   ├── __init__.py
│   │   └── llm_service.py
│   └── audio/
│       ├── __init__.py
│       ├── tts_service.py
│       └── mixer_service.py
└── utils/
    ├── __init__.py
    └── ai_providers/
        ├── __init__.py
        ├── base.py
        ├── mock_providers.py
        └── llm_providers.py
```

## 🧪 Testing Standards

### Test Structure

```python
"""Tests for Character model (WP1)."""

import pytest
from src.models import Character


class TestCharacterModel:
    """Test suite for Character model."""
    
    def test_character_creation_valid(self):
        """Test creating character with valid data."""
        char = Character(
            name="Test Character",
            character_id="test_char",
            personality={"traits": ["curious"]},
            voice_config={"provider": "mock", "voice_id": "test"}
        )
        assert char.name == "Test Character"
    
    def test_character_invalid_id(self):
        """Test character_id validation rejects invalid format."""
        with pytest.raises(ValueError):
            Character(
                name="Test",
                character_id="Invalid ID!",  # Spaces not allowed
                personality={},
                voice_config={}
            )
```

### Test Markers

Use pytest markers to categorize tests:

```python
import pytest

@pytest.mark.unit
def test_model_validation():
    """Unit test with no external dependencies."""
    pass

@pytest.mark.integration
def test_service_integration():
    """Integration test with mocked services."""
    pass

@pytest.mark.llm_service
def test_openai_provider():
    """Test requiring real LLM API (gated)."""
    pass

@pytest.mark.tts_service
def test_elevenlabs_provider():
    """Test requiring real TTS API (gated)."""
    pass

@pytest.mark.e2e
def test_full_pipeline():
    """End-to-end test (expensive)."""
    pass
```

### Running Tests

```bash
# All unit tests (free, fast)
pytest

# Specific work package
pytest tests/test_wp1_*.py

# Integration tests (with mocks)
pytest -m integration

# Real API tests (requires confirmation, costs money)
pytest -m llm_service --real
pytest -m tts_service --real

# E2E tests (expensive)
pytest -m e2e --real-apis --confirm

# With coverage
pytest --cov=src --cov-report=html
```

## 🔒 Security & Secrets

### Never Commit:
- API keys
- `.env` files
- Credentials
- Generated episodes (large files)

### Use:
- `.env.example` for templates
- Environment variables for secrets
- `.gitignore` (already configured)

### If You Accidentally Commit Secrets:
1. Rotate the exposed credentials immediately
2. Use `git filter-branch` or BFG Repo-Cleaner
3. Force push to remove from history
4. Notify team

## 🎯 Definition of Done

A work package task is "done" when:

- [x] **Code Complete:** All subtasks implemented
- [x] **Tests Pass:** Unit tests pass, integration tests with mocks pass
- [x] **Real API Tested:** At least one manual test with real API (if applicable)
- [x] **Documented:** Docstrings added, WP checklist updated
- [x] **Formatted:** `ruff format` and `ruff check` pass
- [x] **Reviewed:** Code review completed (self-review OK for solo dev)
- [x] **Integrated:** No merge conflicts with main
- [x] **Tracked:** PROGRESS.md updated, GitHub issue closed

## 🔄 Integration Points

When integrating services, always:

1. **Check INTERFACES.md** for contract specifications
2. **Use factory pattern** for provider injection
3. **Handle errors gracefully** with try/except and logging
4. **Add integration tests** with mocked dependencies
5. **Update interface docs** if changing contracts

## 📊 Cost Tracking

### During Development

```python
from src.utils.cost_tracker import track_cost

@track_cost
def generate_content(prompt: str) -> str:
    """Generate content with cost tracking."""
    # Implementation calls LLM
    pass
```

### View Costs

```bash
# Show costs for current development session
python -m src.utils.cost_tracker show

# Show costs for specific work package
python -m src.utils.cost_tracker show --wp=2

# Export cost report
python -m src.utils.cost_tracker export --format=csv
```

## 🐛 Debugging Tips

### Mock vs Real Services

```python
# .env
USE_MOCK_SERVICES=true   # For debugging logic
USE_MOCK_SERVICES=false  # For debugging real API integration
```

### Logging

```python
import logging

logger = logging.getLogger(__name__)
logger.info("Processing episode: %s", episode_id)
logger.debug("Full character data: %s", character.model_dump())
logger.error("API call failed", exc_info=True)
```

### Testing Individual Services

```bash
# Test just LLM service
python -m src.modules.content.llm_service --test

# Test with real API
python -m src.modules.content.llm_service --test --real
```

## 🤝 Getting Help

1. **Read the docs:** Check WP specification and INTERFACES.md
2. **Review ADRs:** See `docs/decisions/` for design rationale
3. **Check examples:** Look at completed WPs for patterns
4. **Ask questions:** Open GitHub discussion or comment on issue

## 📚 Additional Resources

- [Pydantic Documentation](https://docs.pydantic.dev/)
- [pytest Documentation](https://docs.pytest.org/)
- [Typer CLI Tutorial](https://typer.tiangolo.com/)
- [Python Type Hints Cheat Sheet](https://mypy.readthedocs.io/en/stable/cheat_sheet_py3.html)

---

**Ready to contribute?** Pick a work package from [work_packages/README.md](work_packages/README.md) and start coding!
