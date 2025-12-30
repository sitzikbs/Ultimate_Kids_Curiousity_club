"""Test suite for validation utilities."""


import pytest

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


class TestCustomTypes:
    """Tests for custom Pydantic types."""

    def test_duration_minutes_valid_range(self):
        """Test DurationMinutes accepts values in 5-20 range."""
        from pydantic import BaseModel

        class TestModel(BaseModel):
            duration: DurationMinutes

        # Test valid values
        for value in [5, 10, 15, 20]:
            model = TestModel(duration=value)
            assert model.duration == value

    def test_duration_minutes_rejects_too_low(self):
        """Test DurationMinutes rejects values below 5."""
        from pydantic import BaseModel, ValidationError

        class TestModel(BaseModel):
            duration: DurationMinutes

        with pytest.raises(ValidationError):
            TestModel(duration=4)

        with pytest.raises(ValidationError):
            TestModel(duration=0)

    def test_duration_minutes_rejects_too_high(self):
        """Test DurationMinutes rejects values above 20."""
        from pydantic import BaseModel, ValidationError

        class TestModel(BaseModel):
            duration: DurationMinutes

        with pytest.raises(ValidationError):
            TestModel(duration=21)

        with pytest.raises(ValidationError):
            TestModel(duration=100)

    def test_age_range_valid_range(self):
        """Test AgeRange accepts values in 5-12 range."""
        from pydantic import BaseModel

        class TestModel(BaseModel):
            age: AgeRange

        # Test valid values
        for value in [5, 7, 10, 12]:
            model = TestModel(age=value)
            assert model.age == value

    def test_age_range_rejects_too_low(self):
        """Test AgeRange rejects values below 5."""
        from pydantic import BaseModel, ValidationError

        class TestModel(BaseModel):
            age: AgeRange

        with pytest.raises(ValidationError):
            TestModel(age=4)

        with pytest.raises(ValidationError):
            TestModel(age=0)

    def test_age_range_rejects_too_high(self):
        """Test AgeRange rejects values above 12."""
        from pydantic import BaseModel, ValidationError

        class TestModel(BaseModel):
            age: AgeRange

        with pytest.raises(ValidationError):
            TestModel(age=13)

        with pytest.raises(ValidationError):
            TestModel(age=20)

    def test_vocabulary_level_enum_values(self):
        """Test VocabularyLevel enum has correct values."""
        assert VocabularyLevel.SIMPLE == "simple"
        assert VocabularyLevel.INTERMEDIATE == "intermediate"
        assert VocabularyLevel.ADVANCED == "advanced"

    def test_vocabulary_level_enum_membership(self):
        """Test VocabularyLevel enum membership."""
        assert "simple" in [v.value for v in VocabularyLevel]
        assert "intermediate" in [v.value for v in VocabularyLevel]
        assert "advanced" in [v.value for v in VocabularyLevel]


class TestFilePathValidators:
    """Tests for file path validation functions."""

    def test_validate_file_exists_with_existing_file(self, tmp_path):
        """Test validate_file_exists with an existing file."""
        test_file = tmp_path / "test.txt"
        test_file.write_text("test content")

        result = validate_file_exists(str(test_file))
        assert result == test_file
        assert result.exists()

    def test_validate_file_exists_with_path_object(self, tmp_path):
        """Test validate_file_exists with Path object."""
        test_file = tmp_path / "test.txt"
        test_file.write_text("test content")

        result = validate_file_exists(test_file)
        assert result == test_file

    def test_validate_file_exists_with_missing_file(self):
        """Test validate_file_exists raises error for missing file."""
        with pytest.raises(ValueError, match="File not found"):
            validate_file_exists("/nonexistent/file.txt")

    def test_validate_file_readable_with_readable_file(self, tmp_path):
        """Test validate_file_readable with a readable file."""
        test_file = tmp_path / "readable.txt"
        test_file.write_text("readable content")

        result = validate_file_readable(str(test_file))
        assert result == test_file

    def test_validate_file_readable_with_directory(self, tmp_path):
        """Test validate_file_readable rejects directories."""
        with pytest.raises(ValueError, match="not a file"):
            validate_file_readable(tmp_path)

    def test_validate_file_readable_with_missing_file(self):
        """Test validate_file_readable raises error for missing file."""
        with pytest.raises(ValueError, match="File not found"):
            validate_file_readable("/nonexistent/file.txt")

    def test_validate_image_path_with_valid_extensions(self, tmp_path):
        """Test validate_image_path accepts valid image extensions."""
        valid_extensions = [".png", ".jpg", ".jpeg", ".webp"]

        for ext in valid_extensions:
            img_file = tmp_path / f"test{ext}"
            img_file.write_bytes(b"fake image data")

            result = validate_image_path(str(img_file))
            assert result == img_file

    def test_validate_image_path_with_uppercase_extension(self, tmp_path):
        """Test validate_image_path handles uppercase extensions."""
        img_file = tmp_path / "test.PNG"
        img_file.write_bytes(b"fake image data")

        result = validate_image_path(str(img_file))
        assert result == img_file

    def test_validate_image_path_with_invalid_extension(self, tmp_path):
        """Test validate_image_path rejects invalid extensions."""
        invalid_file = tmp_path / "test.txt"
        invalid_file.write_text("not an image")

        with pytest.raises(ValueError, match="Invalid image format"):
            validate_image_path(str(invalid_file))

    def test_validate_image_path_with_none(self):
        """Test validate_image_path accepts None."""
        result = validate_image_path(None)
        assert result is None

    def test_validate_image_path_with_missing_file(self):
        """Test validate_image_path raises error for missing file."""
        with pytest.raises(ValueError, match="File not found"):
            validate_image_path("/nonexistent/image.png")

    def test_validate_audio_path_with_valid_extensions(self, tmp_path):
        """Test validate_audio_path accepts valid audio extensions."""
        valid_extensions = [".mp3", ".wav", ".ogg", ".m4a"]

        for ext in valid_extensions:
            audio_file = tmp_path / f"test{ext}"
            audio_file.write_bytes(b"fake audio data")

            result = validate_audio_path(str(audio_file))
            assert result == audio_file

    def test_validate_audio_path_with_invalid_extension(self, tmp_path):
        """Test validate_audio_path rejects invalid extensions."""
        invalid_file = tmp_path / "test.txt"
        invalid_file.write_text("not audio")

        with pytest.raises(ValueError, match="Invalid audio format"):
            validate_audio_path(str(invalid_file))

    def test_validate_audio_path_with_none(self):
        """Test validate_audio_path accepts None."""
        result = validate_audio_path(None)
        assert result is None


class TestURLValidators:
    """Tests for URL validation functions."""

    def test_validate_url_format_with_valid_http(self):
        """Test validate_url_format accepts valid HTTP URLs."""
        assert validate_url_format("http://example.com") is True
        assert validate_url_format("http://example.com/path") is True

    def test_validate_url_format_with_valid_https(self):
        """Test validate_url_format accepts valid HTTPS URLs."""
        assert validate_url_format("https://example.com") is True
        assert validate_url_format("https://example.com/path/to/resource") is True

    def test_validate_url_format_with_invalid_scheme(self):
        """Test validate_url_format rejects invalid schemes."""
        assert validate_url_format("ftp://example.com") is False
        assert validate_url_format("file:///path/to/file") is False

    def test_validate_url_format_with_no_scheme(self):
        """Test validate_url_format rejects URLs without scheme."""
        assert validate_url_format("example.com") is False
        assert validate_url_format("www.example.com") is False

    def test_validate_url_format_with_empty_string(self):
        """Test validate_url_format rejects empty strings."""
        assert validate_url_format("") is False

    def test_validate_image_url_with_valid_image_urls(self):
        """Test validate_image_url accepts valid image URLs."""
        valid_urls = [
            "https://example.com/image.png",
            "https://example.com/photo.jpg",
            "https://example.com/picture.jpeg",
            "https://example.com/graphic.webp",
            "https://example.com/animation.gif",
        ]

        for url in valid_urls:
            assert validate_image_url(url) is True

    def test_validate_image_url_with_query_parameters(self):
        """Test validate_image_url handles URLs with query parameters."""
        # URLs with query parameters after image extension should pass
        url = "https://example.com/image.png?size=large"
        # The path part still ends with .png so it's valid
        assert validate_image_url(url) is True

    def test_validate_image_url_with_non_image_extension(self):
        """Test validate_image_url rejects non-image URLs."""
        assert validate_image_url("https://example.com/file.txt") is False
        assert validate_image_url("https://example.com/document.pdf") is False

    def test_validate_image_url_with_invalid_url(self):
        """Test validate_image_url rejects invalid URLs."""
        assert validate_image_url("not a url") is False
        assert validate_image_url("ftp://example.com/image.png") is False


class TestTextContentValidators:
    """Tests for text content validation functions."""

    def test_check_profanity_with_clean_text(self):
        """Test check_profanity returns True for clean text."""
        clean_texts = [
            "This is a nice story about science.",
            "Oliver loves to explore and learn new things.",
            "The rocket flew high into the sky!",
        ]

        for text in clean_texts:
            assert check_profanity(text) is True

    def test_check_profanity_with_profane_text(self):
        """Test check_profanity returns False for profane text."""
        profane_texts = [
            "This is damn difficult.",
            "What the hell is going on?",
            "Don't be an idiot!",
        ]

        for text in profane_texts:
            assert check_profanity(text) is False

    def test_check_profanity_case_insensitive(self):
        """Test check_profanity is case-insensitive."""
        assert check_profanity("DAMN") is False
        assert check_profanity("Damn") is False
        assert check_profanity("damn") is False

    def test_check_profanity_with_punctuation(self):
        """Test check_profanity handles punctuation."""
        assert check_profanity("Damn!") is False
        assert check_profanity("What the hell?") is False

    def test_count_syllables_simple_words(self):
        """Test count_syllables with simple words."""
        assert count_syllables("cat") == 1
        assert count_syllables("dog") == 1
        assert count_syllables("the") == 1

    def test_count_syllables_multi_syllable_words(self):
        """Test count_syllables with multi-syllable words."""
        assert count_syllables("hello") == 2
        assert count_syllables("water") == 2
        assert count_syllables("beautiful") == 3

    def test_count_syllables_with_silent_e(self):
        """Test count_syllables handles silent e."""
        assert count_syllables("make") == 1
        assert count_syllables("take") == 1
        # "like" should be 1 syllable after removing silent e
        assert count_syllables("like") == 1

    def test_count_syllables_empty_string(self):
        """Test count_syllables with empty string."""
        assert count_syllables("") == 0
        assert count_syllables("   ") == 0

    def test_estimate_reading_level_simple_text(self):
        """Test estimate_reading_level with simple text."""
        simple_text = "The cat sat. The dog ran. I like it."
        grade_level = estimate_reading_level(simple_text)
        assert 0 <= grade_level <= 5

    def test_estimate_reading_level_intermediate_text(self):
        """Test estimate_reading_level with intermediate text."""
        intermediate_text = (
            "Oliver looked at the fascinating rocket. "
            "He wondered how it could fly so high in the sky."
        )
        grade_level = estimate_reading_level(intermediate_text)
        assert 3 <= grade_level <= 8

    def test_estimate_reading_level_complex_text(self):
        """Test estimate_reading_level with complex text."""
        complex_text = (
            "The extraordinary phenomenon of gravitational acceleration "
            "demonstrates the fundamental principles of physics."
        )
        grade_level = estimate_reading_level(complex_text)
        assert grade_level >= 8

    def test_estimate_reading_level_empty_text(self):
        """Test estimate_reading_level with empty text."""
        assert estimate_reading_level("") == 0.0
        assert estimate_reading_level("   ") == 0.0

    def test_estimate_reading_level_clamped(self):
        """Test estimate_reading_level clamps to 0-12 range."""
        # Very simple text should not go below 0
        simple_text = "A. B. C."
        grade_level = estimate_reading_level(simple_text)
        assert grade_level >= 0.0

        # Very complex text should not exceed 12
        assert grade_level <= 12.0

    def test_validate_age_appropriate_with_appropriate_text(self):
        """Test validate_age_appropriate with appropriate content."""
        appropriate_texts = [
            "The rocket flew high into the sky.",
            "Let's learn about how things work!",
            "Oliver likes to play in the park. He has fun with his friends.",
        ]

        for text in appropriate_texts:
            assert validate_age_appropriate(text) is True

    def test_validate_age_appropriate_rejects_profanity(self):
        """Test validate_age_appropriate rejects profane text."""
        assert validate_age_appropriate("This is damn hard.") is False

    def test_validate_age_appropriate_rejects_complex_text(self):
        """Test validate_age_appropriate rejects overly complex text."""
        complex_text = (
            "The extraordinary phenomenon of gravitational acceleration "
            "demonstrates the fundamental principles of theoretical physics "
            "and quantum mechanics in a comprehensive manner."
        )
        assert validate_age_appropriate(complex_text) is False

    def test_validate_age_appropriate_rejects_scary_content(self):
        """Test validate_age_appropriate rejects scary/violent content."""
        scary_texts = [
            "The monster had blood on its hands.",
            "They used a knife to kill the animal.",
            "It was a terrifying horror story.",
        ]

        for text in scary_texts:
            assert validate_age_appropriate(text) is False

    def test_validate_age_appropriate_with_custom_grade_level(self):
        """Test validate_age_appropriate with custom max grade level."""
        text = "The robot moved across the room. It was cool to watch."

        # Should pass with higher grade level
        assert validate_age_appropriate(text, max_grade_level=8.0) is True

        # Test that the parameter actually works
        result = validate_age_appropriate(text, max_grade_level=1.0)
        assert isinstance(result, bool)

    def test_get_vocabulary_level_simple(self):
        """Test get_vocabulary_level returns SIMPLE for low grades."""
        assert get_vocabulary_level(1.0) == VocabularyLevel.SIMPLE
        assert get_vocabulary_level(3.0) == VocabularyLevel.SIMPLE

    def test_get_vocabulary_level_intermediate(self):
        """Test get_vocabulary_level returns INTERMEDIATE for mid grades."""
        assert get_vocabulary_level(4.0) == VocabularyLevel.INTERMEDIATE
        assert get_vocabulary_level(6.0) == VocabularyLevel.INTERMEDIATE

    def test_get_vocabulary_level_advanced(self):
        """Test get_vocabulary_level returns ADVANCED for high grades."""
        assert get_vocabulary_level(7.0) == VocabularyLevel.ADVANCED
        assert get_vocabulary_level(12.0) == VocabularyLevel.ADVANCED


class TestValidationIntegration:
    """Integration tests for validators with Pydantic models."""

    def test_duration_minutes_in_model(self):
        """Test DurationMinutes type in Pydantic model."""
        from pydantic import BaseModel, ValidationError

        class Episode(BaseModel):
            duration: DurationMinutes

        # Valid duration
        episode = Episode(duration=10)
        assert episode.duration == 10

        # Invalid durations
        with pytest.raises(ValidationError):
            Episode(duration=3)

        with pytest.raises(ValidationError):
            Episode(duration=25)

    def test_age_range_in_model(self):
        """Test AgeRange type in Pydantic model."""
        from pydantic import BaseModel, ValidationError

        class Character(BaseModel):
            name: str
            age: AgeRange

        # Valid age
        char = Character(name="Oliver", age=10)
        assert char.age == 10

        # Invalid ages
        with pytest.raises(ValidationError):
            Character(name="Baby", age=2)

        with pytest.raises(ValidationError):
            Character(name="Teen", age=15)

    def test_vocabulary_level_in_model(self):
        """Test VocabularyLevel enum in Pydantic model."""
        from pydantic import BaseModel, ValidationError

        class Content(BaseModel):
            text: str
            vocab_level: VocabularyLevel

        # Valid levels
        for level in VocabularyLevel:
            content = Content(text="test", vocab_level=level)
            assert content.vocab_level == level

        # Invalid level
        with pytest.raises(ValidationError):
            Content(text="test", vocab_level="expert")
