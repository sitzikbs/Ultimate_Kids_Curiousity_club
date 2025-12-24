"""File-based storage for episodes with checkpoint support."""

import json
from datetime import datetime
from pathlib import Path
from typing import Any

from src.config import get_settings
from src.models.episode import Episode, PipelineStage
from src.utils.errors import EpisodeNotFoundError, StorageError


class EpisodeStorage:
    """Storage class for episode save/load operations with checkpointing."""

    def __init__(self, episodes_dir: Path | None = None):
        """Initialize the storage.

        Args:
            episodes_dir: Directory for episode storage (default: from settings)
        """
        self.episodes_dir = episodes_dir or get_settings().EPISODES_DIR

    def save_episode(self, episode: Episode) -> None:
        """Save episode to disk with atomic write.

        Args:
            episode: Episode to save

        Raises:
            StorageError: If saving fails
        """
        show_dir = self.episodes_dir / episode.show_id
        show_dir.mkdir(parents=True, exist_ok=True)

        episode_path = show_dir / f"{episode.episode_id}.json"
        temp_path = show_dir / f"{episode.episode_id}.tmp"

        try:
            # Update timestamp
            episode.updated_at = datetime.now()

            # Convert to dict
            episode_dict = self._episode_to_dict(episode)

            # Write to temporary file first (atomic write)
            with open(temp_path, "w") as f:
                json.dump(episode_dict, f, indent=2, default=str)

            # Rename to final location
            temp_path.replace(episode_path)

        except (OSError, json.JSONDecodeError) as e:
            if temp_path.exists():
                temp_path.unlink()
            raise StorageError(
                f"Failed to save episode '{episode.episode_id}': {e}",
                episode_id=episode.episode_id,
                show_id=episode.show_id,
            ) from e

    def load_episode(self, show_id: str, episode_id: str) -> Episode:
        """Load episode from disk.

        Args:
            show_id: Show identifier
            episode_id: Episode identifier

        Returns:
            Episode instance

        Raises:
            EpisodeNotFoundError: If episode doesn't exist
            StorageError: If loading fails
        """
        episode_path = self.episodes_dir / show_id / f"{episode_id}.json"

        if not episode_path.exists():
            raise EpisodeNotFoundError(
                f"Episode '{episode_id}' not found",
                episode_id=episode_id,
                show_id=show_id,
            )

        try:
            with open(episode_path) as f:
                episode_dict = json.load(f)

            return self._dict_to_episode(episode_dict)

        except (OSError, json.JSONDecodeError) as e:
            raise StorageError(
                f"Failed to load episode '{episode_id}': {e}",
                episode_id=episode_id,
                show_id=show_id,
            ) from e

    def save_checkpoint(
        self, episode: Episode, stage: PipelineStage, data: dict[str, Any] | None = None
    ) -> None:
        """Save checkpoint at a specific pipeline stage.

        Args:
            episode: Episode to checkpoint
            stage: Current pipeline stage
            data: Optional additional checkpoint data

        Raises:
            StorageError: If saving fails
        """
        episode.update_stage(stage)

        # Create checkpoint directory
        checkpoint_dir = (
            self.episodes_dir / episode.show_id / "checkpoints" / episode.episode_id
        )
        checkpoint_dir.mkdir(parents=True, exist_ok=True)

        # Save checkpoint data if provided
        if data:
            checkpoint_path = checkpoint_dir / f"{stage.value}.json"
            try:
                with open(checkpoint_path, "w") as f:
                    json.dump(
                        {
                            "stage": stage.value,
                            "timestamp": datetime.now().isoformat(),
                            "data": data,
                        },
                        f,
                        indent=2,
                        default=str,
                    )
            except (OSError, json.JSONDecodeError) as e:
                raise StorageError(
                    f"Failed to save checkpoint for episode "
                    f"'{episode.episode_id}': {e}",
                    episode_id=episode.episode_id,
                    show_id=episode.show_id,
                    stage=stage.value,
                ) from e

        # Save full episode state
        self.save_episode(episode)

    def load_checkpoint(
        self, show_id: str, episode_id: str, stage: PipelineStage
    ) -> dict[str, Any] | None:
        """Load checkpoint data for a specific stage.

        Args:
            show_id: Show identifier
            episode_id: Episode identifier
            stage: Pipeline stage to load

        Returns:
            Checkpoint data or None if not found

        Raises:
            StorageError: If loading fails
        """
        checkpoint_path = (
            self.episodes_dir
            / show_id
            / "checkpoints"
            / episode_id
            / f"{stage.value}.json"
        )

        if not checkpoint_path.exists():
            return None

        try:
            with open(checkpoint_path) as f:
                checkpoint = json.load(f)
                return checkpoint.get("data")

        except (OSError, json.JSONDecodeError) as e:
            raise StorageError(
                f"Failed to load checkpoint for episode '{episode_id}': {e}",
                episode_id=episode_id,
                show_id=show_id,
                stage=stage.value,
            ) from e

    def list_episodes(self, show_id: str) -> list[str]:
        """List all episodes for a show.

        Args:
            show_id: Show identifier

        Returns:
            List of episode IDs
        """
        show_dir = self.episodes_dir / show_id

        if not show_dir.exists():
            return []

        return [ep.stem for ep in show_dir.glob("*.json")]

    def delete_episode(self, show_id: str, episode_id: str) -> None:
        """Delete an episode and its checkpoints.

        Args:
            show_id: Show identifier
            episode_id: Episode identifier

        Raises:
            EpisodeNotFoundError: If episode doesn't exist
            StorageError: If deletion fails
        """
        episode_path = self.episodes_dir / show_id / f"{episode_id}.json"

        if not episode_path.exists():
            raise EpisodeNotFoundError(
                f"Episode '{episode_id}' not found",
                episode_id=episode_id,
                show_id=show_id,
            )

        try:
            # Delete episode file
            episode_path.unlink()

            # Delete checkpoints directory
            checkpoint_dir = self.episodes_dir / show_id / "checkpoints" / episode_id
            if checkpoint_dir.exists():
                for checkpoint_file in checkpoint_dir.glob("*.json"):
                    checkpoint_file.unlink()
                checkpoint_dir.rmdir()

        except OSError as e:
            raise StorageError(
                f"Failed to delete episode '{episode_id}': {e}",
                episode_id=episode_id,
                show_id=show_id,
            ) from e

    def _episode_to_dict(self, episode: Episode) -> dict[str, Any]:
        """Convert Episode to dict for JSON serialization.

        Args:
            episode: Episode to convert

        Returns:
            Dictionary representation
        """
        return {
            "episode_id": episode.episode_id,
            "show_id": episode.show_id,
            "topic": episode.topic,
            "title": episode.title,
            "outline": (
                episode.outline.model_dump(mode="json") if episode.outline else None
            ),
            "segments": [seg.model_dump(mode="json") for seg in episode.segments],
            "scripts": [script.model_dump(mode="json") for script in episode.scripts],
            "audio_path": str(episode.audio_path) if episode.audio_path else None,
            "current_stage": episode.current_stage.value,
            "approval_status": episode.approval_status.value,
            "approval_feedback": episode.approval_feedback,
            "created_at": episode.created_at.isoformat(),
            "updated_at": episode.updated_at.isoformat(),
            "cost_estimate": episode.cost_estimate,
        }

    def _dict_to_episode(self, data: dict[str, Any]) -> Episode:
        """Convert dict to Episode instance.

        Args:
            data: Episode data

        Returns:
            Episode instance
        """
        return Episode(
            episode_id=data["episode_id"],
            show_id=data["show_id"],
            topic=data["topic"],
            title=data.get("title", ""),
            outline=data.get("outline"),
            segments=data.get("segments", []),
            scripts=data.get("scripts", []),
            audio_path=data.get("audio_path"),
            current_stage=data.get("current_stage", PipelineStage.PENDING),
            approval_status=data.get("approval_status", "NOT_REQUIRED"),
            approval_feedback=data.get("approval_feedback", ""),
            created_at=data.get("created_at"),
            updated_at=data.get("updated_at"),
            cost_estimate=data.get("cost_estimate", 0.0),
        )
