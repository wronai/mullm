from __future__ import annotations

import json
from datetime import datetime, timezone
from typing import Any

from app.observability.logging import log_event

DEFAULT_LOG_EXPORT_LIMIT = 100
MAX_LOG_EXPORT_LIMIT = 500
NFO_EXPORT_SCHEMA = "mullm.logs.nfo.v1"

try:  # Optional in local tests; pinned in service requirements for Docker.
    import nfo as _nfo
except Exception:  # pragma: no cover - depends on runtime image extras.
    _nfo = None


def format_logs_text(bundle: dict[str, Any]) -> str:
    lines: list[str] = [
        "# Mullm observability export",
        f"generated_at: {bundle.get('generated_at', '')}",
        f"correlation_id: {bundle.get('correlation_id', '')}",
        "",
    ]
    _append_nfo(lines, bundle.get("nfo") or _build_nfo_package(bundle))
    _append_rag_health(lines, bundle.get("rag_health") or {})
    _append_incidents(lines, bundle.get("incidents") or [])
    _append_incident_feed(lines, bundle.get("incident_feed") or [])
    _append_rag_snapshots(lines, bundle.get("rag_snapshots") or [])
    _append_workspace_session(lines, bundle.get("session") or {})
    lines.append("## Raw JSON")
    lines.append(json.dumps(bundle, indent=2, default=str))
    return "\n".join(lines)


def clamp_log_export_limit(limit: int | str | None) -> int:
    try:
        value = int(limit) if limit is not None else DEFAULT_LOG_EXPORT_LIMIT
    except (TypeError, ValueError):
        value = DEFAULT_LOG_EXPORT_LIMIT
    return min(max(value, 1), MAX_LOG_EXPORT_LIMIT)


def _nfo_package_version() -> str:
    return str(getattr(_nfo, "__version__", "unavailable"))


def _build_nfo_package(bundle: dict[str, Any]) -> dict[str, Any]:
    return {
        "schema": NFO_EXPORT_SCHEMA,
        "package": "nfo",
        "package_version": _nfo_package_version(),
        "service": bundle.get("service") or "orchestrator",
        "generated_at": bundle.get("generated_at"),
        "correlation_id": bundle.get("correlation_id"),
        "limit": clamp_log_export_limit(bundle.get("log_limit")),
        "counts": _nfo_counts(bundle),
        "errors": _nfo_errors(bundle),
    }


def _nfo_counts(bundle: dict[str, Any]) -> dict[str, int]:
    rag_payload = bundle.get("rag_health")
    rag_health = rag_payload if isinstance(rag_payload, dict) else {}
    session = bundle.get("session") if isinstance(bundle.get("session"), dict) else {}
    return {
        "rag_checks": len(rag_health.get("checks") or []),
        "incidents": len(bundle.get("incidents") or []),
        "incident_feed": len(bundle.get("incident_feed") or []),
        "rag_snapshots": len(bundle.get("rag_snapshots") or []),
        "session_events": len(session.get("events") or []),
        "chat_messages": len(session.get("chat_history") or []),
    }


def _nfo_errors(bundle: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    for key in ("incidents_error", "incident_feed_error", "rag_snapshots_error"):
        if bundle.get(key):
            errors.append(f"{key}: {bundle[key]}")
    rag_health = bundle.get("rag_health")
    if isinstance(rag_health, dict) and rag_health.get("error"):
        errors.append(f"rag_health: {rag_health['error']}")
    return errors


def _append_nfo(lines: list[str], package: dict[str, Any]) -> None:
    if not package:
        return
    lines.append("## NFO")
    lines.append(f"package: {package.get('package')} {package.get('package_version')}")
    lines.append(f"schema: {package.get('schema')}")
    lines.append(f"service: {package.get('service')}")
    lines.append(f"limit: {package.get('limit')}")
    counts = package.get("counts") or {}
    if counts:
        lines.append(
            "counts: "
            + ", ".join(f"{key}={value}" for key, value in counts.items())
        )
    for err in package.get("errors") or []:
        lines.append(f"error: {err}")
    lines.append("")


def _append_rag_health(lines: list[str], rag: dict[str, Any]) -> None:
    if not rag:
        return
    lines.append("## RAG health")
    lines.append(f"status: {rag.get('status')}")
    lines.append(f"primary_incident_code: {rag.get('primary_incident_code')}")
    for check in rag.get("checks") or []:
        lines.append(
            f"  - {check.get('name')}: {check.get('status')} "
            f"{check.get('detail', '')}"
        )
    for rec in rag.get("recommendations") or []:
        lines.append(f"  recommendation: {rec}")
    lines.append("")


def _append_incidents(lines: list[str], incidents: list[dict[str, Any]]) -> None:
    if not incidents:
        return
    lines.append("## Incidents")
    for inc in incidents:
        lines.append(
            f"- [{inc.get('created_at')}] {inc.get('incident_code')} "
            f"({inc.get('severity')}) {inc.get('message')}"
        )
        if inc.get("retrieval_trace_id"):
            lines.append(f"    trace={inc.get('retrieval_trace_id')}")
        if inc.get("fallback_taken"):
            lines.append(f"    fallback={inc.get('fallback_taken')}")
    lines.append("")


def _append_incident_feed(lines: list[str], feed: list[dict[str, Any]]) -> None:
    if not feed:
        return
    lines.append("## Incident feed (projector)")
    for row in feed:
        lines.append(
            f"- {row.get('created_at')} {row.get('error_code') or row.get('incident_code')} "
            f"({row.get('status')}) — {row.get('message', '')[:120]}"
        )
    lines.append("")


def _append_rag_snapshots(lines: list[str], snapshots: list[dict[str, Any]]) -> None:
    if not snapshots:
        return
    lines.append("## RAG health snapshots")
    for snapshot in snapshots:
        lines.append(f"- {snapshot.get('created_at')} status={snapshot.get('status')}")
    lines.append("")


def _append_workspace_session(lines: list[str], session: dict[str, Any]) -> None:
    if not session:
        return
    lines.append("## Workspace session")
    lines.append(f"session_id: {session.get('session_id')}")
    _append_workspace_context(lines, session.get("context") or {})
    _append_workspace_events(lines, session.get("events") or [])
    _append_workspace_chat(lines, session.get("chat_history") or [])
    lines.append("")


def _append_workspace_context(lines: list[str], ctx: dict[str, Any]) -> None:
    for key in ("ticket_id", "project", "branch", "agent_id"):
        if ctx.get(key):
            lines.append(f"  {key}: {ctx[key]}")


def _append_workspace_events(lines: list[str], events: list[dict[str, Any]]) -> None:
    for event in events:
        lines.append(f"  event: {event.get('type')} — {event.get('summary', '')[:100]}")


def _append_workspace_chat(lines: list[str], history: list[dict[str, Any]]) -> None:
    for msg in history:
        role = msg.get("role", "?")
        content = (msg.get("content") or "")[:300].replace("\n", " ")
        lines.append(f"  chat[{role}]: {content}")


async def build_orchestrator_bundle(
    *,
    postgres: Any,
    rag_diagnostics: Any,
    correlation_id: str | None = None,
    limit: int = DEFAULT_LOG_EXPORT_LIMIT,
) -> dict[str, Any]:
    limit = clamp_log_export_limit(limit)
    now = datetime.now(timezone.utc).isoformat()
    bundle: dict[str, Any] = {
        "generated_at": now,
        "correlation_id": correlation_id,
        "service": "orchestrator",
        "log_limit": limit,
    }
    log_event(
        severity="info",
        component="observability_export",
        message="Observability export started",
        correlation_id=correlation_id,
        limit=limit,
    )
    bundle["rag_health"] = await _safe_rag_health(rag_diagnostics)
    bundle["incidents"] = await _safe_fetch_incidents(
        postgres,
        correlation_id=correlation_id,
        limit=limit,
        bundle=bundle,
    )
    bundle["incident_feed"] = await _safe_fetch_incident_feed(
        postgres,
        correlation_id=correlation_id,
        limit=limit,
        bundle=bundle,
    )
    bundle["rag_snapshots"] = await _safe_fetch_rag_snapshots(
        postgres,
        correlation_id=correlation_id,
        limit=limit,
        bundle=bundle,
    )
    bundle["nfo"] = _build_nfo_package(bundle)
    bundle["text"] = format_logs_text(bundle)
    log_event(
        severity="info",
        component="observability_export",
        message="Observability export finished",
        correlation_id=correlation_id,
        limit=limit,
        **_nfo_counts(bundle),
    )
    return bundle


async def _safe_rag_health(rag_diagnostics: Any) -> dict[str, Any]:
    try:
        return await rag_diagnostics.run(query=None)
    except Exception as exc:
        return {"status": "error", "error": str(exc)}


async def _safe_fetch_incidents(
    postgres: Any,
    *,
    correlation_id: str | None,
    limit: int,
    bundle: dict[str, Any],
) -> list[dict[str, Any]]:
    try:
        rows = await _fetch_incidents(
            postgres,
            correlation_id=correlation_id,
            limit=limit,
        )
        return [dict(row) for row in rows]
    except Exception as exc:
        bundle["incidents_error"] = str(exc)
        return []


async def _fetch_incidents(
    postgres: Any,
    *,
    correlation_id: str | None,
    limit: int,
) -> list[Any]:
    if correlation_id:
        return await postgres.fetch(
            """
            select incident_id, correlation_id, retrieval_trace_id, chat_session_id,
                   incident_code, severity, message, status, fallback_taken,
                   diagnostics, remediation, created_at
            from incidents
            where correlation_id = $1 or chat_session_id = $1
            order by created_at desc
            limit $2
            """,
            correlation_id,
            limit,
        )
    return await postgres.fetch(
        """
        select incident_id, correlation_id, retrieval_trace_id, chat_session_id,
               incident_code, severity, message, status, fallback_taken,
               diagnostics, remediation, created_at
        from incidents
        order by created_at desc
        limit $1
        """,
        limit,
    )


async def _safe_fetch_incident_feed(
    postgres: Any,
    *,
    correlation_id: str | None,
    limit: int,
    bundle: dict[str, Any],
) -> list[dict[str, Any]]:
    try:
        rows = await _fetch_incident_feed(
            postgres,
            correlation_id=correlation_id,
            limit=limit,
        )
        return [dict(row) for row in rows]
    except Exception as exc:
        bundle["incident_feed_error"] = str(exc)
        return []


async def _fetch_incident_feed(
    postgres: Any,
    *,
    correlation_id: str | None,
    limit: int,
) -> list[Any]:
    if correlation_id:
        return await postgres.fetch(
            """
            select incident_id, incident_type, error_code, severity, message,
                   status, correlation_id, created_at, updated_at
            from incident_feed
            where correlation_id = $1
            order by updated_at desc
            limit $2
            """,
            correlation_id,
            limit,
        )
    return await postgres.fetch(
        """
        select incident_id, incident_type, error_code, severity, message,
               status, correlation_id, created_at, updated_at
        from incident_feed
        order by updated_at desc
        limit $1
        """,
        limit,
    )


async def _safe_fetch_rag_snapshots(
    postgres: Any,
    *,
    correlation_id: str | None,
    limit: int,
    bundle: dict[str, Any],
) -> list[dict[str, Any]]:
    try:
        rows = await _fetch_rag_snapshots(
            postgres,
            correlation_id=correlation_id,
            limit=limit,
        )
        return [dict(row) for row in rows]
    except Exception as exc:
        bundle["rag_snapshots_error"] = str(exc)
        return []


async def _fetch_rag_snapshots(
    postgres: Any,
    *,
    correlation_id: str | None,
    limit: int,
) -> list[Any]:
    if correlation_id:
        return await postgres.fetch(
            """
            select snapshot_id, retrieval_trace_id, correlation_id, status, checks, created_at
            from rag_health_snapshots
            where correlation_id = $1
            order by created_at desc
            limit $2
            """,
            correlation_id,
            limit,
        )
    return await postgres.fetch(
        """
        select snapshot_id, retrieval_trace_id, correlation_id, status, checks, created_at
        from rag_health_snapshots
        order by created_at desc
        limit $1
        """,
        limit,
    )
