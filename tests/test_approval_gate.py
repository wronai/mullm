import pytest

from app.application.sagas.approval_gate import ApprovalRequired, ensure_approval

PLUGIN_MANIFEST = {
    "risk_level": "medium",
    "inputs": {},
    "outputs": {},
    "health_check": "/health",
    "rollback_strategy": "disable",
}


@pytest.mark.asyncio
async def test_activate_plugin_requires_approval(command_bus):
    await command_bus.handle(
        command_type="ProposePlugin",
        data={
            "plugin_id": "risky-plugin",
            "version": "1.0.0",
            "capabilities": ["shell"],
            "manifest": PLUGIN_MANIFEST,
        },
    )
    await command_bus.handle(
        command_type="ValidatePlugin",
        data={"plugin_id": "risky-plugin"},
    )
    await command_bus.handle(
        command_type="InstallPlugin",
        data={"plugin_id": "risky-plugin"},
    )

    with pytest.raises(ApprovalRequired):
        await command_bus.handle(
            command_type="ActivatePlugin",
            data={"plugin_id": "risky-plugin"},
        )


@pytest.mark.asyncio
async def test_activate_plugin_with_granted_approval(command_bus):
    await command_bus.handle(
        command_type="ProposePlugin",
        data={"plugin_id": "p1", "version": "1.0.0", "capabilities": [], "manifest": PLUGIN_MANIFEST},
    )
    await command_bus.handle(
        command_type="ValidatePlugin",
        data={"plugin_id": "p1"},
    )
    await command_bus.handle(
        command_type="InstallPlugin",
        data={"plugin_id": "p1"},
    )

    approval = await command_bus.handle(
        command_type="CreateApprovalRequest",
        data={
            "action_type": "ActivatePlugin",
            "target_id": "p1",
            "requested_by": "user-1",
        },
    )
    approval_id = approval["aggregate_id"]

    result = await command_bus.handle(
        command_type="ApproveRequest",
        data={"approval_id": approval_id, "approved_by": "ops"},
    )
    assert "follow_up" in result
    assert result["follow_up"]["events"][-1]["event_type"] == "PluginActivated"


@pytest.mark.asyncio
async def test_skip_approval_for_dev(command_bus):
    await command_bus.handle(
        command_type="ProposePlugin",
        data={
            "plugin_id": "p2",
            "version": "1.0.0",
            "capabilities": [],
            "manifest": PLUGIN_MANIFEST,
        },
    )
    await command_bus.handle(
        command_type="ValidatePlugin",
        data={"plugin_id": "p2"},
    )
    await command_bus.handle(
        command_type="InstallPlugin",
        data={"plugin_id": "p2"},
    )
    await command_bus.handle(
        command_type="ActivatePlugin",
        data={"plugin_id": "p2", "skip_approval": True},
    )
    events = await command_bus.event_store.get_events_for_aggregate("plugin", "p2")
    assert events[-1].event_type == "PluginActivated"


@pytest.mark.asyncio
async def test_ensure_approval_rejects_wrong_target(command_bus):
    created = await command_bus.handle(
        command_type="CreateApprovalRequest",
        data={
            "action_type": "ActivatePlugin",
            "target_id": "plugin-a",
            "requested_by": "u1",
        },
    )
    await command_bus.handle(
        command_type="ApproveRequest",
        data={"approval_id": created["aggregate_id"], "approved_by": "ops", "auto_execute": False},
    )
    with pytest.raises(ValueError, match="does not match"):
        await ensure_approval(
            command_bus.event_store,
            "ActivatePlugin",
            {"plugin_id": "plugin-b", "approval_id": created["aggregate_id"]},
        )
