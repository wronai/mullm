from __future__ import annotations

import json
from pathlib import Path
from typing import Any


class ArchitectureCatalog:
    """Samopiszący katalog architektury mullm (domains, events, capabilities, policies)."""

    def __init__(self, root: Path | str | None = None) -> None:
        if root:
            self.root = Path(root)
        else:
            candidates = [
                Path(__file__).resolve().parents[4] / "catalog",
                Path("/app/catalog"),
                Path.cwd() / "catalog",
            ]
            self.root = next((p for p in candidates if p.exists()), candidates[0])
        self.root = Path(self.root)
        self._cache: dict[str, Any] = {}

    def _load_json(self, relative: str) -> Any:
        if relative in self._cache:
            return self._cache[relative]
        path = self.root / relative
        if not path.exists():
            return {}
        data = json.loads(path.read_text(encoding="utf-8"))
        self._cache[relative] = data
        return data

    @property
    def index(self) -> dict[str, Any]:
        return self._load_json("index.json")

    @property
    def domains(self) -> dict[str, Any]:
        return self._load_json("domains.json")

    @property
    def capabilities(self) -> dict[str, Any]:
        return self._load_json("capabilities.json")

    @property
    def services(self) -> dict[str, Any]:
        return self._load_json("services.json")

    @property
    def policies(self) -> dict[str, Any]:
        return self._load_json("policies.json")

    def list_events(self) -> list[dict[str, Any]]:
        events_dir = self.root / "events"
        if not events_dir.exists():
            return []
        items: list[dict[str, Any]] = []
        for path in sorted(events_dir.glob("*.json")):
            doc = json.loads(path.read_text(encoding="utf-8"))
            for event in doc.get("events", []):
                items.append(
                    {
                        "aggregate": doc.get("aggregate"),
                        "schema_version": doc.get("schema_version"),
                        **event,
                    }
                )
        return items

    def get_event_schema(self, event_type: str) -> dict[str, Any] | None:
        for item in self.list_events():
            if item.get("type") == event_type:
                return item
        return None

    def get_capability(self, capability_id: str) -> dict[str, Any] | None:
        for cap in self.capabilities.get("capabilities", []):
            if cap.get("id") == capability_id:
                return cap
        return None

    def as_graph(self) -> dict[str, Any]:
        """Topologia dla agentów / UI — usługi, domeny, zdarzenia."""
        return {
            "index": self.index,
            "domains": self.domains,
            "services": self.services,
            "capabilities": self.capabilities,
            "events": self.list_events(),
            "policy_rules": list(self.policies.get("rules", {}).keys()),
        }
