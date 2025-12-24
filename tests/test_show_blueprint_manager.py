"""Tests for ShowBlueprintManager."""

import pytest

from src.models import Character, Protagonist, WorldDescription
from src.modules import ShowBlueprintManager
from src.utils.errors import ShowNotFoundError


class TestShowBlueprintManager:
    """Tests for ShowBlueprintManager."""

    def test_load_existing_show(self):
        """Test loading an existing show."""
        manager = ShowBlueprintManager()

        # Load olivers_workshop which exists in the repo
        blueprint = manager.load_show("olivers_workshop")

        assert blueprint.show.show_id == "olivers_workshop"
        assert blueprint.show.title == "Oliver the Inventor"
        assert blueprint.protagonist.name == "Oliver the Inventor"
        assert blueprint.protagonist.age == 8
        assert len(blueprint.world.rules) > 0

    def test_load_nonexistent_show(self):
        """Test loading a show that doesn't exist."""
        manager = ShowBlueprintManager()

        with pytest.raises(ShowNotFoundError):
            manager.load_show("nonexistent_show")

    def test_list_shows(self):
        """Test listing all shows."""
        manager = ShowBlueprintManager()
        shows = manager.list_shows()

        # Should have at least olivers_workshop
        assert len(shows) >= 1
        show_ids = [show.show_id for show in shows]
        assert "olivers_workshop" in show_ids

    def test_save_and_load_show(self, temp_data_dir, show_blueprint):
        """Test saving and loading a show."""
        shows_dir = temp_data_dir / "shows"
        manager = ShowBlueprintManager(shows_dir=shows_dir)

        # Save the show
        manager.save_show(show_blueprint)

        # Load it back
        loaded = manager.load_show("test_show")

        assert loaded.show.show_id == show_blueprint.show.show_id
        assert loaded.show.title == show_blueprint.show.title
        assert loaded.protagonist.name == show_blueprint.protagonist.name
        assert loaded.world.setting == show_blueprint.world.setting

    def test_update_protagonist(self, temp_data_dir, show_blueprint):
        """Test updating protagonist."""
        shows_dir = temp_data_dir / "shows"
        manager = ShowBlueprintManager(shows_dir=shows_dir)

        # Save initial show
        manager.save_show(show_blueprint)

        # Update protagonist
        new_protagonist = Protagonist(
            name="Updated Hero",
            age=9,
            description="An updated hero",
        )
        manager.update_protagonist("test_show", new_protagonist)

        # Load and verify
        loaded = manager.load_show("test_show")
        assert loaded.protagonist.name == "Updated Hero"
        assert loaded.protagonist.age == 9

    def test_update_world(self, temp_data_dir, show_blueprint):
        """Test updating world description."""
        shows_dir = temp_data_dir / "shows"
        manager = ShowBlueprintManager(shows_dir=shows_dir)

        # Save initial show
        manager.save_show(show_blueprint)

        # Update world
        new_world = WorldDescription(
            setting="A new exciting world",
            rules=["New rule 1", "New rule 2"],
            atmosphere="Mysterious",
        )
        manager.update_world("test_show", new_world)

        # Load and verify
        loaded = manager.load_show("test_show")
        assert "new exciting world" in loaded.world.setting.lower()
        assert len(loaded.world.rules) == 2

    def test_add_character(self, temp_data_dir, show_blueprint):
        """Test adding a character."""
        shows_dir = temp_data_dir / "shows"
        manager = ShowBlueprintManager(shows_dir=shows_dir)

        # Save initial show
        manager.save_show(show_blueprint)

        # Add a character
        new_character = Character(
            name="New Character",
            role="Mentor",
            description="Wise and helpful",
            personality="Patient and kind",
        )
        manager.add_character("test_show", new_character)

        # Load and verify
        loaded = manager.load_show("test_show")
        assert len(loaded.characters) == 2  # Original + new
        char_names = [c.name for c in loaded.characters]
        assert "New Character" in char_names

    def test_add_concept(self, temp_data_dir, show_blueprint):
        """Test adding a concept."""
        shows_dir = temp_data_dir / "shows"
        manager = ShowBlueprintManager(shows_dir=shows_dir)

        # Save initial show
        manager.save_show(show_blueprint)

        # Add concept
        manager.add_concept("test_show", "magnetism", "ep_001", "introductory")

        # Load and verify
        loaded = manager.load_show("test_show")
        concepts = loaded.concepts_history.get_covered_concepts()
        assert "magnetism" in concepts

    def test_get_covered_concepts(self, temp_data_dir, show_blueprint):
        """Test getting covered concepts."""
        shows_dir = temp_data_dir / "shows"
        manager = ShowBlueprintManager(shows_dir=shows_dir)

        # Save initial show and add concepts
        manager.save_show(show_blueprint)
        manager.add_concept("test_show", "gravity", "ep_001")
        manager.add_concept("test_show", "friction", "ep_002")

        # Get concepts
        concepts = manager.get_covered_concepts("test_show")
        assert len(concepts) == 2
        assert "gravity" in concepts
        assert "friction" in concepts
