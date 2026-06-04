from __future__ import annotations

from dataclasses import dataclass
from typing import Any, ClassVar

from app.domain.events.base import DomainEvent, _json_value
from app.domain.value_objects import (
    AgentId,
    ExecutionMode,
    Priority,
    TaskId,
)


@dataclass(frozen=True)
class TaskCreated(DomainEvent):
    task_id: TaskId = TaskId("")
    title: str = ""
    description: str | None = None
    agent_id: AgentId | None = None
    priority: Priority = Priority.MEDIUM
    metadata: dict[str, Any] | None = None
    execution_mode: ExecutionMode = ExecutionMode.SEMI_AUTO
    required_capabilities: list[str] | None = None

    event_type: ClassVar[str] = "TaskCreated"
    aggregate_type: ClassVar[str] = "task"

    @property
    def aggregate_id(self) -> str:
        return str(self.task_id)

    @property
    def data(self) -> dict[str, Any]:
        return {
            "task_id": str(self.task_id),
            "title": self.title,
            "description": self.description,
            "agent_id": str(self.agent_id) if self.agent_id else None,
            "priority": _json_value(self.priority),
            "status": "pending",
            "execution_mode": _json_value(self.execution_mode),
            "required_capabilities": self.required_capabilities or [],
            "metadata": self.metadata or {},
        }


@dataclass(frozen=True)
class TaskAssigned(DomainEvent):
    task_id: TaskId = TaskId("")
    agent_id: AgentId = AgentId("")

    event_type: ClassVar[str] = "TaskAssigned"
    aggregate_type: ClassVar[str] = "task"

    @property
    def aggregate_id(self) -> str:
        return str(self.task_id)

    @property
    def data(self) -> dict[str, Any]:
        return {
            "task_id": str(self.task_id),
            "agent_id": str(self.agent_id),
            "status": "assigned",
        }


@dataclass(frozen=True)
class TaskStarted(DomainEvent):
    task_id: TaskId = TaskId("")
    agent_id: AgentId | None = None

    event_type: ClassVar[str] = "TaskStarted"
    aggregate_type: ClassVar[str] = "task"

    @property
    def aggregate_id(self) -> str:
        return str(self.task_id)

    @property
    def data(self) -> dict[str, Any]:
        return {
            "task_id": str(self.task_id),
            "agent_id": str(self.agent_id) if self.agent_id else None,
            "status": "running",
        }


@dataclass(frozen=True)
class TaskCompleted(DomainEvent):
    task_id: TaskId = TaskId("")
    agent_id: AgentId | None = None
    result: dict[str, Any] | None = None

    event_type: ClassVar[str] = "TaskCompleted"
    aggregate_type: ClassVar[str] = "task"

    @property
    def aggregate_id(self) -> str:
        return str(self.task_id)

    @property
    def data(self) -> dict[str, Any]:
        return {
            "task_id": str(self.task_id),
            "agent_id": str(self.agent_id) if self.agent_id else None,
            "result": self.result or {},
            "status": "completed",
        }


@dataclass(frozen=True)
class TaskFailed(DomainEvent):
    task_id: TaskId = TaskId("")
    agent_id: AgentId | None = None
    error: str = ""

    event_type: ClassVar[str] = "TaskFailed"
    aggregate_type: ClassVar[str] = "task"

    @property
    def aggregate_id(self) -> str:
        return str(self.task_id)

    @property
    def data(self) -> dict[str, Any]:
        return {
            "task_id": str(self.task_id),
            "agent_id": str(self.agent_id) if self.agent_id else None,
            "error": self.error,
            "status": "failed",
        }
