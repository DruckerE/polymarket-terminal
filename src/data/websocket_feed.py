"""Real-time WebSocket feed for orderbook, trade, and price events."""

from __future__ import annotations

import asyncio
import json
import logging
import time
from collections.abc import Callable
from dataclasses import dataclass
from enum import Enum

import websockets
from websockets.asyncio.client import ClientConnection

from src.config.constants import WS_MAX_RETRIES, WS_PING_INTERVAL, WS_RECONNECT_DELAY, WS_URL

logger = logging.getLogger(__name__)


class EventType(Enum):
    BOOK = "book"
    TRADE = "last_trade_price"
    PRICE = "price_change"
    TICK_SIZE = "tick_size_change"


@dataclass(frozen=True)
class WSEvent:
    """A parsed WebSocket event."""

    event_type: EventType
    asset_id: str
    data: dict
    timestamp: float


class WebSocketFeed:
    """Manages WebSocket connection to Polymarket CLOB with auto-reconnect."""

    def __init__(self) -> None:
        self._connection: ClientConnection | None = None
        self._subscribed_assets: set[str] = set()
        self._handlers: dict[EventType, list[Callable[[WSEvent], None]]] = {
            et: [] for et in EventType
        }
        self._running = False
        self._retry_count = 0
        self._on_connect: Callable[[], None] | None = None
        self._on_disconnect: Callable[[], None] | None = None

    @property
    def is_connected(self) -> bool:
        return self._connection is not None and self._running

    def on_event(self, event_type: EventType, handler: Callable[[WSEvent], None]) -> None:
        self._handlers[event_type].append(handler)

    def set_connect_handler(self, handler: Callable[[], None]) -> None:
        self._on_connect = handler

    def set_disconnect_handler(self, handler: Callable[[], None]) -> None:
        self._on_disconnect = handler

    async def subscribe(self, asset_id: str) -> None:
        self._subscribed_assets.add(asset_id)
        if self._connection:
            await self._send_subscribe(asset_id)

    async def unsubscribe(self, asset_id: str) -> None:
        self._subscribed_assets.discard(asset_id)
        if self._connection:
            msg = json.dumps({
                "type": "unsubscribe",
                "assets_ids": [asset_id],
            })
            await self._connection.send(msg)

    async def start(self) -> None:
        self._running = True
        self._retry_count = 0
        while self._running and self._retry_count < WS_MAX_RETRIES:
            try:
                await self._connect_and_listen()
            except (
                websockets.ConnectionClosed,
                websockets.InvalidStatusCode,
                OSError,
                asyncio.TimeoutError,
            ) as exc:
                logger.warning("WebSocket disconnected: %s", exc)
                if self._on_disconnect:
                    self._on_disconnect()
                self._retry_count += 1
                if self._running:
                    await asyncio.sleep(WS_RECONNECT_DELAY * min(self._retry_count, 5))
            except Exception:
                logger.exception("Unexpected WebSocket error")
                if self._on_disconnect:
                    self._on_disconnect()
                self._retry_count += 1
                if self._running:
                    await asyncio.sleep(WS_RECONNECT_DELAY * min(self._retry_count, 5))

    async def stop(self) -> None:
        self._running = False
        if self._connection:
            await self._connection.close()
            self._connection = None

    async def _connect_and_listen(self) -> None:
        async with websockets.connect(
            WS_URL,
            ping_interval=WS_PING_INTERVAL,
            ping_timeout=10,
        ) as ws:
            self._connection = ws
            self._retry_count = 0

            for asset_id in self._subscribed_assets:
                await self._send_subscribe(asset_id)

            if self._on_connect:
                self._on_connect()

            async for raw_msg in ws:
                if not self._running:
                    break
                self._process_message(raw_msg)

    async def _send_subscribe(self, asset_id: str) -> None:
        if not self._connection:
            return
        for event_type in EventType:
            msg = json.dumps({
                "auth": {},
                "type": event_type.value,
                "assets_ids": [asset_id],
            })
            await self._connection.send(msg)

    def _process_message(self, raw: str | bytes) -> None:
        try:
            data = json.loads(raw)
        except json.JSONDecodeError:
            return

        event_type_str = data.get("event_type", "")
        asset_id = data.get("asset_id", "")

        try:
            event_type = EventType(event_type_str)
        except ValueError:
            return

        event = WSEvent(
            event_type=event_type,
            asset_id=asset_id,
            data=data,
            timestamp=time.time(),
        )

        for handler in self._handlers.get(event_type, []):
            try:
                handler(event)
            except Exception:
                logger.exception("Error in WS event handler")
