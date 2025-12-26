"""DALL-E image provider (future implementation)."""

from PIL import Image

from services.image.base import BaseImageProvider


class DALLEProvider(BaseImageProvider):
    """DALL-E image generation provider (stub for future implementation).

    This provider will integrate with OpenAI's DALL-E API for
    image generation. Currently returns a NotImplementedError.
    """

    def __init__(self, api_key: str | None = None):
        """Initialize DALL-E provider.

        Args:
            api_key: OpenAI API key (optional for future use)
        """
        self.api_key = api_key

    def generate(
        self,
        prompt: str,
        width: int = 1024,
        height: int = 1024,
        style: str | None = None,
    ) -> Image.Image:
        """Generate image using DALL-E API.

        Args:
            prompt: Text description of desired image
            width: Image width in pixels (DALL-E supports 1024x1024, 1792x1024, 1024x1792)
            height: Image height in pixels
            style: Optional style modifier

        Returns:
            Generated PIL Image

        Raises:
            NotImplementedError: DALL-E integration not yet implemented
        """
        raise NotImplementedError(
            "DALL-E provider is a stub for future implementation. "
            "Use MockImageProvider for testing."
        )

    def get_cost(self, width: int, height: int) -> float:
        """Calculate cost for DALL-E image generation.

        Args:
            width: Image width in pixels
            height: Image height in pixels

        Returns:
            Estimated cost in USD

        Note:
            Cost estimates will be implemented when DALL-E integration is added.
            DALL-E 3 costs: $0.040 for 1024x1024, $0.080 for 1024x1792 or 1792x1024
        """
        # Placeholder cost estimate based on standard 1024x1024
        if width <= 1024 and height <= 1024:
            return 0.040
        else:
            return 0.080
