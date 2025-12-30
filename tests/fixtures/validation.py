"""Test fixtures for validation testing."""

import pytest


@pytest.fixture
def valid_image_path(tmp_path):
    """Create a temporary valid image file.

    Args:
        tmp_path: pytest's tmp_path fixture

    Returns:
        Path to a valid PNG image file
    """
    img_path = tmp_path / "test_image.png"
    img_path.write_bytes(b"PNG_MOCK_DATA")
    return str(img_path)


@pytest.fixture
def valid_audio_path(tmp_path):
    """Create a temporary valid audio file.

    Args:
        tmp_path: pytest's tmp_path fixture

    Returns:
        Path to a valid MP3 audio file
    """
    audio_path = tmp_path / "test_audio.mp3"
    audio_path.write_bytes(b"MP3_MOCK_DATA")
    return str(audio_path)


@pytest.fixture
def invalid_image_path():
    """Non-existent image path.

    Returns:
        Path to a non-existent image file
    """
    return "/nonexistent/path/image.png"


@pytest.fixture
def invalid_audio_path():
    """Non-existent audio path.

    Returns:
        Path to a non-existent audio file
    """
    return "/nonexistent/path/audio.mp3"


@pytest.fixture
def age_appropriate_text():
    """Sample text appropriate for ages 5-12.

    Returns:
        Kid-friendly text content
    """
    return (
        "Oliver looked at the rocket and wondered how it could fly so high! "
        "He decided to learn about gravity and forces. "
        "Science is so much fun when you discover how things work!"
    )


@pytest.fixture
def inappropriate_text_profanity():
    """Sample text with profanity.

    Returns:
        Text containing inappropriate language
    """
    return "This damn problem is really hard to solve."


@pytest.fixture
def inappropriate_text_scary():
    """Sample text with scary content.

    Returns:
        Text containing scary/violent content
    """
    return "The monster had blood dripping from its knife. It was a terrifying horror."


@pytest.fixture
def complex_text():
    """Sample text that's too complex for target age group.

    Returns:
        Text with advanced vocabulary and complex sentences
    """
    return (
        "The extraordinary phenomenon of gravitational acceleration "
        "demonstrates the fundamental principles of theoretical physics "
        "and quantum mechanics in a comprehensive and sophisticated manner."
    )


@pytest.fixture
def simple_text():
    """Sample text with simple vocabulary.

    Returns:
        Text with simple, age-appropriate vocabulary
    """
    return "The cat sat on the mat. The dog ran to the park. I like ice cream."


@pytest.fixture
def valid_image_urls():
    """List of valid image URLs.

    Returns:
        List of properly formatted image URLs
    """
    return [
        "https://example.com/image.png",
        "https://example.com/photo.jpg",
        "https://example.com/picture.jpeg",
        "https://example.com/graphic.webp",
        "http://cdn.example.com/assets/icon.png",
    ]


@pytest.fixture
def invalid_image_urls():
    """List of invalid image URLs.

    Returns:
        List of improperly formatted or non-image URLs
    """
    return [
        "not a url",
        "ftp://example.com/image.png",
        "https://example.com/document.pdf",
        "example.com/image.png",
        "",
    ]


@pytest.fixture
def test_episodes_data():
    """Sample episode data with various durations.

    Returns:
        List of episode dictionaries for testing
    """
    return [
        {"id": "ep001", "duration": 5, "title": "Short Episode"},
        {"id": "ep002", "duration": 10, "title": "Medium Episode"},
        {"id": "ep003", "duration": 20, "title": "Long Episode"},
    ]


@pytest.fixture
def test_characters_data():
    """Sample character data with various ages.

    Returns:
        List of character dictionaries for testing
    """
    return [
        {"name": "Young Oliver", "age": 5, "description": "Youngest protagonist"},
        {"name": "Oliver", "age": 10, "description": "Main protagonist"},
        {"name": "Older Oliver", "age": 12, "description": "Oldest protagonist"},
    ]
