"""Tests for WebSocket functionality."""

import asyncio
import json
from datetime import datetime

import pytest
from fastapi.testclient import TestClient

from api.main import app
from api.websocket import ConnectionManager


@pytest.fixture
def client() -> TestClient:
    """Create test client."""
    return TestClient(app)


class TestWebSocketEndpoint:
    """Tests for WebSocket endpoint."""

    def test_websocket_connection(self, client: TestClient) -> None:
        """Test WebSocket connection establishment."""
        with client.websocket_connect("/ws") as websocket:
            # Connection should be established
            assert websocket is not None

    def test_websocket_ping_pong(self, client: TestClient) -> None:
        """Test WebSocket ping-pong mechanism."""
        with client.websocket_connect("/ws") as websocket:
            # Send a pong message
            websocket.send_text(json.dumps({"event_type": "pong"}))

            # Should not receive error
            # Wait briefly to ensure no error is sent
            try:
                data = websocket.receive_text(timeout=0.5)
                msg = json.loads(data)
                # Should receive status confirmation or heartbeat ping
                assert "event_type" in msg or "status" in msg
            except TimeoutError:
                # No immediate response is also acceptable
                pass

    def test_websocket_echo(self, client: TestClient) -> None:
        """Test WebSocket echo functionality."""
        with client.websocket_connect("/ws") as websocket:
            # Send a test message
            test_message = {"event_type": "test", "data": {"message": "Hello"}}
            websocket.send_text(json.dumps(test_message))

            # Receive response
            data = websocket.receive_text()
            response = json.loads(data)

            # Should receive a confirmation
            assert "status" in response or "event_type" in response


class TestConnectionManager:
    """Tests for ConnectionManager class."""

    @pytest.mark.asyncio
    async def test_connection_manager_broadcast(self) -> None:
        """Test ConnectionManager broadcast functionality."""
        manager = ConnectionManager()

        # Create mock websocket
        class MockWebSocket:
            def __init__(self):
                self.messages = []

            async def send_text(self, message: str) -> None:
                self.messages.append(message)

        # Add mock connection
        mock_ws = MockWebSocket()
        manager.active_connections.append(mock_ws)

        # Broadcast message
        test_message = {
            "event_type": "test_event",
            "data": {"test": "data"},
        }
        await manager.broadcast(test_message)

        # Verify message was sent
        assert len(mock_ws.messages) == 1
        sent_message = json.loads(mock_ws.messages[0])
        assert sent_message["event_type"] == "test_event"
        assert sent_message["data"]["test"] == "data"

    @pytest.mark.asyncio
    async def test_connection_manager_episode_status_change(self) -> None:
        """Test broadcasting episode status change."""
        manager = ConnectionManager()

        # Create mock websocket
        class MockWebSocket:
            def __init__(self):
                self.messages = []

            async def send_text(self, message: str) -> None:
                self.messages.append(message)

        # Add mock connection
        mock_ws = MockWebSocket()
        manager.active_connections.append(mock_ws)

        # Broadcast episode status change
        await manager.broadcast_episode_status_change(
            episode_id="ep001",
            show_id="test_show",
            old_stage="PENDING",
            new_stage="APPROVED",
        )

        # Verify message
        assert len(mock_ws.messages) == 1
        sent_message = json.loads(mock_ws.messages[0])
        assert sent_message["event_type"] == "episode_status_changed"
        assert sent_message["data"]["episode_id"] == "ep001"
        assert sent_message["data"]["old_stage"] == "PENDING"
        assert sent_message["data"]["new_stage"] == "APPROVED"

    @pytest.mark.asyncio
    async def test_connection_manager_progress_update(self) -> None:
        """Test broadcasting progress update."""
        manager = ConnectionManager()

        # Create mock websocket
        class MockWebSocket:
            def __init__(self):
                self.messages = []

            async def send_text(self, message: str) -> None:
                self.messages.append(message)

        # Add mock connection
        mock_ws = MockWebSocket()
        manager.active_connections.append(mock_ws)

        # Broadcast progress update
        await manager.broadcast_progress_update(
            episode_id="ep001",
            show_id="test_show",
            stage="AUDIO_SYNTHESIS",
            progress=75.0,
            message="Generating audio...",
        )

        # Verify message
        assert len(mock_ws.messages) == 1
        sent_message = json.loads(mock_ws.messages[0])
        assert sent_message["event_type"] == "progress_update"
        assert sent_message["data"]["episode_id"] == "ep001"
        assert sent_message["data"]["stage"] == "AUDIO_SYNTHESIS"
        assert sent_message["data"]["progress"] == 75.0
        assert sent_message["data"]["message"] == "Generating audio..."

    @pytest.mark.asyncio
    async def test_connection_manager_disconnect_on_error(self) -> None:
        """Test that failed connections are removed."""
        manager = ConnectionManager()

        # Create mock websockets (one good, one bad)
        class GoodWebSocket:
            async def send_text(self, message: str) -> None:
                pass

        class BadWebSocket:
            async def send_text(self, message: str) -> None:
                raise Exception("Connection failed")

        good_ws = GoodWebSocket()
        bad_ws = BadWebSocket()

        manager.active_connections.extend([good_ws, bad_ws])
        assert len(manager.active_connections) == 2

        # Broadcast should remove bad connection
        await manager.broadcast({"event_type": "test", "data": {}})

        # Only good connection should remain
        assert len(manager.active_connections) == 1
        assert manager.active_connections[0] == good_ws


class TestWebSocketIntegration:
    """Integration tests for WebSocket with API."""

    def test_websocket_multiple_clients(self, client: TestClient) -> None:
        """Test multiple WebSocket clients can connect."""
        with client.websocket_connect("/ws") as ws1:
            with client.websocket_connect("/ws") as ws2:
                # Both connections should be active
                assert ws1 is not None
                assert ws2 is not None

                # Send message to ws1
                ws1.send_text(json.dumps({"event_type": "test1"}))

                # Receive response
                response1 = ws1.receive_text()
                assert response1 is not None

                # Send message to ws2
                ws2.send_text(json.dumps({"event_type": "test2"}))

                # Receive response
                response2 = ws2.receive_text()
                assert response2 is not None
