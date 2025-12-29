"""Unit tests for MockImageProvider."""

import pytest
from PIL import Image

from services.image.providers.mock_provider import MockImageProvider


@pytest.fixture
def mock_provider():
    """Create MockImageProvider instance."""
    return MockImageProvider()


@pytest.mark.unit
def test_mock_provider_generate_basic(mock_provider):
    """Test basic image generation."""
    img = mock_provider.generate("Test prompt", width=512, height=512)

    assert isinstance(img, Image.Image)
    assert img.size == (512, 512)
    assert img.mode == "RGB"


@pytest.mark.unit
def test_mock_provider_generate_default_size(mock_provider):
    """Test image generation with default size."""
    img = mock_provider.generate("Test prompt")

    assert img.size == (1024, 1024)


@pytest.mark.unit
def test_mock_provider_generate_with_style(mock_provider):
    """Test image generation with different styles."""
    styles = ["cartoon", "realistic", "vibrant", "dark"]

    for style in styles:
        img = mock_provider.generate(f"Test {style}", style=style)
        assert isinstance(img, Image.Image)
        assert img.size == (1024, 1024)


@pytest.mark.unit
def test_mock_provider_generate_custom_size(mock_provider):
    """Test image generation with custom dimensions."""
    img = mock_provider.generate("Custom size", width=800, height=600)

    assert img.size == (800, 600)


@pytest.mark.unit
def test_mock_provider_get_cost(mock_provider):
    """Test that mock provider cost is always zero."""
    assert mock_provider.get_cost(1024, 1024) == 0.0
    assert mock_provider.get_cost(512, 512) == 0.0
    assert mock_provider.get_cost(2048, 2048) == 0.0


@pytest.mark.unit
def test_mock_provider_long_prompt(mock_provider):
    """Test image generation with long prompt."""
    long_prompt = "This is a very long prompt that should be truncated " * 10
    img = mock_provider.generate(long_prompt)

    assert isinstance(img, Image.Image)


@pytest.mark.unit
def test_mock_provider_wrap_text(mock_provider):
    """Test text wrapping functionality."""
    text = "This is a very long text that needs to be wrapped into multiple lines"
    lines = mock_provider._wrap_text(text, max_chars=30)

    assert len(lines) <= 3
    for line in lines:
        assert len(line) <= 30


@pytest.mark.unit
def test_mock_provider_color_for_style(mock_provider):
    """Test color selection based on style."""
    color_cartoon = mock_provider._get_color_for_style("cartoon")
    color_dark = mock_provider._get_color_for_style("dark")
    color_default = mock_provider._get_color_for_style(None)

    assert color_cartoon != color_dark
    assert len(color_cartoon) == 3  # RGB tuple
    assert len(color_dark) == 3
    assert len(color_default) == 3
