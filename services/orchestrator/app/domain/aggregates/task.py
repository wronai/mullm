from datetime import datetime, timezone
from typing import Dict, Any, Optional, List
from uuid import uuid4

from ..events import TaskCreated, TaskAssigned, TaskStarted, TaskCompleted, TaskFailed
from ..value_objects import AgentId, ExecutionMode, Priority, TaskId, TaskStatus


def _event_type(event: Any) -> str:
    return getattr(event, "event_type", "")


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


def _event_data(event: Any) -> Dict[str, Any]:
    data = getattr(event, "data", {})
    return data() if callable(data) else data


def _event_timestamp(event: Any) -> datetime:
    timestamp = getattr(event, "timestamp", None)
    if isinstance(timestamp, datetime):
        return timestamp
    occurred_at = getattr(event, "occurred_at", None)
    if isinstance(occurred_at, datetime):
        return occurred_at
    return _utc_now()


class Task:
    def __init__(
        self,
        task_id: Optional[TaskId] = None,
        title: str = "",
        description: Optional[str] = None,
        agent_id: Optional[AgentId] = None,
        priority: Priority = Priority.MEDIUM,
        metadata: Optional[Dict[str, Any]] = None,
        execution_mode: ExecutionMode = ExecutionMode.SEMI_AUTO,
        required_capabilities: Optional[List[str]] = None
    ):
        self.task_id = task_id or TaskId(str(uuid4()))
        self.title = title
        self.description = description
        self.agent_id = agent_id
        self.priority = priority
        self.execution_mode = execution_mode
        self.required_capabilities = required_capabilities or []
        self.status = TaskStatus.PENDING
        self.metadata = metadata or {}
        self.created_at = _utc_now()
        self.updated_at = _utc_now()
        self.completed_at = None
        self.result = None
        self.error = None
        self._events = []

    @classmethod
    def create(
        cls,
        title: str,
        description: Optional[str] = None,
        agent_id: Optional[AgentId] = None,
        priority: Priority = Priority.MEDIUM,
        metadata: Optional[Dict[str, Any]] = None,
        execution_mode: ExecutionMode = ExecutionMode.SEMI_AUTO,
        required_capabilities: Optional[List[str]] = None
    ) -> 'Task':
        task = cls(
            title=title,
            description=description,
            agent_id=agent_id,
            priority=priority,
            metadata=metadata,
            execution_mode=execution_mode,
            required_capabilities=required_capabilities
        )

        task._events.append(TaskCreated(
            task_id=task.task_id,
            title=title,
            description=description,
            agent_id=agent_id,
            priority=priority,
            metadata=metadata,
            execution_mode=execution_mode,
            required_capabilities=required_capabilities or [],
            timestamp=task.created_at
        ))

        return task

    @classmethod
    def from_events(cls, events: List[Any]) -> 'Task':
        task = cls()
        task._events.clear()
        for event in events:
            task.apply(event)
        return task

    def assign_to_agent(self, agent_id: AgentId) -> None:
        if self.status not in [TaskStatus.PENDING, TaskStatus.ASSIGNED]:
            raise ValueError(f"Cannot assign task in {self.status} status")

        self.agent_id = agent_id
        self.status = TaskStatus.ASSIGNED
        self.updated_at = _utc_now()

        self._events.append(TaskAssigned(
            task_id=self.task_id,
            agent_id=agent_id,
            timestamp=self.updated_at
        ))

    def start(self) -> None:
        if self.status not in [TaskStatus.PENDING, TaskStatus.ASSIGNED]:
            raise ValueError(f"Cannot start task in {self.status} status")

        if not self.agent_id:
            raise ValueError("Task must be assigned to an agent before starting")

        self.status = TaskStatus.RUNNING
        self.updated_at = _utc_now()

        self._events.append(TaskStarted(
            task_id=self.task_id,
            agent_id=self.agent_id,
            timestamp=self.updated_at
        ))

    def complete(self, result: Optional[Dict[str, Any]] = None) -> None:
        if self.status not in [TaskStatus.ASSIGNED, TaskStatus.RUNNING]:
            raise ValueError(f"Cannot complete task in {self.status} status")

        self.status = TaskStatus.COMPLETED
        self.result = result
        self.completed_at = _utc_now()
        self.updated_at = self.completed_at

        self._events.append(TaskCompleted(
            task_id=self.task_id,
            agent_id=self.agent_id,
            result=result,
            timestamp=self.completed_at
        ))

    def fail(self, error: str) -> None:
        if self.status not in [TaskStatus.PENDING, TaskStatus.ASSIGNED, TaskStatus.RUNNING]:
            raise ValueError(f"Cannot fail task in {self.status} status")

        self.status = TaskStatus.FAILED
        self.error = error
        self.updated_at = _utc_now()

        self._events.append(TaskFailed(
            task_id=self.task_id,
            agent_id=self.agent_id,
            error=error,
            timestamp=self.updated_at
        ))

    def apply(self, event: Any) -> None:
        event_type = _event_type(event)
        data = _event_data(event)
        timestamp = _event_timestamp(event)

        if event_type == "TaskCreated":
            self.task_id = TaskId(data["task_id"])
            self.title = data["title"]
            self.description = data.get("description")
            agent_id = data.get("agent_id")
            self.agent_id = AgentId(agent_id) if agent_id else None
            self.priority = Priority.from_value(data.get("priority"))
            self.execution_mode = ExecutionMode.from_value(data.get("execution_mode"))
            self.required_capabilities = data.get("required_capabilities") or []
            self.metadata = data.get("metadata") or {}
            self.status = TaskStatus.PENDING
            self.created_at = timestamp
            self.updated_at = timestamp
            return

        if event_type == "TaskAssigned":
            self.agent_id = AgentId(data["agent_id"])
            self.status = TaskStatus.ASSIGNED
            self.updated_at = timestamp
            return

        if event_type == "TaskStarted":
            agent_id = data.get("agent_id")
            self.agent_id = AgentId(agent_id) if agent_id else self.agent_id
            self.status = TaskStatus.RUNNING
            self.updated_at = timestamp
            return

        if event_type == "TaskCompleted":
            self.status = TaskStatus.COMPLETED
            self.result = data.get("result") or {}
            self.completed_at = timestamp
            self.updated_at = timestamp
            return

        if event_type == "TaskFailed":
            self.status = TaskStatus.FAILED
            self.error = data.get("error")
            self.updated_at = timestamp

    def get_uncommitted_events(self) -> List:
        return self._events.copy()

    def mark_events_committed(self) -> None:
        self._events.clear()

    def to_dict(self) -> Dict[str, Any]:
        return {
            "task_id": str(self.task_id),
            "title": self.title,
            "description": self.description,
            "agent_id": str(self.agent_id) if self.agent_id else None,
            "priority": self.priority.value,
            "execution_mode": self.execution_mode.value,
            "required_capabilities": self.required_capabilities,
            "status": self.status.value,
            "metadata": self.metadata,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "result": self.result,
            "error": self.error
        }
