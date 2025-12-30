#!/usr/bin/env python3
"""Standalone script to run API tests without pytest import issues.

This script demonstrates that all API tests pass when run with proper imports.
Run this script to verify API functionality.
"""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

import tempfile
from datetime import UTC, datetime

from fastapi.testclient import TestClient

from api.main import app
from config import get_settings, reset_settings
from models.episode import Episode, PipelineStage
from models.show import (
    ConceptsHistory,
    Protagonist,
    Show,
    ShowBlueprint,
    WorldDescription,
)
from models.story import StoryOutline
from modules.episode_storage import EpisodeStorage
from modules.show_blueprint_manager import ShowBlueprintManager


def setup_test_data(temp_dir: Path):
    """Create test show and episode data."""
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

    manager = ShowBlueprintManager(shows_dir=temp_dir)
    manager.save_show(blueprint)

    episode = Episode(
        episode_id="test_episode",
        show_id="test_show",
        topic="Test Topic",
        title="Test Episode",
        current_stage=PipelineStage.PENDING,
    )

    storage = EpisodeStorage(shows_dir=temp_dir)
    storage.save_episode(episode)

    # Update show to include episode
    blueprint.episodes.append("test_episode")
    manager.save_show(blueprint)

    return blueprint, episode


def test_health_endpoint(client):
    """Test health check endpoint."""
    print("  Testing /health endpoint...")
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert "timestamp" in data
    print("    ✓ Health check passed")


def test_shows_endpoints(client):
    """Test show endpoints."""
    print("  Testing show endpoints...")
    
    # Test list shows
    response = client.get("/api/shows")
    assert response.status_code == 200
    print("    ✓ GET /api/shows passed")
    
    # Test get show
    response = client.get("/api/shows/test_show")
    assert response.status_code == 200
    data = response.json()
    assert data["show"]["show_id"] == "test_show"
    print("    ✓ GET /api/shows/{show_id} passed")
    
    # Test update show
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
    print("    ✓ PUT /api/shows/{show_id} passed")


def test_episode_endpoints(client):
    """Test episode endpoints."""
    print("  Testing episode endpoints...")
    
    # Test list episodes
    response = client.get("/api/shows/test_show/episodes")
    assert response.status_code == 200
    print("    ✓ GET /api/shows/{show_id}/episodes passed")
    
    # Test get episode
    response = client.get("/api/episodes/test_episode")
    assert response.status_code == 200
    data = response.json()
    assert data["episode_id"] == "test_episode"
    print("    ✓ GET /api/episodes/{episode_id} passed")
    
    # Test update outline (note: outline structure matches StoryOutline model)
    outline_data = {
        "outline": {
            "episode_id": "test_episode",
            "show_id": "test_show",
            "topic": "Test Topic",
            "title": "Test Episode",
            "educational_concept": "Test Concept",
            "story_beats": []
        }
    }
    response = client.put("/api/episodes/test_episode/outline", json=outline_data)
    assert response.status_code == 200, f"Expected 200 but got {response.status_code}: {response.text}"
    print("    ✓ PUT /api/episodes/{episode_id}/outline passed")
    
    # Test approve episode
    approval_data = {"approved": True, "feedback": "Looks great!"}
    response = client.post("/api/episodes/test_episode/approve", json=approval_data)
    assert response.status_code == 200
    data = response.json()
    assert data["approval_status"] == "approved"
    print("    ✓ POST /api/episodes/{episode_id}/approve passed")


def test_api_documentation(client):
    """Test API documentation endpoints."""
    print("  Testing API documentation...")
    
    response = client.get("/docs")
    assert response.status_code == 200
    print("    ✓ GET /docs passed")
    
    response = client.get("/redoc")
    assert response.status_code == 200
    print("    ✓ GET /redoc passed")
    
    response = client.get("/openapi.json")
    assert response.status_code == 200
    data = response.json()
    assert data["info"]["title"] == "Ultimate Kids Curiosity Club API"
    print("    ✓ GET /openapi.json passed")


def main():
    """Run all API tests."""
    print("=" * 60)
    print("API Tests - Standalone Execution")
    print("=" * 60)
    print()
    
    # Create temporary directory for test data
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)
        
        # Override settings
        reset_settings()
        settings = get_settings()
        original_shows_dir = settings.SHOWS_DIR
        settings.SHOWS_DIR = temp_path
        
        try:
            # Setup test data
            print("Setting up test data...")
            blueprint, episode = setup_test_data(temp_path)
            print("  ✓ Test data created")
            print()
            
            # Create test client
            client = TestClient(app)
            
            # Run tests
            print("Running API tests...")
            test_health_endpoint(client)
            test_shows_endpoints(client)
            test_episode_endpoints(client)
            test_api_documentation(client)
            
            print()
            print("=" * 60)
            print("✓ All API tests passed!")
            print("=" * 60)
            return 0
            
        except AssertionError as e:
            print()
            print("=" * 60)
            print(f"✗ Test failed: {e}")
            print("=" * 60)
            return 1
        finally:
            # Restore settings
            settings.SHOWS_DIR = original_shows_dir


if __name__ == "__main__":
    sys.exit(main())
