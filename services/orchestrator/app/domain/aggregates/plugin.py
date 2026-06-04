from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from app.domain.events import (
    PluginActivated,
    PluginInstalled,
    PluginProposed,
    PluginRolledBack,
    PluginValidated,
)
from app.domain.value_objects import PluginId


class PluginStatus:
    PROPOSED = "proposed"
    VALIDATED = "validated"
    INSTALLED = "installed"
    ACTIVE = "active"
    ROLLED_BACK = "rolled_back"


@dataclass
class Plugin:
    plugin_id: PluginId
    version: str
    capabilities: list[str] = field(default_factory=list)
    manifest: dict[str, Any] = field(default_factory=dict)
    status: str = PluginStatus.PROPOSED
    _events: list[Any] = field(default_factory=list)

    @classmethod
    def propose(
        cls,
        plugin_id: str,
        version: str,
        capabilities: list[str],
        manifest: dict[str, Any] | None = None,
    ) -> "Plugin":
        plugin = cls(
            plugin_id=PluginId(plugin_id),
            version=version,
            capabilities=capabilities,
            manifest=manifest or {},
        )
        plugin._events.append(
            PluginProposed(
                plugin_id=plugin.plugin_id,
                version=version,
                capabilities=capabilities,
                manifest=plugin.manifest,
            )
        )
        return plugin

    def validate(self) -> None:
        if self.status != PluginStatus.PROPOSED:
            raise ValueError(f"Cannot validate plugin in {self.status} status")
        self.status = PluginStatus.VALIDATED
        self._events.append(
            PluginValidated(plugin_id=self.plugin_id, version=self.version)
        )

    def install(self) -> None:
        if self.status != PluginStatus.VALIDATED:
            raise ValueError(f"Cannot install plugin in {self.status} status")
        self.status = PluginStatus.INSTALLED
        self._events.append(
            PluginInstalled(plugin_id=self.plugin_id, version=self.version)
        )

    def activate(self) -> None:
        if self.status not in {PluginStatus.INSTALLED, PluginStatus.VALIDATED}:
            raise ValueError(f"Cannot activate plugin in {self.status} status")
        self.status = PluginStatus.ACTIVE
        self._events.append(
            PluginActivated(plugin_id=self.plugin_id, version=self.version)
        )

    def rollback(self, reason: str = "") -> None:
        if self.status == PluginStatus.ROLLED_BACK:
            raise ValueError("Plugin already rolled back")
        self.status = PluginStatus.ROLLED_BACK
        self._events.append(
            PluginRolledBack(
                plugin_id=self.plugin_id,
                version=self.version,
                reason=reason,
            )
        )

    def get_uncommitted_events(self) -> list[Any]:
        return self._events.copy()

    def mark_events_committed(self) -> None:
        self._events.clear()
