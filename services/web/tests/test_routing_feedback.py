"""Ocena routingu i tickety poprawy."""

from __future__ import annotations

from uuid import uuid4

import pytest

from app import chat as chat_service
from app import routing_feedback
from app.workspace import new_session


@pytest.fixture
def feedback_store(tmp_path, monkeypatch):
    monkeypatch.setenv("MULLM_FEEDBACK_DIR", str(tmp_path))
    return tmp_path


def test_record_good_feedback(feedback_store) -> None:
    session = new_session()
    chat_service._append(session.session_id, "user", "lista plikow usera")
    chat_service._append(
        session.session_id,
        "assistant",
        "ok",
        routing={"route": "mullm_file_list", "turn_id": "turn-1"},
    )
    out = routing_feedback.record_feedback(
        session_id=session.session_id,
        turn_id="turn-1",
        rating="good",
    )
    assert out["rating"] == "good"
    assert out["improvement_ticket_id"] is None
    items = routing_feedback.list_feedback(session_id=session.session_id)
    assert len(items) == 1


def test_record_bad_creates_improvement_ticket(feedback_store) -> None:
    session = new_session()
    chat_service._append(session.session_id, "user", "lista plikow usera")
    chat_service._append(
        session.session_id,
        "assistant",
        "zła",
        routing={"route": "mullm_shell", "turn_id": "turn-2"},
    )
    out = routing_feedback.record_feedback(
        session_id=session.session_id,
        turn_id="turn-2",
        rating="bad",
        expected_route="mullm_file_list",
        improvement_notes="Powinna być lista z rejestru",
    )
    assert out["improvement_ticket_id"]
    assert out["improvement_ticket"]["suggested_actions"]
    tickets = routing_feedback.list_improvement_tickets()
    assert len(tickets) == 1


def test_aggregate_learnings_proposes_expectation(feedback_store) -> None:
    session = new_session()
    for _ in range(2):
        routing_feedback.record_feedback(
            session_id=session.session_id,
            turn_id=str(uuid4()),
            rating="bad",
            user_message="lista plikow usera",
            routing={"route": "mullm_shell"},
            expected_route="mullm_file_list",
        )
    learnings = routing_feedback.aggregate_learnings()
    assert learnings["stats"]["negative_total"] >= 2
    assert learnings["proposals"]
