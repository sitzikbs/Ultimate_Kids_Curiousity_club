"""Reusable validation functions and custom Pydantic types."""

from enum import Enum
from pathlib import Path
from typing import Annotated

from pydantic import AfterValidator, BeforeValidator, Field


class VocabularyLevel(str, Enum):
    """Vocabulary complexity levels for age-appropriate content."""

    SIMPLE = "SIMPLE"
    INTERMEDIATE = "INTERMEDIATE"
    ADVANCED = "ADVANCED"


def validate_duration(value: int | float) -> int:
    """Validate duration is within acceptable range (5-20 minutes).
    
    Args:
        value: Duration in minutes
        
    Returns:
        Validated duration
        
    Raises:
        ValueError: If duration is outside acceptable range
    """
    duration = int(value)
    if not 5 <= duration <= 20:
        raise ValueError("Duration must be between 5 and 20 minutes")
    return duration


def validate_age(value: int) -> int:
    """Validate age is within target range (5-12 years).
    
    Args:
        value: Age in years
        
    Returns:
        Validated age
        
    Raises:
        ValueError: If age is outside target range
    """
    if not 5 <= value <= 12:
        raise ValueError("Age must be between 5 and 12 years")
    return value


def validate_file_path(value: str | Path | None) -> Path | None:
    """Validate file path exists and is readable.
    
    Args:
        value: File path to validate
        
    Returns:
        Validated Path object or None
        
    Raises:
        ValueError: If path doesn't exist or isn't readable
    """
    if value is None:
        return None

    path = Path(value) if isinstance(value, str) else value

    # Allow relative paths that don't exist yet (for future assets)
    if not path.is_absolute() and not path.exists():
        return path

    if path.exists() and not path.is_file():
        raise ValueError(f"Path exists but is not a file: {path}")

    return path


def validate_image_path(value: str | Path | None) -> Path | None:
    """Validate image file path has correct extension.
    
    Args:
        value: Image file path to validate
        
    Returns:
        Validated Path object or None
        
    Raises:
        ValueError: If path has invalid extension
    """
    if value is None:
        return None

    path = validate_file_path(value)
    if path is None:
        return None

    valid_extensions = {".png", ".jpg", ".jpeg", ".webp"}
    if path.suffix.lower() not in valid_extensions:
        raise ValueError(
            f"Invalid image extension: {path.suffix}. "
            f"Must be one of {valid_extensions}"
        )

    return path


def validate_url(value: str | None) -> str | None:
    """Validate URL format.
    
    Args:
        value: URL to validate
        
    Returns:
        Validated URL or None
        
    Raises:
        ValueError: If URL format is invalid
    """
    if value is None:
        return None

    if not value.startswith(("http://", "https://")):
        raise ValueError("URL must start with http:// or https://")

    return value


def validate_show_id(value: str) -> str:
    """Validate show ID format (lowercase, underscores, alphanumeric).
    
    Args:
        value: Show ID to validate
        
    Returns:
        Validated show ID
        
    Raises:
        ValueError: If show ID format is invalid
    """
    if not value:
        raise ValueError("Show ID cannot be empty")

    if not value.replace("_", "").isalnum():
        raise ValueError(
            "Show ID must contain only letters, numbers, and underscores"
        )

    if value != value.lower():
        raise ValueError("Show ID must be lowercase")

    return value


def validate_episode_id(value: str) -> str:
    """Validate episode ID format.
    
    Args:
        value: Episode ID to validate
        
    Returns:
        Validated episode ID
        
    Raises:
        ValueError: If episode ID format is invalid
    """
    if not value:
        raise ValueError("Episode ID cannot be empty")

    # Allow alphanumeric, underscores, and hyphens
    if not all(c.isalnum() or c in "_-" for c in value):
        raise ValueError(
            "Episode ID must contain only letters, numbers, underscores, and hyphens"
        )

    return value


# Custom Pydantic types
DurationMinutes = Annotated[int, AfterValidator(validate_duration), Field(ge=5, le=20)]
AgeRange = Annotated[int, AfterValidator(validate_age), Field(ge=5, le=12)]
FilePath = Annotated[Path | None, BeforeValidator(validate_file_path)]
ImagePath = Annotated[Path | None, BeforeValidator(validate_image_path)]
Url = Annotated[str | None, AfterValidator(validate_url)]
ShowId = Annotated[str, AfterValidator(validate_show_id)]
EpisodeId = Annotated[str, AfterValidator(validate_episode_id)]
