"""Service protocol definitions for the pipeline orchestrator.

Defines ``Protocol`` classes for every service the orchestrator consumes,
enabling type-safe dependency injection without coupling to concrete classes.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any, Protocol, runtime_checkable

from models.episode import Episode
from models.show import Show, ShowBlueprint
from models.story import Script, StoryOutline, StorySegment

# ---------------------------------------------------------------------------
# LLM service protocols
# ---------------------------------------------------------------------------


@runtime_checkable
class PromptEnhancerProtocol(Protocol):
    """Enhances prompts with Show Blueprint context."""

    def enhance_ideation_prompt(
        self, topic: str, show_blueprint: ShowBlueprint
    ) -> str: ...

    def enhance_outline_prompt(
        self, concept: str, show_blueprint: ShowBlueprint
    ) -> str: ...

    def enhance_segment_prompt(
        self, outline: StoryOutline, show_blueprint: ShowBlueprint
    ) -> str: ...

    def enhance_script_prompt(
        self, segments: list[StorySegment], show_blueprint: ShowBlueprint
    ) -> str: ...


@runtime_checkable
class IdeationServiceProtocol(Protocol):
    """Generates story concepts from topics."""

    async def generate_concept(
        self,
        topic: str,
        show_blueprint: ShowBlueprint,
        **kwargs: Any,
    ) -> str: ...


@runtime_checkable
class OutlineServiceProtocol(Protocol):
    """Generates story outlines from concepts."""

    async def generate_outline(
        self,
        concept: str,
        show_blueprint: ShowBlueprint,
        episode_id: str = "temp_episode",
        **kwargs: Any,
    ) -> StoryOutline: ...


@runtime_checkable
class SegmentServiceProtocol(Protocol):
    """Generates story segments from outlines."""

    async def generate_segments(
        self,
        outline: StoryOutline,
        show_blueprint: ShowBlueprint,
        **kwargs: Any,
    ) -> list[StorySegment]: ...


@runtime_checkable
class ScriptServiceProtocol(Protocol):
    """Generates scripts from story segments."""

    async def generate_scripts(
        self,
        segments: list[StorySegment],
        show_blueprint: ShowBlueprint,
        **kwargs: Any,
    ) -> list[Script]: ...


# ---------------------------------------------------------------------------
# Audio service protocols
# ---------------------------------------------------------------------------


@runtime_checkable
class AudioSynthesisProtocol(Protocol):
    """Converts scripts to audio via TTS."""

    def synthesize_segment(
        self,
        text: str,
        character_id: str,
        voice_config: dict[str, Any],
        segment_number: int,
        emotion: str | None = None,
    ) -> Any:
        """Synthesize a single text segment to audio.

        Returns an object with at minimum an ``audio_path`` attribute.
        """
        ...


@runtime_checkable
class AudioMixerProtocol(Protocol):
    """Mixes audio segments into a final episode file."""

    def mix_segments(self, segment_paths: list[Path | str]) -> Any:
        """Mix multiple audio segments into one.

        Returns an audio object with an ``export(path, format)`` method.
        """
        ...


# ---------------------------------------------------------------------------
# Storage & management protocols
# ---------------------------------------------------------------------------


@runtime_checkable
class BlueprintManagerProtocol(Protocol):
    """Manages Show Blueprint CRUD operations."""

    def load_show(self, show_id: str) -> ShowBlueprint: ...
    def save_show(self, blueprint: ShowBlueprint) -> None: ...
    def list_shows(self) -> list[Show]: ...
    def add_concept(self, show_id: str, concept: str, episode_id: str) -> None: ...
    def link_episode(self, show_id: str, episode_id: str) -> None: ...


@runtime_checkable
class EpisodeStorageProtocol(Protocol):
    """Persists episode state to storage."""

    def save_episode(self, episode: Episode) -> None: ...
    def load_episode(self, show_id: str, episode_id: str) -> Episode: ...
    def list_episodes(self, show_id: str) -> list[str]: ...
    def get_episode_path(self, show_id: str, episode_id: str) -> Path: ...
    def delete_episode(self, show_id: str, episode_id: str) -> None: ...
