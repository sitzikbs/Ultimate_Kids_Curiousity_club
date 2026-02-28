"""Service factory for CLI commands.

Centralises the wiring of all service dependencies so CLI commands
can obtain a fully-configured PipelineOrchestrator or ApprovalWorkflow
with a single call.
"""

from config import get_settings
from modules.episode_storage import EpisodeStorage
from modules.prompts.enhancer import PromptEnhancer
from modules.show_blueprint_manager import ShowBlueprintManager
from orchestrator.approval import ApprovalWorkflow
from orchestrator.events import EventCallback
from orchestrator.pipeline import PipelineOrchestrator
from services.audio.mixer import AudioMixer
from services.llm.cost_tracker import CostTracker
from services.llm.factory import LLMProviderFactory
from services.llm.ideation_service import IdeationService
from services.llm.outline_service import OutlineService
from services.llm.script_generation_service import ScriptGenerationService
from services.llm.segment_generation_service import SegmentGenerationService
from services.tts.factory import TTSProviderFactory
from services.tts.synthesis_service import AudioSynthesisService


def _resolve_api_key(settings: "Settings") -> str | None:  # noqa: F821
    """Pick the correct API key for the active LLM provider."""
    provider = settings.LLM_PROVIDER
    key_map = {
        "openai": settings.OPENAI_API_KEY,
        "anthropic": settings.ANTHROPIC_API_KEY,
        "gemini": settings.GEMINI_API_KEY,
    }
    return key_map.get(provider)


def create_pipeline(
    event_callback: EventCallback | None = None,
    budget_limit: float | None = None,
) -> PipelineOrchestrator:
    """Create a fully-wired PipelineOrchestrator from current settings.

    Args:
        event_callback: Optional event callback for pipeline events.
        budget_limit: Optional USD budget cap for LLM cost tracking.

    Returns:
        Ready-to-use PipelineOrchestrator instance.
    """
    settings = get_settings()

    # Shared components
    enhancer = PromptEnhancer()
    cost_tracker = CostTracker(budget_limit=budget_limit) if budget_limit else None

    # LLM provider
    llm_type = "mock" if settings.USE_MOCK_SERVICES else settings.LLM_PROVIDER
    llm_provider = LLMProviderFactory.create_provider(
        provider_type=llm_type,
        api_key=_resolve_api_key(settings),
    )

    # LLM services
    ideation = IdeationService(provider=llm_provider, enhancer=enhancer)
    outline = OutlineService(provider=llm_provider, enhancer=enhancer)
    segment = SegmentGenerationService(
        provider=llm_provider, enhancer=enhancer, cost_tracker=cost_tracker
    )
    script = ScriptGenerationService(
        provider=llm_provider, enhancer=enhancer, cost_tracker=cost_tracker
    )

    # TTS provider
    tts_type = "mock" if settings.USE_MOCK_SERVICES else settings.TTS_PROVIDER
    tts_provider = TTSProviderFactory.create_provider(
        provider_type=tts_type,
        api_key=settings.ELEVENLABS_API_KEY,
    )

    # Audio services
    synthesis = AudioSynthesisService(
        tts_provider=tts_provider,
        output_dir=settings.AUDIO_OUTPUT_DIR,
    )
    mixer = AudioMixer()

    # Storage & management
    storage = EpisodeStorage(shows_dir=settings.SHOWS_DIR)
    blueprint_mgr = ShowBlueprintManager(shows_dir=settings.SHOWS_DIR)

    return PipelineOrchestrator(
        prompt_enhancer=enhancer,
        ideation_service=ideation,
        outline_service=outline,
        segment_service=segment,
        script_service=script,
        synthesis_service=synthesis,
        audio_mixer=mixer,
        show_blueprint_manager=blueprint_mgr,
        episode_storage=storage,
        event_callback=event_callback,
    )


def create_approval_workflow(
    event_callback: EventCallback | None = None,
) -> ApprovalWorkflow:
    """Create an ApprovalWorkflow from current settings.

    Args:
        event_callback: Optional event callback for approval events.

    Returns:
        Ready-to-use ApprovalWorkflow instance.
    """
    settings = get_settings()
    storage = EpisodeStorage(shows_dir=settings.SHOWS_DIR)
    return ApprovalWorkflow(
        episode_storage=storage,
        event_callback=event_callback,
    )


def create_storage() -> EpisodeStorage:
    """Create an EpisodeStorage from current settings."""
    settings = get_settings()
    return EpisodeStorage(shows_dir=settings.SHOWS_DIR)


def create_blueprint_manager() -> ShowBlueprintManager:
    """Create a ShowBlueprintManager from current settings."""
    settings = get_settings()
    return ShowBlueprintManager(shows_dir=settings.SHOWS_DIR)
