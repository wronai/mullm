import pytest


@pytest.mark.asyncio
async def test_create_and_assign_task(command_bus, fake_bus):
    created = await command_bus.handle(
        command_type="CreateTask",
        data={"title": "Check pipeline", "priority": "high"},
    )
    task_id = created["aggregate_id"]

    await command_bus.handle(
        command_type="AssignTask",
        data={
            "task_id": task_id,
            "agent_id": "shell-agent-a",
            "command": "echo ok",
        },
    )

    messages = [subject for subject, _ in fake_bus.messages]
    assert "mullm.events" in messages
    assert "task.assigned.shell" in messages


@pytest.mark.asyncio
async def test_register_agent_and_heartbeat(command_bus):
    result = await command_bus.handle(
        command_type="RegisterAgent",
        data={
            "agent_id": "shell-agent-a",
            "agent_type": "shell",
            "capabilities": ["shell"],
        },
    )
    assert result["aggregate_id"] == "shell-agent-a"

    await command_bus.handle(
        command_type="AgentHeartbeat",
        data={"agent_id": "shell-agent-a", "load_score": 10},
    )


@pytest.mark.asyncio
async def test_approval_flow(command_bus):
    created = await command_bus.handle(
        command_type="CreateApprovalRequest",
        data={
            "action_type": "ActivatePlugin",
            "target_id": "plugin-x",
            "requested_by": "user-1",
        },
    )
    approval_id = created["aggregate_id"]
    result = await command_bus.handle(
        command_type="ApproveRequest",
        data={"approval_id": approval_id, "approved_by": "user-ops"},
    )
    assert result["events"][-1]["event_type"] == "ApprovalGranted"


@pytest.mark.asyncio
async def test_plugin_and_workflow_version_flow(command_bus):
    plugin_result = await command_bus.handle(
        command_type="ProposePlugin",
        data={
            "plugin_id": "deploy-tools",
            "version": "1.0.0",
            "capabilities": ["shell"],
        },
    )
    plugin_id = plugin_result["aggregate_id"]
    await command_bus.handle(
        command_type="ValidatePlugin",
        data={"plugin_id": plugin_id},
    )
    await command_bus.handle(
        command_type="InstallPlugin",
        data={"plugin_id": plugin_id},
    )

    wf_result = await command_bus.handle(
        command_type="ProposeWorkflowVersion",
        data={
            "workflow_id": "wf-ci",
            "version": 1,
            "definition": {"steps": ["lint"]},
        },
    )
    workflow_id = wf_result["aggregate_id"]
    await command_bus.handle(
        command_type="ValidateWorkflowVersion",
        data={"workflow_id": workflow_id},
    )
    await command_bus.handle(
        command_type="ActivateWorkflowVersion",
        data={"workflow_id": workflow_id},
    )
