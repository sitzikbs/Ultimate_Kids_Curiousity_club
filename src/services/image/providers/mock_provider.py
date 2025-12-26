"""Mock image provider for testing and placeholder generation."""

from PIL import Image, ImageDraw, ImageFont

from services.image.base import BaseImageProvider


class MockImageProvider(BaseImageProvider):
    """Mock provider that generates placeholder images.

    This provider is used for testing and when no real image generation
    service is available. It creates simple colored images with text overlays.
    """

    def generate(
        self,
        prompt: str,
        width: int = 1024,
        height: int = 1024,
        style: str | None = None,
    ) -> Image.Image:
        """Generate simple placeholder image with prompt text.

        Args:
            prompt: Text description to display on image
            width: Image width in pixels
            height: Image height in pixels
            style: Optional style modifier (affects background color)

        Returns:
            Generated PIL Image with colored background and text
        """
        # Choose background color based on style
        color = self._get_color_for_style(style)

        # Create solid color background
        img = Image.new("RGB", (width, height), color=color)

        # Add text overlay
        draw = ImageDraw.Draw(img)

        # Truncate prompt to fit
        text_lines = self._wrap_text(prompt, max_chars=50)
        text = "MOCK IMAGE\n" + "\n".join(text_lines)

        # Try to use default font
        try:
            # Use a larger font size for better visibility
            font = ImageFont.load_default()
        except Exception:
            font = None

        # Calculate text position (centered)
        if font:
            # Get text bounding box
            bbox = draw.textbbox((0, 0), text, font=font)
            text_width = bbox[2] - bbox[0]
            text_height = bbox[3] - bbox[1]
        else:
            # Estimate text size
            lines = text.split("\n")
            text_width = max(len(line) for line in lines) * 6
            text_height = len(lines) * 10

        position = ((width - text_width) // 2, (height - text_height) // 2)

        # Draw text
        draw.text(position, text, fill=(255, 255, 255), font=font)

        return img

    def get_cost(self, width: int, height: int) -> float:
        """Calculate cost for mock image generation.

        Mock images are always free.

        Args:
            width: Image width in pixels (unused)
            height: Image height in pixels (unused)

        Returns:
            0.0 (mock generation is free)
        """
        return 0.0

    def _get_color_for_style(self, style: str | None) -> tuple[int, int, int]:
        """Get background color based on style.

        Args:
            style: Style modifier (cartoon, realistic, etc.)

        Returns:
            RGB color tuple
        """
        color_map = {
            "cartoon": (100, 150, 250),  # Light blue
            "realistic": (80, 120, 100),  # Muted green
            "vibrant": (250, 100, 150),  # Pink
            "dark": (50, 50, 50),  # Dark gray
        }
        return color_map.get(style, (100, 150, 200))  # Default blue

    def _wrap_text(self, text: str, max_chars: int = 50) -> list[str]:
        """Wrap text into multiple lines.

        Args:
            text: Text to wrap
            max_chars: Maximum characters per line

        Returns:
            List of text lines
        """
        words = text.split()
        lines = []
        current_line = []
        current_length = 0

        for word in words:
            if current_length + len(word) + 1 <= max_chars:
                current_line.append(word)
                current_length += len(word) + 1
            else:
                if current_line:
                    lines.append(" ".join(current_line))
                current_line = [word]
                current_length = len(word)

        if current_line:
            lines.append(" ".join(current_line))

        # Limit to first 3 lines
        return lines[:3]
