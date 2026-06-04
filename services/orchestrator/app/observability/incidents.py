from __future__ import annotations

import json
import uuid
from dataclasses import dataclass
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
    for predicate, code in _RAG_FAILURE_RULES:
        if predicate(http_status, text, llm_error, source_count):
            return code
    return IncidentCode.UNKNOWN


def _backend_unavailable(
    http_status: int | None,
    text: str,
    llm_error: str | None,
    source_count: int,
) -> bool:
    return bool(http_status and http_status >= 500)


def _rag_timeout(
    http_status: int | None,
    text: str,
    llm_error: str | None,
    source_count: int,
) -> bool:
    return "timeout" in text or "timed out" in text


def _vector_db_unavailable(
    http_status: int | None,
    text: str,
    llm_error: str | None,
    source_count: int,
) -> bool:
    return "vector" in text or ("relation" in text and "does not exist" in text)


def _embedding_pipeline_failed(
    http_status: int | None,
    text: str,
    llm_error: str | None,
    source_count: int,
) -> bool:
    return "embedding" in text


def _llm_unavailable(
    http_status: int | None,
    text: str,
    llm_error: str | None,
    source_count: int,
) -> bool:
    return "openrouter" in text or "not a valid model" in text or "api_key" in text


def _retriever_empty_result(
    http_status: int | None,
    text: str,
    llm_error: str | None,
    source_count: int,
) -> bool:
    return source_count == 0


def _grounding_failed(
    http_status: int | None,
    text: str,
    llm_error: str | None,
    source_count: int,
) -> bool:
    return bool(llm_error and source_count > 0)


_RAG_FAILURE_RULES = (
    (_backend_unavailable, IncidentCode.RAG_BACKEND_UNAVAILABLE),
    (_rag_timeout, IncidentCode.RAG_TIMEOUT),
    (_vector_db_unavailable, IncidentCode.VECTOR_DB_UNAVAILABLE),
    (_embedding_pipeline_failed, IncidentCode.EMBEDDING_PIPELINE_FAILED),
    (_llm_unavailable, IncidentCode.LLM_UNAVAILABLE),
    (_retriever_empty_result, IncidentCode.RETRIEVER_EMPTY_RESULT),
    (_grounding_failed, IncidentCode.GROUNDING_FAILED),
)


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
        row = _incident_row(
            code=code,
            message=message,
            severity=severity,
            component=component,
            correlation_id=correlation_id,
            retrieval_trace_id=retrieval_trace_id,
            chat_session_id=chat_session_id,
            diagnostics=diagnostics,
            remediation=remediation,
            fallback_taken=fallback_taken,
            trace_steps=trace_steps,
        )
        _log_incident_row(row)
        await self._persist(row)
        for event_type, payload_row in _incident_event_plan(row):
            await self._publish_event(event_type, payload_row)
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


def _incident_row(
    *,
    code: IncidentCode,
    message: str,
    severity: str,
    component: str,
    correlation_id: str | None,
    retrieval_trace_id: str | None,
    chat_session_id: str | None,
    diagnostics: dict[str, Any] | None,
    remediation: dict[str, Any] | None,
    fallback_taken: str | None,
    trace_steps: list[dict[str, Any]] | None,
) -> dict[str, Any]:
    return {
        "incident_id": str(uuid.uuid4()),
        "correlation_id": _incident_correlation_id(correlation_id),
        "retrieval_trace_id": _incident_trace_id(retrieval_trace_id),
        "chat_session_id": chat_session_id,
        "incident_code": code.value,
        "severity": severity,
        "component": component,
        "message": message,
        "diagnostics": _incident_dict(diagnostics),
        "remediation": _incident_dict(remediation),
        "status": "open",
        "fallback_taken": fallback_taken,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "trace_steps": trace_steps if isinstance(trace_steps, list) else [],
    }


def _incident_correlation_id(correlation_id: str | None) -> str:
    return correlation_id or get_correlation_id() or str(uuid.uuid4())


def _incident_trace_id(retrieval_trace_id: str | None) -> str | None:
    return retrieval_trace_id or get_retrieval_trace_id()


def _incident_dict(value: dict[str, Any] | None) -> dict[str, Any]:
    return value if isinstance(value, dict) else {}


def _log_incident_row(row: dict[str, Any]) -> None:
    log_event(
        severity=row["severity"],
        component=row["component"],
        message=row["message"],
        error_code=row["incident_code"],
        incident_id=row["incident_id"],
        fallback_taken=row["fallback_taken"],
    )


def _incident_event_plan(row: dict[str, Any]) -> list[tuple[str, dict[str, Any]]]:
    events: list[tuple[str, dict[str, Any]]] = []
    if row.get("component") == "rag":
        events.append(("RagRequestFailed", row))
    events.extend(
        [
            ("IncidentDetected", row),
            ("IncidentClassified", row),
        ]
    )
    events.extend(_diagnostics_event_plan(row))
    events.extend(_remediation_event_plan(row))
    return events


def _diagnostics_event_plan(row: dict[str, Any]) -> list[tuple[str, dict[str, Any]]]:
    diagnostics = row.get("diagnostics") or {}
    if not diagnostics:
        return []
    return [
        ("DiagnosticsStarted", row),
        ("DiagnosticsCompleted", {**row, "diagnostics": diagnostics}),
    ]


def _remediation_event_plan(row: dict[str, Any]) -> list[tuple[str, dict[str, Any]]]:
    remediation = row.get("remediation") or {}
    if not remediation.get("attempted"):
        return []
    events: list[tuple[str, dict[str, Any]]] = [("RemediationStarted", row)]
    status = remediation.get("status")
    if not status or status == "running":
        return events
    events.append((_remediation_done_event(status), row))
    verification_event = _verification_event(remediation)
    if verification_event:
        events.append((verification_event, row))
    return events


def _remediation_done_event(status: str) -> str:
    if status in {"failed", "error"}:
        return "RemediationFailed"
    return "RemediationSucceeded"


def _verification_event(remediation: dict[str, Any]) -> str | None:
    if remediation.get("verification") is None:
        return None
    if remediation.get("verification", {}).get("ok"):
        return "PostRemediationVerificationPassed"
    return "PostRemediationVerificationFailed"


def _event_payload(event_type: str, row: dict[str, Any]) -> dict[str, Any]:
    code = row["incident_code"]
    diagnostics = row.get("diagnostics") or {}
    remediation = row.get("remediation") or {}
    playbook_id = remediation.get("playbook_id") or _default_playbook(code)
    payload = _base_event_payload(
        event_type,
        row,
        code=code,
        diagnostics=diagnostics,
        remediation=remediation,
        playbook_id=playbook_id,
    )
    _apply_event_payload_details(
        payload,
        event_type,
        row=row,
        diagnostics=diagnostics,
        remediation=remediation,
        code=code,
    )
    return payload


def _base_event_payload(
    event_type: str,
    row: dict[str, Any],
    *,
    code: str,
    diagnostics: dict[str, Any],
    remediation: dict[str, Any],
    playbook_id: str,
) -> dict[str, Any]:
    component = row.get("component") or "rag"
    return {
        "incident_id": row["incident_id"],
        "incident_type": component,
        "incident_class": _incident_class(code),
        "incident_code": code,
        "error_code": code,
        "correlation_id": row.get("correlation_id"),
        "retrieval_trace_id": row.get("retrieval_trace_id"),
        "chat_session_id": row.get("chat_session_id"),
        "source": f"orchestrator.{component}",
        "message": row.get("message") or "",
        "severity": row.get("severity") or "warning",
        "status": _event_status(event_type, row),
        "context": _event_context(row),
        "diagnostics": diagnostics,
        "remediation": remediation,
        "fallback_taken": row.get("fallback_taken"),
        "playbook_id": playbook_id,
    }


def _event_context(row: dict[str, Any]) -> dict[str, Any]:
    return {
        "retrieval_trace_id": row.get("retrieval_trace_id"),
        "chat_session_id": row.get("chat_session_id"),
        "fallback_taken": row.get("fallback_taken"),
        "trace_steps": row.get("trace_steps") or [],
    }


def _apply_event_payload_details(
    payload: dict[str, Any],
    event_type: str,
    *,
    row: dict[str, Any],
    diagnostics: dict[str, Any],
    remediation: dict[str, Any],
    code: str,
) -> None:
    handler = _PAYLOAD_DETAIL_HANDLERS.get(event_type)
    if handler:
        handler(
            payload,
            row=row,
            diagnostics=diagnostics,
            remediation=remediation,
            code=code,
        )
    elif event_type.startswith("PostRemediationVerification"):
        payload["verification"] = remediation.get("verification") or {}


def _payload_rag_request_failed(
    payload: dict[str, Any],
    *,
    row: dict[str, Any],
    diagnostics: dict[str, Any],
    remediation: dict[str, Any],
    code: str,
) -> None:
    payload["query"] = _query_from_trace(row.get("trace_steps") or [])


def _payload_incident_classified(
    payload: dict[str, Any],
    *,
    row: dict[str, Any],
    diagnostics: dict[str, Any],
    remediation: dict[str, Any],
    code: str,
) -> None:
    payload["confidence"] = 0.8


def _payload_diagnostics_started(
    payload: dict[str, Any],
    *,
    row: dict[str, Any],
    diagnostics: dict[str, Any],
    remediation: dict[str, Any],
    code: str,
) -> None:
    payload["checks"] = _check_names(diagnostics)


def _payload_diagnostics_completed(
    payload: dict[str, Any],
    *,
    row: dict[str, Any],
    diagnostics: dict[str, Any],
    remediation: dict[str, Any],
    code: str,
) -> None:
    payload["checks"] = _checks_payload(diagnostics)
    payload["root_cause"] = _root_cause(diagnostics, code)


def _payload_remediation_started(
    payload: dict[str, Any],
    *,
    row: dict[str, Any],
    diagnostics: dict[str, Any],
    remediation: dict[str, Any],
    code: str,
) -> None:
    payload["action"] = remediation.get("action")


def _payload_remediation_result(
    payload: dict[str, Any],
    *,
    row: dict[str, Any],
    diagnostics: dict[str, Any],
    remediation: dict[str, Any],
    code: str,
) -> None:
    payload["result"] = remediation.get("result") or {}
    payload["error"] = remediation.get("error")


_PAYLOAD_DETAIL_HANDLERS = {
    "RagRequestFailed": _payload_rag_request_failed,
    "IncidentClassified": _payload_incident_classified,
    "DiagnosticsStarted": _payload_diagnostics_started,
    "DiagnosticsCompleted": _payload_diagnostics_completed,
    "RemediationStarted": _payload_remediation_started,
    "RemediationSucceeded": _payload_remediation_result,
    "RemediationFailed": _payload_remediation_result,
}


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
        return _checks_list_payload(checks)
    return {}


def _checks_list_payload(checks: list[Any]) -> dict[str, Any]:
    return {
        str(item.get("name", idx)): _check_payload(item)
        for idx, item in enumerate(checks)
        if isinstance(item, dict)
    }


def _check_payload(item: dict[str, Any]) -> dict[str, Any]:
    return {key: value for key, value in item.items() if key != "name"}


def _root_cause(diagnostics: dict[str, Any], code: str) -> str:
    if diagnostics.get("root_cause"):
        return str(diagnostics["root_cause"])
    if diagnostics.get("primary_incident_code"):
        return str(diagnostics["primary_incident_code"])
    if diagnostics.get("status") in {"unhealthy", "degraded"}:
        return code
    return code


def _event_status(event_type: str, row: dict[str, Any]) -> str:
    statuses = {
        "IncidentClassified": "classified",
        "DiagnosticsStarted": "diagnosing",
        "DiagnosticsCompleted": "diagnosed",
        "RemediationStarted": "remediating",
        "RemediationSucceeded": "remediated",
        "RemediationFailed": "remediation_failed",
        "PostRemediationVerificationPassed": "verified",
        "PostRemediationVerificationFailed": "verification_failed",
    }
    if event_type == "IncidentDetected":
        return row.get("status") or "detected"
    return statuses.get(event_type) or row.get("status") or "open"


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
