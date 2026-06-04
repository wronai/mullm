"""End-to-end flow on in-memory event store (bez Docker)."""

import pytest


@pytest.mark.asyncio
async def test_full_task_lifecycle(command_bus, fake_bus):
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
            "title": "Run echo",
            "auto_assign": True,
            "shell_command": "echo e2e",
        },
    )
    task_id = created["aggregate_id"]
    assert "auto_assign" in created

    await command_bus.handle(
        command_type="StartTask",
        data={"task_id": task_id},
    )

    await command_bus.handle(
        command_type="CompleteTask",
        data={"task_id": task_id, "result": {"stdout": "e2e\n"}},
    )

    events = await command_bus.event_store.get_events_for_aggregate("task", task_id)
    types = [e.event_type for e in events]
    assert "TaskCreated" in types
    assert "TaskAssigned" in types
    assert "TaskCompleted" in types

    subjects = [s for s, _ in fake_bus.messages]
    assert "task.assigned.shell" in subjects
