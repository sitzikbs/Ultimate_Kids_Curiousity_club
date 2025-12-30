"""Tests for API routes (shows and episodes)."""

from datetime import UTC, datetime
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from api.main import app
from config import get_settings
from models.episode import Episode, PipelineStage
from models.show import (
    ConceptsHistory,
    Protagonist,
    Show,
    ShowBlueprint,
    WorldDescription,
)
from modules.episode_storage import EpisodeStorage
from modules.show_blueprint_manager import ShowBlueprintManager


@pytest.fixture
def test_shows_dir(tmp_path: Path) -> Path:
    """Create temporary shows directory."""
    shows_dir = tmp_path / "shows"
    shows_dir.mkdir()
    return shows_dir


@pytest.fixture
def client(test_shows_dir: Path) -> TestClient:
    """Create test client with temporary directory."""
    # Override settings
    settings = get_settings()
    settings.SHOWS_DIR = test_shows_dir

    # Create test client
    return TestClient(app)


@pytest.fixture
def sample_show(test_shows_dir: Path) -> ShowBlueprint:
    """Create and save sample show."""
    blueprint = ShowBlueprint(
        show=Show(
            show_id="test_show",
            title="Test Show",
            description="A test show",
            theme="Testing",
            narrator_voice_config={"provider": "mock", "voice_id": "test"},
        ),
        protagonist=Protagonist(
            name="Test Hero",
            age=10,
            description="A test protagonist",
            values=["courage", "curiosity"],
            voice_config={"provider": "mock", "voice_id": "test_hero"},
        ),
        world=WorldDescription(
            setting="Test World",
            rules=["Test rule 1", "Test rule 2"],
            atmosphere="Test atmosphere",
        ),
        characters=[],
        concepts_history=ConceptsHistory(concepts=[], last_updated=datetime.now(UTC)),
        episodes=[],
    )

    manager = ShowBlueprintManager(shows_dir=test_shows_dir)
    manager.save_show(blueprint)
    return blueprint


@pytest.fixture
def sample_episode(test_shows_dir: Path, sample_show: ShowBlueprint) -> Episode:
    """Create and save sample episode."""
    episode = Episode(
        episode_id="test_episode",
        show_id="test_show",
        topic="Test Topic",
        title="Test Episode",
        current_stage=PipelineStage.PENDING,
    )

    storage = EpisodeStorage(shows_dir=test_shows_dir)
    storage.save_episode(episode)

    # Update show to include episode
    sample_show.episodes.append("test_episode")
    manager = ShowBlueprintManager(shows_dir=test_shows_dir)
    manager.save_show(sample_show)

    return episode


class TestHealthEndpoint:
    """Tests for health check endpoint."""

    def test_health_check(self, client: TestClient) -> None:
        """Test health check endpoint."""
        response = client.get("/health")
        assert response.status_code == 200

        data = response.json()
        assert data["status"] == "healthy"
        assert "timestamp" in data


class TestShowEndpoints:
    """Tests for show endpoints."""

    def test_list_shows_empty(self, client: TestClient) -> None:
        """Test listing shows when none exist."""
        response = client.get("/api/shows")
        assert response.status_code == 200
        assert response.json() == []

    def test_list_shows(self, client: TestClient, sample_show: ShowBlueprint) -> None:
        """Test listing shows."""
        response = client.get("/api/shows")
        assert response.status_code == 200

        data = response.json()
        assert len(data) == 1
        assert data[0]["show_id"] == "test_show"
        assert data[0]["title"] == "Test Show"

    def test_get_show(self, client: TestClient, sample_show: ShowBlueprint) -> None:
        """Test getting show details."""
        response = client.get("/api/shows/test_show")
        assert response.status_code == 200

        data = response.json()
        assert data["show"]["show_id"] == "test_show"
        assert data["protagonist"]["name"] == "Test Hero"
        assert data["world"]["setting"] == "Test World"

    def test_get_show_not_found(self, client: TestClient) -> None:
        """Test getting non-existent show."""
        response = client.get("/api/shows/nonexistent")
        assert response.status_code == 404

    def test_update_show_protagonist(
        self, client: TestClient, sample_show: ShowBlueprint
    ) -> None:
        """Test updating show protagonist."""
        update_data = {
            "protagonist": {
                "name": "Updated Hero",
                "age": 12,
                "description": "An updated protagonist",
                "values": ["bravery"],
                "voice_config": {"provider": "mock", "voice_id": "updated"},
            }
        }

        response = client.put("/api/shows/test_show", json=update_data)
        assert response.status_code == 200

        data = response.json()
        assert data["protagonist"]["name"] == "Updated Hero"
        assert data["protagonist"]["age"] == 12

    def test_update_show_world(
        self, client: TestClient, sample_show: ShowBlueprint
    ) -> None:
        """Test updating show world."""
        update_data = {
            "world": {
                "setting": "Updated World",
                "rules": ["New rule"],
                "atmosphere": "Updated atmosphere",
            }
        }

        response = client.put("/api/shows/test_show", json=update_data)
        assert response.status_code == 200

        data = response.json()
        assert data["world"]["setting"] == "Updated World"

    def test_update_show_not_found(self, client: TestClient) -> None:
        """Test updating non-existent show."""
        update_data = {"protagonist": {"name": "Test"}}
        response = client.put("/api/shows/nonexistent", json=update_data)
        assert response.status_code == 404


class TestEpisodeEndpoints:
    """Tests for episode endpoints."""

    def test_list_episodes_empty(
        self, client: TestClient, sample_show: ShowBlueprint
    ) -> None:
        """Test listing episodes when none exist."""
        response = client.get("/api/shows/test_show/episodes")
        assert response.status_code == 200
        assert response.json() == []

    def test_list_episodes(self, client: TestClient, sample_episode: Episode) -> None:
        """Test listing episodes."""
        response = client.get("/api/shows/test_show/episodes")
        assert response.status_code == 200

        data = response.json()
        assert len(data) == 1
        assert data[0]["episode_id"] == "test_episode"
        assert data[0]["title"] == "Test Episode"

    def test_get_episode(self, client: TestClient, sample_episode: Episode) -> None:
        """Test getting episode details."""
        response = client.get("/api/episodes/test_episode")
        assert response.status_code == 200

        data = response.json()
        assert data["episode_id"] == "test_episode"
        assert data["show_id"] == "test_show"
        assert data["title"] == "Test Episode"

    def test_get_episode_not_found(self, client: TestClient) -> None:
        """Test getting non-existent episode."""
        response = client.get("/api/episodes/nonexistent")
        assert response.status_code == 404

    def test_update_outline(self, client: TestClient, sample_episode: Episode) -> None:
        """Test updating episode outline."""
        outline_data = {
            "outline": {
                "hook": "Test hook",
                "discovery": "Test discovery",
                "challenge": "Test challenge",
                "resolution": "Test resolution",
                "lesson_learned": "Test lesson",
                "key_moments": ["moment1", "moment2"],
                "educational_concepts": ["concept1"],
                "age_appropriate_notes": "Test notes",
            }
        }

        response = client.put("/api/episodes/test_episode/outline", json=outline_data)
        assert response.status_code == 200

        data = response.json()
        assert data["outline"]["hook"] == "Test hook"
        assert data["outline"]["discovery"] == "Test discovery"

    def test_approve_episode(self, client: TestClient, sample_episode: Episode) -> None:
        """Test approving episode."""
        approval_data = {"approved": True, "feedback": "Looks great!"}

        response = client.post("/api/episodes/test_episode/approve", json=approval_data)
        assert response.status_code == 200

        data = response.json()
        assert data["approval_status"] == "approved"
        assert data["approval_feedback"] == "Looks great!"
        assert data["current_stage"] == "APPROVED"

    def test_reject_episode(self, client: TestClient, sample_episode: Episode) -> None:
        """Test rejecting episode."""
        rejection_data = {"approved": False, "feedback": "Needs work"}

        response = client.post(
            "/api/episodes/test_episode/approve", json=rejection_data
        )
        assert response.status_code == 200

        data = response.json()
        assert data["approval_status"] == "rejected"
        assert data["approval_feedback"] == "Needs work"
        assert data["current_stage"] == "REJECTED"


class TestAPIDocumentation:
    """Tests for API documentation endpoints."""

    def test_openapi_docs(self, client: TestClient) -> None:
        """Test that OpenAPI docs are available."""
        response = client.get("/docs")
        assert response.status_code == 200

    def test_redoc_docs(self, client: TestClient) -> None:
        """Test that ReDoc docs are available."""
        response = client.get("/redoc")
        assert response.status_code == 200

    def test_openapi_json(self, client: TestClient) -> None:
        """Test that OpenAPI JSON schema is available."""
        response = client.get("/openapi.json")
        assert response.status_code == 200

        data = response.json()
        assert data["info"]["title"] == "Ultimate Kids Curiosity Club API"
        assert "paths" in data
