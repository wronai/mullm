"""
Wspólny kontrakt orientacji routingu (PR-1).

Zsynchronizowany z nlp2dsl/nlp-service/app/routing/orientation.py oraz
app.local_orient.OrientationResult.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Literal

QueryCategory = Literal[
    "file_list_registry",
    "file_list_host",
    "shell",
    "workflow",
    "system_local",
    "unknown",
]

OrientationSource = Literal["nlp2dsl_service", "nlp2dsl_backend", "local_orient", "unknown"]

ShellTranslationSource = Literal["builtin", "nlp2cmd", "none"]

_EXECUTION_STATUSES = Literal[
    "pending",
    "queued",
    "running",
    "completed",
    "timeout",
    "failed",
]


@dataclass
class OrientationDecision:
    category: QueryCategory
    suggested_action: str | None
    confidence: float
    reason_codes: list[str] = field(default_factory=list)
    shell_command: str | None = None
    list_scope: str | None = None
    connector: str = "mullm"
    source: OrientationSource = "unknown"
    latency_ms: float = 0.0

    @classmethod
    def from_dict(cls, data: dict[str, Any] | None) -> OrientationDecision | None:
        if not data:
            return None
        category = str(data.get("category") or "unknown")
        if category not in (
            "file_list_registry",
            "file_list_host",
            "shell",
            "workflow",
            "system_local",
            "unknown",
        ):
            category = "unknown"
        source = str(data.get("source") or "unknown")
        if source not in ("nlp2dsl_service", "nlp2dsl_backend", "local_orient"):
            source = "unknown"
        return cls(
            category=category,  # type: ignore[arg-type]
            suggested_action=data.get("suggested_action"),
            confidence=float(data.get("confidence") or 0.0),
            reason_codes=list(data.get("reason_codes") or []),
            shell_command=(data.get("shell_command") or None),
            list_scope=data.get("list_scope"),
            connector=str(data.get("connector") or "mullm"),
            source=source,  # type: ignore[arg-type]
            latency_ms=float(data.get("latency_ms") or 0.0),
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "category": self.category,
            "suggested_action": self.suggested_action,
            "confidence": self.confidence,
            "reason_codes": self.reason_codes,
            "shell_command": self.shell_command,
            "list_scope": self.list_scope,
            "connector": self.connector,
            "source": self.source,
            "latency_ms": round(self.latency_ms, 2),
        }

    @property
    def is_actionable(self) -> bool:
        return self.category not in ("unknown", "system_local")

    @property
    def shell_translation_source(self) -> ShellTranslationSource:
        if self.shell_command:
            return "builtin"
        if self.category == "shell":
            return "nlp2cmd"
        return "none"
