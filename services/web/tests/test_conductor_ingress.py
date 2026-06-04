"""Ingress pipeline — file list nie woła nlp2dsl."""

from __future__ import annotations

import pytest

from app import conductor
from app import nlp2dsl_bridge as nlp


@pytest.mark.asyncio
async def test_file_list_pipeline_skips_nlp2dsl(monkeypatch):
    nlp_calls: list[str] = []

    async def fake_health() -> bool:
        return True

    async def fake_chat_start(text: str) -> dict:
        nlp_calls.append(text)
        return {"conversation_id": "x", "status": "in_progress", "message": "should not run"}

    async def fake_file_list(**kwargs):
        return {
            "reply": "pliki: 0",
            "intent": "file_list",
            "routing": {"route": "mullm_file_list"},
        }

    monkeypatch.setattr(nlp, "health", fake_health)
    monkeypatch.setattr(nlp, "chat_start", fake_chat_start)
    monkeypatch.setattr(nlp, "chat_message", fake_chat_start)
    monkeypatch.setattr(conductor, "_mullm_file_list_turn", fake_file_list)

    out = await conductor.handle_turn(
        session_id="sess-file-list-skip",
        message="lista plikow usera",
        nlp_conversation_id=None,
        chat_mode="discuss",
        use_rag=False,
    )

    assert nlp_calls == []
    assert out.get("intent") == "file_list"
    assert out.get("routing", {}).get("route") == "mullm_file_list"


@pytest.mark.asyncio
async def test_agent_shell_uses_nlp2cmd_not_nlp2dsl(
    monkeypatch,
    patch_nlp2cmd_translate,
    patch_nlp2dsl_down,
):
    nlp_calls: list[str] = []
    task_calls: list[str] = []

    async def fake_chat_start(text: str) -> dict:
        nlp_calls.append(text)
        return {"conversation_id": "x"}

    async def fake_create_task(session_id, *, shell: str, **kwargs):
        task_calls.append(shell)
        return {"ok": True, "task_id": "t-shell-1"}

    import app.nlp2dsl_bridge as nlp

    monkeypatch.setattr(nlp, "chat_start", fake_chat_start)
    monkeypatch.setattr(conductor, "_create_shell_task", fake_create_task)

    out = await conductor.handle_turn(
        session_id="sess-nlp2cmd-shell",
        message="sprawdz miejsce na dysku",
        nlp_conversation_id=None,
        chat_mode="discuss",
        use_rag=False,
    )

    assert nlp_calls == []
    assert task_calls == ["df -h"]
    routing = out.get("routing") or {}
    assert routing.get("route") == "nlp2cmd_shell"
    assert routing.get("shell_plugin") == "nlp2cmd"
    assert routing.get("nlp2dsl_skipped") is True
