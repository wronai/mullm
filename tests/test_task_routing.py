import pytest

from app.application.sagas.task_routing import maybe_auto_assign, pick_idle_agent


@pytest.mark.asyncio
async def test_pick_idle_agent(command_bus):
    await command_bus.handle(
        command_type="RegisterAgent",
        data={
            "agent_id": "shell-agent-a",
            "agent_type": "shell",
            "capabilities": ["shell"],
        },
    )
    await command_bus.handle(
        command_type="RegisterAgent",
        data={
            "agent_id": "shell-agent-b",
            "agent_type": "shell",
            "capabilities": ["shell"],
        },
    )
    agent_id = await pick_idle_agent(command_bus.event_store, ["shell"])
    assert agent_id in {"shell-agent-a", "shell-agent-b"}


@pytest.mark.asyncio
async def test_auto_assign_after_create(command_bus):
    await command_bus.handle(
        command_type="RegisterAgent",
        data={
            "agent_id": "shell-agent-a",
            "agent_type": "shell",
            "capabilities": ["shell"],
        },
    )
    created = await command_bus.handle(
        command_type="CreateTask",
        data={
            "title": "Auto routed",
            "auto_assign": True,
            "shell_command": "echo routed",
        },
    )
    assert "auto_assign" in created
    assert created["auto_assign"]["aggregate_id"] == created["aggregate_id"]
