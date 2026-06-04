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
        return await _eventstoredb_backend(eventstore_url, info)
    if normalized == "dual":
        return await _dual_backend(primary, eventstore_url, info)
    raise ValueError(f"Unknown EVENT_STORE_BACKEND: {backend}")


def _require_eventstore_url(eventstore_url: str | None, backend: str) -> str:
    if not eventstore_url:
        raise ValueError(f"EVENTSTORE_URL is required for {backend} backend")
    return eventstore_url


async def _eventstoredb_backend(
    eventstore_url: str | None,
    info: dict[str, str],
) -> tuple[Any, dict[str, str]]:
    url = _require_eventstore_url(eventstore_url, "eventstoredb")
    esdb = EsdbEventStore(url)
    await esdb.connect()
    info["eventstore_url"] = url
    return esdb, info


async def _dual_backend(
    primary: Any,
    eventstore_url: str | None,
    info: dict[str, str],
) -> tuple[Any, dict[str, str]]:
    url = _require_eventstore_url(eventstore_url, "dual")
    esdb = EsdbEventStore(url)
    try:
        await esdb.connect()
    except Exception as exc:
        logger.warning("EventStoreDB mirror unavailable: %s", exc)
        info["mirror"] = "unavailable"
        return primary, info
    info["eventstore_url"] = url
    info["mirror"] = "connected"
    return DualEventStore(primary, esdb), info
