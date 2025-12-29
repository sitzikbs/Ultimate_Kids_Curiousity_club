"""Test suite for ShowBlueprintManager."""

from pathlib import Path

import pytest

from models.show import (
    Character,
    Protagonist,
    Show,
    ShowBlueprint,
    WorldDescription,
)
from modules.show_blueprint_manager import ShowBlueprintManager


class TestShowBlueprintManager:
    """Tests for ShowBlueprintManager class."""

    @pytest.fixture
    def temp_shows_dir(self, tmp_path: Path) -> Path:
        """Create temporary shows directory."""
        shows_dir = tmp_path / "shows"
        shows_dir.mkdir()
        return shows_dir

    @pytest.fixture
    def manager(self, temp_shows_dir: Path) -> ShowBlueprintManager:
        """Create ShowBlueprintManager with temporary directory."""
        return ShowBlueprintManager(shows_dir=temp_shows_dir)

    @pytest.fixture
    def sample_show(self) -> Show:
        """Create sample Show for testing."""
        return Show(
            show_id="test_show",
            title="Test Show",
            description="A test show",
            theme="Testing",
            narrator_voice_config={"provider": "mock", "voice_id": "test"},
        )

    @pytest.fixture
    def sample_protagonist(self) -> Protagonist:
        """Create sample Protagonist for testing."""
        return Protagonist(
            name="Test Hero",
            age=10,
            description="A test protagonist",
            values=["courage", "curiosity"],
            catchphrases=["Let's go!"],
            backstory="Test backstory",
            image_path=None,
            voice_config={"provider": "mock", "voice_id": "hero"},
        )

    @pytest.fixture
    def sample_world(self) -> WorldDescription:
        """Create sample WorldDescription for testing."""
        return WorldDescription(
            setting="A test world",
            rules=["Rule 1", "Rule 2"],
            atmosphere="Mysterious",
            locations=[{"name": "Location 1", "description": "Test location"}],
        )

    @pytest.fixture
    def sample_blueprint(
        self,
        sample_show: Show,
        sample_protagonist: Protagonist,
        sample_world: WorldDescription,
    ) -> ShowBlueprint:
        """Create sample ShowBlueprint for testing."""
        return ShowBlueprint(
            show=sample_show,
            protagonist=sample_protagonist,
            world=sample_world,
            characters=[],
            episodes=[],
        )

    def test_init_default_shows_dir(self):
        """Test manager initialization with default shows directory."""
        manager = ShowBlueprintManager()
        assert manager.shows_dir == Path("data/shows")

    def test_init_custom_shows_dir(self, temp_shows_dir: Path):
        """Test manager initialization with custom shows directory."""
        manager = ShowBlueprintManager(shows_dir=temp_shows_dir)
        assert manager.shows_dir == temp_shows_dir

    def test_save_show(
        self, manager: ShowBlueprintManager, sample_blueprint: ShowBlueprint
    ):
        """Test saving show blueprint to disk."""
        manager.save_show(sample_blueprint)

        show_dir = manager.shows_dir / "test_show"
        assert show_dir.exists()
        assert (show_dir / "show.yaml").exists()
        assert (show_dir / "protagonist.yaml").exists()
        assert (show_dir / "world.yaml").exists()
        assert (show_dir / "concepts_covered.json").exists()
        assert (show_dir / "episodes").exists()

    def test_load_show(
        self, manager: ShowBlueprintManager, sample_blueprint: ShowBlueprint
    ):
        """Test loading show blueprint from disk."""
        manager.save_show(sample_blueprint)
        loaded = manager.load_show("test_show")

        assert loaded.show.show_id == sample_blueprint.show.show_id
        assert loaded.show.title == sample_blueprint.show.title
        assert loaded.protagonist.name == sample_blueprint.protagonist.name
        assert loaded.world.setting == sample_blueprint.world.setting

    def test_load_show_not_found(self, manager: ShowBlueprintManager):
        """Test loading non-existent show raises FileNotFoundError."""
        with pytest.raises(FileNotFoundError, match="Show directory not found"):
            manager.load_show("nonexistent")

    def test_list_shows_empty(self, manager: ShowBlueprintManager):
        """Test listing shows when directory is empty."""
        shows = manager.list_shows()
        assert shows == []

    def test_list_shows(
        self, manager: ShowBlueprintManager, sample_blueprint: ShowBlueprint
    ):
        """Test listing all available shows."""
        manager.save_show(sample_blueprint)

        # Create another show
        sample_blueprint.show.show_id = "test_show_2"
        sample_blueprint.show.title = "Test Show 2"
        manager.save_show(sample_blueprint)

        shows = manager.list_shows()
        assert len(shows) == 2
        assert any(s.show_id == "test_show" for s in shows)
        assert any(s.show_id == "test_show_2" for s in shows)

    def test_list_shows_directory_not_found(self, tmp_path: Path):
        """Test listing shows when directory doesn't exist."""
        manager = ShowBlueprintManager(shows_dir=tmp_path / "nonexistent")
        with pytest.raises(FileNotFoundError, match="Shows directory not found"):
            manager.list_shows()

    def test_update_protagonist(
        self, manager: ShowBlueprintManager, sample_blueprint: ShowBlueprint
    ):
        """Test updating protagonist for a show."""
        manager.save_show(sample_blueprint)

        new_protagonist = Protagonist(
            name="Updated Hero",
            age=12,
            description="Updated description",
            values=["wisdom"],
            voice_config={"provider": "mock"},
        )

        manager.update_protagonist("test_show", new_protagonist)
        loaded = manager.load_show("test_show")

        assert loaded.protagonist.name == "Updated Hero"
        assert loaded.protagonist.age == 12

    def test_update_protagonist_not_found(
        self, manager: ShowBlueprintManager, sample_protagonist: Protagonist
    ):
        """Test updating protagonist for non-existent show."""
        with pytest.raises(FileNotFoundError, match="Show directory not found"):
            manager.update_protagonist("nonexistent", sample_protagonist)

    def test_update_world(
        self, manager: ShowBlueprintManager, sample_blueprint: ShowBlueprint
    ):
        """Test updating world description for a show."""
        manager.save_show(sample_blueprint)

        new_world = WorldDescription(
            setting="Updated world",
            rules=["New rule"],
            atmosphere="Bright",
            locations=[],
        )

        manager.update_world("test_show", new_world)
        loaded = manager.load_show("test_show")

        assert loaded.world.setting == "Updated world"
        assert loaded.world.rules == ["New rule"]

    def test_update_world_not_found(
        self, manager: ShowBlueprintManager, sample_world: WorldDescription
    ):
        """Test updating world for non-existent show."""
        with pytest.raises(FileNotFoundError, match="Show directory not found"):
            manager.update_world("nonexistent", sample_world)

    def test_add_character(
        self, manager: ShowBlueprintManager, sample_blueprint: ShowBlueprint
    ):
        """Test adding supporting character to show."""
        manager.save_show(sample_blueprint)

        character = Character(
            name="Test Sidekick",
            role="Helper",
            description="A helpful character",
            personality="Friendly",
            voice_config={"provider": "mock"},
        )

        manager.add_character("test_show", character)
        loaded = manager.load_show("test_show")

        assert len(loaded.characters) == 1
        assert loaded.characters[0].name == "Test Sidekick"

    def test_add_character_not_found(self, manager: ShowBlueprintManager):
        """Test adding character to non-existent show."""
        character = Character(
            name="Test",
            role="Role",
            description="Desc",
            personality="Person",
            voice_config={},
        )
        with pytest.raises(FileNotFoundError, match="Show directory not found"):
            manager.add_character("nonexistent", character)

    def test_add_concept(
        self, manager: ShowBlueprintManager, sample_blueprint: ShowBlueprint
    ):
        """Test adding concept to show."""
        manager.save_show(sample_blueprint)

        manager.add_concept("test_show", "Test Concept", "ep001")
        concepts = manager.get_covered_concepts("test_show")

        assert len(concepts) == 1
        assert concepts[0] == "Test Concept"

    def test_add_multiple_concepts(
        self, manager: ShowBlueprintManager, sample_blueprint: ShowBlueprint
    ):
        """Test adding multiple concepts to show."""
        manager.save_show(sample_blueprint)

        manager.add_concept("test_show", "Concept 1", "ep001")
        manager.add_concept("test_show", "Concept 2", "ep002")
        manager.add_concept("test_show", "Concept 3", "ep001")

        concepts = manager.get_covered_concepts("test_show")

        assert len(concepts) == 3
        assert "Concept 1" in concepts
        assert "Concept 2" in concepts
        assert "Concept 3" in concepts

    def test_add_concept_not_found(self, manager: ShowBlueprintManager):
        """Test adding concept to non-existent show."""
        with pytest.raises(FileNotFoundError, match="Show directory not found"):
            manager.add_concept("nonexistent", "Concept", "ep001")

    def test_get_covered_concepts_empty(
        self, manager: ShowBlueprintManager, sample_blueprint: ShowBlueprint
    ):
        """Test getting concepts when none are covered."""
        manager.save_show(sample_blueprint)
        concepts = manager.get_covered_concepts("test_show")
        assert concepts == []

    def test_get_covered_concepts_not_found(self, manager: ShowBlueprintManager):
        """Test getting concepts for non-existent show."""
        with pytest.raises(FileNotFoundError, match="Show directory not found"):
            manager.get_covered_concepts("nonexistent")

    def test_create_from_oliver_template(self):
        """Test creating show from Oliver template."""
        blueprint = ShowBlueprintManager.create_from_template(
            "oliver_template", "new_oliver"
        )

        assert blueprint.show.show_id == "new_oliver"
        assert blueprint.show.title == "Oliver's STEM Adventures"
        assert blueprint.protagonist.name == "Oliver the Inventor"
        assert blueprint.protagonist.age == 8
        assert "curiosity" in blueprint.protagonist.values

    def test_create_from_hannah_template(self):
        """Test creating show from Hannah template."""
        blueprint = ShowBlueprintManager.create_from_template(
            "hannah_template", "new_hannah"
        )

        assert blueprint.show.show_id == "new_hannah"
        assert blueprint.show.title == "Hannah's History Adventures"
        assert blueprint.protagonist.name == "Hannah the Historian"
        assert blueprint.protagonist.age == 10
        assert "curiosity" in blueprint.protagonist.values

    def test_create_from_invalid_template(self):
        """Test creating show from invalid template."""
        with pytest.raises(ValueError, match="Unknown template"):
            ShowBlueprintManager.create_from_template("invalid_template", "new_show")

    def test_save_and_load_with_characters(
        self, manager: ShowBlueprintManager, sample_blueprint: ShowBlueprint
    ):
        """Test saving and loading show with multiple characters."""
        char1 = Character(
            name="Character One",
            role="Helper",
            description="First character",
            personality="Helpful",
            voice_config={"provider": "mock"},
        )
        char2 = Character(
            name="Character Two",
            role="Guide",
            description="Second character",
            personality="Wise",
            voice_config={"provider": "mock"},
        )

        sample_blueprint.characters = [char1, char2]
        manager.save_show(sample_blueprint)

        loaded = manager.load_show("test_show")
        assert len(loaded.characters) == 2
        assert loaded.characters[0].name == "Character One"
        assert loaded.characters[1].name == "Character Two"

    def test_save_and_load_preserves_all_fields(
        self, manager: ShowBlueprintManager, sample_blueprint: ShowBlueprint
    ):
        """Test that save and load preserves all blueprint fields."""
        sample_blueprint.protagonist.catchphrases = ["Phrase 1", "Phrase 2"]
        sample_blueprint.world.rules = ["Rule A", "Rule B", "Rule C"]

        manager.save_show(sample_blueprint)
        loaded = manager.load_show("test_show")

        assert loaded.protagonist.catchphrases == ["Phrase 1", "Phrase 2"]
        assert loaded.world.rules == ["Rule A", "Rule B", "Rule C"]

    def test_image_path_validation(
        self, manager: ShowBlueprintManager, sample_blueprint: ShowBlueprint
    ):
        """Test that image paths are properly saved and loaded."""
        sample_blueprint.protagonist.image_path = "path/to/image.png"
        manager.save_show(sample_blueprint)

        loaded = manager.load_show("test_show")
        assert loaded.protagonist.image_path == "path/to/image.png"

    def test_load_show_with_episodes(
        self, manager: ShowBlueprintManager, sample_blueprint: ShowBlueprint
    ):
        """Test loading show correctly identifies episode directories."""
        manager.save_show(sample_blueprint)

        # Create episode directories
        episodes_dir = manager.shows_dir / "test_show" / "episodes"
        (episodes_dir / "ep001").mkdir()
        (episodes_dir / "ep002").mkdir()

        loaded = manager.load_show("test_show")
        assert len(loaded.episodes) == 2
        assert "ep001" in loaded.episodes
        assert "ep002" in loaded.episodes

    def test_concept_metadata_preservation(
        self, manager: ShowBlueprintManager, sample_blueprint: ShowBlueprint
    ):
        """Test that concept metadata is preserved."""
        manager.save_show(sample_blueprint)
        manager.add_concept("test_show", "Test Concept", "ep001")

        # Read the concepts file directly to verify metadata
        import json

        concepts_path = manager.shows_dir / "test_show" / "concepts_covered.json"
        with concepts_path.open("r") as f:
            data = json.load(f)

        assert len(data["concepts"]) == 1
        assert data["concepts"][0]["concept"] == "Test Concept"
        assert data["concepts"][0]["episode_id"] == "ep001"
        assert "covered_at" in data["concepts"][0]
        assert "last_updated" in data


class TestShowBlueprintManagerIntegration:
    """Integration tests for ShowBlueprintManager with real shows."""

    def test_load_olivers_workshop(self):
        """Test loading Oliver's Workshop show."""
        manager = ShowBlueprintManager()
        blueprint = manager.load_show("olivers_workshop")

        assert blueprint.show.show_id == "olivers_workshop"
        assert "Oliver" in blueprint.show.title
        assert blueprint.protagonist.name == "Oliver the Inventor"
        assert blueprint.protagonist.age == 8

    def test_load_hannah_show(self):
        """Test loading Hannah's show."""
        manager = ShowBlueprintManager()
        blueprint = manager.load_show("hannah")

        assert blueprint.show.show_id == "hannah"
        assert "Hannah" in blueprint.show.title
        assert blueprint.protagonist.name == "Hannah the Historian"
        assert blueprint.protagonist.age == 10

    def test_list_real_shows(self):
        """Test listing real shows in data/shows."""
        manager = ShowBlueprintManager()
        shows = manager.list_shows()

        assert len(shows) >= 2
        show_ids = [s.show_id for s in shows]
        assert "olivers_workshop" in show_ids
        assert "hannah" in show_ids
