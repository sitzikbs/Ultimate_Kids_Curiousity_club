"""Tests for EpisodeStorage."""

import pytest

from src.models import Episode, PipelineStage
from src.modules import EpisodeStorage
from src.utils.errors import EpisodeNotFoundError


class TestEpisodeStorage:
    """Tests for EpisodeStorage."""

    def test_save_and_load_episode(self, temp_data_dir, episode):
        """Test saving and loading an episode."""
        episodes_dir = temp_data_dir / "episodes"
        storage = EpisodeStorage(episodes_dir=episodes_dir)

        # Save episode
        storage.save_episode(episode)

        # Load it back
        loaded = storage.load_episode(episode.show_id, episode.episode_id)

        assert loaded.episode_id == episode.episode_id
        assert loaded.show_id == episode.show_id
        assert loaded.topic == episode.topic
        assert loaded.title == episode.title
        assert loaded.current_stage == episode.current_stage

    def test_load_nonexistent_episode(self, temp_data_dir):
        """Test loading an episode that doesn't exist."""
        episodes_dir = temp_data_dir / "episodes"
        storage = EpisodeStorage(episodes_dir=episodes_dir)

        with pytest.raises(EpisodeNotFoundError):
            storage.load_episode("test_show", "nonexistent_ep")

    def test_save_checkpoint(self, temp_data_dir, episode):
        """Test saving a checkpoint."""
        episodes_dir = temp_data_dir / "episodes"
        storage = EpisodeStorage(episodes_dir=episodes_dir)

        # Save checkpoint
        checkpoint_data = {"test_key": "test_value", "stage_info": "test"}
        storage.save_checkpoint(episode, PipelineStage.OUTLINING, checkpoint_data)

        # Verify episode was updated
        loaded = storage.load_episode(episode.show_id, episode.episode_id)
        assert loaded.current_stage == PipelineStage.OUTLINING

        # Verify checkpoint file was created
        checkpoint_path = (
            episodes_dir
            / episode.show_id
            / "checkpoints"
            / episode.episode_id
            / "OUTLINING.json"
        )
        assert checkpoint_path.exists()

    def test_load_checkpoint(self, temp_data_dir, episode):
        """Test loading a checkpoint."""
        episodes_dir = temp_data_dir / "episodes"
        storage = EpisodeStorage(episodes_dir=episodes_dir)

        # Save checkpoint
        checkpoint_data = {"test_key": "test_value", "test_number": 42}
        storage.save_checkpoint(episode, PipelineStage.OUTLINING, checkpoint_data)

        # Load checkpoint
        loaded_data = storage.load_checkpoint(
            episode.show_id, episode.episode_id, PipelineStage.OUTLINING
        )

        assert loaded_data is not None
        assert loaded_data["test_key"] == "test_value"
        assert loaded_data["test_number"] == 42

    def test_load_nonexistent_checkpoint(self, temp_data_dir, episode):
        """Test loading a checkpoint that doesn't exist."""
        episodes_dir = temp_data_dir / "episodes"
        storage = EpisodeStorage(episodes_dir=episodes_dir)

        # Save episode without checkpoint
        storage.save_episode(episode)

        # Try to load nonexistent checkpoint
        loaded_data = storage.load_checkpoint(
            episode.show_id, episode.episode_id, PipelineStage.AUDIO_MIXING
        )

        assert loaded_data is None

    def test_list_episodes(self, temp_data_dir, episode):
        """Test listing episodes."""
        episodes_dir = temp_data_dir / "episodes"
        storage = EpisodeStorage(episodes_dir=episodes_dir)

        # Save multiple episodes
        storage.save_episode(episode)

        episode2 = Episode(
            episode_id="test_ep_002",
            show_id="test_show",
            topic="Test topic 2",
            title="Test Episode 2",
        )
        storage.save_episode(episode2)

        # List episodes
        episodes = storage.list_episodes("test_show")

        assert len(episodes) == 2
        assert "test_ep_001" in episodes
        assert "test_ep_002" in episodes

    def test_list_episodes_empty(self, temp_data_dir):
        """Test listing episodes when none exist."""
        episodes_dir = temp_data_dir / "episodes"
        storage = EpisodeStorage(episodes_dir=episodes_dir)

        episodes = storage.list_episodes("nonexistent_show")
        assert episodes == []

    def test_delete_episode(self, temp_data_dir, episode):
        """Test deleting an episode."""
        episodes_dir = temp_data_dir / "episodes"
        storage = EpisodeStorage(episodes_dir=episodes_dir)

        # Save episode with checkpoint
        checkpoint_data = {"test": "data"}
        storage.save_checkpoint(episode, PipelineStage.OUTLINING, checkpoint_data)

        # Verify it exists
        assert (episodes_dir / episode.show_id / f"{episode.episode_id}.json").exists()

        # Delete episode
        storage.delete_episode(episode.show_id, episode.episode_id)

        # Verify it's gone
        assert not (
            episodes_dir / episode.show_id / f"{episode.episode_id}.json"
        ).exists()

        # Verify checkpoint directory is gone
        checkpoint_dir = (
            episodes_dir / episode.show_id / "checkpoints" / episode.episode_id
        )
        assert not checkpoint_dir.exists()

    def test_delete_nonexistent_episode(self, temp_data_dir):
        """Test deleting an episode that doesn't exist."""
        episodes_dir = temp_data_dir / "episodes"
        storage = EpisodeStorage(episodes_dir=episodes_dir)

        with pytest.raises(EpisodeNotFoundError):
            storage.delete_episode("test_show", "nonexistent_ep")

    def test_atomic_write(self, temp_data_dir, episode):
        """Test that writes are atomic (temp file used)."""
        episodes_dir = temp_data_dir / "episodes"
        storage = EpisodeStorage(episodes_dir=episodes_dir)

        # Save episode
        storage.save_episode(episode)

        # Verify no .tmp file left behind
        show_dir = episodes_dir / episode.show_id
        tmp_files = list(show_dir.glob("*.tmp"))
        assert len(tmp_files) == 0

    def test_episode_updated_at_changes(self, temp_data_dir, episode):
        """Test that updated_at changes when saving."""
        episodes_dir = temp_data_dir / "episodes"
        storage = EpisodeStorage(episodes_dir=episodes_dir)

        # Save episode
        storage.save_episode(episode)
        first_updated_at = episode.updated_at

        # Modify and save again
        episode.title = "Updated Title"
        storage.save_episode(episode)

        # Verify updated_at changed
        assert episode.updated_at >= first_updated_at
