from __future__ import annotations

from collections import defaultdict
from datetime import datetime
from typing import Any
from uuid import uuid4

from app.infrastructure.eventstore import EventRecord


class FakeEventStore:
    def __init__(self):
        self.records: dict[tuple[str, str], list[EventRecord]] = defaultdict(list)

    async def append(
        self,
        aggregate_type: str,
        aggregate_id: str,
        events: list[Any],
        *,
        causation_id: str | None = None,
        correlation_id: str | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> list[EventRecord]:
        stream_id = f"{aggregate_type}-{aggregate_id}"
        key = (aggregate_type, aggregate_id)
        records: list[EventRecord] = []
        revision = len(self.records[key])
        for event in events:
            revision += 1
            payload = getattr(event, "data")
            if callable(payload):
                payload = payload()
            record = EventRecord(
                event_id=str(uuid4()),
                stream_id=stream_id,
                aggregate_type=aggregate_type,
                aggregate_id=aggregate_id,
                event_type=getattr(event, "event_type"),
                revision=revision,
                timestamp=getattr(event, "timestamp", datetime.utcnow()),
                causation_id=causation_id,
                correlation_id=correlation_id,
                data=payload,
                metadata=metadata or {},
            )
            self.records[key].append(record)
            records.append(record)
        return records

    async def get_events_for_aggregate(self, aggregate_type: str, aggregate_id: str):
        return self.records[(aggregate_type, aggregate_id)]

    async def get_aggregate_ids(self, aggregate_type: str):
        return sorted({aggregate_id for kind, aggregate_id in self.records if kind == aggregate_type})


class FakeMessageBus:
    def __init__(self):
        self.messages: list[tuple[str, dict[str, Any]]] = []

    async def publish(self, subject: str, payload: dict[str, Any]):
        self.messages.append((subject, payload))
