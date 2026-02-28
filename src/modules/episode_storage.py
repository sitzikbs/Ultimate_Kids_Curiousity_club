"""Episode storage module for file-based persistence.

This module provides the EpisodeStorage class for managing episode data
persistence, including checkpoint saving/loading, atomic writes, and file
locking for concurrent access.

Note: File locking requires Unix-like systems (Linux, macOS). The fcntl module
is used for file locking operations.
"""

import fcntl  # Unix-specific file locking
import json
import shutil
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from models.episode import Episode, PipelineStage
from utils.errors import StorageError, ValidationError


class EpisodeStorage:
    """Manages episode file persistence with checkpoint support.

    Provides methods for saving/loading episodes, managing checkpoints at different
    pipeline stages, and ensuring data integrity through atomic writes and file locking.
    """

    def __init__(self, shows_dir: Path | None = None) -> None:
        """Initialize storage with shows directory.

        Args:
            shows_dir: Path to shows directory. If None, uses config default.
        """
        if shows_dir is None:
            from config import get_settings

            shows_dir = get_settings().SHOWS_DIR

        self.shows_dir = Path(shows_dir)
        self.shows_dir.mkdir(parents=True, exist_ok=True)

    def get_episode_path(self, show_id: str, episode_id: str) -> Path:
        """Get path to episode directory.

        Args:
            show_id: Show identifier
            episode_id: Episode identifier

        Returns:
            Path to episode directory
        """
        return self.shows_dir / show_id / "episodes" / episode_id

    def save_episode(self, episode: Episode) -> None:
        """Save episode to disk with atomic write.

        Creates episode directory structure and saves the complete episode data.
        Updates the updated_at timestamp automatically.

        Args:
            episode: Episode to save

        Raises:
            StorageError: If save operation fails
            ValidationError: If episode data is invalid
        """
        if not episode.episode_id:
            raise ValidationError("Episode must have an episode_id", episode=episode)

        if not episode.show_id:
            raise ValidationError("Episode must have a show_id", episode=episode)

        # Update timestamp
        episode.updated_at = datetime.now(UTC)

        # Get episode path and create directory
        episode_path = self.get_episode_path(episode.show_id, episode.episode_id)
        episode_path.mkdir(parents=True, exist_ok=True)

        # Create audio subdirectory
        audio_dir = episode_path / "audio"
        audio_dir.mkdir(exist_ok=True)

        # Save episode with atomic write
        episode_file = episode_path / "episode.json"
        self._atomic_write(episode_file, episode.model_dump_json(indent=2))

    def load_episode(self, show_id: str, episode_id: str) -> Episode:
        """Load episode from disk.

        Args:
            show_id: Show identifier
            episode_id: Episode identifier

        Returns:
            Loaded Episode object

        Raises:
            StorageError: If episode file not found or invalid
        """
        episode_path = self.get_episode_path(show_id, episode_id)
        episode_file = episode_path / "episode.json"

        if not episode_file.exists():
            raise StorageError(
                f"Episode not found: {episode_id}",
                show_id=show_id,
                episode_id=episode_id,
                path=str(episode_file),
            )

        try:
            with open(episode_file, encoding="utf-8") as f:
                # Use fcntl for file locking (Unix-like systems)
                try:
                    fcntl.flock(f.fileno(), fcntl.LOCK_SH | fcntl.LOCK_NB)
                except OSError as e:
                    raise StorageError(
                        f"Could not acquire lock on episode file: {episode_id}",
                        show_id=show_id,
                        episode_id=episode_id,
                        error=str(e),
                    )

                try:
                    data = json.load(f)
                    return Episode.model_validate(data)
                finally:
                    fcntl.flock(f.fileno(), fcntl.LOCK_UN)

        except json.JSONDecodeError as e:
            raise StorageError(
                f"Invalid JSON in episode file: {episode_id}",
                show_id=show_id,
                episode_id=episode_id,
                error=str(e),
            )
        except Exception as e:
            if isinstance(e, StorageError):
                raise
            raise StorageError(
                f"Failed to load episode: {episode_id}",
                show_id=show_id,
                episode_id=episode_id,
                error=str(e),
            )

    def save_checkpoint(self, episode: Episode, stage: PipelineStage) -> None:
        """Save intermediate state at pipeline stage.

        Saves a checkpoint file for the specified pipeline stage, allowing
        the pipeline to resume from this point if needed.

        Args:
            episode: Episode with data to checkpoint
            stage: Pipeline stage to save

        Raises:
            StorageError: If checkpoint save fails
        """
        episode_path = self.get_episode_path(episode.show_id, episode.episode_id)
        episode_path.mkdir(parents=True, exist_ok=True)

        # Determine checkpoint filename based on stage
        checkpoint_files = {
            PipelineStage.IDEATION: "concept.json",
            PipelineStage.OUTLINING: "outline.json",
            PipelineStage.SEGMENT_GENERATION: "segments.json",
            PipelineStage.SCRIPT_GENERATION: "scripts.json",
            PipelineStage.AUDIO_SYNTHESIS: "audio_segments.json",
            PipelineStage.AUDIO_MIXING: "audio_mix.json",
        }

        checkpoint_file = checkpoint_files.get(stage)
        if not checkpoint_file:
            # For other stages, just save the full episode
            self.save_episode(episode)
            return

        checkpoint_path = episode_path / checkpoint_file

        # Prepare checkpoint data based on stage
        checkpoint_data: dict[str, Any] = {
            "stage": stage.value,
            "episode_id": episode.episode_id,
            "show_id": episode.show_id,
            "saved_at": datetime.now(UTC).isoformat(),
        }

        if stage == PipelineStage.IDEATION and episode.concept:
            checkpoint_data["concept"] = episode.concept
        elif stage == PipelineStage.OUTLINING and episode.outline:
            # Use model_dump with mode='json' to properly serialize datetime objects
            checkpoint_data["outline"] = episode.outline.model_dump(mode="json")
        elif stage == PipelineStage.SEGMENT_GENERATION and episode.segments:
            checkpoint_data["segments"] = [
                seg.model_dump(mode="json") for seg in episode.segments
            ]
        elif stage == PipelineStage.SCRIPT_GENERATION and episode.scripts:
            checkpoint_data["scripts"] = [
                script.model_dump(mode="json") for script in episode.scripts
            ]
        elif stage == PipelineStage.AUDIO_SYNTHESIS and episode.audio_segment_paths:
            checkpoint_data["audio_segment_paths"] = episode.audio_segment_paths
        elif stage == PipelineStage.AUDIO_MIXING and episode.audio_path:
            checkpoint_data["audio_path"] = episode.audio_path

        # Save checkpoint with atomic write
        self._atomic_write(checkpoint_path, json.dumps(checkpoint_data, indent=2))

        # Also update the main episode file
        self.save_episode(episode)

    def list_episodes(self, show_id: str) -> list[str]:
        """List all episode IDs for a show.

        Args:
            show_id: Show identifier

        Returns:
            List of episode IDs

        Raises:
            StorageError: If show directory doesn't exist
        """
        show_path = self.shows_dir / show_id / "episodes"

        if not show_path.exists():
            return []

        try:
            # List all directories in the episodes folder
            episode_ids = [
                d.name
                for d in show_path.iterdir()
                if d.is_dir() and (d / "episode.json").exists()
            ]
            return sorted(episode_ids)
        except Exception as e:
            raise StorageError(
                f"Failed to list episodes for show: {show_id}",
                show_id=show_id,
                error=str(e),
            )

    def delete_episode(self, show_id: str, episode_id: str) -> None:
        """Delete episode and all associated files.

        Args:
            show_id: Show identifier
            episode_id: Episode identifier

        Raises:
            StorageError: If deletion fails
        """
        episode_path = self.get_episode_path(show_id, episode_id)

        if not episode_path.exists():
            raise StorageError(
                f"Episode not found: {episode_id}",
                show_id=show_id,
                episode_id=episode_id,
            )

        try:
            shutil.rmtree(episode_path)
        except Exception as e:
            raise StorageError(
                f"Failed to delete episode: {episode_id}",
                show_id=show_id,
                episode_id=episode_id,
                error=str(e),
            )

    def _atomic_write(self, path: Path, content: str) -> None:
        """Write file atomically to prevent corruption.

        Writes to a temporary file first, then renames it to the target path.
        The rename operation is atomic on POSIX systems.

        Args:
            path: Target file path
            content: Content to write

        Raises:
            StorageError: If write operation fails
        """
        tmp_path = path.with_suffix(path.suffix + ".tmp")

        try:
            # Write to temporary file with exclusive lock
            with open(tmp_path, "w", encoding="utf-8") as f:
                try:
                    fcntl.flock(f.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
                except OSError as e:
                    raise StorageError(
                        "Could not acquire exclusive lock for writing",
                        path=str(path),
                        error=str(e),
                    )

                try:
                    f.write(content)
                    f.flush()
                finally:
                    fcntl.flock(f.fileno(), fcntl.LOCK_UN)

            # Atomic rename
            tmp_path.rename(path)

        except Exception as e:
            # Clean up temporary file if it exists
            if tmp_path.exists():
                try:
                    tmp_path.unlink()
                except Exception:
                    pass

            if isinstance(e, StorageError):
                raise

            raise StorageError(
                "Failed to write file atomically",
                path=str(path),
                error=str(e),
            )
