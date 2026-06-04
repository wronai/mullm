"""
Ładowanie polityki routingu (YAML) — kolejność ingress, mapowanie agentów.
"""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import yaml

_DEFAULT_ORDER = ["rag_probe", "rules", "nlp2dsl", "rag_answer"]

_VALID_STEPS = frozenset(_DEFAULT_ORDER)


@dataclass
class RagProbeSettings:
    enabled: bool = True
    min_hits: int = 1
    search_limit: int = 4
    answer_on_hit: bool = False
    skip_file_list_intent: bool = True
    skip_shell_prefix: bool = True


@dataclass
class RoutingPolicy:
    version: int = 1
    ingress_order: list[str] = field(default_factory=lambda: list(_DEFAULT_ORDER))
    agents_default: str = "shell_agent"
    agents_by_route: dict[str, str] = field(default_factory=dict)
    prefer_session_agent: bool = True
    rag_probe: RagProbeSettings = field(default_factory=RagProbeSettings)
    mode_overrides: dict[str, list[str]] = field(default_factory=dict)
    source_path: str = ""

    def ingress_for_mode(self, chat_mode: str) -> list[str]:
        override = self.mode_overrides.get(chat_mode)
        if override:
            return [s for s in override if s in _VALID_STEPS]
        return list(self.ingress_order)

    def agent_for_route(
        self,
        route: str,
        *,
        session_agent_id: str | None = None,
    ) -> str:
        if session_agent_id and self.prefer_session_agent:
            return session_agent_id
        return self.agents_by_route.get(route) or self.agents_default

    def to_dict(self) -> dict[str, Any]:
        return {
            "version": self.version,
            "ingress_order": self.ingress_order,
            "mode_overrides": self.mode_overrides,
            "agents": {
                "default": self.agents_default,
                "by_route": self.agents_by_route,
                "prefer_session_agent": self.prefer_session_agent,
            },
            "rag_probe": {
                "enabled": self.rag_probe.enabled,
                "min_hits": self.rag_probe.min_hits,
                "search_limit": self.rag_probe.search_limit,
                "answer_on_hit": self.rag_probe.answer_on_hit,
                "skip_file_list_intent": self.rag_probe.skip_file_list_intent,
                "skip_shell_prefix": self.rag_probe.skip_shell_prefix,
            },
            "source_path": self.source_path,
        }


_cached: RoutingPolicy | None = None


def _policy_path() -> Path:
    env = os.getenv("MULLM_ROUTING_POLICY_PATH", "").strip()
    if env:
        return Path(env)
    return Path(__file__).resolve().parent.parent / "data" / "routing_policy.yaml"


def _parse_policy(data: dict[str, Any], path: Path) -> RoutingPolicy:
    agents = _parse_agents(data.get("agents") or {})
    rp = data.get("rag_probe") or {}
    return RoutingPolicy(
        version=int(data.get("version") or 1),
        ingress_order=_valid_ingress_order(data.get("ingress_order")),
        agents_default=agents["default"],
        agents_by_route=agents["by_route"],
        prefer_session_agent=agents["prefer_session_agent"],
        rag_probe=_parse_rag_probe(rp),
        mode_overrides=_parse_mode_overrides(data.get("mode_overrides") or {}),
        source_path=str(path),
    )


def _parse_agents(raw_agents: dict[str, Any]) -> dict[str, Any]:
    by_route = dict(raw_agents.get("by_route") or {})
    return {
        "default": str(raw_agents.get("default") or "shell_agent"),
        "by_route": {str(k): str(v) for k, v in by_route.items()},
        "prefer_session_agent": bool(raw_agents.get("prefer_session_agent", True)),
    }


def _valid_ingress_order(raw_order: Any) -> list[str]:
    order = raw_order or _DEFAULT_ORDER
    return [step for step in order if step in _VALID_STEPS] or list(_DEFAULT_ORDER)


def _parse_mode_overrides(overrides: dict[str, Any]) -> dict[str, list[str]]:
    parsed: dict[str, list[str]] = {}
    for mode, spec in overrides.items():
        parsed[str(mode)] = _valid_override_steps(spec)
    return parsed


def _valid_override_steps(spec: Any) -> list[str]:
    raw_steps: list[Any] = []
    if isinstance(spec, list):
        raw_steps = spec
    elif isinstance(spec, dict):
        raw_steps = list(spec.get("ingress_order") or [])
    return [step for step in raw_steps if step in _VALID_STEPS]


def _parse_rag_probe(raw: dict[str, Any]) -> RagProbeSettings:
    return RagProbeSettings(
        enabled=bool(raw.get("enabled", True)),
        min_hits=int(raw.get("min_hits", 1)),
        search_limit=int(raw.get("search_limit", 4)),
        answer_on_hit=bool(raw.get("answer_on_hit", False)),
        skip_file_list_intent=bool(raw.get("skip_file_list_intent", True)),
        skip_shell_prefix=bool(raw.get("skip_shell_prefix", True)),
    )


def load_policy(*, reload: bool = False) -> RoutingPolicy:
    global _cached
    if _cached is not None and not reload:
        return _cached
    path = _policy_path()
    if not path.is_file():
        _cached = RoutingPolicy(source_path="(built-in default)")
        return _cached
    with path.open(encoding="utf-8") as f:
        data = yaml.safe_load(f) or {}
    _cached = _parse_policy(data, path)
    return _cached
