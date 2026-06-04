import pytest

from app.domain.aggregates.agent import Agent
from app.domain.value_objects import AgentId, AgentStatus, TaskId


def test_register_agent():
    agent = Agent.register(
        agent_id="shell-agent-a",
        agent_type="shell",
        capabilities=["shell"],
    )
    events = agent.get_uncommitted_events()
    assert events[0].event_type == "AgentRegistered"
    assert agent.status == AgentStatus.IDLE


def test_assign_task_marks_busy():
    agent = Agent.register("a1", "shell", ["shell"])
    agent.assign_task(TaskId("task-1"))
    assert agent.status == AgentStatus.BUSY
    assert agent.current_task_id == TaskId("task-1")


def test_disabled_agent_cannot_take_task():
    agent = Agent(
        agent_id=AgentId("a1"),
        agent_type="shell",
        status=AgentStatus.DISABLED,
    )
    with pytest.raises(ValueError, match="disabled"):
        agent.assign_task(TaskId("task-1"))
