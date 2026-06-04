from __future__ import annotations

from typing import Any
import json


async def project_plugin_catalog(db, event: dict[str, Any]) -> None:
    if event["aggregate_type"] != "plugin":
        return

    payload = event["payload"]
    event_type = event["event_type"]
    occurred_at = event["occurred_at"]

    if event_type not in {
        "PluginProposed",
        "PluginValidated",
        "PluginInstalled",
        "PluginActivated",
        "PluginRolledBack",
    }:
        return

    await db.execute(
        """
        insert into plugin_catalog (
          plugin_id, version, status, capabilities, manifest, updated_at
        )
        values ($1, $2, $3, $4::jsonb, $5::jsonb, $6)
        on conflict (plugin_id, version) do update set
          status = excluded.status,
          capabilities = excluded.capabilities,
          manifest = excluded.manifest,
          updated_at = excluded.updated_at
        """,
        payload["plugin_id"],
        payload["version"],
        payload.get("status", "proposed"),
        json.dumps(payload.get("capabilities") or []),
        json.dumps(payload.get("manifest") or {}),
        occurred_at,
    )
