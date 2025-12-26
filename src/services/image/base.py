"""Abstract base class for image generation providers."""

from abc import ABC, abstractmethod

from PIL import Image


class BaseImageProvider(ABC):
    """Abstract base class for image generation providers.

    This class defines the interface that all image generation providers
    (Mock, Flux, DALL-E) must implement.
    """

    @abstractmethod
    def generate(
        self,
        prompt: str,
        width: int = 1024,
        height: int = 1024,
        style: str | None = None,
    ) -> Image.Image:
        """Generate image from text prompt.

        Args:
            prompt: Text description of desired image
            width: Image width in pixels
            height: Image height in pixels
            style: Optional style modifier (e.g., "cartoon", "realistic")

        Returns:
            Generated PIL Image

        Raises:
            ValueError: If parameters are invalid
            RuntimeError: If image generation fails
        """
        pass

    @abstractmethod
    def get_cost(self, width: int, height: int) -> float:
        """Calculate cost for image generation.

        Args:
            width: Image width in pixels
            height: Image height in pixels

        Returns:
            Estimated cost in USD
        """
        pass
