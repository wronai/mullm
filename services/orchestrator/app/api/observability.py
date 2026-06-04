from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Request
from pydantic import BaseModel

from app.observability.context import (
    get_correlation_id,
    new_correlation_id,
    new_retrieval_trace_id,
    observability_context,
)
from app.observability.export import (
    DEFAULT_LOG_EXPORT_LIMIT,
    build_orchestrator_bundle,
    clamp_log_export_limit,
)

router = APIRouter()


class DiagnoseBody(BaseModel):
    query: str | None = None


PLAYBOOKS: list[dict[str, Any]] = [
    {
        "playbook_id": "rag.healthcheck_and_degraded_mode",
        "incident_codes": ["RAG_BACKEND_UNAVAILABLE"],
        "automation": "conditional",
        "actions": [
            "run_rag_diagnostics",
            "return_degraded_response",
            "publish_incident_events",
        ],
    },
    {
        "playbook_id": "rag.vector_store_healthcheck",
        "incident_codes": ["VECTOR_DB_UNAVAILABLE"],
        "automation": "manual_approval",
        "actions": ["check_postgres", "check_rag_tables", "escalate_if_schema_missing"],
    },
    {
        "playbook_id": "rag.reindex_recent_resources",
        "incident_codes": ["RETRIEVER_EMPTY_RESULT", "INDEX_STALE"],
        "automation": "manual_approval",
        "actions": ["list_recent_resources", "queue_reindex", "verify_smoke_query"],
    },
    {
        "playbook_id": "rag.llm_degraded_mode",
        "incident_codes": ["LLM_UNAVAILABLE"],
        "automation": "automatic",
        "actions": ["serve_retrieved_fragments", "record_llm_incident"],
    },
]


@router.get("/health/rag")
async def rag_health(request: Request):
    diag = request.app.state.rag_diagnostics
    with observability_context(retrieval_trace_id=new_retrieval_trace_id()):
        result = await diag.run(query=None)
    return result


@router.post("/rag/diagnose")
async def rag_diagnose(body: DiagnoseBody, request: Request):
    diag = request.app.state.rag_diagnostics
    with observability_context(retrieval_trace_id=new_retrieval_trace_id()):
        return await diag.run(query=body.query)


@router.get("/playbooks")
async def list_playbooks():
    return {"items": PLAYBOOKS}


@router.get("/logs/export")
async def export_logs(
    request: Request,
    correlation_id: str | None = None,
    limit: int = DEFAULT_LOG_EXPORT_LIMIT,
):
    """Paczka diagnostyczna (JSON + pole `text` do schowka)."""
    limit = clamp_log_export_limit(limit)
    with observability_context(correlation_id=correlation_id or new_correlation_id()):
        return await build_orchestrator_bundle(
            postgres=request.app.state.postgres,
            rag_diagnostics=request.app.state.rag_diagnostics,
            correlation_id=correlation_id,
            limit=limit,
        )


@router.get("/incidents")
async def list_incidents(request: Request, limit: int = DEFAULT_LOG_EXPORT_LIMIT):
    limit = clamp_log_export_limit(limit)
    try:
        rows = await request.app.state.postgres.fetch(
            """
            select incident_id, correlation_id, retrieval_trace_id, incident_code,
                   severity, message, status, fallback_taken, created_at
            from incidents
            order by created_at desc
            limit $1
            """,
            limit,
        )
        return {"items": [dict(r) for r in rows], "correlation_id": get_correlation_id()}
    except Exception as exc:
        return {"items": [], "error": str(exc)}
