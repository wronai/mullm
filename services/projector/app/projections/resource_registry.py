from __future__ import annotations

from typing import Any
import json


async def project_resource_registry(db, event: dict[str, Any]) -> None:
    if event["aggregate_type"] != "resource":
        return

    payload = event["payload"]
    event_type = event["event_type"]
    occurred_at = event["occurred_at"]

    if event_type == "ResourceRegistered":
        await db.execute(
            """
            insert into resource_registry (
              resource_id, uri, name, adapter, classification, status,
              metadata, updated_at, created_at
            )
            values ($1, $2, $3, $4, $5, $6, $7::jsonb, $8, $9)
            on conflict (resource_id) do update set
              uri = excluded.uri,
              name = excluded.name,
              status = excluded.status,
              metadata = excluded.metadata,
              updated_at = excluded.updated_at
            """,
            payload["resource_id"],
            payload["uri"],
            payload["name"],
            payload["adapter"],
            payload.get("classification", "document"),
            payload.get("status", "registered"),
            json.dumps(payload.get("metadata") or {}, default=str),
            occurred_at,
            occurred_at,
        )
        return

    if event_type == "TransferRequested":
        await db.execute(
            """
            update resource_registry
            set status = 'transferring',
                last_transfer_id = $2,
                updated_at = $3
            where resource_id = $1
            """,
            payload["resource_id"],
            payload["transfer_id"],
            occurred_at,
        )
        await db.execute(
            """
            insert into transfer_log (
              transfer_id, resource_id, source_uri, destination_uri,
              status, requested_by, started_at
            )
            values ($1, $2, $3, $4, 'running', $5, $6)
            on conflict (transfer_id) do nothing
            """,
            payload["transfer_id"],
            payload["resource_id"],
            payload["source_uri"],
            payload["destination_uri"],
            payload.get("requested_by"),
            occurred_at,
        )
        return

    if event_type == "TransferCompleted":
        await db.execute(
            """
            update resource_registry
            set status = 'available', updated_at = $2
            where resource_id = $1
            """,
            payload["resource_id"],
            occurred_at,
        )
        await db.execute(
            """
            update transfer_log
            set status = 'completed',
                outcome = $2::jsonb,
                completed_at = $3
            where transfer_id = $1
            """,
            payload["transfer_id"],
            json.dumps(payload.get("outcome") or {}, default=str),
            occurred_at,
        )
        return

    if event_type == "TransferFailed":
        await db.execute(
            """
            update resource_registry
            set status = 'error', updated_at = $2
            where resource_id = $1
            """,
            payload["resource_id"],
            occurred_at,
        )
        await db.execute(
            """
            update transfer_log
            set status = 'failed',
                error = $2,
                completed_at = $3
            where transfer_id = $1
            """,
            payload["transfer_id"],
            payload.get("error"),
            occurred_at,
        )
