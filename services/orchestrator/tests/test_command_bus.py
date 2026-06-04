import pytest

from app.application.command_bus import CommandBus

from .fakes import FakeEventStore, FakeMessageBus


@pytest.mark.asyncio
async def test_command_bus_creates_assigns_and_completes_task():
    event_store = FakeEventStore()
    message_bus = FakeMessageBus()
    bus = CommandBus(event_store=event_store, message_bus=message_bus)

    created = await bus.handle(
        command_type="CreateTask",
        command_id="cmd-create",
        data={"title": "Check staging", "required_capabilities": ["shell"]},
    )
    task_id = created["aggregate_id"]

    assigned = await bus.handle(
        command_type="AssignTask",
        command_id="cmd-assign",
        data={"task_id": task_id, "agent_id": "shell-agent-1", "command": "pwd"},
    )
    completed = await bus.handle(
        command_type="CompleteTask",
        command_id="cmd-complete",
        data={"task_id": task_id, "result": {"exit_code": 0}},
    )

    task_events = await event_store.get_events_for_aggregate("task", task_id)
    assert [event.event_type for event in task_events] == [
        "TaskCreated",
        "TaskAssigned",
        "TaskCompleted",
    ]
    assert assigned["events"][0]["payload"]["agent_id"] == "shell-agent-1"
    assert completed["events"][0]["payload"]["status"] == "completed"
    assert ("task.assigned.shell", {"task_id": task_id, "agent_id": "shell-agent-1", "command": "pwd"}) in message_bus.messages
    assert [subject for subject, _ in message_bus.messages].count("mullm.events") >= 3


@pytest.mark.asyncio
async def test_command_bus_registers_agent():
    event_store = FakeEventStore()
    bus = CommandBus(event_store=event_store)

    result = await bus.handle(
        command_type="RegisterAgent",
        command_id="cmd-agent",
        data={"agent_id": "shell-agent-1", "agent_type": "shell", "capabilities": ["shell"]},
    )

    assert result["aggregate_id"] == "shell-agent-1"
    assert result["events"][0]["event_type"] == "AgentRegistered"
