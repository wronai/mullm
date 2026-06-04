"""Kontrakt pluginów agentów zewnętrznych (Mullm = orchestrator, nie wykonawca)."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Protocol, runtime_checkable


@dataclass(frozen=True)
class ShellTranslation:
    """Wynik tłumaczenia NL → polecenie shell (bez wykonania)."""

    command: str
    confidence: float = 0.0
    domain: str = ""
    intent: str = ""
    raw: dict[str, Any] = field(default_factory=dict)


@runtime_checkable
class AgentPlugin(Protocol):
    """Plugin łączący Mullm z usługą agenta (HTTP/CLI w sibling repo)."""

    @property
    def plugin_id(self) -> str:
        """Stały identyfikator, np. nlp2cmd, nlp2dsl."""

    @property
    def title(self) -> str:
        ...

    @property
    def executor_agent_id(self) -> str:
        """Agent Mullm wykonujący wynik (NATS shell-agent, coordinator, …)."""

    @property
    def ingress_steps(self) -> frozenset[str]:
        """Kroki pipeline, które ten plugin obsługuje (np. agent_shell)."""

    @property
    def route_kinds(self) -> frozenset[str]:
        """Trasy prompt_router powiązane z pluginem."""

    async def health(self) -> bool:
        ...

    async def translate_shell(self, message: str, *, dsl: str = "shell") -> ShellTranslation | None:
        """NL → polecenie; None gdy nieobsługiwane lub błąd."""
