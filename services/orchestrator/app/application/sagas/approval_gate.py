from __future__ import annotations

from typing import Any, Callable


class ApprovalRequired(Exception):
    """Komenda wymaga wcześniejszego ApprovalGranted."""

    def __init__(
        self,
        *,
        action_type: str,
        target_id: str,
        message: str,
    ) -> None:
        self.action_type = action_type
        self.target_id = target_id
        super().__init__(message)


RISKY_COMMANDS: dict[str, tuple[str, Callable[[dict[str, Any]], str]]] = {
    "ActivatePlugin": ("ActivatePlugin", lambda d: d["plugin_id"]),
    "RollbackPlugin": ("RollbackPlugin", lambda d: d["plugin_id"]),
    "ActivateWorkflowVersion": (
        "ActivateWorkflowVersion",
        lambda d: d["workflow_id"],
    ),
    "RollbackWorkflowVersion": (
        "RollbackWorkflowVersion",
        lambda d: d["workflow_id"],
    ),
}

AUTO_EXECUTE_ON_GRANT = {
    "ActivatePlugin": "ActivatePlugin",
    "RollbackPlugin": "RollbackPlugin",
    "ActivateWorkflowVersion": "ActivateWorkflowVersion",
    "RollbackWorkflowVersion": "RollbackWorkflowVersion",
}


def _is_skipped(data: dict[str, Any], metadata: dict[str, Any] | None) -> bool:
    if data.get("skip_approval"):
        return True
    meta = metadata or {}
    return bool(meta.get("skip_approval"))


async def ensure_approval(
    event_store: Any,
    command_type: str,
    data: dict[str, Any],
    *,
    metadata: dict[str, Any] | None = None,
) -> None:
    """Weryfikuje, że ryzykowna komenda ma przyznaną zgodę."""
    if _is_skipped(data, metadata):
        return
    spec = RISKY_COMMANDS.get(command_type)
    if not spec:
        return

    action_type, target_fn = spec
    target_id = target_fn(data)
    approval_id = data.get("approval_id")
    if not approval_id:
        raise ApprovalRequired(
            action_type=action_type,
            target_id=target_id,
            message=(
                f"{command_type} requires approval_id. "
                f"Create approval via CreateApprovalRequest "
                f"(action_type={action_type}, target_id={target_id}) then ApproveRequest."
            ),
        )

    events = await event_store.get_events_for_aggregate("approval", approval_id)
    if not events:
        raise ValueError(f"Approval not found: {approval_id}")

    first = events[0].data
    last = events[-1].data
    if first.get("action_type") != action_type or first.get("target_id") != target_id:
        raise ValueError(
            f"Approval {approval_id} does not match {action_type} on {target_id}"
        )
    if last.get("status") != "granted":
        raise ValueError(
            f"Approval {approval_id} is not granted (status={last.get('status')})"
        )


async def follow_up_after_grant(
    command_bus: Any,
    *,
    action_type: str,
    target_id: str,
    approval_id: str,
    approved_by: str,
    correlation_id: str | None,
    metadata: dict[str, Any] | None,
) -> dict[str, Any] | None:
    """Po ApprovalGranted wykonuje powiązaną komendę (saga kontynuacji)."""
    command_type = AUTO_EXECUTE_ON_GRANT.get(action_type)
    if not command_type:
        return None

    payload: dict[str, Any] = {
        "approval_id": approval_id,
        "skip_approval": True,
    }
    if command_type in {"ActivatePlugin", "RollbackPlugin"}:
        payload["plugin_id"] = target_id
    else:
        payload["workflow_id"] = target_id
    if command_type.startswith("Rollback"):
        payload["reason"] = f"approved rollback by {approved_by}"

    return await command_bus.handle(
        command_type=command_type,
        command_id=f"approval-followup-{approval_id}",
        data=payload,
        correlation_id=correlation_id,
        metadata={
            **(metadata or {}),
            "actor": {"type": "system", "id": "approval-gate"},
            "triggered_by_approval": approval_id,
        },
    )
