"""
WebSocket manager for real-time updates.
"""

from typing import Set, Dict, Any
from fastapi import WebSocket
import json
import asyncio

class WebSocketManager:
    """Manages WebSocket connections for real-time bot updates."""

    def __init__(self):
        self.active_connections: Set[WebSocket] = set()
        self._lock = asyncio.Lock()

    async def connect(self, websocket: WebSocket):
        """Accept a new WebSocket connection."""
        await self._lock.acquire()
        try:
            self.active_connections.add(websocket)
        finally:
            self._lock.release()

        print(f"WebSocket connected. Total connections: {len(self.active_connections)}")

    async def disconnect(self, websocket: WebSocket):
        """Remove a WebSocket connection."""
        await self._lock.acquire()
        try:
            self.active_connections.discard(websocket)
        finally:
            self._lock.release()

        print(f"WebSocket disconnected. Total connections: {len(self.active_connections)}")

    async def broadcast(self, message: Dict[str, Any]):
        """Broadcast a message to all connected clients."""
        if not self.active_connections:
            return

        message_json = json.dumps(message)

        disconnected = []
        for connection in self.active_connections:
            try:
                await connection.send_text(message_json)
            except Exception as e:
                print(f"Error sending to WebSocket: {e}")
                disconnected.append(connection)

        # Remove disconnected connections
        for conn in disconnected:
            self.active_connections.discard(conn)

        print(f"Broadcast message to {len(self.active_connections)} clients")

    async def send_personal(self, websocket: WebSocket, message: Dict[str, Any]):
        """Send a message to a specific client."""
        try:
            message_json = json.dumps(message)
            await websocket.send_text(message_json)
        except Exception as e:
            print(f"Error sending to WebSocket: {e}")


# Global WebSocket manager instance
ws_manager = WebSocketManager()
