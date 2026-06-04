from __future__ import annotations

import logging
from typing import Any

from app.infrastructure.eventstore import EventStore as PostgresEventStore
from app.infrastructure.eventstore_dual import DualEventStore
from app.infrastructure.eventstore_esdb import EsdbEventStore


logger = logging.getLogger(__name__)


async def build_event_store(
    *,
    backend: str,
    postgres: Any,
    eventstore_url: str | None = None,
) -> tuple[Any, dict[str, str]]:
    """Tworzy event store wg EVENT_STORE_BACKEND."""
    normalized = (backend or "postgres").lower()
    primary = PostgresEventStore(postgres)
    info = {"backend": normalized}

    if normalized == "postgres":
        return primary, info

    if normalized == "eventstoredb":
        if not eventstore_url:
            raise ValueError("EVENTSTORE_URL is required for eventstoredb backend")
        esdb = EsdbEventStore(eventstore_url)
        await esdb.connect()
        info["eventstore_url"] = eventstore_url
        return esdb, info

    if normalized == "dual":
        if not eventstore_url:
            raise ValueError("EVENTSTORE_URL is required for dual backend")
        esdb = EsdbEventStore(eventstore_url)
        try:
            await esdb.connect()
            info["eventstore_url"] = eventstore_url
            info["mirror"] = "connected"
        except Exception as exc:
            logger.warning("EventStoreDB mirror unavailable: %s", exc)
            info["mirror"] = "unavailable"
            return primary, info
        return DualEventStore(primary, esdb), info

    raise ValueError(f"Unknown EVENT_STORE_BACKEND: {backend}")
