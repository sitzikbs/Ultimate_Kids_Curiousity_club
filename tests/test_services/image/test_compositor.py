"""Unit tests for ImageCompositor."""


import pytest
from PIL import Image

from services.image.compositor import ImageCompositor
from services.image.manager import ImageManager


@pytest.fixture
def compositor():
    """Create ImageCompositor instance."""
    return ImageCompositor()


@pytest.fixture
def character_images(tmp_path):
    """Create sample character images."""
    images = []
    colors = [(255, 0, 0), (0, 255, 0), (0, 0, 255)]

    for i, color in enumerate(colors):
        img = Image.new("RGB", (512, 512), color=color)
        img_path = tmp_path / f"char_{i}.png"
        img.save(img_path)
        images.append(img_path)

    return images


@pytest.fixture
def background_template(tmp_path):
    """Create a background template."""
    img = Image.new("RGBA", (1400, 1400), color=(100, 100, 100, 255))
    img_path = tmp_path / "background.png"
    img.save(img_path)
    return img_path


@pytest.mark.unit
def test_compositor_initialization():
    """Test that ImageCompositor initializes correctly."""
    compositor = ImageCompositor()

    assert isinstance(compositor.manager, ImageManager)


@pytest.mark.unit
def test_compose_characters_single(compositor, character_images):
    """Test composing a single character."""
    img = compositor.compose_characters([character_images[0]])

    assert isinstance(img, Image.Image)
    assert img.size == (1400, 1400)


@pytest.mark.unit
def test_compose_characters_multiple(compositor, character_images):
    """Test composing multiple characters side-by-side."""
    img = compositor.compose_characters(character_images[:2])

    assert isinstance(img, Image.Image)
    assert img.size == (1400, 1400)


@pytest.mark.unit
def test_compose_characters_custom_size(compositor, character_images):
    """Test composing with custom output size."""
    img = compositor.compose_characters(
        character_images,
        output_size=(1920, 1080)
    )

    assert img.size == (1920, 1080)


@pytest.mark.unit
def test_compose_characters_custom_background(compositor, character_images):
    """Test composing with custom background color."""
    img = compositor.compose_characters(
        [character_images[0]],
        background_color=(255, 255, 0)
    )

    assert isinstance(img, Image.Image)


@pytest.mark.unit
def test_compose_characters_empty_list(compositor):
    """Test that empty character list raises ValueError."""
    with pytest.raises(ValueError):
        compositor.compose_characters([])


@pytest.mark.unit
def test_compose_characters_nonexistent_file(compositor, tmp_path):
    """Test that nonexistent file raises FileNotFoundError."""
    fake_path = tmp_path / "nonexistent.png"

    with pytest.raises(FileNotFoundError):
        compositor.compose_characters([fake_path])


@pytest.mark.unit
def test_add_background_template(compositor, character_images, background_template):
    """Test applying background template."""
    # First create a foreground image
    foreground = Image.new("RGBA", (1400, 1400), color=(255, 0, 0, 128))

    result = compositor.add_background_template(foreground, background_template)

    assert isinstance(result, Image.Image)
    assert result.size == (1400, 1400)
    assert result.mode == "RGB"


@pytest.mark.unit
def test_add_title_banner_top(compositor, character_images):
    """Test adding title banner at top."""
    img = Image.new("RGB", (1400, 1400), color=(100, 100, 100))

    result = compositor.add_title_banner(img, "Episode Title", position="top")

    assert isinstance(result, Image.Image)
    assert result.size == img.size


@pytest.mark.unit
def test_add_title_banner_bottom(compositor, character_images):
    """Test adding title banner at bottom."""
    img = Image.new("RGB", (1400, 1400), color=(100, 100, 100))

    result = compositor.add_title_banner(img, "Episode Title", position="bottom")

    assert isinstance(result, Image.Image)


@pytest.mark.unit
def test_add_title_banner_with_subtitle(compositor):
    """Test adding title banner with subtitle."""
    img = Image.new("RGB", (1400, 1400), color=(100, 100, 100))

    result = compositor.add_title_banner(
        img,
        "Episode Title",
        subtitle="Subtitle Text",
        position="top"
    )

    assert isinstance(result, Image.Image)


@pytest.mark.unit
def test_add_title_banner_invalid_position(compositor):
    """Test that invalid position raises ValueError."""
    img = Image.new("RGB", (1400, 1400), color=(100, 100, 100))

    with pytest.raises(ValueError):
        compositor.add_title_banner(img, "Title", position="middle")


@pytest.mark.unit
def test_resize_with_aspect_ratio(compositor):
    """Test resizing with aspect ratio preservation."""
    img = Image.new("RGB", (1600, 800), color=(255, 0, 0))

    resized = compositor._resize_with_aspect_ratio(img, max_width=800, max_height=600)

    # Should maintain aspect ratio (2:1)
    assert resized.width <= 800
    assert resized.height <= 600
    # Check aspect ratio is maintained (approximately)
    original_ratio = img.width / img.height
    resized_ratio = resized.width / resized.height
    assert abs(original_ratio - resized_ratio) < 0.01


@pytest.mark.unit
def test_resize_with_aspect_ratio_square(compositor):
    """Test resizing square image."""
    img = Image.new("RGB", (1000, 1000), color=(0, 255, 0))

    resized = compositor._resize_with_aspect_ratio(img, max_width=500, max_height=500)

    assert resized.size == (500, 500)
