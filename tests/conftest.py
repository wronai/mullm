from __future__ import annotations

import re
from dataclasses import dataclass
from datetime import datetime
from typing import Any
from uuid import uuid4

import pytest

from app.application.command_bus import CommandBus
from app.infrastructure.eventstore import EventRecord, EventStore


@dataclass
class FakeRow:
    _data: dict[str, Any]

    def __getitem__(self, key: str) -> Any:
        return self._data[key]

    def get(self, key: str, default: Any = None) -> Any:
        return self._data.get(key, default)

    def keys(self):
        return self._data.keys()


class InMemoryPostgres:
    def __init__(self) -> None:
        self.events: list[dict[str, Any]] = []
        self.rag_documents: dict[str, dict[str, Any]] = {}
        self.rag_chunks: list[dict[str, Any]] = []
        self.incidents: list[dict[str, Any]] = []
        self.rag_health_snapshots: list[dict[str, Any]] = []

    async def connect(self) -> None:
        return None

    async def disconnect(self) -> None:
        return None

    async def execute(self, query: str, *args: Any) -> str:
        if "insert into experiments" in query:
            return "OK"
        if "insert into change_proposals" in query:
            return "OK"
        if "insert into capability_registry" in query:
            return "OK"
        if "insert into resource_registry" in query:
            return "OK"
        if "insert into transfer_log" in query:
            return "OK"
        if "update resource_registry" in query:
            return "OK"
        if "update transfer_log" in query:
            return "OK"
        if "insert into evolution_metrics" in query:
            return "OK"
        if "update evolution_metrics" in query:
            return "OK"
        if "insert into rag_documents" in query:
            resource_id, uri, name, classification = args[0], args[1], args[2], args[3]
            self.rag_documents[resource_id] = {
                "resource_id": resource_id,
                "uri": uri,
                "name": name,
                "classification": classification,
                "status": "indexing",
                "chunk_count": 0,
                "embedding_model": None,
                "error": None,
            }
            return "OK"
        if "update rag_documents" in query and "status = 'indexed'" in query:
            resource_id, chunk_count, embedding_model = args[0], args[1], args[2]
            doc = self.rag_documents.setdefault(resource_id, {"resource_id": resource_id})
            doc.update(
                {
                    "status": "indexed",
                    "chunk_count": chunk_count,
                    "embedding_model": embedding_model,
                    "error": None,
                }
            )
            return "OK"
        if "update rag_documents" in query and "status = 'failed'" in query:
            resource_id, error = args[0], args[1]
            doc = self.rag_documents.setdefault(resource_id, {"resource_id": resource_id})
            doc.update({"status": "failed", "error": error})
            return "OK"
        if "delete from rag_chunks" in query:
            resource_id = args[0]
            self.rag_chunks = [
                c for c in self.rag_chunks if c["resource_id"] != resource_id
            ]
            return "OK"
        if "insert into rag_chunks" in query:
            chunk_id, resource_id, position, content, embedding = args[:5]
            doc = self.rag_documents.get(resource_id, {})
            self.rag_chunks.append(
                {
                    "chunk_id": chunk_id,
                    "resource_id": resource_id,
                    "position": position,
                    "content": content,
                    "embedding": embedding,
                    "uri": doc.get("uri", ""),
                    "name": doc.get("name", ""),
                }
            )
            return "OK"
        if "insert into incidents" in query:
            self.incidents.append(
                {
                    "incident_id": args[0],
                    "correlation_id": args[1],
                    "retrieval_trace_id": args[2],
                    "chat_session_id": args[3],
                    "incident_code": args[4],
                    "severity": args[5],
                    "component": args[6],
                    "message": args[7],
                    "diagnostics": args[8],
                    "remediation": args[9],
                    "status": args[10],
                    "fallback_taken": args[11],
                    "created_at": args[12],
                }
            )
            return "OK"
        if "insert into rag_health_snapshots" in query:
            self.rag_health_snapshots.append(
                {
                    "snapshot_id": args[0],
                    "retrieval_trace_id": args[1],
                    "correlation_id": args[2],
                    "status": args[3],
                    "checks": args[4],
                }
            )
            return "OK"
        if "insert into events" in query:
            self.events.append(
                {
                    "event_id": args[0],
                    "stream_id": args[1],
                    "aggregate_type": args[2],
                    "aggregate_id": args[3],
                    "event_type": args[4],
                    "revision": args[5],
                    "occurred_at": args[6],
                    "causation_id": args[7],
                    "correlation_id": args[8],
                    "payload": args[9],
                    "metadata": args[10],
                }
            )
        return "OK"

    async def fetchrow(self, query: str, *args: Any) -> FakeRow | None:
        if "select 1 as ok" in query:
            return FakeRow({"ok": 1})
        if "count(*)::int as n from rag_documents" in query:
            return FakeRow({"n": len(self.rag_documents)})
        if "count(*)::int as n from rag_chunks" in query:
            return FakeRow({"n": len(self.rag_chunks)})

        stream_id = args[0]
        revision = max(
            (
                event["revision"]
                for event in self.events
                if event["stream_id"] == stream_id
            ),
            default=0,
        )
        return FakeRow({"revision": revision})

    async def fetch(self, query: str, *args: Any) -> list[FakeRow]:
        if "from incidents" in query and "order by created_at desc" in query:
            rows = sorted(
                self.incidents,
                key=lambda item: item["created_at"],
                reverse=True,
            )
            limit = args[-1] if args else 100
            return [FakeRow(row) for row in rows[:limit]]

        if "from rag_documents" in query and "order by updated_at" in query:
            docs = list(self.rag_documents.values())
            return [FakeRow(doc) for doc in docs[: args[0] if args else 100]]

        if "from rag_chunks" in query and "plainto_tsquery" in query:
            query_text = (args[0] if args else "").lower()
            tokens = [t for t in re.split(r"\W+", query_text) if len(t) > 2]
            hits = []
            for chunk in self.rag_chunks:
                doc = self.rag_documents.get(chunk["resource_id"], {})
                if doc.get("status") != "indexed":
                    continue
                text = chunk["content"].lower()
                score = sum(1 for token in tokens if token in text)
                if score:
                    row = {**chunk, "uri": doc.get("uri", ""), "name": doc.get("name", ""), "rank": float(score)}
                    hits.append((score, FakeRow(row)))
            hits.sort(key=lambda item: item[0], reverse=True)
            limit = args[1] if len(args) > 1 else 8
            return [row for _, row in hits[:limit]]

        if "from rag_chunks" in query and "c.embedding is not null" in query:
            rows = []
            for chunk in self.rag_chunks:
                if chunk.get("embedding"):
                    rows.append(FakeRow(chunk))
            return rows[:500]

        if "from rag_chunks" in query and "order by c.created_at desc" in query:
            limit = 300
            return [FakeRow(c) for c in self.rag_chunks[:limit]]

        if "distinct aggregate_id" in query:
            aggregate_type = args[0]
            ids = sorted(
                {
                    event["aggregate_id"]
                    for event in self.events
                    if event["aggregate_type"] == aggregate_type
                }
            )
            return [FakeRow({"aggregate_id": item}) for item in ids]

        if "aggregate_type = $1 and aggregate_id = $2" in query:
            aggregate_type, aggregate_id = args[0], args[1]
            rows = [
                event
                for event in self.events
                if event["aggregate_type"] == aggregate_type
                and event["aggregate_id"] == aggregate_id
            ]
            rows.sort(key=lambda item: item["revision"])
            return [self._event_row(row) for row in rows]

        rows = sorted(self.events, key=lambda item: item["revision"])
        return [self._event_row(row) for row in rows]

    def _event_row(self, event: dict[str, Any]) -> FakeRow:
        return FakeRow(
            {
                "event_id": event["event_id"],
                "stream_id": event["stream_id"],
                "aggregate_type": event["aggregate_type"],
                "aggregate_id": event["aggregate_id"],
                "event_type": event["event_type"],
                "revision": event["revision"],
                "occurred_at": event["occurred_at"],
                "causation_id": event["causation_id"],
                "correlation_id": event["correlation_id"],
                "payload": event["payload"],
                "metadata": event["metadata"],
            }
        )


class FakeMessageBus:
    def __init__(self) -> None:
        self.messages: list[tuple[str, dict[str, Any]]] = []

    async def publish(self, subject: str, payload: dict[str, Any]) -> None:
        self.messages.append((subject, payload))


@pytest.fixture
def fake_postgres() -> InMemoryPostgres:
    return InMemoryPostgres()


@pytest.fixture
def fake_bus() -> FakeMessageBus:
    return FakeMessageBus()


@pytest.fixture
def event_store(fake_postgres: InMemoryPostgres) -> EventStore:
    return EventStore(fake_postgres)


@pytest.fixture
def catalog():
    from pathlib import Path

    from app.evolution.catalog import ArchitectureCatalog

    root = Path(__file__).resolve().parents[1] / "catalog"
    return ArchitectureCatalog(root)


@pytest.fixture
def command_bus(
    event_store: EventStore,
    fake_bus: FakeMessageBus,
    fake_postgres: InMemoryPostgres,
    catalog,
) -> CommandBus:
    from app.evolution.experiments import ExperimentManager
    from app.evolution.policy_engine import PolicyEngine

    from app.access.transport import TransportService
    from app.rag import OpenRouterClient, RagIndexer, RagStore

    transport = TransportService()
    openrouter = OpenRouterClient(None, llm_model="test/model", embedding_model="test/embed")
    rag_indexer = RagIndexer(RagStore(fake_postgres), transport, openrouter)

    return CommandBus(
        event_store=event_store,
        message_bus=fake_bus,
        postgres=fake_postgres,
        policy_engine=PolicyEngine(catalog),
        experiments=ExperimentManager(fake_postgres),
        transport=transport,
        rag_indexer=rag_indexer,
        environment="dev",
    )


@pytest.fixture
def sample_command_id() -> str:
    return str(uuid4())


@pytest.fixture
def orchestrator_app(command_bus, event_store, fake_postgres, catalog):
    from fastapi import FastAPI

    from app.api.commands import router as commands_router
    from app.api.queries import router as queries_router

    app = FastAPI()
    app.state.command_bus = command_bus
    app.state.event_store = event_store
    app.state.postgres = fake_postgres
    app.state.catalog = catalog
    app.include_router(commands_router, prefix="/api/commands")
    app.include_router(queries_router, prefix="/api/queries")
    return app


@pytest.fixture
def api_client(orchestrator_app):
    from starlette.testclient import TestClient

    return TestClient(orchestrator_app)
