from __future__ import annotations

import asyncio
import json
import logging
from datetime import datetime, timezone
from typing import Any
from uuid import uuid4

from app.infrastructure.eventstore import EventRecord, _utc_now


logger = logging.getLogger(__name__)


def _parse_esdb_uri(uri: str) -> str:
    normalized = uri.strip()
    if normalized.startswith("esdb://"):
        return normalized
    if normalized.startswith("http://"):
        return "esdb://" + normalized.removeprefix("http://") + "?tls=false"
    if normalized.startswith("https://"):
        return "esdb://" + normalized.removeprefix("https://") + "?tls=true"
    return f"esdb://{normalized}?tls=false"


class EsdbEventStore:
    """Adapter EventStoreDB przez pakiet `esdbclient`."""

    def __init__(self, uri: str) -> None:
        self.uri = _parse_esdb_uri(uri)
        self._client: Any = None

    async def connect(self) -> None:
        try:
            from esdbclient import EsdbClient
        except ModuleNotFoundError as exc:
            raise RuntimeError(
                "Install esdbclient to use EVENT_STORE_BACKEND=eventstoredb or dual"
            ) from exc

        self._client = await asyncio.to_thread(EsdbClient, uri=self.uri)
        logger.info("Connected to EventStoreDB at %s", self.uri)

    async def disconnect(self) -> None:
        client = self._client
        self._client = None
        if client is not None and hasattr(client, "close"):
            await asyncio.to_thread(client.close)

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
        if not events or self._client is None:
            return []

        from esdbclient import NewEvent, StreamState

        stream_id = f"{aggregate_type}-{aggregate_id}"

        def _append() -> list[EventRecord]:
            try:
                existing = list(self._client.get_stream(stream_name=stream_id))
                current_version = len(existing) - 1 if existing else StreamState.NO_STREAM
            except Exception:
                current_version = StreamState.NO_STREAM

            new_events = []
            for event in events:
                payload = getattr(event, "data")
                if callable(payload):
                    payload = payload()
                event_metadata = {
                    **(metadata or {}),
                    "aggregate_type": aggregate_type,
                    "aggregate_id": aggregate_id,
                    "causation_id": causation_id,
                    "correlation_id": correlation_id,
                }
                new_events.append(
                    NewEvent(
                        type=getattr(event, "event_type"),
                        data=json.dumps(payload, default=str).encode(),
                        metadata=json.dumps(event_metadata, default=str).encode(),
                        id=uuid4(),
                    )
                )

            self._client.append_to_stream(
                stream_name=stream_id,
                current_version=current_version,
                events=new_events,
            )
            recorded = list(self._client.get_stream(stream_name=stream_id))
            records: list[EventRecord] = []
            start = max(0, len(recorded) - len(events))
            for idx, recorded_event in enumerate(recorded[start:], start=start + 1):
                payload = json.loads(recorded_event.data.decode())
                event_metadata = json.loads(recorded_event.metadata.decode() or "{}")
                records.append(
                    EventRecord(
                        event_id=str(recorded_event.id),
                        stream_id=stream_id,
                        aggregate_type=aggregate_type,
                        aggregate_id=aggregate_id,
                        event_type=recorded_event.type,
                        revision=idx,
                        timestamp=_utc_now(),
                        causation_id=causation_id,
                        correlation_id=correlation_id,
                        data=payload,
                        metadata=event_metadata,
                    )
                )
            return records

        return await asyncio.to_thread(_append)

    async def get_events_for_aggregate(
        self,
        aggregate_type: str,
        aggregate_id: str,
    ) -> list[EventRecord]:
        if self._client is None:
            return []

        stream_id = f"{aggregate_type}-{aggregate_id}"

        def _read() -> list[EventRecord]:
            try:
                recorded = list(self._client.get_stream(stream_name=stream_id))
            except Exception:
                return []
            records: list[EventRecord] = []
            for idx, recorded_event in enumerate(recorded, start=1):
                payload = json.loads(recorded_event.data.decode())
                event_metadata = json.loads(recorded_event.metadata.decode() or "{}")
                records.append(
                    EventRecord(
                        event_id=str(recorded_event.id),
                        stream_id=stream_id,
                        aggregate_type=aggregate_type,
                        aggregate_id=aggregate_id,
                        event_type=recorded_event.type,
                        revision=idx,
                        timestamp=datetime.now(timezone.utc),
                        causation_id=event_metadata.get("causation_id"),
                        correlation_id=event_metadata.get("correlation_id"),
                        data=payload,
                        metadata=event_metadata,
                    )
                )
            return records

        return await asyncio.to_thread(_read)

    async def get_aggregate_ids(self, aggregate_type: str) -> list[str]:
        if self._client is None:
            return []

        category = f"$ce-{aggregate_type}"

        def _read() -> list[str]:
            try:
                recorded = list(self._client.get_stream(stream_name=category))
            except Exception:
                return []
            prefix = f"{aggregate_type}-"
            ids = []
            for item in recorded:
                stream_name = getattr(item, "type", "") or ""
                if stream_name.startswith(prefix):
                    ids.append(stream_name.removeprefix(prefix))
            return sorted(set(ids))

        return await asyncio.to_thread(_read)

    async def all_events(self, *, limit: int = 100, offset: int = 0) -> list[EventRecord]:
        return []
