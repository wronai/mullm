from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any
from uuid import uuid4

from app.domain.events import (
    ApprovalExpired,
    ApprovalGranted,
    ApprovalRejected,
    ApprovalRequested,
)
from app.domain.value_objects import ApprovalId


class ApprovalStatus:
    PENDING = "pending"
    GRANTED = "granted"
    REJECTED = "rejected"
    EXPIRED = "expired"


@dataclass
class Approval:
    approval_id: ApprovalId
    action_type: str
    target_id: str
    risk_level: str = "medium"
    requested_by: str = ""
    status: str = ApprovalStatus.PENDING
    approved_by: str | None = None
    rejected_by: str | None = None
    reject_reason: str | None = None
    _events: list[Any] = field(default_factory=list)

    @classmethod
    def create_request(
        cls,
        *,
        action_type: str,
        target_id: str,
        risk_level: str = "medium",
        requested_by: str,
        approval_id: str | None = None,
    ) -> "Approval":
        approval = cls(
            approval_id=ApprovalId(approval_id or str(uuid4())),
            action_type=action_type,
            target_id=target_id,
            risk_level=risk_level,
            requested_by=requested_by,
        )
        approval._events.append(
            ApprovalRequested(
                approval_id=approval.approval_id,
                action_type=action_type,
                target_id=target_id,
                risk_level=risk_level,
                requested_by=requested_by,
            )
        )
        return approval

    def approve(self, approved_by: str) -> None:
        if self.status != ApprovalStatus.PENDING:
            raise ValueError(f"Cannot approve request in {self.status} status")
        self.status = ApprovalStatus.GRANTED
        self.approved_by = approved_by
        self._events.append(
            ApprovalGranted(approval_id=self.approval_id, approved_by=approved_by)
        )

    def reject(self, rejected_by: str, reason: str = "") -> None:
        if self.status != ApprovalStatus.PENDING:
            raise ValueError(f"Cannot reject request in {self.status} status")
        self.status = ApprovalStatus.REJECTED
        self.rejected_by = rejected_by
        self.reject_reason = reason
        self._events.append(
            ApprovalRejected(
                approval_id=self.approval_id,
                rejected_by=rejected_by,
                reason=reason,
            )
        )

    def expire(self) -> None:
        if self.status != ApprovalStatus.PENDING:
            raise ValueError(f"Cannot expire request in {self.status} status")
        self.status = ApprovalStatus.EXPIRED
        self._events.append(ApprovalExpired(approval_id=self.approval_id))

    def get_uncommitted_events(self) -> list[Any]:
        return self._events.copy()

    def mark_events_committed(self) -> None:
        self._events.clear()
