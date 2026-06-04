from __future__ import annotations

from typing import Any
from uuid import uuid4
import logging

from app.domain.events import (
    DiagnosticsCompleted,
    DiagnosticsStarted,
    IncidentClassified,
    IncidentDetected,
    PostRemediationVerificationFailed,
    PostRemediationVerificationPassed,
    RagRequestFailed,
    RemediationFailed,
    RemediationStarted,
    RemediationSucceeded,
)


logger = logging.getLogger(__name__)


_RAG_ERROR_RULES = [
    (
        lambda message: (
            "does not exist" in message
            and ("rag_chunks" in message or "rag_documents" in message)
        ),
        {
            "incident_class": "config incident",
            "error_code": "RAG_SCHEMA_MISSING",
            "playbook_id": "rag.apply_schema_migrations",
            "severity": "critical",
            "confidence": 0.98,
        },
    ),
    (
        lambda message: "timeout" in message or "timed out" in message,
        {
            "incident_class": "availability incident",
            "error_code": "RAG_TIMEOUT",
            "playbook_id": "rag.degraded_retry",
            "severity": "warning",
            "confidence": 0.9,
        },
    ),
    (
        lambda message: (
            "openrouter" in message
            or "api_key" in message
            or "unauthorized" in message
        ),
        {
            "incident_class": "config incident",
            "error_code": "EMBEDDING_PIPELINE_FAILED",
            "playbook_id": "rag.degraded_fts",
            "severity": "warning",
            "confidence": 0.85,
        },
    ),
    (
        lambda message: "no matching chunks" in message or "empty" in message,
        {
            "incident_class": "data incident",
            "error_code": "RETRIEVER_EMPTY_RESULT",
            "playbook_id": "rag.reindex_recent_resources",
            "severity": "info",
            "confidence": 0.8,
        },
    ),
]

_DEFAULT_RAG_ERROR = {
    "incident_class": "availability incident",
    "error_code": "RAG_BACKEND_UNAVAILABLE",
    "playbook_id": "rag.healthcheck_and_degraded_mode",
    "severity": "critical",
    "confidence": 0.75,
}


def classify_rag_error(error: Exception | str) -> dict[str, Any]:
    lowered = str(error).lower()
    for predicate, classification in _RAG_ERROR_RULES:
        if predicate(lowered):
            return dict(classification)
    return dict(_DEFAULT_RAG_ERROR)


def _rag_root_cause(checks: dict[str, Any]) -> str:
    combined_errors = " ".join(
        str(value.get("error", ""))
        for value in checks.values()
        if isinstance(value, dict)
    ).lower()
    for predicate, root_cause in _RAG_ROOT_CAUSE_RULES:
        if predicate(checks, combined_errors):
            return root_cause
    return "unknown"


def _rag_schema_missing(checks: dict[str, Any], combined_errors: str) -> bool:
    return "does not exist" in combined_errors


def _rag_index_empty(checks: dict[str, Any], combined_errors: str) -> bool:
    return checks.get("rag_documents", {}).get("count_sample") == 0


def _retriever_empty_result(checks: dict[str, Any], combined_errors: str) -> bool:
    return checks.get("rag_chunks", {}).get("sample_hits") == 0


def _openrouter_unconfigured(checks: dict[str, Any], combined_errors: str) -> bool:
    return not checks.get("openrouter_health", {}).get("configured", False)


_RAG_ROOT_CAUSE_RULES = (
    (_rag_schema_missing, "rag_schema_missing"),
    (_rag_index_empty, "rag_index_empty"),
    (_retriever_empty_result, "retriever_empty_result"),
    (_openrouter_unconfigured, "openrouter_unconfigured_degraded_fts"),
)


class IncidentPipeline:
    def __init__(
        self,
        *,
        event_store: Any,
        message_bus: Any = None,
        postgres: Any = None,
        rag_store: Any = None,
        openrouter: Any = None,
    ) -> None:
        self.event_store = event_store
        self.message_bus = message_bus
        self.postgres = postgres
        self.rag_store = rag_store
        self.openrouter = openrouter

    async def handle_rag_failure(
        self,
        *,
        query: str,
        error: Exception | str,
        correlation_id: str | None = None,
        context: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        incident_id = str(uuid4())
        classification = classify_rag_error(error)
        checks = ["openrouter_health", "rag_documents", "rag_chunks"]
        diagnostics = await self._run_rag_diagnostics(query)

        events: list[Any] = [
            RagRequestFailed(
                incident_id=incident_id,
                query=query,
                error_code=classification["error_code"],
                message=str(error),
                context=context or {},
            ),
            IncidentDetected(
                incident_id=incident_id,
                incident_type="rag",
                severity=classification["severity"],
                source="orchestrator.rag",
                error_code=classification["error_code"],
                message=str(error),
                context={**(context or {}), "query": query},
            ),
            IncidentClassified(
                incident_id=incident_id,
                incident_class=classification["incident_class"],
                error_code=classification["error_code"],
                confidence=classification["confidence"],
                playbook_id=classification["playbook_id"],
            ),
            DiagnosticsStarted(incident_id=incident_id, checks=checks),
            DiagnosticsCompleted(
                incident_id=incident_id,
                root_cause=diagnostics["root_cause"],
                checks=diagnostics["checks"],
            ),
        ]

        remediation = await self._remediate_rag_incident(
            query=query,
            classification=classification,
            diagnostics=diagnostics,
        )
        if remediation:
            events.extend(remediation["events"])

        records = await self._append_and_publish(
            incident_id,
            events,
            correlation_id=correlation_id,
        )
        return {
            "incident_id": incident_id,
            "classification": classification,
            "diagnostics": diagnostics,
            "remediation": remediation["summary"] if remediation else None,
            "events": [
                record.to_message() if hasattr(record, "to_message") else record
                for record in records
            ],
        }

    async def _run_rag_diagnostics(self, query: str) -> dict[str, Any]:
        checks: dict[str, Any] = {}
        checks["openrouter_health"] = await self._openrouter_health_check()
        checks["rag_documents"] = await self._rag_document_check()
        checks["rag_chunks"] = await self._rag_chunk_check(query)
        return {"root_cause": _rag_root_cause(checks), "checks": checks}

    async def _openrouter_health_check(self) -> dict[str, Any]:
        if not self.openrouter:
            return {"configured": False}
        try:
            return await self.openrouter.health()
        except Exception as exc:
            return {"ok": False, "error": str(exc)}

    async def _rag_document_check(self) -> dict[str, Any]:
        if not self.rag_store:
            return {"ok": False, "error": "rag_store not configured"}
        try:
            docs = await self.rag_store.list_documents(limit=5)
            return {
                "ok": True,
                "count_sample": len(docs),
                "statuses": sorted({doc.get("status", "unknown") for doc in docs}),
            }
        except Exception as exc:
            return {"ok": False, "error": str(exc)}

    async def _rag_chunk_check(self, query: str) -> dict[str, Any]:
        if not self.rag_store:
            return {"ok": False, "error": "rag_store not configured"}
        try:
            hits = await self.rag_store.search(query or "health", limit=1)
            return {"ok": True, "sample_hits": len(hits)}
        except Exception as exc:
            return {"ok": False, "error": str(exc)}

    async def _remediate_rag_incident(
        self,
        *,
        query: str,
        classification: dict[str, Any],
        diagnostics: dict[str, Any],
    ) -> dict[str, Any] | None:
        playbook_id = classification["playbook_id"]
        if playbook_id != "rag.apply_schema_migrations":
            return {
                "summary": {
                    "playbook_id": playbook_id,
                    "automatic": False,
                    "action": "degraded_mode_or_manual_reindex",
                },
                "events": [
                    RemediationStarted(
                        incident_id="",
                        playbook_id=playbook_id,
                        action="degraded_mode_or_manual_reindex",
                    ),
                    RemediationSucceeded(
                        incident_id="",
                        playbook_id=playbook_id,
                        result={"automatic": False, "reason": diagnostics["root_cause"]},
                    ),
                ],
            }

        events: list[Any] = [
            RemediationStarted(
                incident_id="",
                playbook_id=playbook_id,
                action="apply_schema_migrations",
            )
        ]
        try:
            if not self.postgres or not hasattr(self.postgres, "_run_schema_migrations"):
                raise RuntimeError("schema migration hook is not configured")
            await self.postgres._run_schema_migrations()
            events.append(
                RemediationSucceeded(
                    incident_id="",
                    playbook_id=playbook_id,
                    result={"automatic": True, "action": "schema_migrations_applied"},
                )
            )
        except Exception as exc:
            events.append(
                RemediationFailed(
                    incident_id="",
                    playbook_id=playbook_id,
                    error=str(exc),
                )
            )
            return {
                "summary": {
                    "playbook_id": playbook_id,
                    "automatic": True,
                    "ok": False,
                    "error": str(exc),
                },
                "events": events,
            }

        verification = await self._verify_rag(query)
        if verification.get("ok"):
            events.append(PostRemediationVerificationPassed(incident_id="", verification=verification))
        else:
            events.append(PostRemediationVerificationFailed(incident_id="", verification=verification))
        return {
            "summary": {
                "playbook_id": playbook_id,
                "automatic": True,
                "ok": verification.get("ok", False),
            },
            "events": events,
        }

    async def _verify_rag(self, query: str) -> dict[str, Any]:
        if not self.rag_store:
            return {"ok": False, "error": "rag_store not configured"}
        try:
            await self.rag_store.search(query or "health", limit=1)
            return {"ok": True}
        except Exception as exc:
            return {"ok": False, "error": str(exc)}

    async def _append_and_publish(
        self,
        incident_id: str,
        events: list[Any],
        *,
        correlation_id: str | None,
    ) -> list[Any]:
        normalized = [
            self._with_incident_id(event, incident_id)
            for event in events
        ]
        records = await self.event_store.append(
            "incident",
            incident_id,
            normalized,
            causation_id=f"incident-{incident_id}",
            correlation_id=correlation_id,
            metadata={"actor": {"type": "system", "id": "incident-pipeline"}},
        )
        for record in records:
            message = record.to_message() if hasattr(record, "to_message") else record
            if self.message_bus:
                await self.message_bus.publish("mullm.events", message)
        return records

    def _with_incident_id(self, event: Any, incident_id: str) -> Any:
        if getattr(event, "incident_id", None):
            return event
        data = getattr(event, "__dict__", {}).copy()
        data["incident_id"] = incident_id
        return event.__class__(**data)
