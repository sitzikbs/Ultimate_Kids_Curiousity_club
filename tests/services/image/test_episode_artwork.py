"""Unit tests for EpisodeArtworkGenerator."""

import pytest
from PIL import Image

from services.image.episode_artwork import EpisodeArtworkGenerator
from services.image.manager import ImageManager


@pytest.fixture
def artwork_generator():
    """Create EpisodeArtworkGenerator instance."""
    return EpisodeArtworkGenerator()


@pytest.fixture
def custom_image(tmp_path):
    """Create a custom test image."""
    img = Image.new("RGB", (1600, 1600), color=(255, 100, 0))
    img_path = tmp_path / "custom.png"
    img.save(img_path)
    return img_path


@pytest.mark.unit
def test_artwork_generator_initialization():
    """Test that EpisodeArtworkGenerator initializes correctly."""
    generator = EpisodeArtworkGenerator()

    assert isinstance(generator.manager, ImageManager)


@pytest.mark.unit
def test_generate_artwork_with_default_logo(artwork_generator):
    """Test generating artwork with default logo."""
    img = artwork_generator.generate_artwork("Test Episode")

    assert isinstance(img, Image.Image)
    assert img.size == (1400, 1400)


@pytest.mark.unit
def test_generate_artwork_with_custom_image(artwork_generator, custom_image):
    """Test generating artwork with custom image."""
    img = artwork_generator.generate_artwork("Test Episode", custom_image=custom_image)

    assert isinstance(img, Image.Image)
    assert img.size == (1400, 1400)


@pytest.mark.unit
def test_generate_artwork_with_text_overlay(artwork_generator):
    """Test generating artwork with text overlay."""
    img = artwork_generator.generate_artwork(
        "Test Episode with Overlay", add_text_overlay=True
    )

    assert isinstance(img, Image.Image)
    assert img.size == (1400, 1400)


@pytest.mark.unit
def test_generate_artwork_saves_output(artwork_generator, tmp_path):
    """Test that artwork can be saved to file."""
    output_path = tmp_path / "episode_art.png"

    img = artwork_generator.generate_artwork("Test Episode", output_path=output_path)

    assert output_path.exists()
    assert isinstance(img, Image.Image)


@pytest.mark.unit
def test_generate_youtube_thumbnail(artwork_generator):
    """Test generating YouTube thumbnail."""
    img = artwork_generator.generate_youtube_thumbnail("YouTube Episode")

    assert isinstance(img, Image.Image)
    assert img.size == (1280, 720)


@pytest.mark.unit
def test_generate_youtube_thumbnail_with_custom(artwork_generator, custom_image):
    """Test generating YouTube thumbnail with custom image."""
    img = artwork_generator.generate_youtube_thumbnail(
        "YouTube Episode", custom_image=custom_image
    )

    assert isinstance(img, Image.Image)
    assert img.size == (1280, 720)


@pytest.mark.unit
def test_generate_youtube_thumbnail_saves_output(artwork_generator, tmp_path):
    """Test that YouTube thumbnail can be saved."""
    output_path = tmp_path / "youtube_thumb.png"

    artwork_generator.generate_youtube_thumbnail(
        "YouTube Episode", output_path=output_path
    )

    assert output_path.exists()


@pytest.mark.unit
def test_load_default_logo(artwork_generator):
    """Test loading default podcast logo."""
    img = artwork_generator._load_default_logo()

    assert isinstance(img, Image.Image)


@pytest.mark.unit
def test_generate_placeholder_logo(artwork_generator):
    """Test generating placeholder logo."""
    img = artwork_generator._generate_placeholder_logo()

    assert isinstance(img, Image.Image)
    assert img.size == (1400, 1400)
    assert img.mode == "RGB"


@pytest.mark.unit
def test_wrap_text_for_overlay(artwork_generator):
    """Test text wrapping for overlay."""
    short_text = "Short Title"
    wrapped_short = artwork_generator._wrap_text_for_overlay(short_text)

    assert wrapped_short == "Short Title"

    long_text = "This is a very long episode title that needs to be wrapped properly"
    wrapped_long = artwork_generator._wrap_text_for_overlay(long_text, max_chars=30)

    lines = wrapped_long.split("\n")
    assert len(lines) <= 2
    for line in lines:
        assert len(line) <= 30


@pytest.mark.unit
def test_add_text_overlay(artwork_generator, custom_image):
    """Test adding text overlay to image."""
    img = Image.open(custom_image)

    result = artwork_generator._add_text_overlay(img, "Test Overlay")

    assert isinstance(result, Image.Image)
    assert result.mode == "RGB"
    assert result.size == img.size
