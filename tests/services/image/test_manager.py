"""Unit tests for ImageManager."""


import pytest
from PIL import Image

from services.image.manager import ImageManager


@pytest.fixture
def image_manager():
    """Create ImageManager instance."""
    return ImageManager()


@pytest.fixture
def sample_image(tmp_path):
    """Create a sample test image."""
    img = Image.new("RGB", (1600, 1600), color=(255, 0, 0))
    img_path = tmp_path / "test_image.png"
    img.save(img_path)
    return img_path


@pytest.fixture
def small_image(tmp_path):
    """Create a small test image (below minimum size)."""
    img = Image.new("RGB", (800, 800), color=(0, 255, 0))
    img_path = tmp_path / "small_image.png"
    img.save(img_path)
    return img_path


@pytest.mark.unit
def test_image_manager_initialization(image_manager):
    """Test that ImageManager initializes with correct constants."""
    assert image_manager.PODCAST_ART_SIZE == (1400, 1400)
    assert image_manager.YOUTUBE_THUMBNAIL_SIZE == (1280, 720)
    assert image_manager.MAX_FILE_SIZE_KB == 512
    assert "PNG" in image_manager.SUPPORTED_FORMATS
    assert "JPEG" in image_manager.SUPPORTED_FORMATS
    assert "WEBP" in image_manager.SUPPORTED_FORMATS


@pytest.mark.unit
def test_load_image_success(image_manager, sample_image):
    """Test loading a valid image."""
    img = image_manager.load_image(sample_image)

    assert isinstance(img, Image.Image)
    assert img.size == (1600, 1600)
    assert img.format == "PNG"


@pytest.mark.unit
def test_load_image_not_found(image_manager, tmp_path):
    """Test loading a non-existent image raises FileNotFoundError."""
    non_existent = tmp_path / "does_not_exist.png"

    with pytest.raises(FileNotFoundError):
        image_manager.load_image(non_existent)


@pytest.mark.unit
def test_validate_dimensions_pass(image_manager, sample_image):
    """Test dimension validation passes for large enough image."""
    img = image_manager.load_image(sample_image)

    assert image_manager.validate_dimensions(img, min_width=1400, min_height=1400)


@pytest.mark.unit
def test_validate_dimensions_fail(image_manager, small_image):
    """Test dimension validation fails for small image."""
    img = image_manager.load_image(small_image)

    assert not image_manager.validate_dimensions(img, min_width=1400, min_height=1400)


@pytest.mark.unit
def test_resize_for_podcast(image_manager, sample_image):
    """Test resizing image for podcast standard."""
    img = image_manager.load_image(sample_image)
    resized = image_manager.resize_for_podcast(img)

    assert resized.size == (1400, 1400)


@pytest.mark.unit
def test_resize_for_podcast_large(image_manager, sample_image):
    """Test resizing image for large podcast format."""
    img = image_manager.load_image(sample_image)
    resized = image_manager.resize_for_podcast(img, large=True)

    assert resized.size == (3000, 3000)


@pytest.mark.unit
def test_resize_for_youtube(image_manager, sample_image):
    """Test resizing image for YouTube thumbnail."""
    img = image_manager.load_image(sample_image)
    resized = image_manager.resize_for_youtube(img)

    assert resized.size == (1280, 720)


@pytest.mark.unit
def test_resize_for_character(image_manager, sample_image):
    """Test resizing image for character reference."""
    img = image_manager.load_image(sample_image)
    resized = image_manager.resize_for_character(img)

    assert resized.size == (1024, 1024)


@pytest.mark.unit
def test_save_optimized_png(image_manager, sample_image, tmp_path):
    """Test saving optimized PNG image."""
    img = image_manager.load_image(sample_image)
    output_path = tmp_path / "output.png"

    image_manager.save_optimized(img, output_path, format="PNG")

    assert output_path.exists()
    loaded = Image.open(output_path)
    assert loaded.size == img.size


@pytest.mark.unit
def test_save_optimized_jpeg(image_manager, sample_image, tmp_path):
    """Test saving optimized JPEG image."""
    img = image_manager.load_image(sample_image)
    output_path = tmp_path / "output.jpg"

    image_manager.save_optimized(img, output_path, format="JPEG")

    assert output_path.exists()
    loaded = Image.open(output_path)
    assert loaded.size == img.size


@pytest.mark.unit
def test_save_optimized_creates_directory(image_manager, sample_image, tmp_path):
    """Test that save_optimized creates parent directories."""
    img = image_manager.load_image(sample_image)
    output_path = tmp_path / "subdir" / "nested" / "output.png"

    image_manager.save_optimized(img, output_path, format="PNG")

    assert output_path.exists()
    assert output_path.parent.exists()


@pytest.mark.unit
def test_save_optimized_invalid_format(image_manager, sample_image, tmp_path):
    """Test that invalid format raises ValueError."""
    img = image_manager.load_image(sample_image)
    output_path = tmp_path / "output.gif"

    with pytest.raises(ValueError):
        image_manager.save_optimized(img, output_path, format="GIF")


@pytest.mark.unit
def test_convert_format(image_manager, sample_image, tmp_path):
    """Test converting image format."""
    output_path = tmp_path / "converted.jpg"

    image_manager.convert_format(sample_image, output_path, target_format="JPEG")

    assert output_path.exists()
    loaded = Image.open(output_path)
    assert loaded.format == "JPEG"


@pytest.mark.unit
def test_convert_format_invalid(image_manager, sample_image, tmp_path):
    """Test that invalid target format raises ValueError."""
    output_path = tmp_path / "converted.bmp"

    with pytest.raises(ValueError):
        image_manager.convert_format(sample_image, output_path, target_format="BMP")


@pytest.mark.unit
def test_load_jpeg_image(image_manager, tmp_path):
    """Test loading a JPEG image."""
    img = Image.new("RGB", (1400, 1400), color=(0, 0, 255))
    img_path = tmp_path / "test.jpg"
    img.save(img_path, format="JPEG")

    loaded = image_manager.load_image(img_path)

    assert loaded.format == "JPEG"
    assert loaded.size == (1400, 1400)


@pytest.mark.unit
def test_load_webp_image(image_manager, tmp_path):
    """Test loading a WEBP image."""
    img = Image.new("RGB", (1400, 1400), color=(255, 255, 0))
    img_path = tmp_path / "test.webp"
    img.save(img_path, format="WEBP")

    loaded = image_manager.load_image(img_path)

    assert loaded.format == "WEBP"
    assert loaded.size == (1400, 1400)
