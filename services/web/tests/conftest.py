"""Shared fixtures for mullm-web tests."""

from __future__ import annotations

from typing import Any

import pytest


@pytest.fixture(autouse=True)
def _deterministic_routing_env(monkeypatch: pytest.MonkeyPatch) -> None:
    """Testy jednostkowe: rules-only (hybrid testowany osobno)."""
    monkeypatch.setenv("PROMPT_ROUTER_MODE", "rules")
    monkeypatch.delenv("OPENROUTER_API_KEY", raising=False)
    monkeypatch.setenv("MULLM_SHELL_WAIT_SECONDS", "0")


@pytest.fixture
def fake_file_inventory() -> dict[str, Any]:
    return {
        "resources": [
            {
                "name": "RAG Smoke",
                "uri": "mullm://localfs/rag-smoke.txt",
                "status": "registered",
                "classification": "document",
            }
        ],
        "rag_documents": [
            {
                "name": "RAG Smoke",
                "uri": "mullm://localfs/rag-smoke.txt",
                "status": "indexed",
                "chunk_count": 1,
            }
        ],
        "errors": [],
    }


@pytest.fixture
def patch_file_inventory(monkeypatch: pytest.MonkeyPatch, fake_file_inventory: dict[str, Any]):
    import app.chat as chat_mod

    async def _inventory() -> dict[str, Any]:
        return fake_file_inventory

    monkeypatch.setattr(chat_mod, "fetch_file_inventory", _inventory)


@pytest.fixture
def patch_nlp2dsl_down(monkeypatch: pytest.MonkeyPatch):
    import app.nlp2dsl_bridge as nlp

    async def _health() -> bool:
        return False

    monkeypatch.setattr(nlp, "health", _health)


@pytest.fixture
def patch_nlp2cmd_translate(monkeypatch: pytest.MonkeyPatch):
    from app import conductor
    from app.agent_plugins.protocol import ShellTranslation
    from app.agent_plugins import registry as reg

    async def _translate(message: str, *, plugin_id: str = "nlp2cmd", dsl: str = "shell"):
        if "dysk" in message.lower() or "miejsce" in message.lower():
            return ShellTranslation(command="df -h", confidence=0.9, domain="shell")
        return None

    monkeypatch.setattr(reg, "translate_shell_nl", _translate)
    monkeypatch.setattr(conductor, "translate_shell_nl", _translate)


@pytest.fixture
def patch_shell_task(monkeypatch: pytest.MonkeyPatch):
    from app import conductor

    async def _create(session_id: str, *, shell: str, **kwargs):
        return {"ok": True, "task_id": "t-test-shell"}

    monkeypatch.setattr(conductor, "_create_shell_task", _create)
