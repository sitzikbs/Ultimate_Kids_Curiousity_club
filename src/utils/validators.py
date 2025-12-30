"""Validation utilities and custom Pydantic types.

This module provides reusable validation functions, custom Pydantic types,
and validators for the Kids Curiosity Club podcast generation system.
"""

import re
from enum import Enum
from pathlib import Path
from typing import Annotated
from urllib.parse import urlparse

from pydantic import Field

# Custom Pydantic Types
# ----------------------

DurationMinutes = Annotated[
    int, Field(ge=5, le=20, description="Episode duration in minutes (5-20)")
]
"""Episode duration constrained to 5-20 minutes for age-appropriate content length."""

AgeRange = Annotated[int, Field(ge=5, le=12, description="Target age in years (5-12)")]
"""Target audience age constrained to 5-12 years old."""


class VocabularyLevel(str, Enum):
    """Vocabulary complexity level for content."""

    SIMPLE = "simple"
    INTERMEDIATE = "intermediate"
    ADVANCED = "advanced"


# File Path Validators
# ---------------------

def validate_file_exists(path: str | Path) -> Path:
    """Validate that a file exists.

    Args:
        path: File path to validate

    Returns:
        Validated Path object

    Raises:
        ValueError: If file does not exist
    """
    file_path = Path(path) if isinstance(path, str) else path
    if not file_path.exists():
        raise ValueError(f"File not found: {path}")
    return file_path


def validate_file_readable(path: str | Path) -> Path:
    """Validate that a file exists and is readable.

    Args:
        path: File path to validate

    Returns:
        Validated Path object

    Raises:
        ValueError: If file does not exist or is not readable
    """
    file_path = validate_file_exists(path)
    if not file_path.is_file():
        raise ValueError(f"Path is not a file: {path}")

    # Try to read file to check permissions
    try:
        with open(file_path, "rb") as f:
            f.read(1)
    except (PermissionError, OSError) as e:
        raise ValueError(f"File is not readable: {path}") from e

    return file_path


def validate_image_path(path: str | Path | None) -> Path | None:
    """Validate image file exists and has correct extension.

    Args:
        path: Image file path to validate (can be None)

    Returns:
        Validated Path object or None

    Raises:
        ValueError: If file does not exist or has invalid extension
    """
    if path is None:
        return None

    file_path = validate_file_exists(path)

    valid_extensions = {".png", ".jpg", ".jpeg", ".webp"}
    if file_path.suffix.lower() not in valid_extensions:
        raise ValueError(
            f"Invalid image format: {file_path.suffix}. "
            f"Expected one of: {', '.join(valid_extensions)}"
        )

    return file_path


def validate_audio_path(path: str | Path | None) -> Path | None:
    """Validate audio file exists and has correct extension.

    Args:
        path: Audio file path to validate (can be None)

    Returns:
        Validated Path object or None

    Raises:
        ValueError: If file does not exist or has invalid extension
    """
    if path is None:
        return None

    file_path = validate_file_exists(path)

    valid_extensions = {".mp3", ".wav", ".ogg", ".m4a"}
    if file_path.suffix.lower() not in valid_extensions:
        raise ValueError(
            f"Invalid audio format: {file_path.suffix}. "
            f"Expected one of: {', '.join(valid_extensions)}"
        )

    return file_path


# URL Validators
# --------------

def validate_url_format(url: str) -> bool:
    """Validate URL has proper format.

    Args:
        url: URL string to validate

    Returns:
        True if valid URL format, False otherwise
    """
    try:
        parsed = urlparse(url)
        return parsed.scheme in ["http", "https"] and bool(parsed.netloc)
    except Exception:
        return False


def validate_image_url(url: str) -> bool:
    """Validate image URL format and extension.

    Args:
        url: Image URL to validate

    Returns:
        True if valid image URL, False otherwise
    """
    if not validate_url_format(url):
        return False

    parsed = urlparse(url)
    path = parsed.path.lower()

    valid_extensions = [".png", ".jpg", ".jpeg", ".webp", ".gif"]
    return any(path.endswith(ext) for ext in valid_extensions)


# Text Content Validators
# ------------------------

# Basic profanity word list (simplified for demonstration)
PROFANITY_LIST = {
    "damn", "hell", "crap", "stupid", "dumb", "idiot", "shut up",
    # Add more as needed
}

# Scary/violent keywords for age-appropriate filtering
SCARY_KEYWORDS = [
    "blood", "kill", "murder", "weapon",
    "gun", "knife", "terror", "horror"
]

# Vowels for syllable counting
VOWELS = "aeiou"


def check_profanity(text: str) -> bool:
    """Check if text contains profanity.

    Args:
        text: Text to check for profanity

    Returns:
        True if text is clean, False if profanity found
    """
    text_lower = text.lower()

    # Remove punctuation for better matching
    text_normalized = re.sub(r'[^\w\s]', ' ', text_lower)

    for word in PROFANITY_LIST:
        # Check for whole word matches
        pattern = r'\b' + re.escape(word) + r'\b'
        if re.search(pattern, text_normalized):
            return False

    return True


def count_syllables(word: str) -> int:
    """Count syllables in a word (simplified algorithm).

    Args:
        word: Word to count syllables in

    Returns:
        Estimated syllable count
    """
    # Remove punctuation and convert to lowercase
    word = re.sub(r'[^\w]', '', word).lower().strip()
    if not word:
        return 0

    syllable_count = 0
    previous_was_vowel = False

    for char in word:
        is_vowel = char in VOWELS
        if is_vowel and not previous_was_vowel:
            syllable_count += 1
        previous_was_vowel = is_vowel

    # Adjust for silent e at the end
    if word.endswith("e") and syllable_count > 1:
        syllable_count -= 1

    # Every word has at least one syllable
    return max(1, syllable_count)


def estimate_reading_level(text: str) -> float:
    """Estimate reading grade level using Flesch-Kincaid formula.

    Args:
        text: Text to analyze

    Returns:
        Estimated grade level (0-12, clamped)
    """
    # Count sentences
    sentences = [s.strip() for s in re.split(r'[.!?]+', text) if s.strip()]
    sentence_count = len(sentences)

    if sentence_count == 0:
        return 0.0

    # Count words (remove punctuation for accurate count)
    words = [w for w in re.findall(r'\b\w+\b', text) if w]
    word_count = len(words)

    if word_count == 0:
        return 0.0

    # Count syllables
    syllable_count = sum(count_syllables(word) for word in words)

    # Flesch-Kincaid Grade Level formula
    # 0.39 × (words / sentences) + 11.8 × (syllables / words) - 15.59
    grade = (
        0.39 * (word_count / sentence_count)
        + 11.8 * (syllable_count / word_count)
        - 15.59
    )

    # Clamp to 0-12 range
    return max(0.0, min(12.0, grade))


def validate_age_appropriate(text: str, max_grade_level: float = 7.0) -> bool:
    """Check if text content is age-appropriate for 5-12 year olds.

    Args:
        text: Text to validate
        max_grade_level: Maximum acceptable grade level (default: 7.0 for ages 5-12)

    Returns:
        True if content is appropriate, False otherwise
    """
    # Check for profanity
    if not check_profanity(text):
        return False

    # Check reading level
    grade_level = estimate_reading_level(text)
    if grade_level > max_grade_level:
        return False

    # Check for scary/violent keywords (basic filter)
    text_lower = text.lower()
    for keyword in SCARY_KEYWORDS:
        if re.search(r'\b' + re.escape(keyword) + r'\b', text_lower):
            return False

    return True


def get_vocabulary_level(grade_level: float) -> VocabularyLevel:
    """Determine vocabulary level based on reading grade level.

    Args:
        grade_level: Flesch-Kincaid grade level

    Returns:
        Appropriate VocabularyLevel enum value
    """
    if grade_level <= 3.0:
        return VocabularyLevel.SIMPLE
    elif grade_level <= 6.0:
        return VocabularyLevel.INTERMEDIATE
    else:
        return VocabularyLevel.ADVANCED
