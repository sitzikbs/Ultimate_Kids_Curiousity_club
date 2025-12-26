"""Episode artwork generation and management."""

from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

from services.image.manager import ImageManager


class EpisodeArtworkGenerator:
    """Generates and manages episode-specific artwork.

    Handles creation of podcast album art and YouTube thumbnails
    with optional text overlays and custom images.
    """

    def __init__(self, image_manager: ImageManager | None = None):
        """Initialize episode artwork generator.

        Args:
            image_manager: ImageManager instance (creates new one if None)
        """
        self.manager = image_manager or ImageManager()

    def generate_artwork(
        self,
        episode_title: str,
        custom_image: Path | None = None,
        add_text_overlay: bool = False,
        output_path: Path | None = None,
    ) -> Image.Image:
        """Generate episode artwork.

        Args:
            episode_title: Title of the episode
            custom_image: Optional custom image path
            add_text_overlay: Whether to add episode title overlay
            output_path: Optional path to save the artwork

        Returns:
            Generated PIL Image

        Raises:
            FileNotFoundError: If custom_image doesn't exist
        """
        if custom_image:
            # Use custom image
            img = self.manager.load_image(custom_image)
        else:
            # Use default podcast logo
            img = self._load_default_logo()

        # Resize for podcast standards
        img = self.manager.resize_for_podcast(img)

        # Add text overlay if requested
        if add_text_overlay:
            img = self._add_text_overlay(img, episode_title)

        # Save if output path provided
        if output_path:
            self.manager.save_optimized(img, output_path, format="PNG")

        return img

    def generate_youtube_thumbnail(
        self,
        episode_title: str,
        custom_image: Path | None = None,
        output_path: Path | None = None,
    ) -> Image.Image:
        """Generate YouTube thumbnail.

        Args:
            episode_title: Title of the episode
            custom_image: Optional custom image path
            output_path: Optional path to save the thumbnail

        Returns:
            Generated PIL Image in YouTube format (1280x720)

        Raises:
            FileNotFoundError: If custom_image doesn't exist
        """
        if custom_image:
            img = self.manager.load_image(custom_image)
        else:
            img = self._load_default_logo()

        # Resize for YouTube
        img = self.manager.resize_for_youtube(img)

        # Add text overlay (always for YouTube thumbnails)
        img = self._add_text_overlay(img, episode_title, font_size=60)

        # Save if output path provided
        if output_path:
            self.manager.save_optimized(img, output_path, format="PNG")

        return img

    def _load_default_logo(self) -> Image.Image:
        """Load default podcast logo.

        Returns:
            Default logo as PIL Image

        Raises:
            FileNotFoundError: If default logo doesn't exist
        """
        logo_path = Path("data/images/logo.png")

        if not logo_path.exists():
            # Generate placeholder logo if default doesn't exist
            return self._generate_placeholder_logo()

        return self.manager.load_image(logo_path)

    def _generate_placeholder_logo(self) -> Image.Image:
        """Generate placeholder logo when default doesn't exist.

        Returns:
            Placeholder logo as PIL Image
        """
        # Create colorful gradient background
        img = Image.new("RGB", (1400, 1400), color=(50, 100, 200))

        draw = ImageDraw.Draw(img)

        # Add text
        text = "Kids Curiosity\nClub"

        try:
            font = ImageFont.load_default()
        except Exception:
            font = None

        # Center text
        if font:
            bbox = draw.textbbox((0, 0), text, font=font)
            text_width = bbox[2] - bbox[0]
            text_height = bbox[3] - bbox[1]
            position = ((1400 - text_width) // 2, (1400 - text_height) // 2)
        else:
            position = (500, 650)

        draw.text(position, text, fill=(255, 255, 255), font=font)

        return img

    def _add_text_overlay(
        self, image: Image.Image, text: str, font_size: int = 40
    ) -> Image.Image:
        """Add text overlay to image.

        Args:
            image: PIL Image to add text to
            text: Text to overlay
            font_size: Font size for the text

        Returns:
            Image with text overlay
        """
        # Convert to RGBA for transparency support
        if image.mode != "RGBA":
            image = image.convert("RGBA")

        # Create semi-transparent overlay at bottom
        overlay = Image.new("RGBA", image.size, (0, 0, 0, 0))
        overlay_draw = ImageDraw.Draw(overlay)

        # Draw semi-transparent rectangle at bottom
        overlay_height = 150
        overlay_draw.rectangle(
            [(0, image.height - overlay_height), (image.width, image.height)],
            fill=(0, 0, 0, 180),
        )

        # Composite overlay onto image
        image = Image.alpha_composite(image, overlay)

        # Draw text on top
        draw = ImageDraw.Draw(image)

        try:
            font = ImageFont.load_default()
        except Exception:
            font = None

        # Wrap text if too long
        wrapped_text = self._wrap_text_for_overlay(text, max_chars=40)

        # Calculate text position (centered at bottom)
        if font:
            bbox = draw.textbbox((0, 0), wrapped_text, font=font)
            text_width = bbox[2] - bbox[0]
            text_height = bbox[3] - bbox[1]
        else:
            # Estimate
            lines = wrapped_text.split("\n")
            text_width = max(len(line) for line in lines) * 8
            text_height = len(lines) * 15

        position = ((image.width - text_width) // 2, image.height - overlay_height // 2 - text_height // 2)

        draw.text(position, wrapped_text, fill=(255, 255, 255), font=font)

        # Convert back to RGB
        return image.convert("RGB")

    def _wrap_text_for_overlay(self, text: str, max_chars: int = 40) -> str:
        """Wrap text for overlay display.

        Args:
            text: Text to wrap
            max_chars: Maximum characters per line

        Returns:
            Wrapped text with newlines
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

        # Limit to 2 lines
        return "\n".join(lines[:2])
