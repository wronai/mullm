import pytest

from app.domain.aggregates.task import Task
from app.domain.value_objects import AgentId, Priority, TaskStatus


def test_create_task_emits_task_created():
    task = Task.create(title="Deploy staging", priority=Priority.HIGH)
    events = task.get_uncommitted_events()
    assert len(events) == 1
    assert events[0].event_type == "TaskCreated"
    assert task.status == TaskStatus.PENDING


def test_assign_and_complete_lifecycle():
    task = Task.create(title="Run checks")
    task.assign_to_agent(AgentId("shell-agent-a"))
    task.start()
    task.complete(result={"ok": True})

    assert task.status == TaskStatus.COMPLETED
    assert len(task.get_uncommitted_events()) == 4


def test_cannot_complete_without_assignment():
    task = Task.create(title="Orphan task")
    with pytest.raises(ValueError, match="assigned"):
        task.start()


def test_replay_from_events():
    task = Task.create(title="Replay me")
    task.assign_to_agent(AgentId("agent-1"))
    events = task.get_uncommitted_events()
    replayed = Task.from_events(events)
    assert replayed.title == "Replay me"
    assert replayed.status == TaskStatus.ASSIGNED
