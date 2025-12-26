"""Flux image provider (future implementation)."""

from PIL import Image

from services.image.base import BaseImageProvider


class FluxProvider(BaseImageProvider):
    """Flux image generation provider (stub for future implementation).

    This provider will integrate with Replicate's Flux API for
    high-quality image generation. Currently returns a NotImplementedError.
    """

    def __init__(self, api_key: str | None = None):
        """Initialize Flux provider.

        Args:
            api_key: Replicate API key (optional for future use)
        """
        self.api_key = api_key

    def generate(
        self,
        prompt: str,
        width: int = 1024,
        height: int = 1024,
        style: str | None = None,
    ) -> Image.Image:
        """Generate image using Flux API.

        Args:
            prompt: Text description of desired image
            width: Image width in pixels
            height: Image height in pixels
            style: Optional style modifier

        Returns:
            Generated PIL Image

        Raises:
            NotImplementedError: Flux integration not yet implemented
        """
        raise NotImplementedError(
            "Flux provider is a stub for future implementation. "
            "Use MockImageProvider for testing."
        )

    def get_cost(self, width: int, height: int) -> float:
        """Calculate cost for Flux image generation.

        Args:
            width: Image width in pixels
            height: Image height in pixels

        Returns:
            Estimated cost in USD

        Note:
            Cost estimates will be implemented when Flux integration is added.
            Typical Flux costs are approximately $0.003 per image.
        """
        # Placeholder cost estimate
        return 0.003
