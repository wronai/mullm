"""
Rejestr pluginów agentów — Mullm orchestruje, pluginy tłumaczą / planują.

Manifesty w integrations/*/agent_manifest.yaml (dokumentacja).
Implementacje w app/agent_plugins/*_plugin.py.
"""

from __future__ import annotations

from typing import Any

from app.agent_plugins.nlp2cmd_plugin import plugin as nlp2cmd_plugin
from app.agent_plugins.nlp2dsl_plugin import plugin as nlp2dsl_plugin
from app.agent_plugins.protocol import AgentPlugin, ShellTranslation

_PLUGINS: dict[str, AgentPlugin] = {
    nlp2cmd_plugin.plugin_id: nlp2cmd_plugin,
    nlp2dsl_plugin.plugin_id: nlp2dsl_plugin,
}

_bootstrap_done = False


def bootstrap() -> None:
    global _bootstrap_done
    _bootstrap_done = True


def list_plugins() -> list[AgentPlugin]:
    bootstrap()
    return list(_PLUGINS.values())


def get_plugin(plugin_id: str) -> AgentPlugin | None:
    bootstrap()
    return _PLUGINS.get(plugin_id)


def plugins_for_ingress_step(step: str) -> list[AgentPlugin]:
    bootstrap()
    return [p for p in _PLUGINS.values() if step in p.ingress_steps]


async def agents_status() -> list[dict[str, Any]]:
    """Health wszystkich zarejestrowanych pluginów (UI / CLI / smoke)."""
    out: list[dict[str, Any]] = []
    for p in list_plugins():
        healthy = await p.health()
        out.append(
            {
                "id": p.plugin_id,
                "title": p.title,
                "healthy": healthy,
                "executor_agent_id": p.executor_agent_id,
                "ingress_steps": sorted(p.ingress_steps),
                "route_kinds": sorted(p.route_kinds),
            }
        )
    return out


async def translate_shell_nl(
    message: str,
    *,
    plugin_id: str = "nlp2cmd",
    dsl: str = "shell",
) -> ShellTranslation | None:
    plugin = get_plugin(plugin_id)
    if not plugin:
        return None
    if not await plugin.health():
        return None
    return await plugin.translate_shell(message, dsl=dsl)
