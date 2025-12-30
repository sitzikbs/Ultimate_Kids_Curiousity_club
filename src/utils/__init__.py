"""Utility functions and helpers."""

from utils.errors import (
    APIError,
    ApprovalRequiredError,
    AudioProcessingError,
    CharacterNotFoundError,
    PodcastError,
    ShowNotFoundError,
    StorageError,
    ValidationError,
    retry_on_failure,
)
from utils.validators import (
    AgeRange,
    DurationMinutes,
    VocabularyLevel,
    check_profanity,
    count_syllables,
    estimate_reading_level,
    get_vocabulary_level,
    validate_age_appropriate,
    validate_audio_path,
    validate_file_exists,
    validate_file_readable,
    validate_image_path,
    validate_image_url,
    validate_url_format,
)

__all__ = [
    # Errors
    "PodcastError",
    "ShowNotFoundError",
    "CharacterNotFoundError",
    "ValidationError",
    "APIError",
    "AudioProcessingError",
    "ApprovalRequiredError",
    "StorageError",
    "retry_on_failure",
    # Validators
    "DurationMinutes",
    "AgeRange",
    "VocabularyLevel",
    "validate_file_exists",
    "validate_file_readable",
    "validate_image_path",
    "validate_audio_path",
    "validate_url_format",
    "validate_image_url",
    "check_profanity",
    "count_syllables",
    "estimate_reading_level",
    "validate_age_appropriate",
    "get_vocabulary_level",
]
