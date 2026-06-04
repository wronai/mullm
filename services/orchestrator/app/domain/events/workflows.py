from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, ClassVar

from app.domain.events.base import DomainEvent
from app.domain.value_objects import WorkflowId


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
class WorkflowVersionShadowed(DomainEvent):
    workflow_id: WorkflowId = WorkflowId("")
    version: int = 1
    traffic_percent: int = 10

    event_type: ClassVar[str] = "WorkflowVersionShadowed"
    aggregate_type: ClassVar[str] = "workflow"

    @property
    def aggregate_id(self) -> str:
        return str(self.workflow_id)

    @property
    def data(self) -> dict[str, Any]:
        return {
            "workflow_id": str(self.workflow_id),
            "version": self.version,
            "traffic_percent": self.traffic_percent,
            "status": "shadow",
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
