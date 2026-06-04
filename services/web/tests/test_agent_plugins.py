"""Plugin registry i most nlp2cmd."""

from __future__ import annotations

import pytest

from app.agent_plugins.nlp2cmd_plugin import Nlp2CmdPlugin, _translation_from_response
from app.agent_plugins.protocol import ShellTranslation
from app.agent_plugins.registry import get_plugin, list_plugins, translate_shell_nl


def test_registry_lists_builtin_plugins() -> None:
    ids = {p.plugin_id for p in list_plugins()}
    assert ids == {"nlp2cmd", "nlp2dsl"}


def test_translation_from_response() -> None:
    t = _translation_from_response(
        {"success": True, "command": "df -h", "confidence": 0.9, "domain": "shell"}
    )
    assert t is not None
    assert t.command == "df -h"


@pytest.mark.asyncio
async def test_translate_shell_nl_mocked(monkeypatch: pytest.MonkeyPatch) -> None:
    plugin = get_plugin("nlp2cmd")
    assert plugin is not None

    async def _health() -> bool:
        return True

    async def _translate(message: str, *, dsl: str = "shell") -> ShellTranslation | None:
        return ShellTranslation(command="df -h", confidence=0.88, domain="shell")

    monkeypatch.setattr(plugin, "health", _health)
    monkeypatch.setattr(plugin, "translate_shell", _translate)
    out = await translate_shell_nl("sprawdz miejsce na dysku")
    assert out is not None
    assert out.command == "df -h"


def test_nlp2cmd_plugin_metadata() -> None:
    p = Nlp2CmdPlugin()
    assert p.executor_agent_id == "shell_agent"
    assert "agent_shell" in p.ingress_steps
