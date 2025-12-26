"""Test suite for the Ultimate Kids Curiosity Club."""

import pytest


@pytest.mark.unit
def test_basic_import():
    """Test that the package can be imported."""
    # Test that models can be imported
    from models import Episode, PipelineStage, Show

    # Basic smoke test
    assert Show is not None
    assert Episode is not None
    assert PipelineStage is not None
