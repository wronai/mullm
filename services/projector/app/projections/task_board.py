from __future__ import annotations

from typing import Any
import json


async def project_task_board(db, event: dict[str, Any]) -> None:
    if event["aggregate_type"] != "task":
        return

    payload = event["payload"]
    event_type = event["event_type"]
    occurred_at = event["occurred_at"]

    if event_type == "TaskCreated":
        await db.execute(
            """
            insert into task_board (
              task_id, title, status, priority, execution_mode, assigned_agent_id,
              required_capabilities, last_event_type, updated_at, created_at
            )
            values ($1, $2, $3, $4, $5, $6, $7::jsonb, $8, $9, $10)
            on conflict (task_id) do update set
              title = excluded.title,
              status = excluded.status,
              priority = excluded.priority,
              execution_mode = excluded.execution_mode,
              assigned_agent_id = excluded.assigned_agent_id,
              required_capabilities = excluded.required_capabilities,
              last_event_type = excluded.last_event_type,
              updated_at = excluded.updated_at
            """,
            payload["task_id"],
            payload["title"],
            payload.get("status", "pending"),
            payload.get("priority", "medium"),
            payload.get("execution_mode", "semi_auto"),
            payload.get("agent_id"),
            json.dumps(payload.get("required_capabilities") or []),
            event_type,
            occurred_at,
            occurred_at,
        )
        return

    if event_type == "TaskAssigned":
        await db.execute(
            """
            update task_board
            set status = $2,
                assigned_agent_id = $3,
                last_event_type = $4,
                updated_at = $5
            where task_id = $1
            """,
            payload["task_id"],
            payload.get("status", "assigned"),
            payload["agent_id"],
            event_type,
            occurred_at,
        )
        return

    if event_type == "TaskStarted":
        await _update_status(db, payload["task_id"], "running", event_type, occurred_at)
        return

    if event_type == "TaskCompleted":
        await db.execute(
            """
            update task_board
            set status = 'completed',
                result = $2::jsonb,
                last_event_type = $3,
                updated_at = $4
            where task_id = $1
            """,
            payload["task_id"],
            json.dumps(payload.get("result") or {}),
            event_type,
            occurred_at,
        )
        return

    if event_type == "TaskFailed":
        await db.execute(
            """
            update task_board
            set status = 'failed',
                error = $2,
                last_event_type = $3,
                updated_at = $4
            where task_id = $1
            """,
            payload["task_id"],
            payload.get("error"),
            event_type,
            occurred_at,
        )


async def _update_status(db, task_id: str, status: str, event_type: str, occurred_at) -> None:
    await db.execute(
        """
        update task_board
        set status = $2,
            last_event_type = $3,
            updated_at = $4
        where task_id = $1
        """,
        task_id,
        status,
        event_type,
        occurred_at,
    )
