from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, ClassVar

from app.domain.events.base import DomainEvent
from app.domain.value_objects import PluginId


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
