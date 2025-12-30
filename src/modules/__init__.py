"""Educational modules for the Kids Curiosity Club."""

# Lazy imports to avoid circular dependencies during testing

__all__ = ["EpisodeStorage", "PromptEnhancer"]


def __getattr__(name):
    """Lazy import to avoid import-time dependencies."""
    if name == "EpisodeStorage":
        from modules.episode_storage import EpisodeStorage
        return EpisodeStorage
    elif name == "PromptEnhancer":
        from modules.prompts import PromptEnhancer
        return PromptEnhancer
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
