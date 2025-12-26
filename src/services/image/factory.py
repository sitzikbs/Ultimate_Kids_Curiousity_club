"""Factory for creating image provider instances."""

from services.image.base import BaseImageProvider
from services.image.providers.dalle_provider import DALLEProvider
from services.image.providers.flux_provider import FluxProvider
from services.image.providers.mock_provider import MockImageProvider


class ImageProviderFactory:
    """Factory for creating image provider instances.

    Supports multiple providers: mock, flux, dalle.
    """

    @staticmethod
    def create_provider(
        provider_type: str = "mock", api_key: str | None = None
    ) -> BaseImageProvider:
        """Create an image provider instance.

        Args:
            provider_type: Type of provider ("mock", "flux", "dalle")
            api_key: API key for external providers (optional)

        Returns:
            Instance of requested image provider

        Raises:
            ValueError: If provider_type is not recognized
        """
        provider_type = provider_type.lower()

        if provider_type == "mock":
            return MockImageProvider()
        elif provider_type == "flux":
            return FluxProvider(api_key=api_key)
        elif provider_type == "dalle":
            return DALLEProvider(api_key=api_key)
        else:
            raise ValueError(
                f"Unknown provider type: {provider_type}. "
                f"Supported types: mock, flux, dalle"
            )

    @staticmethod
    def get_available_providers() -> list[str]:
        """Get list of available provider types.

        Returns:
            List of provider type names
        """
        return ["mock", "flux", "dalle"]
