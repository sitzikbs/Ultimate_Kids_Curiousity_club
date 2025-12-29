"""WebSocket handler for real-time updates."""

import asyncio
import json
from datetime import UTC, datetime

from fastapi import WebSocket, WebSocketDisconnect

from api.models import WebSocketMessage


class ConnectionManager:
    """Manages WebSocket connections and broadcasting."""

    def __init__(self):
        """Initialize connection manager."""
        self.active_connections: list[WebSocket] = []
        self._heartbeat_task: asyncio.Task | None = None

    async def connect(self, websocket: WebSocket) -> None:
        """Accept and register a new WebSocket connection.

        Args:
            websocket: WebSocket connection to register
        """
        await websocket.accept()
        self.active_connections.append(websocket)

        # Start heartbeat task if not already running
        if self._heartbeat_task is None or self._heartbeat_task.done():
            self._heartbeat_task = asyncio.create_task(self._heartbeat_loop())

    def disconnect(self, websocket: WebSocket) -> None:
        """Remove a WebSocket connection.

        Args:
            websocket: WebSocket connection to remove
        """
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)

    async def send_personal_message(self, message: str, websocket: WebSocket) -> None:
        """Send a message to a specific client.

        Args:
            message: Message to send
            websocket: Target WebSocket connection
        """
        await websocket.send_text(message)

    async def broadcast(self, message: dict) -> None:
        """Broadcast a message to all connected clients.

        Args:
            message: Message dictionary to broadcast
        """
        # Create WebSocket message with timestamp
        ws_message = WebSocketMessage(
            event_type=message.get("event_type", "unknown"),
            data=message.get("data", {}),
            timestamp=datetime.now(UTC),
        )

        # Serialize to JSON
        message_json = json.dumps(ws_message.model_dump(), default=str)

        # Send to all connected clients
        disconnected: list[WebSocket] = []
        for connection in self.active_connections:
            try:
                await connection.send_text(message_json)
            except Exception:
                # Mark for removal if sending fails
                disconnected.append(connection)

        # Remove disconnected clients
        for connection in disconnected:
            self.disconnect(connection)

    async def broadcast_episode_status_change(
        self, episode_id: str, show_id: str, old_stage: str, new_stage: str
    ) -> None:
        """Broadcast episode status change event.

        Args:
            episode_id: Episode identifier
            show_id: Show identifier
            old_stage: Previous pipeline stage
            new_stage: New pipeline stage
        """
        message = {
            "event_type": "episode_status_changed",
            "data": {
                "episode_id": episode_id,
                "show_id": show_id,
                "old_stage": old_stage,
                "new_stage": new_stage,
            },
        }
        await self.broadcast(message)

    async def broadcast_progress_update(
        self,
        episode_id: str,
        show_id: str,
        stage: str,
        progress: float,
        message: str | None = None,
    ) -> None:
        """Broadcast progress update event.

        Args:
            episode_id: Episode identifier
            show_id: Show identifier
            stage: Current pipeline stage
            progress: Progress percentage (0-100)
            message: Optional progress message
        """
        msg = {
            "event_type": "progress_update",
            "data": {
                "episode_id": episode_id,
                "show_id": show_id,
                "stage": stage,
                "progress": progress,
                "message": message,
            },
        }
        await self.broadcast(msg)

    async def _heartbeat_loop(self) -> None:
        """Send periodic heartbeat/ping to all connected clients."""
        while self.active_connections:
            await asyncio.sleep(30)  # Send heartbeat every 30 seconds

            disconnected: list[WebSocket] = []
            for connection in self.active_connections:
                try:
                    # Send ping
                    await connection.send_json(
                        {"event_type": "ping", "timestamp": datetime.now(UTC).isoformat()}
                    )
                except Exception:
                    disconnected.append(connection)

            # Remove disconnected clients
            for connection in disconnected:
                self.disconnect(connection)


# Global connection manager instance
manager = ConnectionManager()


async def websocket_endpoint(websocket: WebSocket) -> None:
    """WebSocket endpoint handler.

    Args:
        websocket: WebSocket connection
    """
    await manager.connect(websocket)
    try:
        while True:
            # Wait for messages from client
            data = await websocket.receive_text()

            # Parse client message
            try:
                client_msg = json.loads(data)

                # Handle pong response to ping
                if client_msg.get("event_type") == "pong":
                    continue

                # Echo back any other messages for now
                await manager.send_personal_message(
                    json.dumps({"status": "received", "data": client_msg}), websocket
                )
            except json.JSONDecodeError:
                await manager.send_personal_message(
                    json.dumps({"error": "Invalid JSON"}), websocket
                )

    except WebSocketDisconnect:
        manager.disconnect(websocket)
