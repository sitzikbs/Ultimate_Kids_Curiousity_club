"""Integration tests for TTS service with mock providers."""

from pathlib import Path

import pytest

from services.tts.cost_tracker import TTSCostTracker
from services.tts.factory import TTSProviderFactory
from services.tts.synthesis_service import AudioSynthesisService
from services.tts.voice_manager import VoiceManager


@pytest.mark.integration
def test_tts_single_segment(tmp_path: Path):
    """Test TTS synthesis for a single dialogue segment.

    Tests converting a single text segment to audio using mock TTS service.
    """
    # Create mock provider
    provider = TTSProviderFactory.create_provider("mock", fast_mode=False)

    # Create synthesis service
    service = AudioSynthesisService(
        tts_provider=provider,
        output_dir=tmp_path / "audio",
    )

    # Synthesize a segment
    voice_config = {
        "voice_id": "mock_narrator",
        "stability": 0.5,
        "similarity_boost": 0.75,
    }

    result = service.synthesize_segment(
        text="Welcome to our science adventure! Today we're exploring gravity.",
        character_id="narrator",
        voice_config=voice_config,
        segment_number=1,
    )

    assert result.audio_path.exists()
    assert result.duration > 0
    assert result.characters > 0


@pytest.mark.integration
def test_tts_multiple_segments(tmp_path: Path, all_characters):
    """Test TTS synthesis for multiple segments in sequence.

    Tests batch processing of multiple dialogue segments to ensure
    consistent audio generation.
    """
    # Create mock provider
    provider = TTSProviderFactory.create_provider("mock", fast_mode=False)

    # Create synthesis service
    service = AudioSynthesisService(
        tts_provider=provider,
        output_dir=tmp_path / "audio",
    )

    # Prepare segments
    segments = []
    for idx, character in enumerate(all_characters[:2]):  # Use first 2 characters
        segments.append(
            {
                "text": f"This is segment {idx + 1} spoken by {character['name']}.",
                "character_id": character["id"],
                "voice_config": character["voice_config"],
                "segment_number": idx + 1,
            }
        )

    # Synthesize batch
    results = service.synthesize_batch(segments, add_padding=True)

    # Should have segments + padding
    assert len(results) == 3  # 2 segments + 1 padding
    assert all(r.audio_path.exists() for r in results)


@pytest.mark.integration
def test_tts_different_voices(tmp_path: Path, all_characters):
    """Test TTS with different character voices.

    Tests that the TTS service correctly handles different voice
    configurations for multiple characters.
    """
    # Create mock provider
    provider = TTSProviderFactory.create_provider("mock")

    # Create synthesis service
    service = AudioSynthesisService(
        tts_provider=provider,
        output_dir=tmp_path / "audio",
    )

    # Synthesize for each character
    results = []
    for idx, character in enumerate(all_characters):
        result = service.synthesize_segment(
            text=f"Hello, I'm {character['name']}!",
            character_id=character["id"],
            voice_config=character["voice_config"],
            segment_number=idx + 1,
        )
        results.append(result)

    assert len(results) == len(all_characters)
    assert all(r.audio_path.exists() for r in results)

    # Check that different voice_ids were used
    voice_ids = [
        r.audio_path.stem.split("_")[-1] for r in results
    ]  # Extract character IDs
    assert len(set(voice_ids)) == len(all_characters)  # All unique


@pytest.mark.integration
def test_tts_provider_switching(tmp_path: Path):
    """Test switching between different TTS providers.

    Tests that we can switch providers and maintain consistent interface.
    """
    providers = ["mock"]  # Only test mock by default

    for provider_type in providers:
        provider = TTSProviderFactory.create_provider(provider_type, fast_mode=True)
        service = AudioSynthesisService(
            tts_provider=provider,
            output_dir=tmp_path / provider_type,
        )

        voice_config = {"voice_id": "mock_narrator"}

        result = service.synthesize_segment(
            text="Testing provider switching.",
            character_id="narrator",
            voice_config=voice_config,
            segment_number=1,
        )

        assert result.audio_path.exists()


@pytest.mark.integration
def test_tts_with_cost_tracking(tmp_path: Path):
    """Test TTS synthesis with cost tracking."""
    # Create provider and tracker
    provider = TTSProviderFactory.create_provider("mock")
    tracker = TTSCostTracker(budget_threshold=1.0)

    # Create service
    service = AudioSynthesisService(
        tts_provider=provider,
        output_dir=tmp_path / "audio",
    )

    # Synthesize segments
    voice_config = {"voice_id": "mock_narrator"}

    segments = [
        {
            "text": f"Segment {i}: This is a test segment for cost tracking.",
            "character_id": "narrator",
            "voice_config": voice_config,
            "segment_number": i,
        }
        for i in range(1, 4)
    ]

    results = service.synthesize_batch(segments, add_padding=False)

    # Track costs
    for result in results:
        cost = provider.get_cost(result.characters)
        tracker.track_request(
            provider="mock",
            voice_id="mock_narrator",
            characters=result.characters,
            cost=cost,
            segment_id=f"segment_{result.segment_number}",
        )

    # Verify tracking
    assert tracker.get_total_characters() > 0
    assert tracker.get_total_cost() == 0.0  # Mock is free

    # Save cost report
    cost_file = tmp_path / "costs.json"
    tracker.save_to_file(cost_file)
    assert cost_file.exists()


@pytest.mark.integration
def test_tts_voice_validation(tmp_path: Path):
    """Test voice validation and preview functionality."""
    # Create provider and voice manager
    provider = TTSProviderFactory.create_provider("mock")
    voice_manager = VoiceManager(
        tts_provider=provider,
        sample_dir=tmp_path / "samples",
    )

    # Test voice validation
    assert voice_manager.validate_voice_id("mock_narrator") is True
    assert voice_manager.validate_voice_id("invalid_voice") is False

    # Test voice config validation
    valid_config = {
        "voice_id": "mock_narrator",
        "stability": 0.5,
        "similarity_boost": 0.75,
    }
    is_valid, error = voice_manager.validate_voice_config(valid_config)
    assert is_valid is True

    # Test voice preview
    preview_path = voice_manager.preview_voice(
        voice_id="mock_narrator",
        sample_text="This is a voice preview test.",
    )
    assert preview_path.exists()


@pytest.mark.integration
def test_tts_error_handling(tmp_path: Path):
    """Test error handling for invalid voice IDs and parameters."""
    provider = TTSProviderFactory.create_provider("mock")
    service = AudioSynthesisService(
        tts_provider=provider,
        output_dir=tmp_path / "audio",
    )

    # Test with invalid voice config (should still work with mock)
    voice_config = {
        "voice_id": "nonexistent_voice",  # Mock doesn't validate
        "stability": 0.5,
    }

    result = service.synthesize_segment(
        text="Testing error handling.",
        character_id="test",
        voice_config=voice_config,
        segment_number=1,
    )

    # Mock provider is lenient, so this should still work
    assert result.audio_path.exists()
