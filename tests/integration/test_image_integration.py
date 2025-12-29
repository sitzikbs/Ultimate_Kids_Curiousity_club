"""Integration tests for image service."""

from pathlib import Path

import pytest
from PIL import Image

from services.image.compositor import ImageCompositor
from services.image.episode_artwork import EpisodeArtworkGenerator
from services.image.factory import ImageProviderFactory
from services.image.manager import ImageManager


@pytest.mark.integration
def test_image_pipeline_full_workflow(tmp_path):
    """Test complete image processing pipeline."""
    # Create manager
    manager = ImageManager()

    # Generate mock image
    provider = ImageProviderFactory.create_provider("mock")
    generated_img = provider.generate("Test character", width=1024, height=1024)

    # Save generated image
    generated_path = tmp_path / "generated.png"
    generated_img.save(generated_path)

    # Load and validate
    loaded_img = manager.load_image(generated_path)
    assert manager.validate_dimensions(loaded_img, min_width=1024, min_height=1024)

    # Resize for podcast
    podcast_img = manager.resize_for_podcast(loaded_img)
    assert podcast_img.size == (1400, 1400)

    # Save optimized
    output_path = tmp_path / "podcast_art.png"
    manager.save_optimized(podcast_img, output_path, format="PNG")

    assert output_path.exists()
    assert output_path.stat().st_size > 0


@pytest.mark.integration
def test_episode_artwork_generation_pipeline(tmp_path):
    """Test episode artwork generation pipeline."""
    # Create custom image using mock provider
    provider = ImageProviderFactory.create_provider("mock")
    custom_img = provider.generate("Episode background", width=1600, height=1600)

    custom_path = tmp_path / "custom_bg.png"
    custom_img.save(custom_path)

    # Generate episode artwork
    generator = EpisodeArtworkGenerator()

    # Test with custom image
    artwork = generator.generate_artwork(
        "How Airplanes Fly", custom_image=custom_path, add_text_overlay=True
    )

    assert artwork.size == (1400, 1400)

    # Save artwork
    output_path = tmp_path / "episode_artwork.png"
    generator.manager.save_optimized(artwork, output_path)

    assert output_path.exists()

    # Generate YouTube thumbnail
    thumbnail = generator.generate_youtube_thumbnail(
        "How Airplanes Fly", custom_image=custom_path
    )

    assert thumbnail.size == (1280, 720)


@pytest.mark.integration
def test_character_composition_pipeline(tmp_path):
    """Test character image composition pipeline."""
    # Generate character images using mock provider
    provider = ImageProviderFactory.create_provider("mock")

    oliver_img = provider.generate("Oliver character", style="cartoon")
    hannah_img = provider.generate("Hannah character", style="vibrant")

    oliver_path = tmp_path / "oliver.png"
    hannah_path = tmp_path / "hannah.png"

    oliver_img.save(oliver_path)
    hannah_img.save(hannah_path)

    # Compose characters
    compositor = ImageCompositor()
    composed = compositor.compose_characters(
        [oliver_path, hannah_path], background_color=(255, 255, 255)
    )

    assert composed.size == (1400, 1400)

    # Add title banner
    with_banner = compositor.add_title_banner(
        composed, "Oliver and Hannah", subtitle="Episode 1", position="bottom"
    )

    assert isinstance(with_banner, Image.Image)

    # Save final composition
    output_path = tmp_path / "character_composition.png"
    compositor.manager.save_optimized(with_banner, output_path)

    assert output_path.exists()


@pytest.mark.integration
def test_image_format_conversion_pipeline(tmp_path):
    """Test image format conversion pipeline."""
    manager = ImageManager()

    # Create test image
    img = Image.new("RGB", (1400, 1400), color=(100, 150, 200))
    png_path = tmp_path / "original.png"
    img.save(png_path)

    # Convert to JPEG
    jpeg_path = tmp_path / "converted.jpg"
    manager.convert_format(png_path, jpeg_path, target_format="JPEG")

    assert jpeg_path.exists()

    # Load and verify
    jpeg_img = manager.load_image(jpeg_path)
    assert jpeg_img.format == "JPEG"
    assert jpeg_img.size == (1400, 1400)

    # Convert to WEBP
    webp_path = tmp_path / "converted.webp"
    manager.convert_format(jpeg_path, webp_path, target_format="WEBP")

    assert webp_path.exists()


@pytest.mark.integration
def test_load_actual_character_images():
    """Test loading actual character placeholder images."""
    manager = ImageManager()

    # Test loading Oliver
    oliver_path = Path("data/characters/images/oliver.png")
    if oliver_path.exists():
        oliver_img = manager.load_image(oliver_path)
        assert oliver_img.size == (1024, 1024)

    # Test loading Hannah
    hannah_path = Path("data/characters/images/hannah.png")
    if hannah_path.exists():
        hannah_img = manager.load_image(hannah_path)
        assert hannah_img.size == (1024, 1024)


@pytest.mark.integration
def test_load_default_podcast_logo():
    """Test loading default podcast logo."""
    manager = ImageManager()

    logo_path = Path("data/images/logo.png")
    if logo_path.exists():
        logo_img = manager.load_image(logo_path)
        assert logo_img.size == (1400, 1400)


@pytest.mark.integration
def test_multiple_providers():
    """Test multiple provider types."""
    factory = ImageProviderFactory

    # Test mock provider
    mock = factory.create_provider("mock")
    mock_img = mock.generate("Test prompt")
    assert isinstance(mock_img, Image.Image)
    assert mock.get_cost(1024, 1024) == 0.0

    # Test flux provider (stub)
    flux = factory.create_provider("flux")
    assert flux.get_cost(1024, 1024) == 0.003

    # Test dalle provider (stub)
    dalle = factory.create_provider("dalle")
    assert dalle.get_cost(1024, 1024) == 0.040


@pytest.mark.integration
def test_image_resizing_maintains_quality(tmp_path):
    """Test that resizing maintains acceptable quality."""
    manager = ImageManager()

    # Create high-resolution image
    img = Image.new("RGB", (3000, 3000), color=(255, 100, 50))
    high_res_path = tmp_path / "high_res.png"
    img.save(high_res_path)

    # Resize for podcast
    loaded = manager.load_image(high_res_path)
    podcast_size = manager.resize_for_podcast(loaded)

    assert podcast_size.size == (1400, 1400)

    # Resize for YouTube
    youtube_size = manager.resize_for_youtube(loaded)
    assert youtube_size.size == (1280, 720)

    # Resize for character
    char_size = manager.resize_for_character(loaded)
    assert char_size.size == (1024, 1024)
