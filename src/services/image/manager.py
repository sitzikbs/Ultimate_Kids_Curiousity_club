"""Image Manager for loading, validating, and processing images."""

from pathlib import Path

from PIL import Image


class ImageManager:
    """Manages image loading, validation, resizing, and optimization.

    Handles core image operations for podcast album art, YouTube thumbnails,
    and character reference images. Supports PNG, JPEG, and WEBP formats.
    """

    # Standard image sizes
    PODCAST_ART_SIZE = (1400, 1400)
    PODCAST_ART_LARGE_SIZE = (3000, 3000)
    YOUTUBE_THUMBNAIL_SIZE = (1280, 720)
    CHARACTER_IMAGE_SIZE = (1024, 1024)

    # File size constraints
    MAX_FILE_SIZE_KB = 512

    # Supported formats
    SUPPORTED_FORMATS = ["PNG", "JPEG", "WEBP"]

    def load_image(self, path: Path) -> Image.Image:
        """Load and validate image file.

        Args:
            path: Path to the image file

        Returns:
            Loaded PIL Image

        Raises:
            FileNotFoundError: If image file doesn't exist
            ValueError: If image format is not supported
        """
        if not path.exists():
            raise FileNotFoundError(f"Image not found: {path}")

        img = Image.open(path)

        # Validate format
        if img.format not in self.SUPPORTED_FORMATS:
            raise ValueError(
                f"Unsupported format: {img.format}. "
                f"Supported formats: {', '.join(self.SUPPORTED_FORMATS)}"
            )

        return img

    def validate_dimensions(
        self, image: Image.Image, min_width: int = 1400, min_height: int = 1400
    ) -> bool:
        """Validate image meets minimum dimension requirements.

        Args:
            image: PIL Image to validate
            min_width: Minimum width in pixels
            min_height: Minimum height in pixels

        Returns:
            True if image meets minimum dimensions
        """
        width, height = image.size
        return width >= min_width and height >= min_height

    def resize_for_podcast(
        self, image: Image.Image, large: bool = False
    ) -> Image.Image:
        """Resize image to podcast album art standard.

        Args:
            image: PIL Image to resize
            large: If True, use 3000x3000 size, otherwise 1400x1400

        Returns:
            Resized PIL Image
        """
        size = self.PODCAST_ART_LARGE_SIZE if large else self.PODCAST_ART_SIZE
        return image.resize(size, Image.Resampling.LANCZOS)

    def resize_for_youtube(self, image: Image.Image) -> Image.Image:
        """Resize image to YouTube thumbnail standard (1280x720).

        Args:
            image: PIL Image to resize

        Returns:
            Resized PIL Image
        """
        return image.resize(self.YOUTUBE_THUMBNAIL_SIZE, Image.Resampling.LANCZOS)

    def resize_for_character(self, image: Image.Image) -> Image.Image:
        """Resize image to character reference standard (1024x1024).

        Args:
            image: PIL Image to resize

        Returns:
            Resized PIL Image
        """
        return image.resize(self.CHARACTER_IMAGE_SIZE, Image.Resampling.LANCZOS)

    def save_optimized(
        self, image: Image.Image, output_path: Path, format: str = "PNG"
    ) -> None:
        """Save image optimized for size.

        If the PNG file exceeds MAX_FILE_SIZE_KB, it will be saved as JPEG
        with quality optimization.

        Args:
            image: PIL Image to save
            output_path: Path where image should be saved
            format: Image format (PNG, JPEG, or WEBP)

        Raises:
            ValueError: If format is not supported
        """
        if format.upper() not in self.SUPPORTED_FORMATS:
            raise ValueError(f"Unsupported save format: {format}")

        # Ensure output directory exists
        output_path.parent.mkdir(parents=True, exist_ok=True)

        # Convert RGBA to RGB for JPEG
        if format.upper() == "JPEG" and image.mode == "RGBA":
            # Create white background
            rgb_image = Image.new("RGB", image.size, (255, 255, 255))
            rgb_image.paste(image, mask=image.split()[3])  # Use alpha channel as mask
            image = rgb_image

        # Save based on format
        if format.upper() == "PNG":
            image.save(output_path, format="PNG", optimize=True)

            # Check file size
            size_kb = output_path.stat().st_size / 1024
            if size_kb > self.MAX_FILE_SIZE_KB:
                # Reduce quality by saving as JPEG instead
                image.save(output_path, format="JPEG", quality=85, optimize=True)
        elif format.upper() == "JPEG":
            image.save(output_path, format="JPEG", quality=85, optimize=True)
        elif format.upper() == "WEBP":
            image.save(output_path, format="WEBP", quality=85, optimize=True)

    def convert_format(
        self, input_path: Path, output_path: Path, target_format: str = "PNG"
    ) -> None:
        """Convert image from one format to another.

        Args:
            input_path: Path to source image
            output_path: Path for converted image
            target_format: Target format (PNG, JPEG, WEBP)

        Raises:
            ValueError: If target format is not supported
            FileNotFoundError: If input image doesn't exist
        """
        if target_format.upper() not in self.SUPPORTED_FORMATS:
            raise ValueError(f"Unsupported target format: {target_format}")

        image = self.load_image(input_path)
        self.save_optimized(image, output_path, format=target_format)
