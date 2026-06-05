"""Ingress nlp2dsl_orient — orientacja przed regułami."""

from __future__ import annotations

from unittest.mock import AsyncMock, patch

import pytest

from app import conductor


@pytest.mark.asyncio
async def test_orient_step_host_file_list(monkeypatch):
    orient_payload = {
        "category": "file_list_host",
        "suggested_action": "mullm_shell_task",
        "confidence": 0.91,
        "reason_codes": ["orientation_file_list_host"],
        "shell_command": "ls -la /host-home",
        "list_scope": "user",
        "connector": "mullm",
    }

    async def fake_shell_task(session_id, *, shell, **kwargs):
        return {"ok": True, "task_id": "t-orient-1"}

    with (
        patch(
            "app.conductor.nlp.orient_direct",
            new_callable=AsyncMock,
            return_value=orient_payload,
        ),
        patch("app.conductor._create_shell_task", new_callable=AsyncMock, side_effect=fake_shell_task),
        patch("app.conductor.chat_service.wait_for_task_terminal", new_callable=AsyncMock, return_value=None),
    ):
        out = await conductor.handle_turn(
            session_id="orient-test",
            message="lista plikow usera",
            nlp_conversation_id=None,
            use_rag=False,
        )

    routing = out.get("routing") or {}
    assert routing.get("route") == "nlp2cmd_shell"
    assert routing.get("policy_flags", {}).get("nlp2dsl_orientation", {}).get("category") == "file_list_host"
    assert out.get("nlp2dsl_routing", {}).get("source") == "orientation"


@pytest.mark.asyncio
async def test_orient_step_registry_file_list(monkeypatch, patch_file_inventory):
    orient_payload = {
        "category": "file_list_registry",
        "suggested_action": "mullm_list_files",
        "confidence": 0.93,
        "reason_codes": ["orientation_file_list_registry"],
        "list_scope": "user",
        "connector": "mullm",
    }

    with patch(
        "app.conductor.nlp.orient_direct",
        new_callable=AsyncMock,
        return_value=orient_payload,
    ):
        out = await conductor.handle_turn(
            session_id="orient-registry",
            message="lista plikow usera z rejestru",
            nlp_conversation_id=None,
            use_rag=False,
        )

    assert (out.get("routing") or {}).get("route") == "mullm_file_list"
    assert out.get("intent") == "file_list"


@pytest.mark.asyncio
async def test_orient_local_fallback_host_list(monkeypatch, patch_file_inventory):
    from app.local_orient import orient_query

    with patch(
        "app.conductor.nlp.orient_direct",
        new_callable=AsyncMock,
        side_effect=lambda text, **kw: orient_query(text, connector=kw.get("connector", "mullm")).to_dict(),
    ), patch(
        "app.conductor._create_shell_task",
        new_callable=AsyncMock,
        return_value={"ok": True, "task_id": "t-local"},
    ), patch(
        "app.conductor.chat_service.wait_for_task_terminal",
        new_callable=AsyncMock,
        return_value=None,
    ):
        out = await conductor.handle_turn(
            session_id="orient-local",
            message="lista plikow usera",
            nlp_conversation_id=None,
            use_rag=False,
        )
    routing = out.get("routing") or {}
    assert routing.get("route") == "nlp2cmd_shell"
    assert routing.get("nlp2dsl_orient") is True
    assert "nlp2dsl orient" in (out.get("reply") or "")


@pytest.mark.asyncio
async def test_orient_registry_falls_through_rules_when_unknown_category(
    monkeypatch, patch_file_inventory
):
    with patch(
        "app.conductor.nlp.orient_direct",
        new_callable=AsyncMock,
        return_value={"category": "unknown", "confidence": 0.3, "source": "local_orient"},
    ):
        out = await conductor.handle_turn(
            session_id="orient-fallback",
            message="lista plikow usera z rejestru access fabric",
            nlp_conversation_id=None,
            use_rag=False,
        )

    assert (out.get("routing") or {}).get("route") == "mullm_file_list"
