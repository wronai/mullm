from __future__ import annotations

from typing import Any
import json


_TITLE_FORMATTERS = {
    "TaskCreated": lambda payload: payload.get("title") or "Task created",
    "AgentRegistered": lambda payload: f"Agent {payload.get('agent_id')} registered",
    "WorkflowStarted": lambda payload: f"Workflow {payload.get('workflow_id')} started",
    "ResourceRegistered": lambda payload: payload.get("name") or payload.get("uri"),
    "TransferCompleted": lambda payload: f"Transfer {payload.get('transfer_id')} completed",
    "IncidentDetected": lambda payload: f"Incident {payload.get('incident_code')}",
    "DiagnosticsCompleted": lambda payload: "RAG diagnostics completed",
    "RemediationSucceeded": lambda payload: (
        f"Remediation OK ({payload.get('incident_code')})"
    ),
}


async def project_operational_feed(db, event: dict[str, Any]) -> None:
    payload = event["payload"]
    metadata = event.get("metadata") or {}
    actor = metadata.get("actor") or {}
    title = _title_for(event["event_type"], payload)
    summary = _summary_for(event["event_type"], payload)

    await db.execute(
        """
        insert into operational_feed (
          event_id, stream_id, aggregate_type, aggregate_id, event_type,
          occurred_at, correlation_id, causation_id, actor_type, actor_id,
          title, summary, payload
        )
        values ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13::jsonb)
        on conflict (event_id) do nothing
        """,
        event["event_id"],
        event["stream_id"],
        event["aggregate_type"],
        event["aggregate_id"],
        event["event_type"],
        event["occurred_at"],
        event.get("correlation_id"),
        event.get("causation_id"),
        actor.get("type"),
        actor.get("id"),
        title,
        summary,
        json.dumps(payload, default=str),
    )


def _title_for(event_type: str, payload: dict[str, Any]) -> str:
    formatter = _TITLE_FORMATTERS.get(event_type)
    if formatter is None:
        return event_type
    return formatter(payload)


def _summary_for(event_type: str, payload: dict[str, Any]) -> str:
    if event_type in {"TaskAssigned", "TaskAssignedToAgent"}:
        return f"Task {payload.get('task_id')} assigned to {payload.get('agent_id')}"
    if event_type == "TaskCompleted":
        return f"Task {payload.get('task_id')} completed"
    if event_type == "TaskFailed":
        return f"Task {payload.get('task_id')} failed"
    if event_type == "IncidentDetected":
        return payload.get("message") or payload.get("incident_code", "")
    return ""
