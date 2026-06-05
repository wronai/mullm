"""nlp2dsl_resume — dopytania w trakcie rozmowy (nie tylko „kontynuuj”)."""

from __future__ import annotations

from unittest.mock import AsyncMock, patch

import pytest

from app import conductor
from app import nlp2dsl_bridge as nlp
from app.workspace import get_or_create


@pytest.mark.asyncio
async def test_nlp2dsl_resume_step_continues_conversation(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("PROMPT_ROUTER_MODE", "rules")
    session_id = "sess-nlp2dsl-resume"
    session = get_or_create(session_id)
    session.nlp2dsl_conversation_id = "conv-abc"
    session.nlp2dsl_status = "in_progress"

    fake_resp = {
        "conversation_id": "conv-abc",
        "status": "in_progress",
        "message": "Podaj kwotę faktury (PLN):",
        "missing": ["send_invoice.amount"],
        "form": {"fields": [{"name": "amount", "label": "Kwota"}]},
    }

    async def _health() -> bool:
        return True

    monkeypatch.setattr(nlp, "health", _health)
    with patch.object(nlp, "chat_message", new_callable=AsyncMock, return_value=fake_resp):
        out = await conductor.handle_turn(
            session_id=session_id,
            message="500 PLN",
            nlp_conversation_id="conv-abc",
            chat_mode="discuss",
            use_rag=False,
        )

    assert out.get("clarify") is not None
    assert out.get("nlp2dsl_conversation_id") == "conv-abc"
    assert "kwot" in (out.get("reply") or "").lower() or "PLN" in (out.get("reply") or "")


@pytest.mark.asyncio
async def test_nlp2dsl_resume_skipped_for_file_list(monkeypatch: pytest.MonkeyPatch) -> None:
    session_id = "sess-resume-file-list"
    session = get_or_create(session_id)
    session.nlp2dsl_conversation_id = "conv-old"
    session.nlp2dsl_status = "in_progress"

    with patch.object(
        nlp,
        "chat_message",
        new_callable=AsyncMock,
    ) as chat_msg:
        with patch(
            "app.conductor._mullm_file_list_turn",
            new_callable=AsyncMock,
            return_value={"reply": "lista", "intent": "file_list"},
        ):
            out = await conductor.handle_turn(
                session_id=session_id,
                message="lista plikow usera z rejestru access fabric",
                nlp_conversation_id="conv-old",
                chat_mode="discuss",
                use_rag=False,
            )
    chat_msg.assert_not_called()
    assert out.get("routing", {}).get("route") == "mullm_file_list"
