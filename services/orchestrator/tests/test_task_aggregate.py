from app.domain.aggregates.task import Task
from app.domain.value_objects import AgentId, TaskStatus


def test_task_rehydrates_from_domain_events():
    task = Task.create(title="Run deployment checks")
    task.assign_to_agent(AgentId("shell-agent-1"))
    task.start()
    task.complete({"ok": True})

    rehydrated = Task.from_events(task.get_uncommitted_events())

    assert rehydrated.title == "Run deployment checks"
    assert rehydrated.agent_id == "shell-agent-1"
    assert rehydrated.status == TaskStatus.COMPLETED
    assert rehydrated.result == {"ok": True}


def test_task_cannot_complete_before_assignment():
    task = Task.create(title="Unassigned work")

    try:
        task.complete({"ok": True})
    except ValueError as exc:
        assert "Cannot complete task" in str(exc)
    else:
        raise AssertionError("Expected task completion to fail")
