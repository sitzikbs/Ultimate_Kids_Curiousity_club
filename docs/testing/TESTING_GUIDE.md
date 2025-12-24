# Testing Guide

This guide covers the testing infrastructure for the Ultimate Kids Curiosity Club project.

## Overview

Our testing strategy follows a **mock-first** approach:
- 95% of tests use mocks (fast, free, reliable)
- 5% of tests use real APIs (slow, costly, gated)

## Test Structure

```
tests/
├── conftest.py              # Global fixtures
├── fixtures/                # Reusable test data
│   ├── characters.py        # Character fixtures
│   ├── episodes.py          # Episode fixtures
│   ├── services.py          # Mock service fixtures
│   └── audio.py             # Audio metadata fixtures
├── unit/                    # Unit tests (fast, isolated)
├── integration/             # Integration tests (mock services)
├── real_api/                # Real API tests (costly, gated)
├── cli/                     # CLI command tests
├── benchmarks/              # Performance benchmarks
└── utils/                   # Test utilities
    ├── fixture_loader.py    # Load JSON fixtures
    └── cost_tracker.py      # Track API costs
```

## Running Tests

### All Tests (Mock Only)

```bash
# Run all tests except real_api
pytest

# With coverage
pytest --cov=src --cov-report=html

# Verbose output
pytest -v
```

### By Category

```bash
# Unit tests only (fast)
pytest -m unit

# Integration tests
pytest -m integration

# Real API tests (costs money!)
pytest -m real_api

# Performance benchmarks
pytest --benchmark-only
```

### Specific Tests

```bash
# Single file
pytest tests/unit/test_models.py

# Single test
pytest tests/unit/test_models.py::test_character_creation

# Pattern matching
pytest -k "test_llm"
```

### Skip Slow Tests

```bash
# Skip tests marked as slow
pytest -m "not slow"

# Skip real_api and slow tests
pytest -m "not real_api and not slow"
```

## Test Markers

We use pytest markers to categorize tests:

| Marker | Description | Run in CI? |
|--------|-------------|------------|
| `unit` | Fast, isolated unit tests | ✅ Yes |
| `integration` | Integration tests with mock services | ✅ Yes |
| `real_api` | Tests that call real APIs (costly) | ❌ No |
| `slow` | Tests that take >5 seconds | ⚠️ Limited |
| `benchmark` | Performance benchmark tests | ⚠️ Limited |

### Using Markers

```python
import pytest

@pytest.mark.unit
def test_character_validation():
    """Fast unit test."""
    pass

@pytest.mark.integration
def test_llm_service_mock():
    """Integration test with mock service."""
    pass

@pytest.mark.real_api
def test_openai_api():
    """Real API test - costs money!"""
    pass

@pytest.mark.slow
@pytest.mark.integration
def test_full_pipeline():
    """Slow integration test."""
    pass
```

## Fixtures

### Built-in Fixtures

We provide comprehensive fixtures for common test scenarios:

```python
def test_with_fixtures(
    oliver_character,     # Oliver the Inventor character
    hannah_character,     # Hannah the Historian character
    new_episode,          # Episode in IDEATION status
    mock_llm_service,     # Mock LLM service
    mock_tts_service,     # Mock TTS service
):
    """Example test using multiple fixtures."""
    pass
```

### Loading Mock Data

```python
from tests.utils.fixture_loader import (
    load_llm_ideation_fixture,
    load_llm_script_fixture,
)

def test_with_mock_data(llm_fixtures_dir):
    """Example loading JSON mock data."""
    ideation = load_llm_ideation_fixture("airplanes", llm_fixtures_dir)
    assert ideation["refined_topic"]
```

## Writing Tests

### Unit Test Example

```python
import pytest
from src.models.character import Character

@pytest.mark.unit
def test_character_creation():
    """Test creating a character with valid data."""
    character = Character(
        id="test",
        name="Test Character",
        age=10,
        personality="Friendly",
    )
    
    assert character.id == "test"
    assert character.name == "Test Character"
    assert character.age == 10
```

### Integration Test Example

```python
import pytest

@pytest.mark.integration
def test_llm_ideation_flow(mock_llm_service, mock_mode_settings):
    """Test LLM ideation flow with mock service."""
    result = mock_llm_service.refine_topic(
        user_topic="How do airplanes fly?",
        duration=10
    )
    
    assert result["refined_topic"]
    assert len(result["learning_objectives"]) >= 3
    assert len(result["key_points"]) >= 5
```

### Using Mock Services

```python
from unittest.mock import MagicMock

def test_with_mock(mock_llm_service):
    """Test using a mock service."""
    # Mock service is already configured with default responses
    result = mock_llm_service.refine_topic("test topic")
    
    # Verify the mock was called correctly
    mock_llm_service.refine_topic.assert_called_once_with("test topic")
```

## Coverage

### Coverage Requirements

- **Overall**: ≥80% coverage required
- **Models**: ≥90% (simple data classes)
- **Services**: ≥80% (business logic)
- **CLI**: ≥75% (user interface)

### Checking Coverage

```bash
# Generate coverage report
pytest --cov=src --cov-report=html

# Open HTML report
open htmlcov/index.html

# Terminal report
pytest --cov=src --cov-report=term-missing
```

### Coverage Configuration

Coverage settings are in `.coveragerc`:

```ini
[run]
source = src
omit = 
    */tests/*
    */test_*.py

[report]
exclude_lines =
    pragma: no cover
    def __repr__
    if __name__ == .__main__.:
```

## Quality Gates

### Local Quality Checks

Run all quality checks before committing:

```bash
# Run the quality gate script
python scripts/quality_gate.py

# Or use pre-commit hooks
pre-commit install
pre-commit run --all-files
```

### CI/CD Pipeline

Our CI pipeline runs on every push and PR:

1. **Lint**: Check code style with ruff
2. **Format**: Verify formatting with ruff
3. **Type Check**: Run mypy on source code
4. **Test**: Run all tests except real_api
5. **Coverage**: Ensure ≥80% coverage
6. **Upload**: Send coverage to Codecov

## Performance Testing

### Running Benchmarks

```bash
# Run all benchmarks
pytest --benchmark-only

# Run specific benchmark
pytest tests/benchmarks/test_performance.py::test_fixture_loading_benchmark

# Save benchmark results
pytest --benchmark-only --benchmark-save=my_baseline

# Compare against baseline
pytest --benchmark-only --benchmark-compare=my_baseline
```

### Benchmark Example

```python
import pytest

@pytest.mark.benchmark
def test_parsing_benchmark(benchmark):
    """Benchmark JSON parsing speed."""
    
    def parse_json():
        return json.loads('{"key": "value"}')
    
    result = benchmark(parse_json)
    assert result["key"] == "value"
```

## Troubleshooting

### Tests Not Found

```bash
# Check pytest discovery
pytest --collect-only
```

### Import Errors

```bash
# Reinstall in editable mode
pip install -e ".[dev]"
```

### Fixture Not Found

Make sure the fixture is:
1. Defined in `conftest.py` or imported fixture file
2. Using the `@pytest.fixture` decorator
3. In scope (function, class, module, or session)

### Coverage Too Low

```bash
# Find uncovered lines
pytest --cov=src --cov-report=term-missing

# Focus on specific module
pytest --cov=src.models --cov-report=term-missing
```

## Best Practices

### 1. Write Tests First

Follow Test-Driven Development (TDD) when possible:
1. Write a failing test
2. Implement the feature
3. Refactor while keeping tests green

### 2. One Assertion Per Test

Keep tests focused:

```python
# Good
def test_character_has_name():
    character = create_character()
    assert character.name == "Oliver"

def test_character_has_age():
    character = create_character()
    assert character.age == 10

# Avoid
def test_character_properties():
    character = create_character()
    assert character.name == "Oliver"
    assert character.age == 10
    assert character.personality == "Curious"
```

### 3. Use Descriptive Names

```python
# Good
def test_llm_service_returns_learning_objectives():
    pass

# Avoid
def test_llm():
    pass
```

### 4. Mock External Dependencies

Never call real APIs in regular tests:

```python
# Good - uses mock
def test_with_mock(mock_llm_service):
    result = mock_llm_service.refine_topic("test")
    assert result

# Avoid - calls real API
def test_without_mock():
    llm = OpenAIService(api_key="real_key")
    result = llm.refine_topic("test")  # Costs money!
```

### 5. Clean Up Resources

```python
@pytest.fixture
def temp_audio_file(tmp_path):
    """Create temp audio file that's automatically cleaned up."""
    audio_file = tmp_path / "test.mp3"
    audio_file.write_bytes(b"mock audio data")
    yield audio_file
    # Cleanup happens automatically with tmp_path
```

## Additional Resources

- [Real API Tests Guide](./REAL_API_TESTS.md) - How to run costly real API tests
- [pytest Documentation](https://docs.pytest.org/)
- [pytest-cov Documentation](https://pytest-cov.readthedocs.io/)
- [pytest-benchmark Documentation](https://pytest-benchmark.readthedocs.io/)
