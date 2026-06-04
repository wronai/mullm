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
