from __future__ import annotations

from typing import Any

from app.infrastructure.eventstore import EventStore as PostgresEventStore


class DualEventStore:
    """Zapis do Postgres (odczyt) + mirror do EventStoreDB."""

    def __init__(self, primary: PostgresEventStore, mirror: Any) -> None:
        self.primary = primary
        self.mirror = mirror

    async def append(
        self,
        aggregate_type: str,
        aggregate_id: str,
        events: list[Any],
        *,
        causation_id: str | None = None,
        correlation_id: str | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> list[Any]:
        records = await self.primary.append(
            aggregate_type,
            aggregate_id,
            events,
            causation_id=causation_id,
            correlation_id=correlation_id,
            metadata=metadata,
        )
        try:
            await self.mirror.append(
                aggregate_type,
                aggregate_id,
                events,
                causation_id=causation_id,
                correlation_id=correlation_id,
                metadata=metadata,
            )
        except Exception:
            pass
        return records

    async def get_events_for_aggregate(
        self,
        aggregate_type: str,
        aggregate_id: str,
    ) -> list[Any]:
        return await self.primary.get_events_for_aggregate(aggregate_type, aggregate_id)

    async def get_aggregate_ids(self, aggregate_type: str) -> list[str]:
        return await self.primary.get_aggregate_ids(aggregate_type)

    async def all_events(self, *, limit: int = 100, offset: int = 0) -> list[Any]:
        return await self.primary.all_events(limit=limit, offset=offset)
