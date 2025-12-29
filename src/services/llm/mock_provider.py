"""Mock LLM provider for cost-free testing."""

import json
from collections.abc import AsyncGenerator
from pathlib import Path
from typing import Any

from services.llm.base import BaseLLMProvider


class MockLLMProvider(BaseLLMProvider):
    """Mock LLM provider that returns fixture-based responses."""

    def __init__(
        self, fixtures_dir: Path | None = None, delay_seconds: float = 0.0
    ) -> None:
        """Initialize mock LLM provider.

        Args:
            fixtures_dir: Directory containing fixture JSON files.
                         Defaults to data/fixtures/llm
            delay_seconds: Artificial delay to simulate API latency
        """
        if fixtures_dir is None:
            # Default to project data/fixtures/llm directory
            fixtures_dir = (
                Path(__file__).parent.parent.parent.parent / "data" / "fixtures" / "llm"
            )

        self.fixtures_dir = Path(fixtures_dir)
        self.delay_seconds = delay_seconds
        self._fixtures_cache: dict[str, Any] = {}
        self._load_fixtures()

    def _load_fixtures(self) -> None:
        """Load all fixture files into memory."""
        if not self.fixtures_dir.exists():
            return

        for fixture_file in self.fixtures_dir.glob("*.json"):
            try:
                with open(fixture_file, encoding="utf-8") as f:
                    self._fixtures_cache[fixture_file.stem] = json.load(f)
            except Exception:
                # Skip invalid fixtures
                pass

    async def generate(
        self,
        prompt: str,
        max_tokens: int = 2000,
        temperature: float = 0.7,
        **kwargs: Any,
    ) -> str:
        """Generate mock response based on prompt content.

        Args:
            prompt: The input prompt for the LLM
            max_tokens: Maximum tokens (ignored in mock)
            temperature: Temperature (ignored in mock)
            **kwargs: Additional parameters (ignored in mock)

        Returns:
            Generated mock response based on fixture data
        """
        # Add artificial delay if specified
        if self.delay_seconds > 0:
            import asyncio

            await asyncio.sleep(self.delay_seconds)

        # Detect type of generation from prompt content
        prompt_lower = prompt.lower()

        # Ideation: Generate story concept
        if (
            "story concept" in prompt_lower or "ideation" in prompt_lower
        ) and "outline" not in prompt_lower:
            return self._generate_concept(prompt)

        # Outline: Generate story beats
        if (
            "story beats" in prompt_lower
            or "outline" in prompt_lower
            or "beat" in prompt_lower
        ):
            return self._generate_outline(prompt)

        # Segment: Generate detailed segments
        if "segment" in prompt_lower or "detailed scene" in prompt_lower:
            return self._generate_segments(prompt)

        # Script: Generate dialogue
        if "script" in prompt_lower or "dialogue" in prompt_lower:
            return self._generate_script(prompt)

        # Default: Return a generic response
        return self._generate_generic_response(prompt)

    async def generate_stream(
        self,
        prompt: str,
        max_tokens: int = 2000,
        temperature: float = 0.7,
        **kwargs: Any,
    ) -> AsyncGenerator[str, None]:
        """Generate mock response with streaming.

        Args:
            prompt: The input prompt for the LLM
            max_tokens: Maximum tokens (ignored in mock)
            temperature: Temperature (ignored in mock)
            **kwargs: Additional parameters (ignored in mock)

        Yields:
            Text chunks simulating streaming
        """
        response = await self.generate(prompt, max_tokens, temperature, **kwargs)

        # Split response into chunks to simulate streaming
        chunk_size = 50
        for i in range(0, len(response), chunk_size):
            chunk = response[i : i + chunk_size]
            if self.delay_seconds > 0:
                import asyncio

                await asyncio.sleep(self.delay_seconds / 10)
            yield chunk

    def _generate_concept(self, prompt: str) -> str:
        """Generate a story concept based on topic in prompt."""
        # Try to extract topic from prompt
        topic = "science"
        if "volcano" in prompt.lower():
            topic = "volcanoes"
        elif "airplane" in prompt.lower():
            topic = "airplanes"
        elif "season" in prompt.lower():
            topic = "seasons"

        # Extract protagonist name
        protagonist = "Oliver"
        if "hannah" in prompt.lower():
            protagonist = "Hannah"

        return (
            f"In this exciting adventure, {protagonist} discovers the "
            f"fascinating world of {topic}! When a curious question pops into "
            f"their mind during an ordinary day, {protagonist} embarks on an "
            f"imaginative journey to uncover the answer. Along the way, they "
            f"encounter surprising phenomena, learn important scientific "
            f"concepts, and demonstrate values like curiosity and perseverance.\n\n"
            f"The story weaves together hands-on exploration with age-appropriate "
            f"explanations, making complex topics accessible and engaging for "
            f"young learners. {protagonist} uses creative problem-solving and "
            f"teamwork to understand the science behind everyday wonders, "
            f"inspiring children to ask their own questions about the world "
            f"around them."
        )

    def _generate_outline(self, prompt: str) -> str:
        """Generate a story outline in YAML format."""
        return """episode_id: mock_episode_001
show_id: olivers_workshop
topic: "How Things Work"
title: "Oliver's Amazing Discovery"
educational_concept: "Scientific inquiry and observation"
created_at: "2024-12-29T00:00:00Z"

story_beats:
  - beat_number: 1
    title: "The Curious Question"
    description: "Oliver encounters something puzzling that sparks his curiosity"
    educational_focus: "Introduction to the topic and why it matters"
    key_moments:
      - "Oliver notices something unusual"
      - "He asks 'How does this work?'"
      - "Decides to investigate and learn more"
    duration_minutes: 3

  - beat_number: 2
    title: "The Investigation Begins"
    description: "Oliver starts exploring and gathering information"
    educational_focus: "Core concepts and scientific principles"
    key_moments:
      - "Oliver observes carefully"
      - "Makes predictions about what will happen"
      - "Tests ideas through experimentation"
    duration_minutes: 4

  - beat_number: 3
    title: "The Big Discovery"
    description: "Oliver has an 'aha!' moment and understands the concept"
    educational_focus: "Key learning insights and connections"
    key_moments:
      - "Oliver connects the dots"
      - "Understands the underlying principle"
      - "Sees how it applies to everyday life"
    duration_minutes: 3

  - beat_number: 4
    title: "Sharing the Knowledge"
    description: "Oliver shares what he learned and inspires others"
    educational_focus: "Recap and real-world applications"
    key_moments:
      - "Oliver explains his discovery"
      - "Shows others how to explore too"
      - "Encourages curiosity and learning"
    duration_minutes: 2
"""

    def _generate_segments(self, prompt: str) -> str:
        """Generate detailed story segments."""
        # Check if this is actually a script request based on prompt keywords
        if "dialogue" in prompt.lower() or "speaker" in prompt.lower():
            return self._generate_script(prompt)

        return """[
  {
    "segment_number": 1,
    "beat_number": 1,
    "description": "Oliver is in his workshop when he notices something unusual.",
    "characters_involved": ["Oliver"],
    "setting": "Oliver's Workshop",
    "educational_content": "Introduction to observation and asking questions"
  },
  {
    "segment_number": 2,
    "beat_number": 1,
    "description": "Oliver examines the phenomenon more closely.",
    "characters_involved": ["Oliver"],
    "setting": "Oliver's Workshop",
    "educational_content": "The importance of careful observation in science"
  }
]"""

    def _generate_script(self, prompt: str) -> str:
        """Generate script with dialogue."""
        return """[
  {
    "speaker": "NARRATOR",
    "text": "Welcome to Oliver's Workshop! Today, Oliver is about to discover!",
    "speaker_voice_id": "narrator_voice",
    "duration_estimate": 4.5
  },
  {
    "speaker": "OLIVER",
    "text": "Wow! I wonder how this works. Let me investigate!",
    "speaker_voice_id": "oliver_voice",
    "duration_estimate": 3.2
  },
  {
    "speaker": "NARRATOR",
    "text": "And so begins another exciting adventure in learning!",
    "speaker_voice_id": "narrator_voice",
    "duration_estimate": 3.8
  }
]"""

    def _generate_generic_response(self, prompt: str) -> str:
        """Generate a generic mock response."""
        return (
            "This is a mock response from the LLM. In production, this would be "
            "replaced with actual AI-generated content based on the prompt. "
            f"Prompt length: {len(prompt)} characters."
        )

    def count_tokens(self, text: str) -> int:
        """Count tokens in text (mock estimation).

        Args:
            text: Text to count tokens for

        Returns:
            Estimated number of tokens (1 token ≈ 4 characters)
        """
        return len(text) // 4

    def get_cost(self, input_tokens: int, output_tokens: int) -> float:
        """Calculate cost for mock provider (always $0).

        Args:
            input_tokens: Number of input tokens (ignored)
            output_tokens: Number of output tokens (ignored)

        Returns:
            Cost in USD (always 0.0)
        """
        return 0.0
