from __future__ import annotations

import json
from datetime import datetime, timezone
from typing import Any


def format_logs_text(bundle: dict[str, Any]) -> str:
    lines: list[str] = [
        "# Mullm observability export",
        f"generated_at: {bundle.get('generated_at', '')}",
        f"correlation_id: {bundle.get('correlation_id', '')}",
        "",
    ]

    rag = bundle.get("rag_health") or {}
    if rag:
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

    incidents = bundle.get("incidents") or []
    if incidents:
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

    feed = bundle.get("incident_feed") or []
    if feed:
        lines.append("## Incident feed (projector)")
        for row in feed:
            lines.append(
                f"- {row.get('created_at')} {row.get('error_code') or row.get('incident_code')} "
                f"({row.get('status')}) — {row.get('message', '')[:120]}"
            )
        lines.append("")

    snapshots = bundle.get("rag_snapshots") or []
    if snapshots:
        lines.append("## RAG health snapshots")
        for s in snapshots:
            lines.append(f"- {s.get('created_at')} status={s.get('status')}")
        lines.append("")

    session = bundle.get("session") or {}
    if session:
        lines.append("## Workspace session")
        lines.append(f"session_id: {session.get('session_id')}")
        ctx = session.get("context") or {}
        for k in ("ticket_id", "project", "branch", "agent_id"):
            if ctx.get(k):
                lines.append(f"  {k}: {ctx[k]}")
        for ev in session.get("events") or []:
            lines.append(f"  event: {ev.get('type')} — {ev.get('summary', '')[:100]}")
        for msg in session.get("chat_history") or []:
            role = msg.get("role", "?")
            content = (msg.get("content") or "")[:300].replace("\n", " ")
            lines.append(f"  chat[{role}]: {content}")
        lines.append("")

    lines.append("## Raw JSON")
    lines.append(json.dumps(bundle, indent=2, default=str))
    return "\n".join(lines)


async def build_orchestrator_bundle(
    *,
    postgres: Any,
    rag_diagnostics: Any,
    correlation_id: str | None = None,
    limit: int = 30,
) -> dict[str, Any]:
    now = datetime.now(timezone.utc).isoformat()
    bundle: dict[str, Any] = {
        "generated_at": now,
        "correlation_id": correlation_id,
        "service": "orchestrator",
    }

    try:
        bundle["rag_health"] = await rag_diagnostics.run(query=None)
    except Exception as exc:
        bundle["rag_health"] = {"status": "error", "error": str(exc)}

    try:
        if correlation_id:
            rows = await postgres.fetch(
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
        else:
            rows = await postgres.fetch(
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
        bundle["incidents"] = [dict(r) for r in rows]
    except Exception as exc:
        bundle["incidents"] = []
        bundle["incidents_error"] = str(exc)

    try:
        if correlation_id:
            feed_rows = await postgres.fetch(
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
        else:
            feed_rows = await postgres.fetch(
                """
                select incident_id, incident_type, error_code, severity, message,
                       status, correlation_id, created_at, updated_at
                from incident_feed
                order by updated_at desc
                limit $1
                """,
                limit,
            )
        bundle["incident_feed"] = [dict(r) for r in feed_rows]
    except Exception:
        bundle["incident_feed"] = []

    try:
        if correlation_id:
            snap_rows = await postgres.fetch(
                """
                select snapshot_id, retrieval_trace_id, correlation_id, status, checks, created_at
                from rag_health_snapshots
                where correlation_id = $1
                order by created_at desc
                limit $2
                """,
                correlation_id,
                min(limit, 10),
            )
        else:
            snap_rows = await postgres.fetch(
                """
                select snapshot_id, retrieval_trace_id, correlation_id, status, checks, created_at
                from rag_health_snapshots
                order by created_at desc
                limit $1
                """,
                min(limit, 10),
            )
        bundle["rag_snapshots"] = [dict(r) for r in snap_rows]
    except Exception:
        bundle["rag_snapshots"] = []

    bundle["text"] = format_logs_text(bundle)
    return bundle
