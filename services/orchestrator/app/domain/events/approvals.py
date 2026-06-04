from __future__ import annotations

from dataclasses import dataclass
from typing import Any, ClassVar

from app.domain.events.base import DomainEvent
from app.domain.value_objects import ApprovalId


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


@dataclass(frozen=True)
class ChangeProposed(DomainEvent):
    change_id: str = ""
    change_type: str = ""
    target_id: str = ""
    hypothesis: str = ""
    proposed_by: str = ""
    payload: dict[str, Any] | None = None

    event_type: ClassVar[str] = "ChangeProposed"
    aggregate_type: ClassVar[str] = "change"

    @property
    def aggregate_id(self) -> str:
        return self.change_id

    @property
    def data(self) -> dict[str, Any]:
        return {
            "change_id": self.change_id,
            "change_type": self.change_type,
            "target_id": self.target_id,
            "hypothesis": self.hypothesis,
            "proposed_by": self.proposed_by,
            "payload": self.payload or {},
            "status": "proposed",
        }
