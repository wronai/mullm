from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, ClassVar
from uuid import uuid4

from app.domain.value_objects import (
    AgentId,
    ApprovalId,
    ExecutionMode,
    PluginId,
    Priority,
    TaskId,
    WorkflowId,
)


def _utc_now() -> datetime:
    return datetime.utcnow()


def _json_value(value: Any) -> Any:
    if isinstance(value, datetime):
        return value.isoformat()
    if isinstance(value, list):
        return [_json_value(item) for item in value]
    if isinstance(value, dict):
        return {key: _json_value(item) for key, item in value.items()}
    if value is None:
        return None
    return getattr(value, "value", value)


@dataclass(frozen=True)
class DomainEvent:
    timestamp: datetime = field(default_factory=_utc_now)

    event_type: ClassVar[str]
    aggregate_type: ClassVar[str]

    @property
    def aggregate_id(self) -> str:
        raise NotImplementedError

    @property
    def data(self) -> dict[str, Any]:
        raise NotImplementedError

    def to_message(
        self,
        *,
        event_id: str | None = None,
        revision: int | None = None,
        causation_id: str | None = None,
        correlation_id: str | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        aggregate_id = self.aggregate_id
        return {
            "event_id": event_id or str(uuid4()),
            "stream_id": f"{self.aggregate_type}-{aggregate_id}",
            "aggregate_type": self.aggregate_type,
            "aggregate_id": aggregate_id,
            "event_type": self.event_type,
            "revision": revision,
            "occurred_at": self.timestamp.isoformat(),
            "causation_id": causation_id,
            "correlation_id": correlation_id,
            "payload": self.data,
            "metadata": metadata or {},
        }


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


@dataclass(frozen=True)
class WorkflowStarted(DomainEvent):
    workflow_id: WorkflowId = WorkflowId("")
    input_data: dict[str, Any] = field(default_factory=dict)
    agent_assignments: dict[str, str] | None = None

    event_type: ClassVar[str] = "WorkflowStarted"
    aggregate_type: ClassVar[str] = "workflow"

    @property
    def aggregate_id(self) -> str:
        return str(self.workflow_id)

    @property
    def data(self) -> dict[str, Any]:
        return {
            "workflow_id": str(self.workflow_id),
            "status": "active",
            "version": 1,
            "definition": {
                "input_data": self.input_data,
                "agent_assignments": self.agent_assignments or {},
            },
        }


@dataclass(frozen=True)
class WorkflowVersionProposed(DomainEvent):
    workflow_id: WorkflowId = WorkflowId("")
    version: int = 1
    definition: dict[str, Any] = field(default_factory=dict)

    event_type: ClassVar[str] = "WorkflowVersionProposed"
    aggregate_type: ClassVar[str] = "workflow"

    @property
    def aggregate_id(self) -> str:
        return str(self.workflow_id)

    @property
    def data(self) -> dict[str, Any]:
        return {
            "workflow_id": str(self.workflow_id),
            "version": self.version,
            "status": "proposed",
            "definition": self.definition,
        }


@dataclass(frozen=True)
class WorkflowVersionValidated(DomainEvent):
    workflow_id: WorkflowId = WorkflowId("")
    version: int = 1

    event_type: ClassVar[str] = "WorkflowVersionValidated"
    aggregate_type: ClassVar[str] = "workflow"

    @property
    def aggregate_id(self) -> str:
        return str(self.workflow_id)

    @property
    def data(self) -> dict[str, Any]:
        return {
            "workflow_id": str(self.workflow_id),
            "version": self.version,
            "status": "validated",
        }


@dataclass(frozen=True)
class WorkflowVersionApproved(DomainEvent):
    workflow_id: WorkflowId = WorkflowId("")
    version: int = 1
    approved_by: str = ""

    event_type: ClassVar[str] = "WorkflowVersionApproved"
    aggregate_type: ClassVar[str] = "workflow"

    @property
    def aggregate_id(self) -> str:
        return str(self.workflow_id)

    @property
    def data(self) -> dict[str, Any]:
        return {
            "workflow_id": str(self.workflow_id),
            "version": self.version,
            "status": "approved",
            "approved_by": self.approved_by,
        }


@dataclass(frozen=True)
class WorkflowVersionActivated(DomainEvent):
    workflow_id: WorkflowId = WorkflowId("")
    version: int = 1

    event_type: ClassVar[str] = "WorkflowVersionActivated"
    aggregate_type: ClassVar[str] = "workflow"

    @property
    def aggregate_id(self) -> str:
        return str(self.workflow_id)

    @property
    def data(self) -> dict[str, Any]:
        return {
            "workflow_id": str(self.workflow_id),
            "version": self.version,
            "status": "active",
        }


@dataclass(frozen=True)
class WorkflowVersionRolledBack(DomainEvent):
    workflow_id: WorkflowId = WorkflowId("")
    version: int = 1
    reason: str = ""

    event_type: ClassVar[str] = "WorkflowVersionRolledBack"
    aggregate_type: ClassVar[str] = "workflow"

    @property
    def aggregate_id(self) -> str:
        return str(self.workflow_id)

    @property
    def data(self) -> dict[str, Any]:
        return {
            "workflow_id": str(self.workflow_id),
            "version": self.version,
            "status": "rolled_back",
            "reason": self.reason,
        }


@dataclass(frozen=True)
class PluginProposed(DomainEvent):
    plugin_id: PluginId = PluginId("")
    version: str = "0.1.0"
    capabilities: list[str] = field(default_factory=list)
    manifest: dict[str, Any] = field(default_factory=dict)

    event_type: ClassVar[str] = "PluginProposed"
    aggregate_type: ClassVar[str] = "plugin"

    @property
    def aggregate_id(self) -> str:
        return str(self.plugin_id)

    @property
    def data(self) -> dict[str, Any]:
        return {
            "plugin_id": str(self.plugin_id),
            "version": self.version,
            "status": "proposed",
            "capabilities": self.capabilities,
            "manifest": self.manifest,
        }


@dataclass(frozen=True)
class PluginValidated(DomainEvent):
    plugin_id: PluginId = PluginId("")
    version: str = "0.1.0"

    event_type: ClassVar[str] = "PluginValidated"
    aggregate_type: ClassVar[str] = "plugin"

    @property
    def aggregate_id(self) -> str:
        return str(self.plugin_id)

    @property
    def data(self) -> dict[str, Any]:
        return {
            "plugin_id": str(self.plugin_id),
            "version": self.version,
            "status": "validated",
        }


@dataclass(frozen=True)
class PluginInstalled(DomainEvent):
    plugin_id: PluginId = PluginId("")
    version: str = "0.1.0"

    event_type: ClassVar[str] = "PluginInstalled"
    aggregate_type: ClassVar[str] = "plugin"

    @property
    def aggregate_id(self) -> str:
        return str(self.plugin_id)

    @property
    def data(self) -> dict[str, Any]:
        return {
            "plugin_id": str(self.plugin_id),
            "version": self.version,
            "status": "installed",
        }


@dataclass(frozen=True)
class PluginActivated(DomainEvent):
    plugin_id: PluginId = PluginId("")
    version: str = "0.1.0"

    event_type: ClassVar[str] = "PluginActivated"
    aggregate_type: ClassVar[str] = "plugin"

    @property
    def aggregate_id(self) -> str:
        return str(self.plugin_id)

    @property
    def data(self) -> dict[str, Any]:
        return {
            "plugin_id": str(self.plugin_id),
            "version": self.version,
            "status": "active",
        }


@dataclass(frozen=True)
class PluginRolledBack(DomainEvent):
    plugin_id: PluginId = PluginId("")
    version: str = "0.1.0"
    reason: str = ""

    event_type: ClassVar[str] = "PluginRolledBack"
    aggregate_type: ClassVar[str] = "plugin"

    @property
    def aggregate_id(self) -> str:
        return str(self.plugin_id)

    @property
    def data(self) -> dict[str, Any]:
        return {
            "plugin_id": str(self.plugin_id),
            "version": self.version,
            "status": "rolled_back",
            "reason": self.reason,
        }


@dataclass(frozen=True)
class ApprovalRequested(DomainEvent):
    approval_id: ApprovalId = ApprovalId("")
    action_type: str = ""
    target_id: str = ""
    risk_level: str = "medium"
    requested_by: str = ""

    event_type: ClassVar[str] = "ApprovalRequested"
    aggregate_type: ClassVar[str] = "approval"

    @property
    def aggregate_id(self) -> str:
        return str(self.approval_id)

    @property
    def data(self) -> dict[str, Any]:
        return {
            "approval_id": str(self.approval_id),
            "action_type": self.action_type,
            "target_id": self.target_id,
            "risk_level": self.risk_level,
            "requested_by": self.requested_by,
            "status": "pending",
        }


@dataclass(frozen=True)
class ApprovalGranted(DomainEvent):
    approval_id: ApprovalId = ApprovalId("")
    approved_by: str = ""

    event_type: ClassVar[str] = "ApprovalGranted"
    aggregate_type: ClassVar[str] = "approval"

    @property
    def aggregate_id(self) -> str:
        return str(self.approval_id)

    @property
    def data(self) -> dict[str, Any]:
        return {
            "approval_id": str(self.approval_id),
            "approved_by": self.approved_by,
            "status": "granted",
        }


@dataclass(frozen=True)
class ApprovalRejected(DomainEvent):
    approval_id: ApprovalId = ApprovalId("")
    rejected_by: str = ""
    reason: str = ""

    event_type: ClassVar[str] = "ApprovalRejected"
    aggregate_type: ClassVar[str] = "approval"

    @property
    def aggregate_id(self) -> str:
        return str(self.approval_id)

    @property
    def data(self) -> dict[str, Any]:
        return {
            "approval_id": str(self.approval_id),
            "rejected_by": self.rejected_by,
            "reason": self.reason,
            "status": "rejected",
        }


@dataclass(frozen=True)
class ApprovalExpired(DomainEvent):
    approval_id: ApprovalId = ApprovalId("")

    event_type: ClassVar[str] = "ApprovalExpired"
    aggregate_type: ClassVar[str] = "approval"

    @property
    def aggregate_id(self) -> str:
        return str(self.approval_id)

    @property
    def data(self) -> dict[str, Any]:
        return {
            "approval_id": str(self.approval_id),
            "status": "expired",
        }
