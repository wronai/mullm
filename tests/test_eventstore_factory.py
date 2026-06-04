import pytest

from app.infrastructure.eventstore import EventStore as PostgresEventStore
from app.infrastructure.eventstore_factory import build_event_store


@pytest.mark.asyncio
async def test_build_postgres_backend(fake_postgres):
    store, info = await build_event_store(
        backend="postgres",
        postgres=fake_postgres,
    )
    assert isinstance(store, PostgresEventStore)
    assert info["backend"] == "postgres"


@pytest.mark.asyncio
async def test_build_dual_without_esdb_falls_back(fake_postgres):
    store, info = await build_event_store(
        backend="dual",
        postgres=fake_postgres,
        eventstore_url="esdb://127.0.0.1:19999?tls=false",
    )
    assert isinstance(store, PostgresEventStore)
    assert info["mirror"] == "unavailable"
