from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, ClassVar

from app.domain.events import DomainEvent


@dataclass(frozen=True)
class RagRequestFailed(DomainEvent):
    incident_id: str = ""
    query: str = ""
    error_code: str = ""
    message: str = ""
    context: dict[str, Any] = field(default_factory=dict)

    event_type: ClassVar[str] = "RagRequestFailed"
    aggregate_type: ClassVar[str] = "incident"

    @property
    def aggregate_id(self) -> str:
        return self.incident_id

    @property
    def data(self) -> dict[str, Any]:
        return {
            "incident_id": self.incident_id,
            "query": self.query,
            "error_code": self.error_code,
            "message": self.message,
            "context": self.context,
        }


@dataclass(frozen=True)
class IncidentDetected(DomainEvent):
    incident_id: str = ""
    incident_type: str = ""
    severity: str = "warning"
    source: str = ""
    error_code: str = ""
    message: str = ""
    context: dict[str, Any] = field(default_factory=dict)
    status: str = "detected"

    event_type: ClassVar[str] = "IncidentDetected"
    aggregate_type: ClassVar[str] = "incident"

    @property
    def aggregate_id(self) -> str:
        return self.incident_id

    @property
    def data(self) -> dict[str, Any]:
        return {
            "incident_id": self.incident_id,
            "incident_type": self.incident_type,
            "severity": self.severity,
            "source": self.source,
            "error_code": self.error_code,
            "message": self.message,
            "context": self.context,
            "status": self.status,
        }


@dataclass(frozen=True)
class IncidentClassified(DomainEvent):
    incident_id: str = ""
    incident_class: str = ""
    error_code: str = ""
    confidence: float | None = None
    playbook_id: str | None = None
    status: str = "classified"

    event_type: ClassVar[str] = "IncidentClassified"
    aggregate_type: ClassVar[str] = "incident"

    @property
    def aggregate_id(self) -> str:
        return self.incident_id

    @property
    def data(self) -> dict[str, Any]:
        return {
            "incident_id": self.incident_id,
            "incident_class": self.incident_class,
            "error_code": self.error_code,
            "confidence": self.confidence,
            "playbook_id": self.playbook_id,
            "status": self.status,
        }


@dataclass(frozen=True)
class DiagnosticsStarted(DomainEvent):
    incident_id: str = ""
    checks: list[str] = field(default_factory=list)
    status: str = "diagnosing"

    event_type: ClassVar[str] = "DiagnosticsStarted"
    aggregate_type: ClassVar[str] = "incident"

    @property
    def aggregate_id(self) -> str:
        return self.incident_id

    @property
    def data(self) -> dict[str, Any]:
        return {
            "incident_id": self.incident_id,
            "checks": self.checks,
            "status": self.status,
        }


@dataclass(frozen=True)
class DiagnosticsCompleted(DomainEvent):
    incident_id: str = ""
    root_cause: str | None = None
    checks: dict[str, Any] = field(default_factory=dict)
    status: str = "diagnosed"

    event_type: ClassVar[str] = "DiagnosticsCompleted"
    aggregate_type: ClassVar[str] = "incident"

    @property
    def aggregate_id(self) -> str:
        return self.incident_id

    @property
    def data(self) -> dict[str, Any]:
        return {
            "incident_id": self.incident_id,
            "root_cause": self.root_cause,
            "checks": self.checks,
            "status": self.status,
        }


@dataclass(frozen=True)
class RemediationStarted(DomainEvent):
    incident_id: str = ""
    playbook_id: str = ""
    action: str | None = None
    status: str = "remediating"

    event_type: ClassVar[str] = "RemediationStarted"
    aggregate_type: ClassVar[str] = "incident"

    @property
    def aggregate_id(self) -> str:
        return self.incident_id

    @property
    def data(self) -> dict[str, Any]:
        return {
            "incident_id": self.incident_id,
            "playbook_id": self.playbook_id,
            "action": self.action,
            "status": self.status,
        }


@dataclass(frozen=True)
class RemediationSucceeded(DomainEvent):
    incident_id: str = ""
    playbook_id: str = ""
    result: dict[str, Any] = field(default_factory=dict)
    status: str = "remediated"

    event_type: ClassVar[str] = "RemediationSucceeded"
    aggregate_type: ClassVar[str] = "incident"

    @property
    def aggregate_id(self) -> str:
        return self.incident_id

    @property
    def data(self) -> dict[str, Any]:
        return {
            "incident_id": self.incident_id,
            "playbook_id": self.playbook_id,
            "result": self.result,
            "status": self.status,
        }


@dataclass(frozen=True)
class RemediationFailed(DomainEvent):
    incident_id: str = ""
    playbook_id: str = ""
    error: str = ""
    status: str = "remediation_failed"

    event_type: ClassVar[str] = "RemediationFailed"
    aggregate_type: ClassVar[str] = "incident"

    @property
    def aggregate_id(self) -> str:
        return self.incident_id

    @property
    def data(self) -> dict[str, Any]:
        return {
            "incident_id": self.incident_id,
            "playbook_id": self.playbook_id,
            "error": self.error,
            "status": self.status,
        }


@dataclass(frozen=True)
class PostRemediationVerificationPassed(DomainEvent):
    incident_id: str = ""
    verification: dict[str, Any] = field(default_factory=dict)
    status: str = "verified"

    event_type: ClassVar[str] = "PostRemediationVerificationPassed"
    aggregate_type: ClassVar[str] = "incident"

    @property
    def aggregate_id(self) -> str:
        return self.incident_id

    @property
    def data(self) -> dict[str, Any]:
        return {
            "incident_id": self.incident_id,
            "verification": self.verification,
            "status": self.status,
        }


@dataclass(frozen=True)
class PostRemediationVerificationFailed(DomainEvent):
    incident_id: str = ""
    verification: dict[str, Any] = field(default_factory=dict)
    status: str = "verification_failed"

    event_type: ClassVar[str] = "PostRemediationVerificationFailed"
    aggregate_type: ClassVar[str] = "incident"

    @property
    def aggregate_id(self) -> str:
        return self.incident_id

    @property
    def data(self) -> dict[str, Any]:
        return {
            "incident_id": self.incident_id,
            "verification": self.verification,
            "status": self.status,
        }
