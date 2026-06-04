"""Pluginy agentów zewnętrznych (nlp2cmd, nlp2dsl, …)."""

from app.agent_plugins.registry import (
    agents_status,
    bootstrap,
    get_plugin,
    list_plugins,
    plugins_for_ingress_step,
    translate_shell_nl,
)

__all__ = [
    "agents_status",
    "bootstrap",
    "get_plugin",
    "list_plugins",
    "plugins_for_ingress_step",
    "translate_shell_nl",
]
