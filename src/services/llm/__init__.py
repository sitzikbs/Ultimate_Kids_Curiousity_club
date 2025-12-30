"""LLM services for story generation."""

# Lazy imports to avoid circular dependencies during testing
# Import only what's needed when explicitly requested

__all__ = [
    "BaseLLMProvider",
    "CostTracker",
    "LLMCallMetrics",
    "LLMProviderFactory",
    "GeminiProvider",
    "IdeationService",
    "LLMResponseParser",
    "OutlineService",
    "ScriptGenerationService",
    "SegmentGenerationService",
]


def __getattr__(name):
    """Lazy import to avoid import-time dependencies."""
    if name == "BaseLLMProvider":
        from services.llm.base import BaseLLMProvider
        return BaseLLMProvider
    elif name == "CostTracker":
        from services.llm.cost_tracker import CostTracker
        return CostTracker
    elif name == "LLMCallMetrics":
        from services.llm.cost_tracker import LLMCallMetrics
        return LLMCallMetrics
    elif name == "LLMProviderFactory":
        from services.llm.factory import LLMProviderFactory
        return LLMProviderFactory
    elif name == "GeminiProvider":
        from services.llm.gemini_provider import GeminiProvider
        return GeminiProvider
    elif name == "IdeationService":
        from services.llm.ideation_service import IdeationService
        return IdeationService
    elif name == "LLMResponseParser":
        from services.llm.parsing import LLMResponseParser
        return LLMResponseParser
    elif name == "OutlineService":
        from services.llm.outline_service import OutlineService
        return OutlineService
    elif name == "ScriptGenerationService":
        from services.llm.script_generation_service import ScriptGenerationService
        return ScriptGenerationService
    elif name == "SegmentGenerationService":
        from services.llm.segment_generation_service import SegmentGenerationService
        return SegmentGenerationService
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
