from __future__ import annotations

from app.domain.events.agents import (
    AgentHeartbeatReceived,
    AgentMarkedIdle,
    AgentRegistered,
    TaskAssignedToAgent,
)
from app.domain.events.approvals import (
    ApprovalExpired,
    ApprovalGranted,
    ApprovalRejected,
    ApprovalRequested,
    ChangeProposed,
)
from app.domain.events.base import DomainEvent
from app.domain.events.incidents import (
    DiagnosticsCompleted,
    DiagnosticsStarted,
    IncidentClassified,
    IncidentDetected,
    PostRemediationVerificationFailed,
    PostRemediationVerificationPassed,
    RagRequestFailed,
    RemediationFailed,
    RemediationStarted,
    RemediationSucceeded,
)
from app.domain.events.plugins import (
    PluginActivated,
    PluginInstalled,
    PluginProposed,
    PluginRolledBack,
    PluginValidated,
)
from app.domain.events.resources import (
    CapabilityRegistered,
    ResourceRegistered,
    TransferCompleted,
    TransferFailed,
    TransferRequested,
)
from app.domain.events.tasks import (
    TaskAssigned,
    TaskCompleted,
    TaskCreated,
    TaskFailed,
    TaskStarted,
)
from app.domain.events.workflows import (
    WorkflowStarted,
    WorkflowVersionActivated,
    WorkflowVersionApproved,
    WorkflowVersionProposed,
    WorkflowVersionRolledBack,
    WorkflowVersionShadowed,
    WorkflowVersionValidated,
)

__all__ = [
    "AgentHeartbeatReceived",
    "AgentMarkedIdle",
    "AgentRegistered",
    "ApprovalExpired",
    "ApprovalGranted",
    "ApprovalRejected",
    "ApprovalRequested",
    "CapabilityRegistered",
    "ChangeProposed",
    "DiagnosticsCompleted",
    "DiagnosticsStarted",
    "DomainEvent",
    "IncidentClassified",
    "IncidentDetected",
    "PluginActivated",
    "PluginInstalled",
    "PluginProposed",
    "PluginRolledBack",
    "PluginValidated",
    "PostRemediationVerificationFailed",
    "PostRemediationVerificationPassed",
    "RagRequestFailed",
    "RemediationFailed",
    "RemediationStarted",
    "RemediationSucceeded",
    "ResourceRegistered",
    "TaskAssigned",
    "TaskAssignedToAgent",
    "TaskCompleted",
    "TaskCreated",
    "TaskFailed",
    "TaskStarted",
    "TransferCompleted",
    "TransferFailed",
    "TransferRequested",
    "WorkflowStarted",
    "WorkflowVersionActivated",
    "WorkflowVersionApproved",
    "WorkflowVersionProposed",
    "WorkflowVersionRolledBack",
    "WorkflowVersionShadowed",
    "WorkflowVersionValidated",
]
