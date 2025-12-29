"""Unit tests for episode storage."""

import json
from datetime import UTC, datetime
from pathlib import Path

import pytest

from models.episode import Episode, PipelineStage
from models.story import Script, ScriptBlock, StoryBeat, StoryOutline, StorySegment
from modules.episode_storage import EpisodeStorage
from utils.errors import StorageError, ValidationError


@pytest.fixture
def temp_storage(tmp_path: Path) -> EpisodeStorage:
    """Create temporary storage directory for tests."""
    shows_dir = tmp_path / "shows"
    shows_dir.mkdir()
    return EpisodeStorage(shows_dir=shows_dir)


@pytest.fixture
def sample_episode() -> Episode:
    """Create a sample episode for testing."""
    return Episode(
        episode_id="test_ep001",
        show_id="test_show",
        topic="How rockets work",
        title="Journey to the Stars",
        current_stage=PipelineStage.IDEATION,
        created_at=datetime.now(UTC),
        updated_at=datetime.now(UTC),
    )


@pytest.fixture
def episode_with_outline(sample_episode: Episode) -> Episode:
    """Create episode with outline."""
    sample_episode.outline = StoryOutline(
        episode_id=sample_episode.episode_id,
        show_id=sample_episode.show_id,
        topic=sample_episode.topic,
        title=sample_episode.title,
        educational_concept="Newton's Third Law",
        story_beats=[
            StoryBeat(
                beat_number=1,
                title="Introduction to Rockets",
                description="Learn what makes rockets fly",
                educational_focus="Basic rocket principles",
                key_moments=["Rocket launch", "How engines work"],
            )
        ],
    )
    sample_episode.current_stage = PipelineStage.OUTLINING
    return sample_episode


@pytest.fixture
def episode_with_segments(episode_with_outline: Episode) -> Episode:
    """Create episode with segments."""
    episode_with_outline.segments = [
        StorySegment(
            segment_number=1,
            beat_number=1,
            description="Opening scene",
            characters_involved=["narrator", "oliver"],
            setting="Launch pad",
            educational_content="Rocket basics",
        ),
        StorySegment(
            segment_number=2,
            beat_number=1,
            description="Explanation scene",
            characters_involved=["oliver", "hannah"],
            setting="Mission control",
            educational_content="Newton's Third Law",
        ),
    ]
    episode_with_outline.current_stage = PipelineStage.SEGMENT_GENERATION
    return episode_with_outline


@pytest.fixture
def episode_with_scripts(episode_with_segments: Episode) -> Episode:
    """Create episode with scripts."""
    episode_with_segments.scripts = [
        Script(
            segment_number=1,
            script_blocks=[
                ScriptBlock(
                    speaker="narrator",
                    text="Welcome to our rocket adventure!",
                    speaker_voice_id="voice_001",
                    duration_estimate=3.5,
                ),
                ScriptBlock(
                    speaker="oliver",
                    text="I can't wait to learn about rockets!",
                    speaker_voice_id="voice_002",
                    duration_estimate=2.8,
                ),
            ],
        ),
        Script(
            segment_number=2,
            script_blocks=[
                ScriptBlock(
                    speaker="hannah",
                    text="Let me explain Newton's Third Law...",
                    speaker_voice_id="voice_003",
                    duration_estimate=4.2,
                ),
            ],
        ),
    ]
    episode_with_segments.current_stage = PipelineStage.SCRIPT_GENERATION
    return episode_with_segments


class TestEpisodeStorageBasics:
    """Test basic episode storage operations."""

    def test_initialization_default_path(self):
        """Test storage initialization with default path from config."""
        storage = EpisodeStorage()
        assert storage.shows_dir.exists()

    def test_initialization_custom_path(self, tmp_path: Path):
        """Test storage initialization with custom path."""
        custom_dir = tmp_path / "custom_shows"
        storage = EpisodeStorage(shows_dir=custom_dir)
        assert storage.shows_dir == custom_dir
        assert custom_dir.exists()

    def test_get_episode_path(self, temp_storage: EpisodeStorage):
        """Test getting episode path."""
        path = temp_storage.get_episode_path("test_show", "ep001")
        assert path == temp_storage.shows_dir / "test_show" / "episodes" / "ep001"


class TestSaveLoadEpisode:
    """Test save and load operations."""

    def test_save_episode_creates_directory(
        self, temp_storage: EpisodeStorage, sample_episode: Episode
    ):
        """Test that save creates episode directory structure."""
        temp_storage.save_episode(sample_episode)

        episode_path = temp_storage.get_episode_path(
            sample_episode.show_id, sample_episode.episode_id
        )
        assert episode_path.exists()
        assert (episode_path / "episode.json").exists()
        assert (episode_path / "audio").exists()

    def test_save_episode_updates_timestamp(
        self, temp_storage: EpisodeStorage, sample_episode: Episode
    ):
        """Test that save updates the updated_at timestamp."""
        original_time = sample_episode.updated_at
        temp_storage.save_episode(sample_episode)

        loaded = temp_storage.load_episode(
            sample_episode.show_id, sample_episode.episode_id
        )
        assert loaded.updated_at >= original_time

    def test_load_episode_success(
        self, temp_storage: EpisodeStorage, sample_episode: Episode
    ):
        """Test successfully loading an episode."""
        temp_storage.save_episode(sample_episode)
        loaded = temp_storage.load_episode(
            sample_episode.show_id, sample_episode.episode_id
        )

        assert loaded.episode_id == sample_episode.episode_id
        assert loaded.show_id == sample_episode.show_id
        assert loaded.title == sample_episode.title
        assert loaded.topic == sample_episode.topic

    def test_load_nonexistent_episode(self, temp_storage: EpisodeStorage):
        """Test loading non-existent episode raises error."""
        with pytest.raises(StorageError, match="Episode not found"):
            temp_storage.load_episode("nonexistent_show", "nonexistent_ep")

    def test_save_episode_without_id(self, temp_storage: EpisodeStorage):
        """Test saving episode without ID raises error."""
        episode = Episode(
            episode_id="",
            show_id="test_show",
            topic="Test",
            title="Test",
        )

        with pytest.raises(ValidationError, match="episode_id"):
            temp_storage.save_episode(episode)

    def test_save_episode_without_show_id(self, temp_storage: EpisodeStorage):
        """Test saving episode without show ID raises error."""
        episode = Episode(
            episode_id="test_ep",
            show_id="",
            topic="Test",
            title="Test",
        )

        with pytest.raises(ValidationError, match="show_id"):
            temp_storage.save_episode(episode)

    def test_save_and_load_preserves_data(
        self, temp_storage: EpisodeStorage, episode_with_scripts: Episode
    ):
        """Test that save/load cycle preserves all episode data."""
        temp_storage.save_episode(episode_with_scripts)
        loaded = temp_storage.load_episode(
            episode_with_scripts.show_id, episode_with_scripts.episode_id
        )

        # Check basic fields
        assert loaded.episode_id == episode_with_scripts.episode_id
        assert loaded.topic == episode_with_scripts.topic
        assert loaded.title == episode_with_scripts.title

        # Check outline
        assert loaded.outline is not None
        assert (
            loaded.outline.educational_concept
            == episode_with_scripts.outline.educational_concept
        )

        # Check segments
        assert len(loaded.segments) == len(episode_with_scripts.segments)
        assert (
            loaded.segments[0].description
            == episode_with_scripts.segments[0].description
        )

        # Check scripts
        assert len(loaded.scripts) == len(episode_with_scripts.scripts)
        assert len(loaded.scripts[0].script_blocks) == len(
            episode_with_scripts.scripts[0].script_blocks
        )


class TestCheckpointOperations:
    """Test checkpoint save and load functionality."""

    def test_save_checkpoint_outlining(
        self, temp_storage: EpisodeStorage, episode_with_outline: Episode
    ):
        """Test saving outline checkpoint."""
        temp_storage.save_checkpoint(episode_with_outline, PipelineStage.OUTLINING)

        episode_path = temp_storage.get_episode_path(
            episode_with_outline.show_id, episode_with_outline.episode_id
        )
        checkpoint_file = episode_path / "outline.json"

        assert checkpoint_file.exists()

        # Verify checkpoint content
        with open(checkpoint_file) as f:
            data = json.load(f)
            assert data["stage"] == PipelineStage.OUTLINING.value
            assert data["episode_id"] == episode_with_outline.episode_id
            assert "outline" in data

    def test_save_checkpoint_segments(
        self, temp_storage: EpisodeStorage, episode_with_segments: Episode
    ):
        """Test saving segments checkpoint."""
        temp_storage.save_checkpoint(
            episode_with_segments, PipelineStage.SEGMENT_GENERATION
        )

        episode_path = temp_storage.get_episode_path(
            episode_with_segments.show_id, episode_with_segments.episode_id
        )
        checkpoint_file = episode_path / "segments.json"

        assert checkpoint_file.exists()

        # Verify checkpoint content
        with open(checkpoint_file) as f:
            data = json.load(f)
            assert data["stage"] == PipelineStage.SEGMENT_GENERATION.value
            assert "segments" in data
            assert len(data["segments"]) == 2

    def test_save_checkpoint_scripts(
        self, temp_storage: EpisodeStorage, episode_with_scripts: Episode
    ):
        """Test saving scripts checkpoint."""
        temp_storage.save_checkpoint(
            episode_with_scripts, PipelineStage.SCRIPT_GENERATION
        )

        episode_path = temp_storage.get_episode_path(
            episode_with_scripts.show_id, episode_with_scripts.episode_id
        )
        checkpoint_file = episode_path / "scripts.json"

        assert checkpoint_file.exists()

        # Verify checkpoint content
        with open(checkpoint_file) as f:
            data = json.load(f)
            assert data["stage"] == PipelineStage.SCRIPT_GENERATION.value
            assert "scripts" in data
            assert len(data["scripts"]) == 2

    def test_save_checkpoint_also_saves_episode(
        self, temp_storage: EpisodeStorage, episode_with_outline: Episode
    ):
        """Test that checkpoint save also updates main episode file."""
        temp_storage.save_checkpoint(episode_with_outline, PipelineStage.OUTLINING)

        # Verify main episode file exists and is up-to-date
        episode_path = temp_storage.get_episode_path(
            episode_with_outline.show_id, episode_with_outline.episode_id
        )
        episode_file = episode_path / "episode.json"

        assert episode_file.exists()

        # Load and verify
        loaded = temp_storage.load_episode(
            episode_with_outline.show_id, episode_with_outline.episode_id
        )
        assert loaded.outline is not None


class TestListDeleteOperations:
    """Test list and delete operations."""

    def test_list_episodes_empty_show(self, temp_storage: EpisodeStorage):
        """Test listing episodes for show with no episodes."""
        episodes = temp_storage.list_episodes("nonexistent_show")
        assert episodes == []

    def test_list_episodes_single(
        self, temp_storage: EpisodeStorage, sample_episode: Episode
    ):
        """Test listing episodes with one episode."""
        temp_storage.save_episode(sample_episode)
        episodes = temp_storage.list_episodes(sample_episode.show_id)

        assert len(episodes) == 1
        assert episodes[0] == sample_episode.episode_id

    def test_list_episodes_multiple(self, temp_storage: EpisodeStorage):
        """Test listing multiple episodes."""
        # Create multiple episodes
        for i in range(3):
            episode = Episode(
                episode_id=f"ep_{i:03d}",
                show_id="test_show",
                topic=f"Topic {i}",
                title=f"Title {i}",
            )
            temp_storage.save_episode(episode)

        episodes = temp_storage.list_episodes("test_show")
        assert len(episodes) == 3
        # Should be sorted
        assert episodes == ["ep_000", "ep_001", "ep_002"]

    def test_delete_episode_success(
        self, temp_storage: EpisodeStorage, sample_episode: Episode
    ):
        """Test successfully deleting an episode."""
        temp_storage.save_episode(sample_episode)
        episode_path = temp_storage.get_episode_path(
            sample_episode.show_id, sample_episode.episode_id
        )

        assert episode_path.exists()

        temp_storage.delete_episode(sample_episode.show_id, sample_episode.episode_id)

        assert not episode_path.exists()

    def test_delete_nonexistent_episode(self, temp_storage: EpisodeStorage):
        """Test deleting non-existent episode raises error."""
        with pytest.raises(StorageError, match="Episode not found"):
            temp_storage.delete_episode("test_show", "nonexistent_ep")

    def test_delete_episode_with_checkpoints(
        self, temp_storage: EpisodeStorage, episode_with_scripts: Episode
    ):
        """Test deleting episode removes all checkpoints."""
        # Save episode with multiple checkpoints
        temp_storage.save_checkpoint(episode_with_scripts, PipelineStage.OUTLINING)
        temp_storage.save_checkpoint(
            episode_with_scripts, PipelineStage.SEGMENT_GENERATION
        )
        temp_storage.save_checkpoint(
            episode_with_scripts, PipelineStage.SCRIPT_GENERATION
        )

        episode_path = temp_storage.get_episode_path(
            episode_with_scripts.show_id, episode_with_scripts.episode_id
        )

        # Verify checkpoints exist
        assert (episode_path / "outline.json").exists()
        assert (episode_path / "segments.json").exists()
        assert (episode_path / "scripts.json").exists()

        # Delete episode
        temp_storage.delete_episode(
            episode_with_scripts.show_id, episode_with_scripts.episode_id
        )

        # Verify everything is gone
        assert not episode_path.exists()


class TestAtomicWriteAndLocking:
    """Test atomic write and file locking mechanisms."""

    def test_atomic_write_creates_temp_file(
        self, temp_storage: EpisodeStorage, sample_episode: Episode, tmp_path: Path
    ):
        """Test that atomic write uses temporary file."""
        test_file = tmp_path / "test.json"
        content = "test content"

        # Atomic write should work
        temp_storage._atomic_write(test_file, content)

        assert test_file.exists()
        assert test_file.read_text() == content

        # Temp file should be cleaned up
        assert not test_file.with_suffix(".json.tmp").exists()

    def test_corrupted_json_raises_error(
        self, temp_storage: EpisodeStorage, sample_episode: Episode
    ):
        """Test that loading corrupted JSON raises StorageError."""
        temp_storage.save_episode(sample_episode)

        episode_path = temp_storage.get_episode_path(
            sample_episode.show_id, sample_episode.episode_id
        )
        episode_file = episode_path / "episode.json"

        # Corrupt the file
        episode_file.write_text("{ invalid json }")

        with pytest.raises(StorageError, match="Invalid JSON"):
            temp_storage.load_episode(sample_episode.show_id, sample_episode.episode_id)


class TestEdgeCases:
    """Test edge cases and error handling."""

    def test_save_episode_with_special_characters_in_id(
        self, temp_storage: EpisodeStorage
    ):
        """Test saving episode with special characters."""
        episode = Episode(
            episode_id="ep_001_test-v2",
            show_id="show-test_v1",
            topic="Test topic",
            title="Test title",
        )

        temp_storage.save_episode(episode)
        loaded = temp_storage.load_episode(episode.show_id, episode.episode_id)

        assert loaded.episode_id == episode.episode_id

    def test_concurrent_save_load(
        self, temp_storage: EpisodeStorage, sample_episode: Episode
    ):
        """Test saving and loading work correctly in sequence."""
        # Save episode
        temp_storage.save_episode(sample_episode)

        # Modify and save again
        sample_episode.title = "Updated Title"
        temp_storage.save_episode(sample_episode)

        # Load and verify latest version
        loaded = temp_storage.load_episode(
            sample_episode.show_id, sample_episode.episode_id
        )
        assert loaded.title == "Updated Title"
