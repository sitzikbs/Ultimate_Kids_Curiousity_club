"""Real API tests for LLM services.

These tests call real API endpoints and incur costs.
Run with: pytest -m real_api
"""

import pytest

from tests.utils.cost_tracker import CostTracker


@pytest.fixture
def cost_tracker() -> CostTracker:
    """Cost tracker fixture for real API tests.

    Yields a cost tracker that monitors API costs and enforces budget limits.
    Prints a summary at the end of the test session.
    """
    tracker = CostTracker()
    tracker.set_budget_limit(10.0)  # $10 budget per test session
    yield tracker

    # Print summary after tests
    tracker.print_summary()

    # Fail if budget exceeded
    within_budget, _ = tracker.check_budget()
    if not within_budget:
        pytest.fail(
            f"Test suite exceeded budget: ${tracker.get_total_cost():.2f} > "
            f"${tracker._budget_limit:.2f}"
        )


@pytest.mark.real_api
def test_openai_ideation_real(
    real_api_settings: dict[str, bool], cost_tracker: CostTracker
) -> None:
    """Test real OpenAI API for topic ideation.

    This test makes a real API call to OpenAI and tracks the cost.
    Expected cost: ~$0.01-0.05 per call

    Note: Requires OPENAI_API_KEY environment variable to be set.
    """
    pytest.skip("Real API test - implement when LLM service is available")

    # Example implementation:
    # from src.services.llm import create_llm_service
    #
    # assert not real_api_settings["USE_MOCK_SERVICES"]
    #
    # llm = create_llm_service(real_api_settings)
    # ideation = llm.refine_topic(
    #     user_topic="How do airplanes fly?",
    #     duration=10
    # )
    #
    # # Validate response
    # assert ideation["refined_topic"]
    # assert len(ideation["learning_objectives"]) >= 3
    # assert len(ideation["key_points"]) >= 5
    #
    # # Track cost (example)
    # cost_tracker.record_call(
    #     service="openai",
    #     operation="completion",
    #     cost_usd=0.02,
    #     tokens_used=500
    # )


@pytest.mark.real_api
def test_anthropic_scripting_real(
    real_api_settings: dict[str, bool], cost_tracker: CostTracker
) -> None:
    """Test real Anthropic API for script generation.

    Expected cost: ~$0.05-0.15 per call

    Note: Requires ANTHROPIC_API_KEY environment variable to be set.
    """
    pytest.skip("Real API test - implement when LLM service is available")


@pytest.mark.real_api
@pytest.mark.slow
def test_full_pipeline_real(
    real_api_settings: dict[str, bool], cost_tracker: CostTracker
) -> None:
    """Test full episode production pipeline with real APIs.

    This is an expensive test that runs the complete pipeline.
    Expected cost: ~$1.00-5.00 per episode

    Only run this test when explicitly needed.
    """
    pytest.skip("Real API test - implement when full pipeline is available")
