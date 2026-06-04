from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel, Field

from app.observability.context import (
    get_correlation_id,
    new_retrieval_trace_id,
    observability_context,
)
from app.observability.incidents import classify_rag_failure

router = APIRouter()


class SearchQuery(BaseModel):
    query: str
    limit: int = Field(default=8, ge=1, le=50)


class AskQuery(BaseModel):
    query: str
    limit: int = Field(default=6, ge=1, le=20)
    chat_session_id: str | None = None


@router.get("/health")
async def rag_health(request: Request):
    client = request.app.state.openrouter
    return await client.health()


@router.get("/documents")
async def list_documents(request: Request, limit: int = 100):
    rows = await request.app.state.rag_store.list_documents(limit=limit)
    return {"items": rows}


@router.post("/search")
async def search(body: SearchQuery, request: Request):
    trace_id = new_retrieval_trace_id()
    steps: list[dict[str, Any]] = []

    def step(name: str, **extra: Any) -> None:
        steps.append(
            {"event": name, "at": datetime.now(timezone.utc).isoformat(), **extra}
        )

    with observability_context(retrieval_trace_id=trace_id):
        step("RagRequestStarted", query=body.query[:500], query_len=len(body.query))
        try:
            step("VectorSearchStarted")
            hits = await request.app.state.rag_retriever.search(
                body.query,
                limit=body.limit,
            )
            step("SourcesResolved", source_count=len(hits))
            return {
                "query": body.query,
                "items": hits,
                "retrieval_trace_id": trace_id,
                "correlation_id": get_correlation_id(),
                "trace_steps": steps,
            }
        except Exception as exc:
            step("FallbackTriggered", reason="search_exception")
            diagnostics = await _safe_rag_diagnostics(request, query=body.query)
            code = classify_rag_failure(exception=str(exc))
            incident = await request.app.state.incident_recorder.record(
                code=code,
                message=str(exc),
                severity="error",
                component="rag",
                correlation_id=get_correlation_id(),
                retrieval_trace_id=trace_id,
                diagnostics=diagnostics,
                fallback_taken="search_exception",
                trace_steps=steps,
            )
            return {
                "query": body.query,
                "items": [],
                "error": f"RAG search unavailable: {code.value}",
                "fallback_taken": True,
                "incident": incident,
                "diagnostics": diagnostics,
                "retrieval_trace_id": trace_id,
                "correlation_id": get_correlation_id() or incident.get("correlation_id"),
                "trace_steps": steps,
            }


@router.post("/ask")
async def ask(body: AskQuery, request: Request):
    trace_id = new_retrieval_trace_id()
    with observability_context(
        retrieval_trace_id=trace_id,
        chat_session_id=body.chat_session_id,
    ):
        result = await request.app.state.rag_pipeline.ask(
            query=body.query,
            limit=body.limit,
            chat_session_id=body.chat_session_id,
        )
    result.setdefault("correlation_id", get_correlation_id())
    return result


@router.post("/ingest/{resource_id}")
async def ingest_resource(resource_id: str, request: Request):
    events = await request.app.state.event_store.get_events_for_aggregate(
        "resource", resource_id
    )
    if not events:
        raise HTTPException(status_code=404, detail="resource not found")
    first = events[0].data
    outcome = await request.app.state.rag_indexer.ingest_resource(
        resource_id=resource_id,
        uri=first["uri"],
        name=first.get("name", ""),
        classification=first.get("classification", "document"),
    )
    return {"result": outcome}


async def _safe_rag_diagnostics(request: Request, *, query: str) -> dict[str, Any]:
    try:
        return await request.app.state.rag_diagnostics.run(query=query)
    except Exception as exc:
        return {
            "status": "error",
            "checks": {
                "diagnostics_runner": {
                    "status": "fail",
                    "detail": str(exc),
                }
            },
            "primary_incident_code": "UNKNOWN",
        }
