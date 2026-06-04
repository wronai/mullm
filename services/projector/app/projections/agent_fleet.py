from __future__ import annotations

from typing import Any
import json


async def project_agent_fleet(db, event: dict[str, Any]) -> None:
    if event["aggregate_type"] != "agent":
        return

    payload = event["payload"]
    event_type = event["event_type"]
    occurred_at = event["occurred_at"]

    if event_type == "AgentRegistered":
        await db.execute(
            """
            insert into agent_fleet (
              agent_id, agent_type, status, capabilities, load_score, updated_at
            )
            values ($1, $2, $3, $4::jsonb, 0, $5)
            on conflict (agent_id) do update set
              agent_type = excluded.agent_type,
              status = excluded.status,
              capabilities = excluded.capabilities,
              updated_at = excluded.updated_at
            """,
            payload["agent_id"],
            payload.get("agent_type", "shell"),
            payload.get("status", "idle"),
            json.dumps(payload.get("capabilities") or []),
            occurred_at,
        )
        return

    if event_type == "AgentHeartbeatReceived":
        await db.execute(
            """
            insert into agent_fleet (
              agent_id, agent_type, status, capabilities, heartbeat_at, load_score, updated_at
            )
            values ($1, 'unknown', 'idle', '[]'::jsonb, $2, $3, $4)
            on conflict (agent_id) do update set
              heartbeat_at = excluded.heartbeat_at,
              load_score = excluded.load_score,
              updated_at = excluded.updated_at
            """,
            payload["agent_id"],
            payload.get("heartbeat_at") or occurred_at,
            int(payload.get("load_score", 0)),
            occurred_at,
        )
        return

    if event_type == "TaskAssignedToAgent":
        await db.execute(
            """
            update agent_fleet
            set status = 'busy',
                current_task_id = $2,
                updated_at = $3
            where agent_id = $1
            """,
            payload["agent_id"],
            payload["task_id"],
            occurred_at,
        )
        return

    if event_type == "AgentMarkedIdle":
        await db.execute(
            """
            update agent_fleet
            set status = 'idle',
                current_task_id = null,
                updated_at = $2
            where agent_id = $1
            """,
            payload["agent_id"],
            occurred_at,
        )
