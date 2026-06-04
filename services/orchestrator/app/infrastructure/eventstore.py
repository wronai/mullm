from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any
from uuid import uuid4
import json


@dataclass(frozen=True)
class EventRecord:
    event_id: str
    stream_id: str
    aggregate_type: str
    aggregate_id: str
    event_type: str
    revision: int
    timestamp: datetime
    data: dict[str, Any]
    metadata: dict[str, Any]
    causation_id: str | None = None
    correlation_id: str | None = None

    def to_message(self) -> dict[str, Any]:
        return {
            "event_id": self.event_id,
            "stream_id": self.stream_id,
            "aggregate_type": self.aggregate_type,
            "aggregate_id": self.aggregate_id,
            "event_type": self.event_type,
            "revision": self.revision,
            "occurred_at": self.timestamp.isoformat(),
            "causation_id": self.causation_id,
            "correlation_id": self.correlation_id,
            "payload": self.data,
            "metadata": self.metadata,
        }


def _loads_json(value: Any) -> dict[str, Any]:
    if value is None:
        return {}
    if isinstance(value, str):
        return json.loads(value)
    return dict(value)


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


class EventStore:
    def __init__(self, postgres):
        self.postgres = postgres

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
        if not events:
            return []

        stream_id = f"{aggregate_type}-{aggregate_id}"
        row = await self.postgres.fetchrow(
            "select coalesce(max(revision), 0) as revision from events where stream_id = $1",
            stream_id,
        )
        revision = int(row["revision"] if row else 0)
        records: list[EventRecord] = []

        for event in events:
            revision += 1
            event_id = str(uuid4())
            event_type = getattr(event, "event_type")
            timestamp = getattr(event, "timestamp", _utc_now())
            payload = getattr(event, "data")
            if callable(payload):
                payload = payload()
            event_metadata = metadata or {}

            await self.postgres.execute(
                """
                insert into events (
                  event_id, stream_id, aggregate_type, aggregate_id, event_type,
                  revision, occurred_at, causation_id, correlation_id, payload, metadata
                )
                values ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10::jsonb, $11::jsonb)
                """,
                event_id,
                stream_id,
                aggregate_type,
                aggregate_id,
                event_type,
                revision,
                timestamp,
                causation_id,
                correlation_id,
                json.dumps(payload, default=str),
                json.dumps(event_metadata, default=str),
            )
            records.append(
                EventRecord(
                    event_id=event_id,
                    stream_id=stream_id,
                    aggregate_type=aggregate_type,
                    aggregate_id=aggregate_id,
                    event_type=event_type,
                    revision=revision,
                    timestamp=timestamp,
                    causation_id=causation_id,
                    correlation_id=correlation_id,
                    data=payload,
                    metadata=event_metadata,
                )
            )

        return records

    async def get_events_for_aggregate(
        self,
        aggregate_type: str,
        aggregate_id: str,
    ) -> list[EventRecord]:
        rows = await self.postgres.fetch(
            """
            select event_id, stream_id, aggregate_type, aggregate_id, event_type,
                   revision, occurred_at, causation_id, correlation_id, payload, metadata
            from events
            where aggregate_type = $1 and aggregate_id = $2
            order by revision asc
            """,
            aggregate_type,
            aggregate_id,
        )
        return [self._record_from_row(row) for row in rows]

    async def get_aggregate_ids(self, aggregate_type: str) -> list[str]:
        rows = await self.postgres.fetch(
            """
            select distinct aggregate_id
            from events
            where aggregate_type = $1
            order by aggregate_id asc
            """,
            aggregate_type,
        )
        return [row["aggregate_id"] for row in rows]

    async def all_events(self, *, limit: int = 100, offset: int = 0) -> list[EventRecord]:
        rows = await self.postgres.fetch(
            """
            select event_id, stream_id, aggregate_type, aggregate_id, event_type,
                   revision, occurred_at, causation_id, correlation_id, payload, metadata
            from events
            order by id asc
            limit $1 offset $2
            """,
            limit,
            offset,
        )
        return [self._record_from_row(row) for row in rows]

    def _record_from_row(self, row: Any) -> EventRecord:
        return EventRecord(
            event_id=row["event_id"],
            stream_id=row["stream_id"],
            aggregate_type=row["aggregate_type"],
            aggregate_id=row["aggregate_id"],
            event_type=row["event_type"],
            revision=row["revision"],
            timestamp=row["occurred_at"],
            causation_id=row["causation_id"],
            correlation_id=row["correlation_id"],
            data=_loads_json(row["payload"]),
            metadata=_loads_json(row["metadata"]),
        )
