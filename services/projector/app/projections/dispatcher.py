from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from app.projections.agent_fleet import project_agent_fleet
from app.projections.approval_requests import project_approval_requests
from app.projections.operational_feed import project_operational_feed
from app.projections.plugin_catalog import project_plugin_catalog
from app.projections.task_board import project_task_board
from app.projections.resource_registry import project_resource_registry
from app.projections.workflow_versions import project_workflow_versions


async def project_event(db, event: dict[str, Any]) -> None:
    normalized = _normalize_event(event)
    await project_operational_feed(db, normalized)
    await project_task_board(db, normalized)
    await project_agent_fleet(db, normalized)
    await project_workflow_versions(db, normalized)
    await project_approval_requests(db, normalized)
    await project_plugin_catalog(db, normalized)
    await project_resource_registry(db, normalized)


def _normalize_event(event: dict[str, Any]) -> dict[str, Any]:
    payload = event.get("payload") or event.get("data") or {}
    occurred_at = event.get("occurred_at") or event.get("timestamp")
    if isinstance(occurred_at, str):
        occurred_at = datetime.fromisoformat(occurred_at.replace("Z", "+00:00"))
    elif occurred_at is None:
        occurred_at = datetime.now(timezone.utc)

    return {
        **event,
        "payload": payload,
        "occurred_at": occurred_at,
        "metadata": event.get("metadata") or {},
    }
