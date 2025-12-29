"""Unit tests for ImageProviderFactory."""

import pytest

from services.image.factory import ImageProviderFactory
from services.image.providers.dalle_provider import DALLEProvider
from services.image.providers.flux_provider import FluxProvider
from services.image.providers.mock_provider import MockImageProvider


@pytest.mark.unit
def test_factory_create_mock_provider():
    """Test creating mock provider through factory."""
    provider = ImageProviderFactory.create_provider("mock")

    assert isinstance(provider, MockImageProvider)


@pytest.mark.unit
def test_factory_create_flux_provider():
    """Test creating Flux provider through factory."""
    provider = ImageProviderFactory.create_provider("flux")

    assert isinstance(provider, FluxProvider)


@pytest.mark.unit
def test_factory_create_dalle_provider():
    """Test creating DALL-E provider through factory."""
    provider = ImageProviderFactory.create_provider("dalle")

    assert isinstance(provider, DALLEProvider)


@pytest.mark.unit
def test_factory_create_with_api_key():
    """Test creating provider with API key."""
    provider = ImageProviderFactory.create_provider("flux", api_key="test_key")

    assert isinstance(provider, FluxProvider)
    assert provider.api_key == "test_key"


@pytest.mark.unit
def test_factory_case_insensitive():
    """Test that factory is case-insensitive."""
    provider1 = ImageProviderFactory.create_provider("MOCK")
    provider2 = ImageProviderFactory.create_provider("Mock")
    provider3 = ImageProviderFactory.create_provider("mock")

    assert isinstance(provider1, MockImageProvider)
    assert isinstance(provider2, MockImageProvider)
    assert isinstance(provider3, MockImageProvider)


@pytest.mark.unit
def test_factory_invalid_provider():
    """Test that invalid provider type raises ValueError."""
    with pytest.raises(ValueError):
        ImageProviderFactory.create_provider("invalid")


@pytest.mark.unit
def test_factory_get_available_providers():
    """Test getting list of available providers."""
    providers = ImageProviderFactory.get_available_providers()

    assert "mock" in providers
    assert "flux" in providers
    assert "dalle" in providers
    assert len(providers) == 3


@pytest.mark.unit
def test_flux_provider_not_implemented():
    """Test that Flux provider raises NotImplementedError."""
    provider = ImageProviderFactory.create_provider("flux")

    with pytest.raises(NotImplementedError):
        provider.generate("test prompt")


@pytest.mark.unit
def test_dalle_provider_not_implemented():
    """Test that DALL-E provider raises NotImplementedError."""
    provider = ImageProviderFactory.create_provider("dalle")

    with pytest.raises(NotImplementedError):
        provider.generate("test prompt")


@pytest.mark.unit
def test_flux_provider_cost():
    """Test Flux provider cost estimation."""
    provider = ImageProviderFactory.create_provider("flux")

    cost = provider.get_cost(1024, 1024)
    assert cost == 0.003


@pytest.mark.unit
def test_dalle_provider_cost():
    """Test DALL-E provider cost estimation."""
    provider = ImageProviderFactory.create_provider("dalle")

    cost_standard = provider.get_cost(1024, 1024)
    cost_large = provider.get_cost(1792, 1024)

    assert cost_standard == 0.040
    assert cost_large == 0.080
