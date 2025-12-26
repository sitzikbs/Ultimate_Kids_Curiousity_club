#!/usr/bin/env python
"""Example usage of the Prompt Enhancement Service."""

from models import (
    Character,
    ConceptsHistory,
    Protagonist,
    Show,
    ShowBlueprint,
    StoryBeat,
    StoryOutline,
    StorySegment,
    WorldDescription,
)
from modules.prompts import PromptEnhancer


def main():
    """Demonstrate the PromptEnhancer functionality."""
    # Create a sample show blueprint
    show = Show(
        show_id="olivers_lab",
        title="Oliver's Science Lab",
        description="Educational science adventures for curious kids",
        theme="STEM Discovery and Problem Solving",
        narrator_voice_config={"provider": "elevenlabs", "voice_id": "narrator_01"},
    )

    protagonist = Protagonist(
        name="Oliver",
        age=10,
        description="A curious inventor who loves to learn and experiment",
        values=["curiosity", "creativity", "persistence", "scientific thinking"],
        catchphrases=["How does it work?", "Let's find out!", "Science is amazing!"],
        backstory="Oliver grew up in a magical laboratory treehouse",
        voice_config={"provider": "elevenlabs", "voice_id": "oliver_voice"},
    )

    world = WorldDescription(
        setting="A magical laboratory in a giant treehouse",
        rules=[
            "Science always works consistently",
            "Curiosity is rewarded with discovery",
            "Experiments teach valuable lessons",
            "Every question has an answer waiting to be found",
        ],
        atmosphere="Exciting, educational, and full of wonder",
        locations=[
            {
                "name": "Main Lab",
                "description": "Where experiments and inventions come to life",
            },
            {"name": "Library", "description": "Books and research materials"},
            {
                "name": "Observatory",
                "description": "For stargazing and space exploration",
            },
        ],
    )

    characters = [
        Character(
            name="Hannah",
            role="Lab Assistant and Best Friend",
            description="Smart and helpful scientist",
            personality="Kind, knowledgeable, and encouraging",
            voice_config={"provider": "elevenlabs", "voice_id": "hannah_voice"},
        ),
        Character(
            name="Professor Quirk",
            role="Mentor Scientist",
            description="Eccentric but brilliant scientist",
            personality="Enthusiastic, wise, and a bit quirky",
            voice_config={"provider": "elevenlabs", "voice_id": "quirk_voice"},
        ),
    ]

    concepts_history = ConceptsHistory(
        concepts=[
            {"episode_id": "ep001", "topic": "Gravity", "date": "2024-01-15"},
            {"episode_id": "ep002", "topic": "Magnetism", "date": "2024-01-20"},
            {
                "episode_id": "ep003",
                "topic": "States of Matter",
                "date": "2024-01-25",
            },
        ]
    )

    show_blueprint = ShowBlueprint(
        show=show,
        protagonist=protagonist,
        world=world,
        characters=characters,
        concepts_history=concepts_history,
    )

    # Initialize the PromptEnhancer
    enhancer = PromptEnhancer(version="1.0.0")

    print("=" * 80)
    print("PROMPT ENHANCEMENT SERVICE DEMO")
    print("=" * 80)
    print()

    # 1. Ideation Stage
    print("1. IDEATION STAGE")
    print("-" * 80)
    topic = "How do plants make their own food through photosynthesis?"
    ideation_prompt = enhancer.enhance_ideation_prompt(
        topic=topic, show_blueprint=show_blueprint
    )
    print(f"Topic: {topic}")
    print()
    print("Enhanced Ideation Prompt:")
    print(ideation_prompt[:500] + "...\n")

    # 2. Outline Stage
    print("2. OUTLINE STAGE")
    print("-" * 80)
    concept = (
        "Oliver discovers how plants use sunlight, water, and carbon dioxide "
        "to create their own food through photosynthesis. With Hannah's help, "
        "he builds a miniature greenhouse to observe the process."
    )
    outline_prompt = enhancer.enhance_outline_prompt(
        concept=concept, show_blueprint=show_blueprint
    )
    print(f"Concept: {concept}")
    print()
    print("Enhanced Outline Prompt:")
    print(outline_prompt[:500] + "...\n")

    # 3. Segment Stage
    print("3. SEGMENT STAGE")
    print("-" * 80)
    story_outline = StoryOutline(
        episode_id="ep004",
        show_id="olivers_lab",
        topic="Photosynthesis",
        title="The Green Machine",
        educational_concept="Plants make food using sunlight, water, and CO2",
        story_beats=[
            StoryBeat(
                beat_number=1,
                title="The Wilting Plant Mystery",
                description="Oliver notices a plant wilting in the lab",
                educational_focus="Plants need certain things to survive",
                key_moments=[
                    "Discovery of wilting plant",
                    "Question: Why is it dying?",
                ],
            ),
            StoryBeat(
                beat_number=2,
                title="Learning About Photosynthesis",
                description="Hannah explains how plants make food",
                educational_focus="The process of photosynthesis",
                key_moments=[
                    "Explanation of sunlight, water, CO2",
                    "Understanding chlorophyll",
                ],
            ),
        ],
    )
    segment_prompt = enhancer.enhance_segment_prompt(
        outline=story_outline, show_blueprint=show_blueprint
    )
    print(f"Outline: {story_outline.title}")
    print()
    print("Enhanced Segment Prompt:")
    print(segment_prompt[:500] + "...\n")

    # 4. Script Stage
    print("4. SCRIPT STAGE")
    print("-" * 80)
    story_segments = [
        StorySegment(
            segment_number=1,
            beat_number=1,
            description=(
                "Oliver enters the main lab and notices his favorite fern "
                "looking droopy and sad. He's concerned and calls Hannah over."
            ),
            characters_involved=["Oliver", "Hannah"],
            setting="Main Lab, morning light streaming through windows",
            educational_content="Plants need care and attention to thrive",
        ),
        StorySegment(
            segment_number=2,
            beat_number=1,
            description=(
                "Hannah examines the plant and asks Oliver questions about "
                "when he last watered it and where it's been sitting."
            ),
            characters_involved=["Oliver", "Hannah"],
            setting="Main Lab, near the window",
            educational_content="Plants need water and light",
        ),
    ]
    script_prompt = enhancer.enhance_script_prompt(
        segments=story_segments, show_blueprint=show_blueprint
    )
    print("Segments: 2 segments from Beat 1")
    print()
    print("Enhanced Script Prompt:")
    print(script_prompt[:500] + "...\n")

    print("=" * 80)
    print("All 4 enhancement stages demonstrated successfully!")
    print("=" * 80)


if __name__ == "__main__":
    main()
