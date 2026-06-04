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
        step = self._step_recorder(steps)

        step("RagRequestStarted", query=query[:500], query_len=len(query))
        step("RetrieverHealthChecked")

        diag = await self._diagnostics_if_enabled(auto_remediate, query, step)
        result, exc = await self._retriever_result(query, limit, step)
        if exc:
            return await self._exception_payload(
                exc,
                trace_id=trace_id,
                correlation_id=correlation_id,
                chat_session_id=chat_session_id,
                diagnostics=diag,
                steps=steps,
                step=step,
            )

        fallback = await self._fallback_payload_if_needed(
            result,
            trace_id=trace_id,
            correlation_id=correlation_id,
            chat_session_id=chat_session_id,
            diagnostics=diag,
            steps=steps,
            step=step,
        )
        if fallback:
            return fallback

        step("RagAnswerBuilt", source_count=len(result.get("sources") or []))
        return _result_with_trace(
            result,
            trace_id=trace_id,
            correlation_id=correlation_id,
            steps=steps,
        )

    def _step_recorder(self, steps: list[dict[str, Any]]):
        def step(name: str, **extra: Any) -> None:
            steps.append(
                {"event": name, "at": datetime.now(timezone.utc).isoformat(), **extra}
            )
            log_event(severity="info", component="rag_pipeline", message=name, **extra)

        return step

    async def _diagnostics_if_enabled(
        self,
        auto_remediate: bool,
        query: str,
        step,
    ) -> dict[str, Any] | None:
        if not auto_remediate:
            return None
        step("DiagnosticsStarted")
        diag = await self.diagnostics.run(query=query)
        step("DiagnosticsCompleted", status=diag["status"])
        return diag

    async def _retriever_result(
        self,
        query: str,
        limit: int,
        step,
    ) -> tuple[dict[str, Any], Exception | None]:
        try:
            step("VectorSearchStarted")
            result = await self.retriever.ask(query, limit=limit)
            step("SourcesResolved", source_count=len(result.get("sources") or []))
            return result, None
        except Exception as exc:
            return {}, exc

    async def _exception_payload(
        self,
        exc: Exception,
        *,
        trace_id: str,
        correlation_id: str | None,
        chat_session_id: str | None,
        diagnostics: dict[str, Any] | None,
        steps: list[dict[str, Any]],
        step,
    ) -> dict[str, Any]:
        code = classify_rag_failure(exception=str(exc))
        incident = await self.incidents.record(
            code=code,
            message=str(exc),
            severity="error",
            correlation_id=correlation_id,
            retrieval_trace_id=trace_id,
            chat_session_id=chat_session_id,
            diagnostics=diagnostics,
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

    async def _fallback_payload_if_needed(
        self,
        result: dict[str, Any],
        *,
        trace_id: str,
        correlation_id: str | None,
        chat_session_id: str | None,
        diagnostics: dict[str, Any] | None,
        steps: list[dict[str, Any]],
        step,
    ) -> dict[str, Any] | None:
        if result.get("llm_error"):
            return await self._llm_error_payload(
                result,
                trace_id=trace_id,
                correlation_id=correlation_id,
                chat_session_id=chat_session_id,
                diagnostics=diagnostics,
                steps=steps,
                step=step,
            )
        if not result.get("sources") and not (result.get("answer") or "").strip():
            return await self._empty_result_payload(
                result,
                trace_id=trace_id,
                correlation_id=correlation_id,
                chat_session_id=chat_session_id,
                diagnostics=diagnostics,
                steps=steps,
                step=step,
            )
        return None

    async def _llm_error_payload(
        self,
        result: dict[str, Any],
        *,
        trace_id: str,
        correlation_id: str | None,
        chat_session_id: str | None,
        diagnostics: dict[str, Any] | None,
        steps: list[dict[str, Any]],
        step,
    ) -> dict[str, Any]:
        llm_error = result["llm_error"]
        code = classify_rag_failure(
            llm_error=llm_error,
            source_count=len(result.get("sources") or []),
        )
        incident = await self.incidents.record(
            code=code,
            message=llm_error,
            severity="warning",
            correlation_id=correlation_id,
            retrieval_trace_id=trace_id,
            chat_session_id=chat_session_id,
            diagnostics=diagnostics,
            fallback_taken="fragment_fallback",
            trace_steps=steps,
        )
        step("FallbackTriggered", reason="llm_error")
        result["incident"] = incident
        return _result_with_trace(
            result,
            trace_id=trace_id,
            correlation_id=correlation_id,
            steps=steps,
        )

    async def _empty_result_payload(
        self,
        result: dict[str, Any],
        *,
        trace_id: str,
        correlation_id: str | None,
        chat_session_id: str | None,
        diagnostics: dict[str, Any] | None,
        steps: list[dict[str, Any]],
        step,
    ) -> dict[str, Any]:
        code = IncidentCode.RETRIEVER_EMPTY_RESULT
        incident = await self.incidents.record(
            code=code,
            message="Brak źródeł i odpowiedzi",
            correlation_id=correlation_id,
            retrieval_trace_id=trace_id,
            chat_session_id=chat_session_id,
            diagnostics=diagnostics,
            fallback_taken="empty",
            trace_steps=steps,
        )
        step("UserErrorShown", incident_code=code.value)
        result["incident"] = incident
        return _result_with_trace(
            result,
            trace_id=trace_id,
            correlation_id=correlation_id,
            steps=steps,
        )

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


def _result_with_trace(
    result: dict[str, Any],
    *,
    trace_id: str,
    correlation_id: str | None,
    steps: list[dict[str, Any]],
) -> dict[str, Any]:
    result["retrieval_trace_id"] = trace_id
    result["correlation_id"] = correlation_id
    result["trace_steps"] = steps
    return result
