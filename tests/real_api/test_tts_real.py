"""Real API tests for Text-to-Speech services.

These tests call real TTS API endpoints and incur costs.
Run with: pytest -m real_api
"""

import pytest

from tests.test_helpers.cost_tracker import CostTracker


@pytest.mark.real_api
def test_elevenlabs_tts_real(
    real_api_settings: dict[str, bool], cost_tracker: CostTracker
) -> None:
    """Test real ElevenLabs API for speech synthesis.

    Expected cost: ~$0.10-0.30 per request (depends on character count)

    Note: Requires ELEVENLABS_API_KEY environment variable to be set.
    """
    pytest.skip("Real API test - implement when TTS service is available")

    # Example implementation:
    # from src.services.tts import create_tts_service
    #
    # tts = create_tts_service(real_api_settings)
    # result = tts.synthesize_speech(
    #     text="Hello, welcome to our show!",
    #     voice_id="narrator",
    #     output_path="/tmp/test_audio.mp3"
    # )
    #
    # # Validate
    # assert result["audio_path"].exists()
    # assert result["duration_seconds"] > 0
    #
    # # Track cost
    # cost_tracker.record_call(
    #     service="elevenlabs",
    #     operation="tts_synthesis",
    #     cost_usd=0.15,
    #     characters=len("Hello, welcome to our show!")
    # )


@pytest.mark.real_api
def test_openai_tts_real(
    real_api_settings: dict[str, bool], cost_tracker: CostTracker
) -> None:
    """Test real OpenAI TTS API for speech synthesis.

    Expected cost: ~$0.015 per 1000 characters

    Note: Requires OPENAI_API_KEY environment variable to be set.
    """
    pytest.skip("Real API test - implement when TTS service is available")
