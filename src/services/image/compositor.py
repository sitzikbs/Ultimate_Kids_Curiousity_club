"""Image composition utilities for combining multiple images."""

from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

from services.image.manager import ImageManager


class ImageCompositor:
    """Composes multiple images into single artwork.

    Supports character layering, background templates, and text overlays
    for creating episode thumbnails and promotional artwork.
    """

    def __init__(self, image_manager: ImageManager | None = None):
        """Initialize image compositor.

        Args:
            image_manager: ImageManager instance (creates new one if None)
        """
        self.manager = image_manager or ImageManager()

    def compose_characters(
        self,
        character_images: list[Path],
        background_color: tuple[int, int, int] = (255, 255, 255),
        output_size: tuple[int, int] = (1400, 1400),
    ) -> Image.Image:
        """Compose multiple character images side-by-side.

        Args:
            character_images: List of paths to character images
            background_color: RGB background color
            output_size: Size of output image

        Returns:
            Composed PIL Image with all characters

        Raises:
            FileNotFoundError: If any character image doesn't exist
            ValueError: If character_images list is empty
        """
        if not character_images:
            raise ValueError("character_images list cannot be empty")

        # Create background
        composite = Image.new("RGB", output_size, color=background_color)

        # Calculate positions for characters (side-by-side)
        num_chars = len(character_images)
        char_width = output_size[0] // num_chars
        char_height = output_size[1]

        for i, char_path in enumerate(character_images):
            # Load character image
            char_img = self.manager.load_image(char_path)

            # Resize to fit allocated space (maintain aspect ratio)
            char_img = self._resize_with_aspect_ratio(
                char_img, max_width=char_width, max_height=char_height
            )

            # Calculate position (center in allocated space)
            x_pos = i * char_width + (char_width - char_img.width) // 2
            y_pos = (char_height - char_img.height) // 2

            # Paste character (handle transparency if present)
            if char_img.mode == "RGBA":
                composite.paste(char_img, (x_pos, y_pos), mask=char_img)
            else:
                composite.paste(char_img, (x_pos, y_pos))

        return composite

    def add_background_template(
        self, foreground: Image.Image, template_path: Path
    ) -> Image.Image:
        """Apply background template to foreground image.

        Args:
            foreground: Foreground PIL Image
            template_path: Path to background template

        Returns:
            Composed image with background

        Raises:
            FileNotFoundError: If template doesn't exist
        """
        # Load background template
        background = self.manager.load_image(template_path)

        # Resize background to match foreground
        background = background.resize(foreground.size, Image.Resampling.LANCZOS)

        # Convert to RGBA for alpha compositing
        if background.mode != "RGBA":
            background = background.convert("RGBA")
        if foreground.mode != "RGBA":
            foreground = foreground.convert("RGBA")

        # Composite foreground over background
        result = Image.alpha_composite(background, foreground)

        return result.convert("RGB")

    def add_title_banner(
        self,
        image: Image.Image,
        title: str,
        subtitle: str | None = None,
        position: str = "top",
    ) -> Image.Image:
        """Add title banner to image.

        Args:
            image: PIL Image to add banner to
            title: Main title text
            subtitle: Optional subtitle text
            position: Banner position ("top" or "bottom")

        Returns:
            Image with title banner

        Raises:
            ValueError: If position is not "top" or "bottom"
        """
        if position not in ["top", "bottom"]:
            raise ValueError("position must be 'top' or 'bottom'")

        # Convert to RGBA
        if image.mode != "RGBA":
            image = image.convert("RGBA")

        # Create banner overlay
        banner_height = 200 if subtitle else 150
        overlay = Image.new("RGBA", image.size, (0, 0, 0, 0))
        overlay_draw = ImageDraw.Draw(overlay)

        # Calculate banner position
        if position == "top":
            banner_y = 0
            text_y = banner_height // 3
        else:
            banner_y = image.height - banner_height
            text_y = image.height - banner_height + banner_height // 3

        # Draw semi-transparent banner
        overlay_draw.rectangle(
            [(0, banner_y), (image.width, banner_y + banner_height)],
            fill=(0, 0, 0, 200),
        )

        # Composite overlay
        image = Image.alpha_composite(image, overlay)

        # Draw text
        draw = ImageDraw.Draw(image)

        try:
            font = ImageFont.load_default()
        except Exception:
            font = None

        # Draw title
        if font:
            bbox = draw.textbbox((0, 0), title, font=font)
            text_width = bbox[2] - bbox[0]
        else:
            text_width = len(title) * 10

        title_x = (image.width - text_width) // 2
        draw.text((title_x, text_y), title, fill=(255, 255, 255), font=font)

        # Draw subtitle if provided
        if subtitle:
            if font:
                bbox = draw.textbbox((0, 0), subtitle, font=font)
                subtitle_width = bbox[2] - bbox[0]
            else:
                subtitle_width = len(subtitle) * 8

            subtitle_x = (image.width - subtitle_width) // 2
            subtitle_y = text_y + 40
            draw.text((subtitle_x, subtitle_y), subtitle, fill=(200, 200, 200), font=font)

        return image.convert("RGB")

    def _resize_with_aspect_ratio(
        self, image: Image.Image, max_width: int, max_height: int
    ) -> Image.Image:
        """Resize image maintaining aspect ratio.

        Args:
            image: PIL Image to resize
            max_width: Maximum width
            max_height: Maximum height

        Returns:
            Resized PIL Image
        """
        # Calculate aspect ratio
        width_ratio = max_width / image.width
        height_ratio = max_height / image.height

        # Use smaller ratio to ensure image fits
        scale = min(width_ratio, height_ratio)

        new_width = int(image.width * scale)
        new_height = int(image.height * scale)

        return image.resize((new_width, new_height), Image.Resampling.LANCZOS)
