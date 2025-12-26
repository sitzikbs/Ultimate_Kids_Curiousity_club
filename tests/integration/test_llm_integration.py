"""Integration tests for LLM service with mock providers."""

import pytest


@pytest.mark.integration
def test_llm_ideation_integration(mock_llm_service, mock_mode_settings):
    """Test LLM ideation flow with mock service.

    Tests the complete ideation workflow from user topic to refined
    learning objectives using mock LLM responses.
    """
    pytest.skip("Integration test - implement when LLM service is available")

    # Example implementation:
    # result = mock_llm_service.refine_topic(
    #     user_topic="How do volcanoes erupt?",
    #     duration=15
    # )
    #
    # assert "refined_topic" in result
    # assert "learning_objectives" in result
    # assert "key_points" in result
    # assert len(result["learning_objectives"]) >= 3
    # assert len(result["key_points"]) >= 5


@pytest.mark.integration
def test_llm_scripting_integration(mock_llm_service, mock_mode_settings):
    """Test LLM script generation with mock service.

    Tests the complete scripting workflow from ideation output to
    full episode script with dialogue segments.
    """
    pytest.skip("Integration test - implement when LLM service is available")


@pytest.mark.integration
def test_llm_ideation_to_scripting_pipeline(mock_llm_service, mock_mode_settings):
    """Test complete ideation → scripting pipeline.

    Tests the full flow from user topic through ideation and scripting
    to ensure data flows correctly between stages.
    """
    pytest.skip("Integration test - implement when LLM service is available")
