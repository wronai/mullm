"""Kontynuacja sesji — fast-path zamiast nlp2dsl unknown."""

from __future__ import annotations

import pytest

from app.chat import is_continue_intent
from app import conductor
from app import nlp2dsl_bridge as nlp


def test_is_continue_intent():
    assert is_continue_intent("kontynuuj")
    assert is_continue_intent("Kontynuuj!")
    assert is_continue_intent("continue")
    assert not is_continue_intent("kontynuuj refaktor")
    assert not is_continue_intent("lista plikow")


@pytest.mark.asyncio
async def test_continue_without_nlp_session_clarifies(monkeypatch):
    async def no_health() -> bool:
        return False

    monkeypatch.setattr(nlp, "health", no_health)

    out = await conductor.handle_turn(
        session_id="sess-continue-clarify",
        message="kontynuuj",
        nlp_conversation_id=None,
        chat_mode="discuss",
        use_rag=False,
    )

    assert "doprecyzuj" in out["reply"].lower() or "konkretn" in out["reply"].lower()
    assert "Nie rozpoznałem intencji" not in out["reply"]
    assert out.get("routing", {}).get("route") in ("workroom_hint", "mullm_continue")
