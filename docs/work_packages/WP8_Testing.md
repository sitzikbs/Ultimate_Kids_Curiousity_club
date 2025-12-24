# WP8: Testing Infrastructure & Quality Assurance

**Status**: ⏳ Not Started  
**Dependencies**: All WPs (cross-cutting)  
**Estimated Effort**: 3-4 days  
**Owner**: TBD  
**Subsystem:** Cross-cutting (all subsystems)

## 📋 Overview

Testing Infrastructure establishes comprehensive test coverage across all modules with focus on mock-first development, cost tracking, and gated real API tests. Includes pytest configuration, fixture system for story-based content generation (Show Blueprint, outlines, segments, scripts), CI/CD integration, and quality gates.

**Key Deliverables**:
- Pytest configuration with custom markers
- Comprehensive fixture system (Show Blueprint, story concepts, outlines, segments, scripts)
- Mock provider fixtures for all 4 LLM services
- Cost tracking for real API tests
- CI/CD pipeline configuration
- Coverage reporting and quality gates

**System Context**:
- **Subsystem:** Cross-cutting (tests all 6 subsystems)
- **Depends on:** All WPs (integration tests after component completion)
- **Parallel Development:** ⚠️ Unit tests can be written alongside each WP; integration tests after WP6 complete
- **Story Format:** Fixtures include Show Blueprint data (protagonist, world, characters), story concepts, outlines (4 segments), segments (20+ story beats), scripts (narrator + character dialogue)

## 🎯 High-Level Tasks

### Task 8.1: Pytest Configuration
Establish testing framework and conventions.

**Subtasks**:
- [ ] 8.1.1: Create pytest.ini with configuration
- [ ] 8.1.2: Define custom markers (unit, integration, real_api, slow)
- [ ] 8.1.3: Configure test discovery patterns
- [ ] 8.1.4: Set up coverage configuration (.coveragerc)
- [ ] 8.1.5: Add pytest plugins (pytest-cov, pytest-mock, pytest-asyncio)
- [ ] 8.1.6: Configure test output formatting

**Expected Outputs**:
- `pytest.ini`
- `.coveragerc`
- Pytest plugin configuration

### Task 8.2: Fixture System
Create reusable test fixtures for all components.

**Subtasks**:
- [ ] 8.2.1: Create character fixtures (Oliver, Hannah, generic)
- [ ] 8.2.2: Create episode fixtures (various stages and statuses)
- [ ] 8.2.3: Create script fixtures (dialogue segments)
- [ ] 8.2.4: Create audio segment fixtures (mock MP3 files)
- [ ] 8.2.5: Create settings fixtures (mock mode, real mode)
- [ ] 8.2.6: Create service fixtures (mock LLM, TTS, mixer)
- [ ] 8.2.7: Create orchestrator fixtures with all dependencies

**Expected Outputs**:
- `tests/fixtures/characters.py`
- `tests/fixtures/episodes.py`
- `tests/fixtures/services.py`
- `tests/conftest.py`

### Task 8.3: Mock Provider Fixtures
Generate realistic mock responses for cost-free testing.

**Subtasks**:
- [ ] 8.3.1: Create LLM ideation fixtures (3-5 topics)
- [ ] 8.3.2: Create LLM scripting fixtures (2-character, single-character)
- [ ] 8.3.3: Create TTS audio fixtures (silent MP3s with realistic duration)
- [ ] 8.3.4: Create image fixtures (placeholder images)
- [ ] 8.3.5: Implement fixture loading utilities
- [ ] 8.3.6: Add fixture validation tests

**Expected Outputs**:
- `data/fixtures/llm/` directory with JSON responses
- `data/fixtures/audio/` directory with silent MP3s
- `data/fixtures/images/` directory with placeholders
- Fixture loading utilities

### Task 8.4: Real API Tests
Gated tests with budget tracking.

**Subtasks**:
- [ ] 8.4.1: Create `@pytest.mark.real_api` marker
- [ ] 8.4.2: Implement cost tracking decorator
- [ ] 8.4.3: Add budget threshold checks (warn if cost > $10)
- [ ] 8.4.4: Create real API test suite (LLM, TTS, full pipeline)
- [ ] 8.4.5: Document how to run real API tests
- [ ] 8.4.6: Add cost reporting after test run

**Expected Outputs**:
- `tests/real_api/` directory
- Cost tracking utilities
- Budget enforcement

### Task 8.5: Integration Test Suites
End-to-end testing for each major component.

**Subtasks**:
- [ ] 8.5.1: LLM service integration tests (ideation → scripting)
- [ ] 8.5.2: TTS service integration tests (script → audio files)
- [ ] 8.5.3: Audio mixer integration tests (segments → final MP3)
- [ ] 8.5.4: Pipeline orchestrator integration tests (topic → complete episode)
- [ ] 8.5.5: CLI integration tests (command execution)

**Expected Outputs**:
- Integration test files for each service
- Full pipeline integration test

### Task 8.6: CI/CD Configuration
Automated testing in GitHub Actions.

**Subtasks**:
- [ ] 8.6.1: Create GitHub Actions workflow (.github/workflows/test.yml)
- [ ] 8.6.2: Run tests on push and pull request
- [ ] 8.6.3: Matrix testing (Python 3.10, 3.11, 3.12)
- [ ] 8.6.4: Run only mock tests in CI (exclude real_api marker)
- [ ] 8.6.5: Upload coverage reports to Codecov
- [ ] 8.6.6: Add status badges to README

**Expected Outputs**:
- `.github/workflows/test.yml`
- CI/CD pipeline running on GitHub

### Task 8.7: Quality Gates
Enforce code quality standards.

**Subtasks**:
- [ ] 8.7.1: Set coverage threshold (80% minimum)
- [ ] 8.7.2: Run ruff linting in CI
- [ ] 8.7.3: Run type checking with mypy in CI
- [ ] 8.7.4: Add pre-commit hooks for local validation
- [ ] 8.7.5: Create quality gate script (check coverage, lint, type errors)

**Expected Outputs**:
- `.pre-commit-config.yaml`
- Quality gate script
- CI enforcement of standards

### Task 8.8: Performance Testing
Monitor execution time and resource usage.

**Subtasks**:
- [ ] 8.8.1: Add pytest-benchmark for performance tests
- [ ] 8.8.2: Benchmark LLM response parsing
- [ ] 8.8.3: Benchmark audio mixing operations
- [ ] 8.8.4: Benchmark full pipeline execution (mock mode)
- [ ] 8.8.5: Set performance baselines (e.g., full mock pipeline < 15 seconds)

**Expected Outputs**:
- Performance benchmark tests
- Baseline metrics

## 🔧 Technical Specifications

### Pytest Configuration
```ini
# pytest.ini
[pytest]
testpaths = tests
python_files = test_*.py
python_classes = Test*
python_functions = test_*
addopts = 
    --verbose
    --strict-markers
    --cov=src
    --cov-report=term-missing
    --cov-report=html
    --cov-fail-under=80

markers =
    unit: Unit tests (fast, isolated)
    integration: Integration tests (mock services)
    real_api: Tests that call real APIs (costly, gated)
    slow: Tests that take >5 seconds
    
filterwarnings =
    ignore::DeprecationWarning
```

### Coverage Configuration
```ini
# .coveragerc
[run]
source = src
omit = 
    */tests/*
    */test_*.py
    */__pycache__/*
    */venv/*

[report]
exclude_lines =
    pragma: no cover
    def __repr__
    raise AssertionError
    raise NotImplementedError
    if __name__ == .__main__.:
    if TYPE_CHECKING:
    @abstractmethod
```

### Character Fixtures
```python
# tests/fixtures/characters.py
import pytest
from src.models.character import Character, VoiceConfig

@pytest.fixture
def oliver_character():
    """Oliver the Inventor character."""
    return Character(
        id="oliver",
        name="Oliver the Inventor",
        age=10,
        personality="Curious inventor who loves building things",
        speaking_style="Uses simple technical words, gets excited about mechanisms",
        vocabulary_level="INTERMEDIATE",
        voice_config=VoiceConfig(
            provider="mock",
            voice_id="mock_oliver",
            stability=0.5,
            similarity_boost=0.75
        )
    )

@pytest.fixture
def hannah_character():
    """Hannah the Historian character."""
    return Character(
        id="hannah",
        name="Hannah the Historian",
        age=11,
        personality="Loves history and storytelling",
        speaking_style="Uses narrative style, often starts with 'Did you know...'",
        vocabulary_level="INTERMEDIATE",
        voice_config=VoiceConfig(
            provider="mock",
            voice_id="mock_hannah",
            stability=0.6,
            similarity_boost=0.7
        )
    )

@pytest.fixture
def all_characters(oliver_character, hannah_character):
    """All default characters."""
    return [oliver_character, hannah_character]
```

### Episode Fixtures
```python
# tests/fixtures/episodes.py
import pytest
from datetime import datetime
from src.models.episode import Episode, EpisodeStatus

@pytest.fixture
def new_episode(oliver_character, hannah_character):
    """New episode in IDEATION status."""
    return Episode(
        id="test_ep001",
        title="How Rockets Work",
        topic="Space exploration and rocket science",
        duration_minutes=15,
        characters=[oliver_character.id, hannah_character.id],
        status=EpisodeStatus.IDEATION,
        created_at=datetime.now()
    )

@pytest.fixture
def complete_episode(new_episode):
    """Completed episode with all checkpoints."""
    new_episode.status = EpisodeStatus.COMPLETE
    new_episode.checkpoints = {
        "ideation": {
            "completed_at": "2024-01-15T10:05:00Z",
            "output": {
                "refined_topic": "How Rockets Work and Space Travel",
                "learning_objectives": ["Newton's Third Law", "Rocket fuel", "Living in space"],
                "key_points": ["Rockets push gas down", "Fuel in tanks", "No air in space"]
            }
        },
        "scripting": {
            "completed_at": "2024-01-15T10:10:00Z",
            "output": {"segments": []}
        },
        "audio_synthesis": {
            "completed_at": "2024-01-15T10:20:00Z",
            "audio_segments": []
        },
        "audio_mixing": {
            "completed_at": "2024-01-15T10:25:00Z",
            "final_audio_path": "data/audio/test_ep001/final.mp3"
        }
    }
    return new_episode
```

### Real API Test with Cost Tracking
```python
# tests/real_api/test_llm_real.py
import pytest
from src.services.llm.cost_tracker import CostTracker

@pytest.mark.real_api
def test_openai_ideation_real(settings_real_mode, cost_tracker):
    """Test real OpenAI ideation (costs ~$0.02)."""
    
    # Ensure real mode
    assert not settings_real_mode.USE_MOCK_SERVICES
    
    # Create service
    llm = create_llm_service(settings_real_mode)
    
    # Execute
    ideation = llm.refine_topic(
        user_topic="How do airplanes fly?",
        duration=10
    )
    
    # Validate
    assert ideation.refined_topic
    assert len(ideation.learning_objectives) >= 3
    assert len(ideation.key_points) >= 5
    
    # Track cost
    cost = cost_tracker.get_total_cost()
    assert cost < 0.05, f"Cost too high: ${cost:.2f}"
    print(f"✓ Test cost: ${cost:.2f}")

@pytest.fixture
def cost_tracker():
    """Cost tracker for real API tests."""
    tracker = CostTracker()
    yield tracker
    
    total = tracker.get_total_cost()
    print(f"\n💰 Total test cost: ${total:.2f}")
    
    # Warn if exceeding budget
    if total > 10.0:
        pytest.fail(f"Test suite exceeded budget: ${total:.2f} > $10.00")
```

### CI/CD Workflow
```yaml
# .github/workflows/test.yml
name: Tests

on:
  push:
    branches: [ main, develop ]
  pull_request:
    branches: [ main ]

jobs:
  test:
    runs-on: ubuntu-latest
    strategy:
      matrix:
        python-version: ["3.10", "3.11", "3.12"]
    
    steps:
    - uses: actions/checkout@v3
    
    - name: Set up Python ${{ matrix.python-version }}
      uses: actions/setup-python@v4
      with:
        python-version: ${{ matrix.python-version }}
    
    - name: Install dependencies
      run: |
        pip install uv
        uv pip install -e ".[dev]"
    
    - name: Lint with ruff
      run: ruff check src/
    
    - name: Type check with mypy
      run: mypy src/
    
    - name: Run tests (mock only)
      run: pytest -m "not real_api" --cov=src --cov-report=xml
    
    - name: Upload coverage to Codecov
      uses: codecov/codecov-action@v3
      with:
        file: ./coverage.xml
        fail_ci_if_error: true
```

## 🧪 Testing Requirements

### Test Coverage Targets
- **Overall**: ≥80%
- **Models**: ≥90% (simple data classes)
- **Services**: ≥80% (business logic)
- **CLI**: ≥75% (user interface)
- **Orchestrator**: ≥85% (critical path)

### Test Categories
- **Unit Tests**: Fast (<1s), isolated, mock all external dependencies
- **Integration Tests**: Slower (<10s), use mock services, test component interaction
- **Real API Tests**: Expensive, gated with marker, track costs
- **Performance Tests**: Benchmark critical operations

## 📝 Implementation Notes

### Dependencies
```toml
[project.optional-dependencies]
dev = [
    "pytest>=7.4.0",
    "pytest-cov>=4.1.0",
    "pytest-mock>=3.11.0",
    "pytest-asyncio>=0.21.0",
    "pytest-benchmark>=4.0.0",
    "ruff>=0.1.0",
    "mypy>=1.5.0",
    "pre-commit>=3.3.0"
]
```

### Key Design Decisions
1. **Mock-First**: 95% of tests use mocks, only 5% use real APIs
2. **Fixture Organization**: Fixtures organized by domain (characters, episodes, services)
3. **Cost Tracking**: Real API tests track and report costs
4. **CI/CD**: Only run mock tests in CI to avoid API costs
5. **Quality Gates**: Enforce 80% coverage, pass linting, pass type checks

### Running Tests
```bash
# All tests (mock only)
pytest

# With coverage
pytest --cov=src --cov-report=html

# Real API tests (requires API keys)
pytest -m real_api

# Specific test file
pytest tests/test_llm_service.py

# Performance benchmarks
pytest --benchmark-only
```

## 📂 File Structure
```
tests/
├── conftest.py            # Global fixtures
├── fixtures/
│   ├── characters.py
│   ├── episodes.py
│   ├── services.py
│   └── audio.py
├── unit/
│   ├── test_models.py
│   ├── test_character_manager.py
│   ├── test_llm_service.py
│   └── test_tts_service.py
├── integration/
│   ├── test_llm_integration.py
│   ├── test_tts_integration.py
│   ├── test_audio_mixer_integration.py
│   └── test_pipeline_integration.py
├── real_api/
│   ├── test_llm_real.py
│   ├── test_tts_real.py
│   └── test_full_pipeline_real.py
├── cli/
│   ├── test_episodes.py
│   ├── test_characters.py
│   └── test_config.py
└── benchmarks/
    └── test_performance.py

.github/workflows/
└── test.yml

.coveragerc
pytest.ini
.pre-commit-config.yaml
```

## ✅ Definition of Done
- [ ] Pytest configuration with custom markers (unit, integration, real_api, slow)
- [ ] Comprehensive fixture system for all components
- [ ] Mock provider fixtures for LLM, TTS, and images
- [ ] Real API test suite with cost tracking
- [ ] Integration tests for each service
- [ ] CI/CD pipeline running on GitHub Actions
- [ ] Coverage reporting with 80% threshold
- [ ] Pre-commit hooks for local quality checks
- [ ] Performance benchmarks for critical operations
- [ ] Documentation includes testing guide and how to run real API tests
