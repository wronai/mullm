"""Integracyjne testy z Postgres — uruchom: MULLM_INTEGRATION=1 pytest tests/test_integration_postgres.py"""

from __future__ import annotations

import os

import pytest

pytestmark = pytest.mark.skipif(
    os.getenv("MULLM_INTEGRATION") != "1",
    reason="Set MULLM_INTEGRATION=1 and start postgres (docker compose up postgres -d)",
)

DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql://mullm:mullm_password@localhost:5432/mullm",
)


@pytest.fixture
async def live_command_bus():
    from app.application.command_bus import CommandBus
    from app.infrastructure.eventstore import EventStore
    from app.infrastructure.postgres import PostgresConnection

    postgres = PostgresConnection(DATABASE_URL)
    await postgres.connect()
    bus = CommandBus(event_store=EventStore(postgres))
    yield bus
    await postgres.disconnect()


@pytest.mark.asyncio
async def test_create_task_persisted(live_command_bus):
    result = await live_command_bus.handle(
        command_type="CreateTask",
        data={"title": "Integration task"},
    )
    task_id = result["aggregate_id"]
    events = await live_command_bus.event_store.get_events_for_aggregate("task", task_id)
    assert len(events) >= 1
    assert events[0].event_type == "TaskCreated"
