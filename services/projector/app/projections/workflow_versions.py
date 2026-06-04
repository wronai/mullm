from __future__ import annotations

from typing import Any
import json


async def project_workflow_versions(db, event: dict[str, Any]) -> None:
    if event["aggregate_type"] != "workflow":
        return

    payload = event["payload"]
    event_type = event["event_type"]
    if event_type not in {
        "WorkflowStarted",
        "WorkflowVersionProposed",
        "WorkflowVersionValidated",
        "WorkflowVersionApproved",
        "WorkflowVersionShadowed",
        "WorkflowVersionActivated",
        "WorkflowVersionRolledBack",
    }:
        return

    activated_at = event["occurred_at"] if event_type in {
        "WorkflowStarted",
        "WorkflowVersionActivated",
    } else None
    status = payload.get("status", "active")

    await db.execute(
        """
        insert into workflow_versions (
          workflow_id, version, status, definition, proposed_at, activated_at
        )
        values ($1, $2, $3, $4::jsonb, $5, $6)
        on conflict (workflow_id, version) do update set
          status = excluded.status,
          definition = excluded.definition,
          activated_at = coalesce(excluded.activated_at, workflow_versions.activated_at)
        """,
        payload["workflow_id"],
        int(payload.get("version", 1)),
        status,
        json.dumps(payload.get("definition") or {}),
        event["occurred_at"],
        activated_at,
    )
