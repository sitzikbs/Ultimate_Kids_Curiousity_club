"""Demo of LLM Provider Abstraction, Ideation & Outline Generation.

This example demonstrates:
1. Creating LLM providers (Mock, OpenAI, Anthropic)
2. Using IdeationService to generate story concepts
3. Using OutlineService to generate story outlines
4. Complete pipeline from topic to outline
"""

import asyncio
from pathlib import Path

from models import (
    ConceptsHistory,
    Protagonist,
    Show,
    ShowBlueprint,
    WorldDescription,
)
from modules.prompts.enhancer import PromptEnhancer
from services.llm.factory import LLMProviderFactory
from services.llm.ideation_service import IdeationService
from services.llm.outline_service import OutlineService


def create_example_show_blueprint() -> ShowBlueprint:
    """Create an example show blueprint for testing."""
    show = Show(
        show_id="olivers_workshop",
        title="Oliver's Workshop",
        description="A workshop where Oliver explores science and engineering",
        theme="Science and Discovery",
        narrator_voice_config={"voice_id": "narrator", "stability": 0.5},
    )

    protagonist = Protagonist(
        name="Oliver",
        age=10,
        description="A curious young inventor with a passion for understanding how things work",
        values=["curiosity", "creativity", "perseverance", "teamwork"],
        catchphrases=["Let's find out!", "Amazing!", "I wonder why..."],
        backstory="Oliver loves taking things apart and building new inventions",
        voice_config={"voice_id": "oliver", "stability": 0.7},
    )

    world = WorldDescription(
        setting="Oliver's Workshop - a magical space filled with tools and experiments",
        rules=[
            "Science-based adventures",
            "Real-world physics applies",
            "Learning through experimentation",
        ],
        atmosphere="Exciting, educational, and full of wonder",
        locations=[
            {
                "name": "Main Workshop",
                "description": "Where Oliver builds and experiments",
            },
            {
                "name": "Science Library",
                "description": "Books and resources for research",
            },
        ],
    )

    concepts_history = ConceptsHistory(
        concepts=[
            {"topic": "gravity", "episode_id": "ep001", "date": "2024-01-01"},
            {"topic": "electricity", "episode_id": "ep002", "date": "2024-01-15"},
        ]
    )

    return ShowBlueprint(
        show=show,
        protagonist=protagonist,
        world=world,
        concepts_history=concepts_history,
    )


async def demo_mock_provider():
    """Demonstrate using the Mock LLM provider."""
    print("\n" + "=" * 80)
    print("DEMO 1: Mock LLM Provider (Cost-free testing)")
    print("=" * 80)

    # Create mock provider
    provider = LLMProviderFactory.create_provider("mock")
    print(f"✓ Created provider: {type(provider).__name__}")

    # Test basic generation
    prompt = "Generate a story concept about how airplanes fly."
    result = await provider.generate(prompt, max_tokens=500)
    print(f"\n✓ Generated concept ({len(result)} chars):")
    print(f"  {result[:200]}...")

    # Test token counting and cost
    tokens = provider.count_tokens(result)
    cost = provider.get_cost(input_tokens=100, output_tokens=tokens)
    print(f"\n✓ Token count: {tokens}")
    print(f"✓ Cost: ${cost:.2f} (always free for mock)")


async def demo_ideation_service():
    """Demonstrate the IdeationService."""
    print("\n" + "=" * 80)
    print("DEMO 2: IdeationService - Topic to Story Concept")
    print("=" * 80)

    # Setup
    provider = LLMProviderFactory.create_provider("mock")
    enhancer = PromptEnhancer()
    service = IdeationService(provider, enhancer)
    blueprint = create_example_show_blueprint()

    # Generate concept
    topic = "How do volcanoes erupt?"
    print(f"\n📝 Topic: {topic}")
    print("⏳ Generating story concept...")

    concept = await service.generate_concept(topic=topic, show_blueprint=blueprint)

    print(f"\n✓ Generated concept ({len(concept.split())} words):")
    print("-" * 80)
    print(concept)
    print("-" * 80)

    # Check for protagonist mention
    if blueprint.protagonist.name in concept:
        print(f"\n✓ Protagonist '{blueprint.protagonist.name}' is mentioned")


async def demo_outline_service():
    """Demonstrate the OutlineService."""
    print("\n" + "=" * 80)
    print("DEMO 3: OutlineService - Concept to Story Outline")
    print("=" * 80)

    # Setup
    provider = LLMProviderFactory.create_provider("mock")
    enhancer = PromptEnhancer()
    service = OutlineService(provider, enhancer)
    blueprint = create_example_show_blueprint()

    # Create a sample concept
    concept = (
        "Oliver discovers the fascinating science behind volcanoes when his model "
        "volcano erupts unexpectedly. Curious about the difference between gentle "
        "lava flows and explosive eruptions, Oliver embarks on an imaginative "
        "journey to explore Earth's interior, learning about tectonic plates, "
        "magma formation, and the various types of volcanic activity."
    )

    print(f"\n📝 Concept: {concept[:100]}...")
    print("⏳ Generating story outline...")

    outline = await service.generate_outline(
        concept=concept, show_blueprint=blueprint, episode_id="ep_volcano_001"
    )

    print(f"\n✓ Generated outline:")
    print(f"  Episode ID: {outline.episode_id}")
    print(f"  Title: {outline.title}")
    print(f"  Topic: {outline.topic}")
    print(f"  Educational Concept: {outline.educational_concept}")
    print(f"  Number of Story Beats: {len(outline.story_beats)}")

    print("\n📖 Story Beats:")
    print("-" * 80)
    for beat in outline.story_beats:
        print(f"\nBeat {beat.beat_number}: {beat.title}")
        print(f"  Description: {beat.description}")
        print(f"  Educational Focus: {beat.educational_focus}")
        if beat.key_moments:
            print(f"  Key Moments:")
            for moment in beat.key_moments:
                print(f"    - {moment}")
    print("-" * 80)


async def demo_full_pipeline():
    """Demonstrate the complete pipeline from topic to outline."""
    print("\n" + "=" * 80)
    print("DEMO 4: Full Pipeline - Topic → Concept → Outline")
    print("=" * 80)

    # Setup
    provider = LLMProviderFactory.create_provider("mock")
    enhancer = PromptEnhancer()
    ideation_service = IdeationService(provider, enhancer)
    outline_service = OutlineService(provider, enhancer)
    blueprint = create_example_show_blueprint()

    # Step 1: Generate concept from topic
    topic = "How do plants make food from sunlight?"
    print(f"\n📝 Topic: {topic}")
    print("⏳ Step 1: Generating story concept...")

    concept = await ideation_service.generate_concept(
        topic=topic, show_blueprint=blueprint
    )
    print(f"✓ Concept generated ({len(concept.split())} words)")

    # Step 2: Generate outline from concept
    print("\n⏳ Step 2: Generating story outline...")

    outline = await outline_service.generate_outline(
        concept=concept, show_blueprint=blueprint, episode_id="ep_photosynthesis_001"
    )

    print(f"✓ Outline generated")
    print(f"\n📊 Results:")
    print(f"  Title: {outline.title}")
    print(f"  Educational Concept: {outline.educational_concept}")
    print(f"  Story Beats: {len(outline.story_beats)}")

    # Step 3: Export to YAML for human review
    print("\n⏳ Step 3: Exporting to YAML for human review...")
    yaml_output = await outline_service.generate_outline_yaml(
        concept=concept, show_blueprint=blueprint, episode_id="ep_photosynthesis_001"
    )

    print("✓ YAML generated:")
    print("-" * 80)
    print(yaml_output[:500])
    print("...")
    print("-" * 80)


async def main():
    """Run all demos."""
    print("\n" + "🎬" * 40)
    print("LLM Services Demo - WP2a Implementation")
    print("🎬" * 40)

    try:
        await demo_mock_provider()
        await demo_ideation_service()
        await demo_outline_service()
        await demo_full_pipeline()

        print("\n" + "=" * 80)
        print("✅ All demos completed successfully!")
        print("=" * 80)

        print("\n💡 Next Steps:")
        print("  1. Try with real OpenAI/Anthropic providers (requires API keys)")
        print("  2. Extend to WP2b: Segment & Script Generation")
        print("  3. Integrate with WP6: Orchestrator for full pipeline")

    except Exception as e:
        print(f"\n❌ Error: {e}")
        raise


if __name__ == "__main__":
    asyncio.run(main())
