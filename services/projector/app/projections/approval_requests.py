from __future__ import annotations

from typing import Any


async def project_approval_requests(db, event: dict[str, Any]) -> None:
    if event["aggregate_type"] != "approval":
        return

    payload = event["payload"]
    event_type = event["event_type"]
    occurred_at = event["occurred_at"]

    if event_type == "ApprovalRequested":
        await db.execute(
            """
            insert into approval_requests (
              approval_id, action_type, target_id, risk_level, requested_by,
              status, updated_at, created_at
            )
            values ($1, $2, $3, $4, $5, $6, $7, $8)
            on conflict (approval_id) do update set
              status = excluded.status,
              updated_at = excluded.updated_at
            """,
            payload["approval_id"],
            payload["action_type"],
            payload["target_id"],
            payload.get("risk_level", "medium"),
            payload["requested_by"],
            payload.get("status", "pending"),
            occurred_at,
            occurred_at,
        )
        return

    if event_type == "ApprovalGranted":
        await db.execute(
            """
            update approval_requests
            set status = 'granted',
                approved_by = $2,
                updated_at = $3
            where approval_id = $1
            """,
            payload["approval_id"],
            payload.get("approved_by"),
            occurred_at,
        )
        return

    if event_type == "ApprovalRejected":
        await db.execute(
            """
            update approval_requests
            set status = 'rejected',
                rejected_by = $2,
                reject_reason = $3,
                updated_at = $4
            where approval_id = $1
            """,
            payload["approval_id"],
            payload.get("rejected_by"),
            payload.get("reason"),
            occurred_at,
        )
        return

    if event_type == "ApprovalExpired":
        await db.execute(
            """
            update approval_requests
            set status = 'expired',
                updated_at = $2
            where approval_id = $1
            """,
            payload["approval_id"],
            occurred_at,
        )
