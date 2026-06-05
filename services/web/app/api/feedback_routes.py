from __future__ import annotations

from fastapi import APIRouter, HTTPException

from app import routing_feedback
from app.api.models import RoutingFeedbackBody
from app.workspace import get_or_create

router = APIRouter()


@router.post("/routing/feedback")
async def routing_feedback_post(body: RoutingFeedbackBody):
    """
    Ocena odpowiedzi asystenta (powiązana z turn_id z routing).
    Przy bad/partial tworzy improvement_ticket z sugestiami poprawy polityki.
    """
    get_or_create(body.session_id)
    try:
        return routing_feedback.record_feedback(
            session_id=body.session_id,
            turn_id=body.turn_id,
            rating=body.rating,
            expected_route=body.expected_route,
            expected_reply_hint=body.expected_reply_hint,
            improvement_notes=body.improvement_notes,
            tags=body.tags,
            user_message=body.user_message,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.get("/routing/feedback")
async def routing_feedback_list(session_id: str | None = None, limit: int = 50):
    return {
        "items": routing_feedback.list_feedback(session_id=session_id, limit=limit),
    }


@router.get("/routing/learnings")
async def routing_learnings(limit: int = 20):
    """Agregat ocen → propozycje user_expectations i otwarte tickety poprawy."""
    return routing_feedback.aggregate_learnings(limit=limit)


@router.get("/routing/improvements")
async def routing_improvements(status: str = "open", limit: int = 30):
    return {
        "items": routing_feedback.list_improvement_tickets(status=status, limit=limit),
    }
