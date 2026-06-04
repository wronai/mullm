from __future__ import annotations

from typing import Any
import json
import logging

try:
    from nats.aio.client import Client as NATS
except ModuleNotFoundError:  # pragma: no cover - exercised only without deps installed
    NATS = None


logger = logging.getLogger(__name__)


class NATSBus:
    def __init__(self, url: str):
        self.url = url
        self.client: Any = None
        self.connected = False

    async def connect(self) -> None:
        if NATS is None:
            logger.warning("nats-py is not installed; message publishing disabled")
            return

        self.client = NATS()
        try:
            await self.client.connect(servers=[self.url])
            self.connected = True
        except Exception as exc:  # pragma: no cover - depends on external NATS
            logger.warning("Could not connect to NATS at %s: %s", self.url, exc)
            self.connected = False

    async def disconnect(self) -> None:
        if self.client and self.connected:
            await self.client.drain()
        self.connected = False

    async def publish(self, subject: str, payload: dict[str, Any] | bytes) -> None:
        if not self.client or not self.connected:
            return
        data = payload if isinstance(payload, bytes) else json.dumps(payload, default=str).encode()
        await self.client.publish(subject, data)

    async def subscribe(self, subject: str, callback):
        if not self.client or not self.connected:
            return None
        return await self.client.subscribe(subject, cb=callback)
