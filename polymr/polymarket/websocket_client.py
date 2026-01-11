"""
WebSocket client for Polymarket CLOB.

Provides real-time orderbook and trade data via WebSocket connections.
"""

import asyncio
import json
import logging
from typing import Any, Callable, Dict, List, Optional, Set

import websockets
from websockets.exceptions import ConnectionClosed

from polymr.config import PolymarketConfig

logger = logging.getLogger(__name__)


class PolymarketWebSocketClient:
    """WebSocket client for real-time Polymarket data."""

    def __init__(self, config: PolymarketConfig):
        self.config = config
        self.ws_url = config.ws_url
        self._websocket: Optional[websockets.WebSocketClientProtocol] = None
        self._subscriptions: Set[str] = set()
        self._running = False
        self._reconnect_delay = 1.0
        self._max_reconnect_delay = 60.0
        self._callbacks: Dict[str, List[Callable]] = {
            "orderbook": [],
            "trade": [],
            "fill": [],
            "error": [],
            "connected": [],
            "disconnected": [],
        }

    def add_callback(self, event: str, callback: Callable) -> None:
        if event in self._callbacks:
            self._callbacks[event].append(callback)

    def remove_callback(self, event: str, callback: Callable) -> None:
        if event in self._callbacks and callback in self._callbacks[event]:
            self._callbacks[event].remove(callback)

    async def _emit(self, event: str, data: Any) -> None:
        for callback in self._callbacks.get(event, []):
            try:
                if asyncio.iscoroutinefunction(callback):
                    await callback(data)
                else:
                    callback(data)
            except Exception as e:
                logger.error(f"Error in {event} callback: {e}")

    async def connect(self) -> bool:
        """Establish WebSocket connection."""
        try:
            self._websocket = await websockets.connect(
                self.ws_url,
                ping_interval=30,
                ping_timeout=10,
                close_timeout=10,
            )
            self._running = True
            await self._emit("connected", None)
            logger.info("WebSocket connected")
            return True
        except Exception as e:
            logger.error(f"WebSocket connection failed: {e}")
            await self._emit("error", str(e))
            return False

    async def disconnect(self) -> None:
        """Close WebSocket connection."""
        self._running = False
        if self._websocket:
            await self._websocket.close()
            self._websocket = None
        await self._emit("disconnected", None)
        logger.info("WebSocket disconnected")

    async def subscribe_orderbook(self, token_ids: List[str]) -> None:
        """Subscribe to orderbook updates."""
        message = {
            "type": "subscribe",
            "channel": "orderbook",
            "keys": token_ids,
        }
        await self._send_message(message)
        self._subscriptions.update(token_ids)

    async def unsubscribe_orderbook(self, token_ids: List[str]) -> None:
        """Unsubscribe from orderbook updates."""
        message = {
            "type": "unsubscribe",
            "channel": "orderbook",
            "keys": token_ids,
        }
        await self._send_message(message)
        self._subscriptions.difference_update(token_ids)

    async def subscribe_trades(self, token_ids: List[str]) -> None:
        """Subscribe to trade updates."""
        message = {
            "type": "subscribe",
            "channel": "trade",
            "keys": token_ids,
        }
        await self._send_message(message)
        self._subscriptions.update(token_ids)

    async def _send_message(self, message: Dict[str, Any]) -> None:
        if self._websocket:
            await self._websocket.send(json.dumps(message))

    async def run(self) -> None:
        """Main loop for processing WebSocket messages."""
        while self._running:
            try:
                if not self._websocket:
                    if not await self.connect():
                        await self._handle_reconnect()
                        continue

                async for message in self._websocket:
                    await self._process_message(json.loads(message))

            except ConnectionClosed:
                logger.warning("WebSocket connection closed")
                await self._emit("disconnected", None)
                await self._handle_reconnect()
            except Exception as e:
                logger.error(f"WebSocket error: {e}")
                await self._emit("error", str(e))
                await self._handle_reconnect()

    async def _handle_reconnect(self) -> None:
        delay = min(self._reconnect_delay, self._max_reconnect_delay)
        logger.info(f"Reconnecting in {delay}s...")
        await asyncio.sleep(delay)
        self._reconnect_delay = min(delay * 2, self._max_reconnect_delay)

    async def _process_message(self, message: Dict[str, Any]) -> None:
        msg_type = message.get("type")

        if msg_type == "orderbook":
            await self._emit("orderbook", message.get("data"))
        elif msg_type == "trade":
            await self._emit("trade", message.get("data"))
        elif msg_type == "fill":
            await self._emit("fill", message.get("data"))
        elif msg_type == "error":
            await self._emit("error", message.get("message"))

    async def get_orderbook_snapshot(
        self, token_id: str, depth: int = 10
    ) -> Dict[str, Any]:
        """Get orderbook snapshot via REST API (fallback)."""
        from polymr.polymarket.rest_client import PolymarketRESTClient
        from polymr.config import Settings

        settings = Settings()
        client = PolymarketRESTClient(settings)
        try:
            return await client.get_orderbook(token_id, depth)
        finally:
            await client.close()
