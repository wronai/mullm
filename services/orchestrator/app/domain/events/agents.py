from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, ClassVar

from app.domain.events.base import DomainEvent
from app.domain.value_objects import AgentId, TaskId


@dataclass(frozen=True)
class AgentRegistered(DomainEvent):
    agent_id: AgentId = AgentId("")
    agent_type: str = "shell"
    capabilities: list[str] = field(default_factory=list)
    metadata: dict[str, Any] | None = None

    event_type: ClassVar[str] = "AgentRegistered"
    aggregate_type: ClassVar[str] = "agent"

    @property
    def aggregate_id(self) -> str:
        return str(self.agent_id)

    @property
    def data(self) -> dict[str, Any]:
        return {
            "agent_id": str(self.agent_id),
            "agent_type": self.agent_type,
            "capabilities": self.capabilities,
            "metadata": self.metadata or {},
            "status": "idle",
        }


@dataclass(frozen=True)
class AgentHeartbeatReceived(DomainEvent):
    agent_id: AgentId = AgentId("")
    load_score: int = 0

    event_type: ClassVar[str] = "AgentHeartbeatReceived"
    aggregate_type: ClassVar[str] = "agent"

    @property
    def aggregate_id(self) -> str:
        return str(self.agent_id)

    @property
    def data(self) -> dict[str, Any]:
        return {
            "agent_id": str(self.agent_id),
            "load_score": self.load_score,
            "heartbeat_at": self.timestamp.isoformat(),
        }


@dataclass(frozen=True)
class TaskAssignedToAgent(DomainEvent):
    agent_id: AgentId = AgentId("")
    task_id: TaskId = TaskId("")

    event_type: ClassVar[str] = "TaskAssignedToAgent"
    aggregate_type: ClassVar[str] = "agent"

    @property
    def aggregate_id(self) -> str:
        return str(self.agent_id)

    @property
    def data(self) -> dict[str, Any]:
        return {
            "agent_id": str(self.agent_id),
            "task_id": str(self.task_id),
            "status": "busy",
            "current_task_id": str(self.task_id),
        }


@dataclass(frozen=True)
class AgentMarkedIdle(DomainEvent):
    agent_id: AgentId = AgentId("")

    event_type: ClassVar[str] = "AgentMarkedIdle"
    aggregate_type: ClassVar[str] = "agent"

    @property
    def aggregate_id(self) -> str:
        return str(self.agent_id)

    @property
    def data(self) -> dict[str, Any]:
        return {
            "agent_id": str(self.agent_id),
            "status": "idle",
            "current_task_id": None,
        }
