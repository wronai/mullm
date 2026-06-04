from fastapi import FastAPI
from fastapi.testclient import TestClient
import pytest

from app.api.commands import router as commands_router
from app.api.queries import router as queries_router
from app.infrastructure.eventstore import EventRecord


class StubCommandBus:
    def __init__(self):
        self.calls = []

    async def handle(self, **kwargs):
        self.calls.append(kwargs)
        return {"aggregate_id": "task-1", "events": []}

    async def handle_envelope(self, envelope):
        self.calls.append(envelope)
        return {"aggregate_id": envelope.get("aggregate_id") or "task-1", "events": []}


class StubEventStore:
    async def get_events_for_aggregate(self, aggregate_type, aggregate_id):
        if aggregate_id == "missing":
            return []
        return [
            EventRecord(
                event_id="evt-1",
                stream_id=f"{aggregate_type}-{aggregate_id}",
                aggregate_type=aggregate_type,
                aggregate_id=aggregate_id,
                event_type="TaskCreated",
                revision=1,
                timestamp=__import__("datetime").datetime.utcnow(),
                data={"task_id": aggregate_id, "title": "Task", "status": "pending"},
                metadata={},
            )
        ]

    async def get_aggregate_ids(self, aggregate_type):
        return ["task-1"]


@pytest.fixture
def client():
    app = FastAPI()
    app.state.command_bus = StubCommandBus()
    app.state.event_store = StubEventStore()
    app.include_router(commands_router, prefix="/api/commands")
    app.include_router(queries_router, prefix="/api/queries")
    return TestClient(app)


def test_create_task_endpoint_dispatches_command(client):
    response = client.post("/api/commands/tasks", json={"title": "Task"})

    assert response.status_code == 200
    assert response.json()["result"]["aggregate_id"] == "task-1"


def test_generic_command_envelope_endpoint(client):
    response = client.post(
        "/api/commands",
        json={
            "aggregate_type": "task",
            "aggregate_id": "task-1",
            "command_type": "CreateTask",
            "payload": {"title": "Task"},
        },
    )

    assert response.status_code == 200
    assert response.json()["accepted"] is True


def test_get_task_query_returns_reconstructed_state(client):
    response = client.get("/api/queries/tasks/task-1")

    assert response.status_code == 200
    assert response.json()["state"]["title"] == "Task"


def test_get_task_query_returns_404(client):
    response = client.get("/api/queries/tasks/missing")

    assert response.status_code == 404
