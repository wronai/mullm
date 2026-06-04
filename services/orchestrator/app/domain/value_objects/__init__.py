from __future__ import annotations

from enum import Enum


class TaskId(str):
    pass


class AgentId(str):
    pass


class WorkflowId(str):
    pass


class PluginId(str):
    pass


class ApprovalId(str):
    pass


class PluginId(str):
    pass


class ApprovalId(str):
    pass


class Priority(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"

    @classmethod
    def from_value(cls, value: str | "Priority" | None) -> "Priority":
        if isinstance(value, cls):
            return value
        if value is None:
            return cls.MEDIUM
        normalized = str(value).lower()
        try:
            return cls(normalized)
        except ValueError as exc:
            raise ValueError(f"Unsupported priority: {value}") from exc


class TaskStatus(str, Enum):
    PENDING = "pending"
    ASSIGNED = "assigned"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"


class ExecutionMode(str, Enum):
    MANUAL = "manual"
    SEMI_AUTO = "semi_auto"
    AUTO = "auto"

    @classmethod
    def from_value(cls, value: str | "ExecutionMode" | None) -> "ExecutionMode":
        if isinstance(value, cls):
            return value
        if value is None:
            return cls.SEMI_AUTO
        normalized = str(value).lower()
        try:
            return cls(normalized)
        except ValueError as exc:
            raise ValueError(f"Unsupported execution mode: {value}") from exc


class AgentStatus(str, Enum):
    IDLE = "idle"
    BUSY = "busy"
    DISABLED = "disabled"


class WorkflowStatus(str, Enum):
    PROPOSED = "proposed"
    VALIDATED = "validated"
    APPROVED = "approved"
    ACTIVE = "active"
    ROLLED_BACK = "rolled_back"
