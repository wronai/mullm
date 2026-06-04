from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Any
from uuid import uuid4

import pytest

from app.application.command_bus import CommandBus
from app.infrastructure.eventstore import EventRecord, EventStore


@dataclass
class FakeRow:
    _data: dict[str, Any]

    def __getitem__(self, key: str) -> Any:
        return self._data[key]


class InMemoryPostgres:
    def __init__(self) -> None:
        self.events: list[dict[str, Any]] = []

    async def connect(self) -> None:
        return None

    async def disconnect(self) -> None:
        return None

    async def execute(self, query: str, *args: Any) -> str:
        if "insert into events" in query:
            self.events.append(
                {
                    "event_id": args[0],
                    "stream_id": args[1],
                    "aggregate_type": args[2],
                    "aggregate_id": args[3],
                    "event_type": args[4],
                    "revision": args[5],
                    "occurred_at": args[6],
                    "causation_id": args[7],
                    "correlation_id": args[8],
                    "payload": args[9],
                    "metadata": args[10],
                }
            )
        return "OK"

    async def fetchrow(self, query: str, *args: Any) -> FakeRow | None:
        stream_id = args[0]
        revision = max(
            (
                event["revision"]
                for event in self.events
                if event["stream_id"] == stream_id
            ),
            default=0,
        )
        return FakeRow({"revision": revision})

    async def fetch(self, query: str, *args: Any) -> list[FakeRow]:
        if "distinct aggregate_id" in query:
            aggregate_type = args[0]
            ids = sorted(
                {
                    event["aggregate_id"]
                    for event in self.events
                    if event["aggregate_type"] == aggregate_type
                }
            )
            return [FakeRow({"aggregate_id": item}) for item in ids]

        if "aggregate_type = $1 and aggregate_id = $2" in query:
            aggregate_type, aggregate_id = args[0], args[1]
            rows = [
                event
                for event in self.events
                if event["aggregate_type"] == aggregate_type
                and event["aggregate_id"] == aggregate_id
            ]
            rows.sort(key=lambda item: item["revision"])
            return [self._event_row(row) for row in rows]

        rows = sorted(self.events, key=lambda item: item["revision"])
        return [self._event_row(row) for row in rows]

    def _event_row(self, event: dict[str, Any]) -> FakeRow:
        return FakeRow(
            {
                "event_id": event["event_id"],
                "stream_id": event["stream_id"],
                "aggregate_type": event["aggregate_type"],
                "aggregate_id": event["aggregate_id"],
                "event_type": event["event_type"],
                "revision": event["revision"],
                "occurred_at": event["occurred_at"],
                "causation_id": event["causation_id"],
                "correlation_id": event["correlation_id"],
                "payload": event["payload"],
                "metadata": event["metadata"],
            }
        )


class FakeMessageBus:
    def __init__(self) -> None:
        self.messages: list[tuple[str, dict[str, Any]]] = []

    async def publish(self, subject: str, payload: dict[str, Any]) -> None:
        self.messages.append((subject, payload))


@pytest.fixture
def fake_postgres() -> InMemoryPostgres:
    return InMemoryPostgres()


@pytest.fixture
def fake_bus() -> FakeMessageBus:
    return FakeMessageBus()


@pytest.fixture
def event_store(fake_postgres: InMemoryPostgres) -> EventStore:
    return EventStore(fake_postgres)


@pytest.fixture
def command_bus(event_store: EventStore, fake_bus: FakeMessageBus) -> CommandBus:
    return CommandBus(event_store=event_store, message_bus=fake_bus)


@pytest.fixture
def sample_command_id() -> str:
    return str(uuid4())
