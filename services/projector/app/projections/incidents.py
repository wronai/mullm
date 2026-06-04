from __future__ import annotations

from typing import Any
import json


async def project_incidents(db, event: dict[str, Any]) -> None:
    if event["aggregate_type"] != "incident":
        return

    handler = _EVENT_HANDLERS.get(event["event_type"])
    if handler:
        await handler(db, event)


async def _handle_rag_request_failed(db, event: dict[str, Any]) -> None:
    payload = event["payload"]
    occurred_at = event["occurred_at"]
    await _upsert_rag_quality(db, payload, occurred_at)
    await _upsert_service_health(
        db,
        service_id="rag",
        component="retriever",
        status="degraded",
        error_code=_error_code(payload),
        details={
            "query": payload.get("query"),
            "message": payload.get("message"),
            "context": payload.get("context") or {},
        },
        occurred_at=occurred_at,
    )


async def _handle_incident_detected(db, event: dict[str, Any]) -> None:
    payload = event["payload"]
    occurred_at = event["occurred_at"]
    await db.execute(
        """
        insert into incident_feed (
          incident_id, incident_type, severity, source, error_code, message,
          status, correlation_id, context, created_at, updated_at
        )
        values ($1, $2, $3, $4, $5, $6, $7, $8, $9::jsonb, $10, $11)
        on conflict (incident_id) do update set
          severity = excluded.severity,
          source = excluded.source,
          error_code = excluded.error_code,
          message = excluded.message,
          status = excluded.status,
          context = excluded.context,
          updated_at = excluded.updated_at
        """,
        payload["incident_id"],
        payload.get("incident_type") or payload.get("component") or "rag",
        payload.get("severity", "warning"),
        payload.get("source") or "orchestrator.rag",
        _error_code(payload),
        payload.get("message", ""),
        payload.get("status", "detected"),
        event.get("correlation_id") or payload.get("correlation_id"),
        json.dumps(payload.get("context") or {}, default=str),
        occurred_at,
        occurred_at,
    )


async def _handle_incident_classified(db, event: dict[str, Any]) -> None:
    payload = event["payload"]
    await db.execute(
        """
        update incident_feed
        set incident_class = $2,
            error_code = $3,
            playbook_id = $4,
            status = $5,
            updated_at = $6
        where incident_id = $1
        """,
        payload["incident_id"],
        payload.get("incident_class", ""),
        _error_code(payload),
        payload.get("playbook_id"),
        payload.get("status", "classified"),
        event["occurred_at"],
    )


async def _handle_diagnostics_started(db, event: dict[str, Any]) -> None:
    payload = event["payload"]
    await _update_incident_status(
        db,
        payload["incident_id"],
        payload.get("status", "diagnosing"),
        event["occurred_at"],
    )


async def _handle_diagnostics_completed(db, event: dict[str, Any]) -> None:
    payload = event["payload"]
    occurred_at = event["occurred_at"]
    checks = _checks_payload(payload)
    await db.execute(
        """
        update incident_feed
        set status = $2,
            root_cause = $3,
            diagnostics = $4::jsonb,
            updated_at = $5
        where incident_id = $1
        """,
        payload["incident_id"],
        payload.get("status", "diagnosed"),
        payload.get("root_cause") or _root_cause(payload),
        json.dumps(checks, default=str),
        occurred_at,
    )
    ok = _diagnostics_ok(checks)
    await _upsert_service_health(
        db,
        service_id="rag",
        component="retriever",
        status="ok" if ok else "degraded",
        error_code=None if ok else _error_code(payload),
        details=checks,
        occurred_at=occurred_at,
    )


async def _handle_remediation_started(db, event: dict[str, Any]) -> None:
    payload = event["payload"]
    occurred_at = event["occurred_at"]
    await db.execute(
        """
        insert into remediation_history (
          incident_id, playbook_id, action, status, started_at, updated_at
        )
        values ($1, $2, $3, $4, $5, $6)
        """,
        payload["incident_id"],
        payload.get("playbook_id", ""),
        payload.get("action"),
        payload.get("status", "remediating"),
        occurred_at,
        occurred_at,
    )
    await _update_incident_status(
        db,
        payload["incident_id"],
        payload.get("status", "remediating"),
        occurred_at,
    )


async def _handle_remediation_finished(db, event: dict[str, Any]) -> None:
    payload = event["payload"]
    occurred_at = event["occurred_at"]
    status = payload.get("status", "remediated")
    await db.execute(
        """
        insert into remediation_history (
          incident_id, playbook_id, status, result, error, finished_at, updated_at
        )
        values ($1, $2, $3, $4::jsonb, $5, $6, $7)
        """,
        payload["incident_id"],
        payload.get("playbook_id", ""),
        status,
        json.dumps(payload.get("result") or {}, default=str),
        payload.get("error"),
        occurred_at,
        occurred_at,
    )
    await _update_incident_status(db, payload["incident_id"], status, occurred_at)


async def _handle_post_remediation_verification(db, event: dict[str, Any]) -> None:
    payload = event["payload"]
    occurred_at = event["occurred_at"]
    status = payload.get("status", "verified")
    await _update_incident_status(db, payload["incident_id"], status, occurred_at)
    await _upsert_service_health(
        db,
        service_id="rag",
        component="retriever",
        status="ok" if status == "verified" else "degraded",
        error_code=None if status == "verified" else "RAG_VERIFICATION_FAILED",
        details=payload.get("verification") or {},
        occurred_at=occurred_at,
    )


async def _upsert_rag_quality(db, payload: dict[str, Any], occurred_at) -> None:
    await db.execute(
        """
        insert into rag_quality_board (
          error_code, failure_count, last_query, last_message, last_failure_at, updated_at
        )
        values ($1, 1, $2, $3, $4, $5)
        on conflict (error_code) do update set
          failure_count = rag_quality_board.failure_count + 1,
          last_query = excluded.last_query,
          last_message = excluded.last_message,
          last_failure_at = excluded.last_failure_at,
          updated_at = excluded.updated_at
        """,
        _error_code(payload),
        payload.get("query"),
        payload.get("message"),
        occurred_at,
        occurred_at,
    )


async def _upsert_service_health(
    db,
    *,
    service_id: str,
    component: str,
    status: str,
    error_code: str | None,
    details: dict[str, Any],
    occurred_at,
) -> None:
    await db.execute(
        """
        insert into service_health (
          service_id, component, status, error_code, details, last_check_at, updated_at
        )
        values ($1, $2, $3, $4, $5::jsonb, $6, $7)
        on conflict (service_id) do update set
          component = excluded.component,
          status = excluded.status,
          error_code = excluded.error_code,
          details = excluded.details,
          last_check_at = excluded.last_check_at,
          updated_at = excluded.updated_at
        """,
        service_id,
        component,
        status,
        error_code,
        json.dumps(details, default=str),
        occurred_at,
        occurred_at,
    )


async def _update_incident_status(db, incident_id: str, status: str, occurred_at) -> None:
    await db.execute(
        """
        update incident_feed
        set status = $2, updated_at = $3
        where incident_id = $1
        """,
        incident_id,
        status,
        occurred_at,
    )


def _error_code(payload: dict[str, Any]) -> str:
    return (
        payload.get("error_code")
        or payload.get("incident_code")
        or payload.get("primary_incident_code")
        or "RAG_BACKEND_UNAVAILABLE"
    )


def _checks_payload(payload: dict[str, Any]) -> dict[str, Any]:
    checks = _raw_checks(payload)
    if isinstance(checks, dict):
        return checks
    if isinstance(checks, list):
        return _checks_list_payload(checks)
    return {}


def _raw_checks(payload: dict[str, Any]) -> Any:
    checks = payload.get("checks")
    if checks is not None:
        return checks
    diagnostics = payload.get("diagnostics") or {}
    return diagnostics.get("checks") if isinstance(diagnostics, dict) else None


def _checks_list_payload(checks: list[Any]) -> dict[str, Any]:
    return {
        str(item.get("name", idx)): _check_payload(item)
        for idx, item in enumerate(checks)
        if isinstance(item, dict)
    }


def _check_payload(item: dict[str, Any]) -> dict[str, Any]:
    return {key: value for key, value in item.items() if key != "name"}


def _root_cause(payload: dict[str, Any]) -> str:
    diagnostics = payload.get("diagnostics") or {}
    if isinstance(diagnostics, dict) and diagnostics.get("primary_incident_code"):
        return str(diagnostics["primary_incident_code"])
    return _error_code(payload)


def _diagnostics_ok(checks: dict[str, Any]) -> bool:
    if not checks:
        return False
    for value in checks.values():
        if not isinstance(value, dict):
            continue
        if value.get("ok") is False:
            return False
        if value.get("status") in {"fail", "error"}:
            return False
    return True


_EVENT_HANDLERS = {
    "RagRequestFailed": _handle_rag_request_failed,
    "IncidentDetected": _handle_incident_detected,
    "IncidentClassified": _handle_incident_classified,
    "DiagnosticsStarted": _handle_diagnostics_started,
    "DiagnosticsCompleted": _handle_diagnostics_completed,
    "RemediationStarted": _handle_remediation_started,
    "RemediationSucceeded": _handle_remediation_finished,
    "RemediationFailed": _handle_remediation_finished,
    "PostRemediationVerificationPassed": _handle_post_remediation_verification,
    "PostRemediationVerificationFailed": _handle_post_remediation_verification,
}
