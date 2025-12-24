# WP1e: Testing & Validation

**Parent WP**: [WP1: Foundation & Data Models](WP1_Foundation.md)  
**Status**: ⏳ Not Started  
**Dependencies**: [WP1a: Core Models](WP1a_Core_Models.md), [WP1b: Configuration](WP1b_Configuration.md), [WP1c: Blueprint Manager](WP1c_Blueprint_Manager.md), [WP1d: Storage](WP1d_Storage.md)  
**Estimated Effort**: 1 day  
**Owner**: TBD  
**Subsystems:** Validation + Testing

## 📋 Overview

Foundation work package establishes the **Storage** and **Show Management subsystems**, providing core data structures and Show Blueprint management that all other components depend on. This is the **critical path** - all parallel development depends on completing this first.

**Key Deliverables**:
- Validation rules and custom types
- Reusable validation utilities
- Comprehensive test suite for foundation components
- Test fixtures and helpers

**Subsystem Responsibilities**:
- **Validation Subsystem:** Data validation, content filtering, type checking

**This Sub-WP Covers**: Validation utilities and comprehensive testing infrastructure.

## 🎯 High-Level Tasks

### Task 1.7: Validation Utilities
Create reusable validation functions and custom Pydantic types.

**Subtasks**:
- [ ] 1.7.1: Create `DurationMinutes` custom type (5-20 minute range)
- [ ] 1.7.2: Create `AgeRange` custom type (5-12 years)
- [ ] 1.7.3: Create `VocabularyLevel` enum (SIMPLE, INTERMEDIATE, ADVANCED)
- [ ] 1.7.4: Implement file path validators (exists, readable, correct extension)
- [ ] 1.7.5: Add URL validators for image references
- [ ] 1.7.6: Create text content validators (profanity filtering, age-appropriate check)

**Expected Outputs**:
- `src/utils/validators.py`
- Validation utility tests

## 🔧 Technical Specifications

### Custom Pydantic Types
```python
from typing import Annotated
from pydantic import Field, validator
from enum import Enum

# Duration constraint (5-20 minutes)
DurationMinutes = Annotated[int, Field(ge=5, le=20)]

# Age constraint (5-12 years)
AgeRange = Annotated[int, Field(ge=5, le=12)]

# Vocabulary levels
class VocabularyLevel(str, Enum):
    SIMPLE = "simple"
    INTERMEDIATE = "intermediate"
    ADVANCED = "advanced"
```

### File Path Validators
```python
from pathlib import Path
from pydantic import field_validator

class WithImagePath:
    """Mixin for models with image paths."""
    
    @field_validator("image_path")
    @classmethod
    def validate_image_path(cls, v: str | None) -> str | None:
        """Validate image file exists and has correct extension."""
        if v is None:
            return None
            
        path = Path(v)
        if not path.exists():
            raise ValueError(f"Image file not found: {v}")
            
        if path.suffix.lower() not in [".png", ".jpg", ".jpeg", ".webp"]:
            raise ValueError(f"Invalid image format: {path.suffix}")
            
        return v
```

### Text Content Validators
```python
def validate_age_appropriate(text: str, max_age: int = 12) -> bool:
    """Check if text content is age-appropriate."""
    # Check for profanity (basic filter)
    # Check for complex vocabulary
    # Check for scary/violent content
    # Return True if appropriate, False otherwise
    pass

def check_profanity(text: str) -> bool:
    """Check if text contains profanity."""
    # Simple word list check
    # Return True if clean, False if profanity found
    pass

def estimate_reading_level(text: str) -> int:
    """Estimate reading grade level (Flesch-Kincaid)."""
    # Calculate reading difficulty
    # Return grade level (1-12)
    pass
```

### URL Validators
```python
import re
from urllib.parse import urlparse

def validate_image_url(url: str) -> bool:
    """Validate image URL format and accessibility."""
    # Check URL format
    parsed = urlparse(url)
    if not parsed.scheme in ["http", "https"]:
        return False
        
    # Check image extension in URL
    path = parsed.path.lower()
    if not any(path.endswith(ext) for ext in [".png", ".jpg", ".jpeg", ".webp"]):
        return False
        
    return True
```

## 🧪 Testing Requirements

### Unit Tests
- **Validation Tests**:
  - DurationMinutes accepts 5-20, rejects < 5 and > 20
  - AgeRange accepts 5-12, rejects < 5 and > 12
  - VocabularyLevel enum values
  - File path validator with existing/missing files
  - File path validator with correct/incorrect extensions
  - URL validator with valid/invalid URLs
  - Profanity filter with clean/dirty text
  - Reading level estimation
  - Age-appropriate content check

### Integration Tests
- Validation integrated with Pydantic models
- File path validation in ShowBlueprint
- Text validation in Episode generation
- End-to-end validation across all models

### Test Fixtures
```python
# tests/fixtures/validation.py
@pytest.fixture
def valid_image_path(tmp_path):
    """Create temporary valid image file."""
    img_path = tmp_path / "test_image.png"
    img_path.write_bytes(b"PNG_MOCK_DATA")
    return str(img_path)

@pytest.fixture
def invalid_image_path():
    """Non-existent image path."""
    return "/nonexistent/image.png"

@pytest.fixture
def age_appropriate_text():
    """Sample text appropriate for ages 5-12."""
    return "Oliver looked at the rocket and wondered how it could fly so high!"

@pytest.fixture
def inappropriate_text():
    """Sample text NOT appropriate for children."""
    return "This text contains scary and violent content..."
```

## 📝 Implementation Notes

### Dependencies
```toml
[project]
dependencies = [
    "pydantic>=2.5.0",
]

[project.optional-dependencies]
dev = [
    "pytest>=7.4.0",
    "pytest-cov>=4.1.0",
    "pytest-mock>=3.11.1"
]
```

### Key Design Decisions
1. **Pydantic-Native Validation**: Use Pydantic's validation framework for consistency
2. **Reusable Validators**: Create validators that can be mixed into any model
3. **Content Safety**: Basic profanity/age-appropriateness checks
4. **Conservative Defaults**: Err on side of caution for child content

### Testing Best Practices
- Use `pytest` as test framework
- Aim for ≥ 80% code coverage
- Use fixtures for reusable test data
- Use `pytest.mark.parametrize` for multiple test cases
- Use mocks for external dependencies (file system, APIs)

### Reading Level Calculation
```python
import re

def flesch_kincaid_grade(text: str) -> float:
    """Calculate Flesch-Kincaid Grade Level."""
    # Count sentences
    sentences = len(re.split(r'[.!?]+', text))
    
    # Count words
    words = len(text.split())
    
    # Count syllables (simplified)
    syllables = sum(count_syllables(word) for word in text.split())
    
    # Flesch-Kincaid formula
    grade = 0.39 * (words / sentences) + 11.8 * (syllables / words) - 15.59
    return max(0, min(12, grade))  # Clamp to 0-12 range

def count_syllables(word: str) -> int:
    """Count syllables in word (simplified)."""
    word = word.lower()
    vowels = "aeiou"
    syllable_count = 0
    previous_was_vowel = False
    
    for char in word:
        is_vowel = char in vowels
        if is_vowel and not previous_was_vowel:
            syllable_count += 1
        previous_was_vowel = is_vowel
        
    # Adjust for silent e
    if word.endswith("e"):
        syllable_count -= 1
        
    return max(1, syllable_count)
```

## 📂 File Structure
```
src/
├── utils/
│   ├── __init__.py
│   └── validators.py
└── __init__.py

tests/
├── test_validators.py
├── test_models.py           # From WP1a
├── test_config.py           # From WP1b
├── test_show_blueprint_manager.py  # From WP1c
├── test_episode_storage.py  # From WP1d
├── test_errors.py           # From WP1d
└── fixtures/
    ├── __init__.py
    ├── characters.py        # From WP1a
    ├── episodes.py          # From WP1d
    ├── shows.py             # From WP1c
    ├── settings.py          # From WP1b
    └── validation.py        # This WP
```

## ✅ Definition of Done
- [ ] All custom Pydantic types implemented (DurationMinutes, AgeRange, VocabularyLevel)
- [ ] File path validators working (exists, extension, readable)
- [ ] URL validators working (format, image extensions)
- [ ] Text content validators implemented (profanity, age-appropriate, reading level)
- [ ] Test coverage ≥ 80% for all foundation modules
- [ ] All fixtures organized and reusable
- [ ] Documentation includes validation examples
- [ ] Integration tests verify validation across all models

## 🔗 Related Sub-WPs
- **Depends On**: [WP1a: Core Models](WP1a_Core_Models.md) - Models to validate
- **Depends On**: [WP1b: Configuration](WP1b_Configuration.md) - Settings validation
- **Depends On**: [WP1c: Blueprint Manager](WP1c_Blueprint_Manager.md) - Show validation
- **Depends On**: [WP1d: Storage](WP1d_Storage.md) - Error handling integration
- **Finalizes**: Foundation work package - All core components validated and tested
