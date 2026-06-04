from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from app.domain.events import WorkflowStarted
from app.domain.value_objects import WorkflowId, WorkflowStatus


@dataclass
class Workflow:
    workflow_id: WorkflowId
    status: WorkflowStatus = WorkflowStatus.ACTIVE
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
            input_data=input_data,
            agent_assignments=agent_assignments or {},
        )
        workflow._events.append(
            WorkflowStarted(
                workflow_id=workflow.workflow_id,
                input_data=workflow.input_data,
                agent_assignments=workflow.agent_assignments,
            )
        )
        return workflow

    def get_uncommitted_events(self) -> list[Any]:
        return self._events.copy()

    def mark_events_committed(self) -> None:
        self._events.clear()
