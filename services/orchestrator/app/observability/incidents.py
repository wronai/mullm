from __future__ import annotations

import json
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any

from app.observability.context import get_correlation_id, get_retrieval_trace_id
from app.observability.logging import log_event


class IncidentCode(str, Enum):
    RAG_BACKEND_UNAVAILABLE = "RAG_BACKEND_UNAVAILABLE"
    RAG_TIMEOUT = "RAG_TIMEOUT"
    VECTOR_DB_UNAVAILABLE = "VECTOR_DB_UNAVAILABLE"
    RETRIEVER_EMPTY_RESULT = "RETRIEVER_EMPTY_RESULT"
    SOURCE_RESOLUTION_FAILED = "SOURCE_RESOLUTION_FAILED"
    GROUNDING_FAILED = "GROUNDING_FAILED"
    EMBEDDING_PIPELINE_FAILED = "EMBEDDING_PIPELINE_FAILED"
    LLM_UNAVAILABLE = "LLM_UNAVAILABLE"
    INDEX_STALE = "INDEX_STALE"
    UNKNOWN = "UNKNOWN"


def classify_rag_failure(
    *,
    http_status: int | None = None,
    llm_error: str | None = None,
    source_count: int = 0,
    exception: str | None = None,
) -> IncidentCode:
    text = " ".join(filter(None, [llm_error, exception, str(http_status)])).lower()
    if http_status and http_status >= 500:
        return IncidentCode.RAG_BACKEND_UNAVAILABLE
    if "timeout" in text or "timed out" in text:
        return IncidentCode.RAG_TIMEOUT
    if "vector" in text or "relation" in text and "does not exist" in text:
        return IncidentCode.VECTOR_DB_UNAVAILABLE
    if "embedding" in text:
        return IncidentCode.EMBEDDING_PIPELINE_FAILED
    if "openrouter" in text or "not a valid model" in text or "api_key" in text:
        return IncidentCode.LLM_UNAVAILABLE
    if source_count == 0:
        return IncidentCode.RETRIEVER_EMPTY_RESULT
    if llm_error and source_count > 0:
        return IncidentCode.GROUNDING_FAILED
    return IncidentCode.UNKNOWN


@dataclass
class IncidentRecorder:
    postgres: Any
    message_bus: Any = None

    async def record(
        self,
        *,
        code: IncidentCode,
        message: str,
        severity: str = "warning",
        component: str = "rag",
        correlation_id: str | None = None,
        retrieval_trace_id: str | None = None,
        chat_session_id: str | None = None,
        diagnostics: dict[str, Any] | None = None,
        remediation: dict[str, Any] | None = None,
        fallback_taken: str | None = None,
        trace_steps: list[dict[str, Any]] | None = None,
    ) -> dict[str, Any]:
        incident_id = str(uuid.uuid4())
        correlation_id = correlation_id or get_correlation_id() or str(uuid.uuid4())
        retrieval_trace_id = retrieval_trace_id or get_retrieval_trace_id()
        now = datetime.now(timezone.utc)

        row = {
            "incident_id": incident_id,
            "correlation_id": correlation_id,
            "retrieval_trace_id": retrieval_trace_id,
            "chat_session_id": chat_session_id,
            "incident_code": code.value,
            "severity": severity,
            "component": component,
            "message": message,
            "diagnostics": diagnostics or {},
            "remediation": remediation or {},
            "status": "open",
            "fallback_taken": fallback_taken,
            "created_at": now.isoformat(),
            "trace_steps": trace_steps or [],
        }

        log_event(
            severity=severity,
            component=component,
            message=message,
            error_code=code.value,
            incident_id=incident_id,
            fallback_taken=fallback_taken,
        )

        await self._persist(row)
        if component == "rag":
            await self._publish_event("RagRequestFailed", row)
        await self._publish_event("IncidentDetected", row)
        await self._publish_event("IncidentClassified", row)
        if diagnostics:
            await self._publish_event("DiagnosticsStarted", row)
            await self._publish_event(
                "DiagnosticsCompleted", {**row, "diagnostics": diagnostics}
            )
        if remediation and remediation.get("attempted"):
            await self._publish_event("RemediationStarted", row)
            status = remediation.get("status")
            if status and status != "running":
                event_type = (
                    "RemediationFailed"
                    if status in {"failed", "error"}
                    else "RemediationSucceeded"
                )
                await self._publish_event(event_type, row)
                if remediation.get("verification") is not None:
                    verification_event = (
                        "PostRemediationVerificationPassed"
                        if remediation.get("verification", {}).get("ok")
                        else "PostRemediationVerificationFailed"
                    )
                    await self._publish_event(verification_event, row)
        return row

    async def _persist(self, row: dict[str, Any]) -> None:
        try:
            await self.postgres.execute(
                """
                insert into incidents (
                  incident_id, correlation_id, retrieval_trace_id, chat_session_id,
                  incident_code, severity, component, service, message,
                  diagnostics, remediation, status, fallback_taken, created_at
                )
                values ($1,$2,$3,$4,$5,$6,$7,'orchestrator',$8,$9::jsonb,$10::jsonb,$11,$12,$13)
                """,
                row["incident_id"],
                row["correlation_id"],
                row["retrieval_trace_id"],
                row["chat_session_id"],
                row["incident_code"],
                row["severity"],
                row["component"],
                row["message"],
                json.dumps({**row["diagnostics"], "trace_steps": row["trace_steps"]}, default=str),
                json.dumps(row["remediation"], default=str),
                row["status"],
                row["fallback_taken"],
                row["created_at"],
            )
        except Exception as exc:
            log_event(
                severity="warning",
                component="incidents",
                message=f"Could not persist incident: {exc}",
                error_code="INCIDENT_PERSIST_FAILED",
            )

    async def _publish_event(self, event_type: str, row: dict[str, Any]) -> None:
        if not self.message_bus:
            return
        payload = _event_payload(event_type, row)
        message = {
            "event_id": str(uuid.uuid4()),
            "stream_id": f"incident-{row['incident_id']}",
            "aggregate_type": "incident",
            "aggregate_id": row["incident_id"],
            "event_type": event_type,
            "revision": 1,
            "occurred_at": datetime.now(timezone.utc).isoformat(),
            "correlation_id": row["correlation_id"],
            "payload": payload,
            "metadata": {"actor": {"type": "system", "id": "observability"}},
        }
        try:
            await self.message_bus.publish("mullm.events", message)
        except Exception:
            pass


def _event_payload(event_type: str, row: dict[str, Any]) -> dict[str, Any]:
    code = row["incident_code"]
    diagnostics = row.get("diagnostics") or {}
    remediation = row.get("remediation") or {}
    playbook_id = remediation.get("playbook_id") or _default_playbook(code)
    context = {
        "retrieval_trace_id": row.get("retrieval_trace_id"),
        "chat_session_id": row.get("chat_session_id"),
        "fallback_taken": row.get("fallback_taken"),
        "trace_steps": row.get("trace_steps") or [],
    }

    payload: dict[str, Any] = {
        "incident_id": row["incident_id"],
        "incident_type": row.get("component") or "rag",
        "incident_class": _incident_class(code),
        "incident_code": code,
        "error_code": code,
        "correlation_id": row.get("correlation_id"),
        "retrieval_trace_id": row.get("retrieval_trace_id"),
        "chat_session_id": row.get("chat_session_id"),
        "source": f"orchestrator.{row.get('component') or 'rag'}",
        "message": row.get("message") or "",
        "severity": row.get("severity") or "warning",
        "status": _event_status(event_type, row),
        "context": context,
        "diagnostics": diagnostics,
        "remediation": remediation,
        "fallback_taken": row.get("fallback_taken"),
        "playbook_id": playbook_id,
    }

    if event_type == "RagRequestFailed":
        payload["query"] = _query_from_trace(row.get("trace_steps") or [])
    elif event_type == "IncidentClassified":
        payload["confidence"] = 0.8
    elif event_type == "DiagnosticsStarted":
        payload["checks"] = _check_names(diagnostics)
    elif event_type == "DiagnosticsCompleted":
        checks = _checks_payload(diagnostics)
        payload["checks"] = checks
        payload["root_cause"] = _root_cause(diagnostics, code)
    elif event_type == "RemediationStarted":
        payload["action"] = remediation.get("action")
    elif event_type in {"RemediationSucceeded", "RemediationFailed"}:
        payload["result"] = remediation.get("result") or {}
        payload["error"] = remediation.get("error")
    elif event_type.startswith("PostRemediationVerification"):
        payload["verification"] = remediation.get("verification") or {}

    return payload


def _query_from_trace(trace_steps: list[dict[str, Any]]) -> str | None:
    for step in trace_steps:
        if step.get("event") == "RagRequestStarted" and step.get("query"):
            return step["query"]
    return None


def _check_names(diagnostics: dict[str, Any]) -> list[str]:
    checks = diagnostics.get("checks") or []
    if isinstance(checks, dict):
        return list(checks.keys())
    if isinstance(checks, list):
        return [str(item.get("name")) for item in checks if isinstance(item, dict)]
    return []


def _checks_payload(diagnostics: dict[str, Any]) -> dict[str, Any]:
    checks = diagnostics.get("checks") or {}
    if isinstance(checks, dict):
        return checks
    if isinstance(checks, list):
        return {
            str(item.get("name", idx)): {
                key: value for key, value in item.items() if key != "name"
            }
            for idx, item in enumerate(checks)
            if isinstance(item, dict)
        }
    return {}


def _root_cause(diagnostics: dict[str, Any], code: str) -> str:
    if diagnostics.get("root_cause"):
        return str(diagnostics["root_cause"])
    if diagnostics.get("primary_incident_code"):
        return str(diagnostics["primary_incident_code"])
    if diagnostics.get("status") in {"unhealthy", "degraded"}:
        return code
    return code


def _event_status(event_type: str, row: dict[str, Any]) -> str:
    if event_type == "IncidentDetected":
        return row.get("status") or "detected"
    if event_type == "IncidentClassified":
        return "classified"
    if event_type == "DiagnosticsStarted":
        return "diagnosing"
    if event_type == "DiagnosticsCompleted":
        return "diagnosed"
    if event_type == "RemediationStarted":
        return "remediating"
    if event_type == "RemediationSucceeded":
        return "remediated"
    if event_type == "RemediationFailed":
        return "remediation_failed"
    if event_type == "PostRemediationVerificationPassed":
        return "verified"
    if event_type == "PostRemediationVerificationFailed":
        return "verification_failed"
    return row.get("status") or "open"


def _incident_class(code: str) -> str:
    if code in {
        IncidentCode.RAG_BACKEND_UNAVAILABLE.value,
        IncidentCode.RAG_TIMEOUT.value,
        IncidentCode.VECTOR_DB_UNAVAILABLE.value,
        IncidentCode.LLM_UNAVAILABLE.value,
    }:
        return "availability incident"
    if code in {
        IncidentCode.RETRIEVER_EMPTY_RESULT.value,
        IncidentCode.INDEX_STALE.value,
        IncidentCode.SOURCE_RESOLUTION_FAILED.value,
    }:
        return "data incident"
    if code in {
        IncidentCode.GROUNDING_FAILED.value,
        IncidentCode.EMBEDDING_PIPELINE_FAILED.value,
    }:
        return "quality incident"
    return "unknown"


def _default_playbook(code: str) -> str:
    mapping = {
        IncidentCode.RAG_BACKEND_UNAVAILABLE.value: "rag.healthcheck_and_degraded_mode",
        IncidentCode.RAG_TIMEOUT.value: "rag.degraded_retry",
        IncidentCode.VECTOR_DB_UNAVAILABLE.value: "rag.vector_store_healthcheck",
        IncidentCode.RETRIEVER_EMPTY_RESULT.value: "rag.reindex_recent_resources",
        IncidentCode.SOURCE_RESOLUTION_FAILED.value: "rag.source_resolution_check",
        IncidentCode.GROUNDING_FAILED.value: "rag.grounding_fallback",
        IncidentCode.EMBEDDING_PIPELINE_FAILED.value: "rag.embedding_healthcheck",
        IncidentCode.LLM_UNAVAILABLE.value: "rag.llm_degraded_mode",
        IncidentCode.INDEX_STALE.value: "rag.reindex_recent_resources",
    }
    return mapping.get(code, "rag.manual_triage")
