"""Ingress pipeline — orient / file list / shell."""

from __future__ import annotations

from unittest.mock import AsyncMock, patch

import pytest

from app import conductor
from app import nlp2dsl_bridge as nlp


@pytest.mark.asyncio
async def test_orient_host_file_list_skips_nlp2dsl_chat(monkeypatch):
    nlp_calls: list[str] = []

    async def fake_chat_start(text: str) -> dict:
        nlp_calls.append(text)
        return {"conversation_id": "x", "status": "in_progress", "message": "should not run"}

    monkeypatch.setattr(nlp, "chat_start", fake_chat_start)
    monkeypatch.setattr(nlp, "chat_message", fake_chat_start)

    with (
        patch("app.conductor._create_shell_task", new_callable=AsyncMock, return_value={"ok": True, "task_id": "t1"}),
        patch("app.conductor.chat_service.wait_for_task_terminal", new_callable=AsyncMock, return_value=None),
    ):
        out = await conductor.handle_turn(
            session_id="sess-orient-host",
            message="lista plikow usera",
            nlp_conversation_id=None,
            chat_mode="discuss",
            use_rag=False,
        )

    assert nlp_calls == []
    assert out.get("routing", {}).get("route") == "nlp2cmd_shell"
    assert out.get("routing", {}).get("nlp2dsl_orient") is True


@pytest.mark.asyncio
async def test_registry_file_list_via_orient(monkeypatch, patch_file_inventory):
    nlp_calls: list[str] = []

    async def fake_chat_start(text: str) -> dict:
        nlp_calls.append(text)
        return {"conversation_id": "x"}

    monkeypatch.setattr(nlp, "chat_start", fake_chat_start)

    out = await conductor.handle_turn(
        session_id="sess-file-list-registry",
        message="lista plikow usera z rejestru access fabric",
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
    assert routing.get("nlp2dsl_orient") is True
    assert routing.get("orientation_source") in ("local_orient", "nlp2dsl_service", "nlp2dsl_backend")
    assert routing.get("shell_translation_source") == "nlp2cmd"


@pytest.mark.asyncio
async def test_jspaint_routes_via_nlp2cmd_run(monkeypatch, patch_nlp2dsl_down):
    nlp_calls: list[str] = []
    task_calls: list[str] = []

    async def fake_chat_start(text: str) -> dict:
        nlp_calls.append(text)
        return {"conversation_id": "x"}

    async def fake_create_task(session_id, *, shell: str, **kwargs):
        task_calls.append(shell)
        return {"ok": True, "task_id": "t-jspaint-1"}

    import app.nlp2dsl_bridge as nlp
    from app.agent_plugins.protocol import ShellTranslation
    from app.agent_plugins import registry as reg

    async def fake_translate(message: str, **kwargs):
        if "jspaint" in message.lower():
            return ShellTranslation(
                command="nlp2cmd -r 'wejdz na jspaint.app i narysuj biedronke'",
                confidence=0.95,
                domain="multi_step",
                intent="canvas_blueprint",
            )
        return None

    monkeypatch.setattr(nlp, "chat_start", fake_chat_start)
    monkeypatch.setattr(reg, "translate_shell_nl", fake_translate)
    monkeypatch.setattr(conductor, "translate_shell_nl", fake_translate)
    monkeypatch.setattr(conductor, "_create_shell_task", fake_create_task)

    out = await conductor.handle_turn(
        session_id="sess-jspaint",
        message="wejdz na jspaint.app i narysuj biedronke",
        nlp_conversation_id=None,
        chat_mode="discuss",
        use_rag=False,
    )

    assert nlp_calls == []
    assert task_calls == ["nlp2cmd -r 'wejdz na jspaint.app i narysuj biedronke'"]
    routing = out.get("routing") or {}
    assert routing.get("route") == "nlp2cmd_shell"
    assert routing.get("shell_plugin") in ("nlp2cmd", "nlp2dsl_orient")
