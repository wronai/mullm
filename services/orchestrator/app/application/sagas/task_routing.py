from __future__ import annotations

from typing import Any


async def pick_idle_agent(event_store, required_capabilities: list[str] | None = None) -> str | None:
    """Wybiera pierwszego idle agenta spełniającego wymagane capability."""
    required = required_capabilities or ["shell"]
    agent_ids = await event_store.get_aggregate_ids("agent")
    for agent_id in agent_ids:
        events = await event_store.get_events_for_aggregate("agent", agent_id)
        state = _agent_route_state(events)
        if _agent_matches(state, required):
            return agent_id
    return None


def _agent_route_state(events: list[Any]) -> dict[str, Any]:
    state: dict[str, Any] = {"capabilities": [], "status": "idle"}
    for record in events:
        if record.event_type == "AgentRegistered":
            state["capabilities"] = record.data.get("capabilities") or []
        state["status"] = record.data.get("status", state["status"])
    return state


def _agent_matches(state: dict[str, Any], required: list[str]) -> bool:
    capabilities = state.get("capabilities") or []
    return state.get("status") == "idle" and all(
        capability in capabilities for capability in required
    )


async def maybe_auto_assign(
    command_bus: Any,
    *,
    task_id: str,
    data: dict[str, Any],
    command_id: str,
    correlation_id: str | None,
    metadata: dict[str, Any] | None,
) -> dict[str, Any] | None:
    """Po CreateTask opcjonalnie przypisuje zadanie do wolnego agenta (saga MVP)."""
    if not data.get("auto_assign"):
        return None
    if data.get("agent_id"):
        return None

    agent_id = await pick_idle_agent(
        command_bus.event_store,
        data.get("required_capabilities") or ["shell"],
    )
    if not agent_id:
        return None

    return await command_bus.handle(
        command_type="AssignTask",
        command_id=f"{command_id}-auto-assign",
        data={
            "task_id": task_id,
            "agent_id": agent_id,
            "command": data.get("shell_command"),
        },
        correlation_id=correlation_id,
        metadata=metadata,
    )
