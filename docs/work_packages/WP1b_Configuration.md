# WP1b: Configuration (Settings & Config)

**Parent WP**: [WP1: Foundation & Data Models](WP1_Foundation.md)  
**Status**: ⏳ Not Started  
**Dependencies**: [WP1a: Core Models](WP1a_Core_Models.md)  
**Estimated Effort**: 1 day  
**Owner**: TBD  
**Subsystems:** Configuration

## 📋 Overview

Foundation work package establishes the **Storage** and **Show Management subsystems**, providing core data structures and Show Blueprint management that all other components depend on. This is the **critical path** - all parallel development depends on completing this first.

**Key Deliverables**:
- Settings system with environment-based configuration
- Mock mode toggle for development
- API key management
- Provider preferences

**Subsystem Responsibilities**:
- **Configuration Subsystem:** Environment variables, settings validation, singleton accessor

**This Sub-WP Covers**: Centralized settings and configuration system with Show Blueprint paths.

## 🎯 High-Level Tasks

### Task 1.3: Settings & Configuration
Implement centralized configuration with Show Blueprint paths.

**Subtasks**:
- [ ] 1.3.1: Create `Settings` class inheriting from `BaseSettings`
- [ ] 1.3.2: Add `USE_MOCK_SERVICES` boolean flag (default: True)
- [ ] 1.3.3: Add API keys section (OPENAI_API_KEY, ANTHROPIC_API_KEY, ELEVENLABS_API_KEY, etc.)
- [ ] 1.3.4: Add storage paths (SHOWS_DIR, EPISODES_DIR, ASSETS_DIR)
- [ ] 1.3.5: Add provider preferences (LLM_PROVIDER, TTS_PROVIDER, IMAGE_PROVIDER)
- [ ] 1.3.6: Implement `.env` loading with `python-dotenv`
- [ ] 1.3.7: Add settings validation (require API keys only when USE_MOCK_SERVICES=False)
- [ ] 1.3.8: Create singleton accessor `get_settings()`

**Expected Outputs**:
- `src/config.py` with Settings class
- `.env.example` template file
- Settings validation tests

## 🔧 Technical Specifications

### Settings Configuration
```python
from pydantic_settings import BaseSettings
from pathlib import Path

class Settings(BaseSettings):
    # Mock toggle
    USE_MOCK_SERVICES: bool = True
    
    # API Keys (required only when USE_MOCK_SERVICES=False)
    OPENAI_API_KEY: str | None = None
    ANTHROPIC_API_KEY: str | None = None
    ELEVENLABS_API_KEY: str | None = None
    
    # Provider selection
    LLM_PROVIDER: str = "openai"  # openai, anthropic, mock
    TTS_PROVIDER: str = "elevenlabs"  # elevenlabs, google, openai, mock
    IMAGE_PROVIDER: str = "flux"  # flux, dalle, mock
    
    # Storage paths
    DATA_DIR: Path = Path("data")
    SHOWS_DIR: Path = DATA_DIR / "shows"
    EPISODES_DIR: Path = DATA_DIR / "episodes"
    ASSETS_DIR: Path = DATA_DIR / "assets"
    AUDIO_OUTPUT_DIR: Path = DATA_DIR / "audio"
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"

_settings: Settings | None = None

def get_settings() -> Settings:
    global _settings
    if _settings is None:
        _settings = Settings()
    return _settings
```

### .env.example Template
```bash
# Mock Mode (set to False to use real services)
USE_MOCK_SERVICES=true

# API Keys (required when USE_MOCK_SERVICES=false)
# OPENAI_API_KEY=sk-...
# ANTHROPIC_API_KEY=sk-ant-...
# ELEVENLABS_API_KEY=...

# Provider Preferences
LLM_PROVIDER=openai
TTS_PROVIDER=elevenlabs
IMAGE_PROVIDER=flux

# Storage Paths (relative to project root)
DATA_DIR=data
SHOWS_DIR=data/shows
EPISODES_DIR=data/episodes
ASSETS_DIR=data/assets
AUDIO_OUTPUT_DIR=data/audio
```

## 🧪 Testing Requirements

### Unit Tests
- **Settings Tests**:
  - Environment variable loading from .env
  - Mock mode with no API keys required
  - Real mode validation (require API keys when USE_MOCK_SERVICES=False)
  - Path creation for storage directories
  - Singleton behavior (same instance returned across calls)
  - Default values applied when env vars not set

### Integration Tests
- Settings singleton behavior across modules
- Path resolution with different working directories
- Environment variable override precedence

## 📝 Implementation Notes

### Dependencies
```toml
[project]
dependencies = [
    "pydantic>=2.5.0",
    "pydantic-settings>=2.1.0",
    "python-dotenv>=1.0.0"
]
```

### Key Design Decisions
1. **Singleton Settings**: Centralized configuration accessible from any module
2. **Mock Mode First**: Default to mocks for development, opt-in to real services
3. **Conditional Validation**: API keys only required when not using mocks
4. **Path Objects**: Use `pathlib.Path` for cross-platform compatibility

### Environment Variable Precedence
1. System environment variables (highest priority)
2. `.env` file in project root
3. Default values in Settings class (lowest priority)

## 📂 File Structure
```
src/
├── config.py              # Settings class and get_settings()
└── __init__.py

.env.example              # Template for environment variables
.env                      # Actual config (gitignored)

tests/
├── test_config.py
└── fixtures/
    └── settings.py
```

## ✅ Definition of Done
- [ ] Settings system loads from .env and validates based on USE_MOCK_SERVICES
- [ ] `.env.example` template created with all configuration options
- [ ] Singleton accessor `get_settings()` implemented
- [ ] Test coverage ≥ 80% for settings module
- [ ] Documentation includes configuration examples for development and production
- [ ] All storage paths created automatically if missing

## 🔗 Related Sub-WPs
- **Depends On**: [WP1a: Core Models](WP1a_Core_Models.md) - Data models
- **Next**: [WP1c: Blueprint Manager](WP1c_Blueprint_Manager.md) - Uses settings for paths
- **Next**: [WP1d: Storage](WP1d_Storage.md) - Uses settings for storage paths
