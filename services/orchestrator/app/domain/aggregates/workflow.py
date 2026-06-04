from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from app.domain.events import (
    WorkflowStarted,
    WorkflowVersionActivated,
    WorkflowVersionApproved,
    WorkflowVersionProposed,
    WorkflowVersionRolledBack,
    WorkflowVersionValidated,
)
from app.domain.value_objects import WorkflowId, WorkflowStatus


@dataclass
class Workflow:
    workflow_id: WorkflowId
    version: int = 1
    status: WorkflowStatus = WorkflowStatus.PROPOSED
    definition: dict[str, Any] = field(default_factory=dict)
    input_data: dict[str, Any] = field(default_factory=dict)
    agent_assignments: dict[str, str] = field(default_factory=dict)
    _events: list[Any] = field(default_factory=list)

    @classmethod
    def start(
        cls,
        workflow_id: str,
        input_data: dict[str, Any],
        agent_assignments: dict[str, str] | None = None,
    ) -> "Workflow":
        workflow = cls(
            workflow_id=WorkflowId(workflow_id),
            status=WorkflowStatus.ACTIVE,
            input_data=input_data,
            agent_assignments=agent_assignments or {},
            definition={
                "input_data": input_data,
                "agent_assignments": agent_assignments or {},
            },
        )
        workflow._events.append(
            WorkflowStarted(
                workflow_id=workflow.workflow_id,
                input_data=workflow.input_data,
                agent_assignments=workflow.agent_assignments,
            )
        )
        return workflow

    @classmethod
    def propose_version(
        cls,
        workflow_id: str,
        version: int,
        definition: dict[str, Any],
    ) -> "Workflow":
        workflow = cls(
            workflow_id=WorkflowId(workflow_id),
            version=version,
            status=WorkflowStatus.PROPOSED,
            definition=definition,
        )
        workflow._events.append(
            WorkflowVersionProposed(
                workflow_id=workflow.workflow_id,
                version=version,
                definition=definition,
            )
        )
        return workflow

    def validate_version(self) -> None:
        if self.status != WorkflowStatus.PROPOSED:
            raise ValueError(f"Cannot validate workflow in {self.status} status")
        self.status = WorkflowStatus.VALIDATED
        self._events.append(
            WorkflowVersionValidated(
                workflow_id=self.workflow_id,
                version=self.version,
            )
        )

    def approve_version(self, approved_by: str) -> None:
        if self.status != WorkflowStatus.VALIDATED:
            raise ValueError(f"Cannot approve workflow in {self.status} status")
        self.status = WorkflowStatus.APPROVED
        self._events.append(
            WorkflowVersionApproved(
                workflow_id=self.workflow_id,
                version=self.version,
                approved_by=approved_by,
            )
        )

    def activate_version(self) -> None:
        if self.status not in {WorkflowStatus.APPROVED, WorkflowStatus.VALIDATED}:
            raise ValueError(f"Cannot activate workflow in {self.status} status")
        self.status = WorkflowStatus.ACTIVE
        self._events.append(
            WorkflowVersionActivated(
                workflow_id=self.workflow_id,
                version=self.version,
            )
        )

    def rollback_version(self, reason: str = "") -> None:
        self.status = WorkflowStatus.ROLLED_BACK
        self._events.append(
            WorkflowVersionRolledBack(
                workflow_id=self.workflow_id,
                version=self.version,
                reason=reason,
            )
        )

    def get_uncommitted_events(self) -> list[Any]:
        return self._events.copy()

    def mark_events_committed(self) -> None:
        self._events.clear()
