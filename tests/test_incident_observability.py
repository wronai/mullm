from __future__ import annotations

import importlib.util
from pathlib import Path
from typing import Any

import pytest

from app.observability.incidents import IncidentCode, IncidentRecorder


@pytest.mark.asyncio
async def test_observability_playbooks_are_exposed():
    from app.api.observability import list_playbooks

    payload = await list_playbooks()

    playbook_ids = {item["playbook_id"] for item in payload["items"]}
    assert "rag.healthcheck_and_degraded_mode" in playbook_ids


@pytest.mark.asyncio
async def test_incident_recorder_publishes_projectable_events(fake_postgres, fake_bus):
    recorder = IncidentRecorder(fake_postgres, message_bus=fake_bus)

    incident = await recorder.record(
        code=IncidentCode.RAG_BACKEND_UNAVAILABLE,
        message="retriever returned 500",
        severity="error",
        diagnostics={
            "status": "unhealthy",
            "primary_incident_code": "RAG_BACKEND_UNAVAILABLE",
            "checks": [
                {"name": "postgres", "status": "pass"},
                {"name": "vector_search", "status": "fail"},
            ],
        },
        fallback_taken="search_exception",
        trace_steps=[
            {
                "event": "RagRequestStarted",
                "query": "what broke?",
            }
        ],
    )

    assert fake_postgres.incidents[0]["incident_id"] == incident["incident_id"]
    published = [message for _, message in fake_bus.messages]
    event_types = [message["event_type"] for message in published]
    assert event_types == [
        "RagRequestFailed",
        "IncidentDetected",
        "IncidentClassified",
        "DiagnosticsStarted",
        "DiagnosticsCompleted",
    ]

    detected = next(m for m in published if m["event_type"] == "IncidentDetected")
    assert detected["aggregate_type"] == "incident"
    assert detected["payload"]["error_code"] == "RAG_BACKEND_UNAVAILABLE"
    assert detected["payload"]["incident_class"] == "availability incident"
    assert detected["payload"]["playbook_id"] == "rag.healthcheck_and_degraded_mode"

    diagnostics = next(
        m for m in published if m["event_type"] == "DiagnosticsCompleted"
    )
    assert diagnostics["payload"]["checks"]["vector_search"]["status"] == "fail"


@pytest.mark.asyncio
async def test_rag_search_failure_returns_incident_payload(fake_postgres, fake_bus):
    from fastapi import FastAPI
    from starlette.testclient import TestClient

    from app.api.rag import router as rag_router

    class FailingRetriever:
        async def search(self, query: str, *, limit: int = 8):
            raise RuntimeError('relation "rag_chunks" does not exist')

    class FakeDiagnostics:
        async def run(self, *, query: str | None = None):
            return {
                "status": "unhealthy",
                "checks": [
                    {
                        "name": "rag_index",
                        "status": "fail",
                        "incident_code": "VECTOR_DB_UNAVAILABLE",
                    }
                ],
                "primary_incident_code": "VECTOR_DB_UNAVAILABLE",
            }

    app = FastAPI()
    app.state.rag_retriever = FailingRetriever()
    app.state.rag_diagnostics = FakeDiagnostics()
    app.state.incident_recorder = IncidentRecorder(fake_postgres, message_bus=fake_bus)
    app.include_router(rag_router, prefix="/api/rag")

    response = TestClient(app).post(
        "/api/rag/search",
        json={"query": "status", "limit": 3},
        headers={"X-Correlation-ID": "test-correlation"},
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["items"] == []
    assert payload["fallback_taken"] is True
    assert payload["incident"]["incident_code"] == "VECTOR_DB_UNAVAILABLE"
    assert payload["correlation_id"]
    assert [m[1]["event_type"] for m in fake_bus.messages][:2] == [
        "RagRequestFailed",
        "IncidentDetected",
    ]


@pytest.mark.asyncio
async def test_project_incidents_accepts_legacy_incident_code_payload():
    project_incidents = _load_project_incidents()
    db = RecordingDb()

    await project_incidents(
        db,
        {
            "aggregate_type": "incident",
            "event_type": "IncidentDetected",
            "occurred_at": "2026-01-01T00:00:00+00:00",
            "correlation_id": "cid-1",
            "payload": {
                "incident_id": "inc-1",
                "incident_code": "RAG_BACKEND_UNAVAILABLE",
                "severity": "error",
                "message": "legacy payload",
            },
        },
    )

    assert db.calls
    args = db.calls[0]["args"]
    assert args[0] == "inc-1"
    assert args[3] == "orchestrator.rag"
    assert args[4] == "RAG_BACKEND_UNAVAILABLE"


def _load_project_incidents():
    path = (
        Path(__file__).resolve().parents[1]
        / "services"
        / "projector"
        / "app"
        / "projections"
        / "incidents.py"
    )
    spec = importlib.util.spec_from_file_location("projector_incidents", path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module.project_incidents


class RecordingDb:
    def __init__(self) -> None:
        self.calls: list[dict[str, Any]] = []

    async def execute(self, query: str, *args: Any) -> str:
        self.calls.append({"query": query, "args": args})
        return "OK"
