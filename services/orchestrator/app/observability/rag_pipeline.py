from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any

from app.observability.context import (
    get_correlation_id,
    get_retrieval_trace_id,
    new_retrieval_trace_id,
)
from app.observability.incidents import IncidentCode, IncidentRecorder, classify_rag_failure
from app.observability.logging import log_event
from app.observability.rag_diagnostics import RagDiagnostics


@dataclass
class RagPipeline:
    retriever: Any
    diagnostics: RagDiagnostics
    incidents: IncidentRecorder

    async def ask(
        self,
        *,
        query: str,
        limit: int = 6,
        chat_session_id: str | None = None,
        auto_remediate: bool = True,
    ) -> dict[str, Any]:
        trace_id = get_retrieval_trace_id() or new_retrieval_trace_id()
        correlation_id = get_correlation_id()
        steps: list[dict[str, Any]] = []

        def step(name: str, **extra: Any) -> None:
            steps.append(
                {"event": name, "at": datetime.now(timezone.utc).isoformat(), **extra}
            )
            log_event(severity="info", component="rag_pipeline", message=name, **extra)

        step("RagRequestStarted", query=query[:500], query_len=len(query))
        step("RetrieverHealthChecked")

        diag = None
        if auto_remediate:
            step("DiagnosticsStarted")
            diag = await self.diagnostics.run(query=query)
            step("DiagnosticsCompleted", status=diag["status"])

        try:
            step("VectorSearchStarted")
            result = await self.retriever.ask(query, limit=limit)
            step("SourcesResolved", source_count=len(result.get("sources") or []))
        except Exception as exc:
            code = classify_rag_failure(exception=str(exc))
            incident = await self.incidents.record(
                code=code,
                message=str(exc),
                severity="error",
                correlation_id=correlation_id,
                retrieval_trace_id=trace_id,
                chat_session_id=chat_session_id,
                diagnostics=diag,
                fallback_taken="exception",
                trace_steps=steps,
            )
            step("FallbackTriggered", reason="exception")
            return self._failure_payload(
                trace_id=trace_id,
                correlation_id=correlation_id,
                incident=incident,
                steps=steps,
                answer=f"Błąd RAG: {code.value}",
            )

        sources = result.get("sources") or []
        llm_error = result.get("llm_error")
        answer = result.get("answer") or ""

        if llm_error:
            code = classify_rag_failure(llm_error=llm_error, source_count=len(sources))
            incident = await self.incidents.record(
                code=code,
                message=llm_error,
                severity="warning",
                correlation_id=correlation_id,
                retrieval_trace_id=trace_id,
                chat_session_id=chat_session_id,
                diagnostics=diag,
                fallback_taken="fragment_fallback",
                trace_steps=steps,
            )
            step("FallbackTriggered", reason="llm_error")
            result["incident"] = incident
            result["retrieval_trace_id"] = trace_id
            result["correlation_id"] = correlation_id
            result["trace_steps"] = steps
            return result

        if not sources and not answer.strip():
            code = IncidentCode.RETRIEVER_EMPTY_RESULT
            incident = await self.incidents.record(
                code=code,
                message="Brak źródeł i odpowiedzi",
                correlation_id=correlation_id,
                retrieval_trace_id=trace_id,
                chat_session_id=chat_session_id,
                diagnostics=diag,
                fallback_taken="empty",
                trace_steps=steps,
            )
            step("UserErrorShown", incident_code=code.value)
            result["incident"] = incident
            result["retrieval_trace_id"] = trace_id
            result["correlation_id"] = correlation_id
            result["trace_steps"] = steps
            return result

        step("RagAnswerBuilt", source_count=len(sources))
        result["retrieval_trace_id"] = trace_id
        result["correlation_id"] = correlation_id
        result["trace_steps"] = steps
        return result

    def _failure_payload(
        self,
        *,
        trace_id: str,
        correlation_id: str | None,
        incident: dict[str, Any],
        steps: list[dict[str, Any]],
        answer: str,
    ) -> dict[str, Any]:
        return {
            "answer": answer,
            "sources": [],
            "llm_error": incident.get("message"),
            "incident": incident,
            "retrieval_trace_id": trace_id,
            "correlation_id": correlation_id,
            "trace_steps": steps,
        }
