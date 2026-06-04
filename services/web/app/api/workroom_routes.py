from __future__ import annotations

from app import agent_workroom
from app.api.models import WorkroomMessage, WorkroomStart
from fastapi import APIRouter, HTTPException

router = APIRouter()


@router.post("/agent-workroom/session")
async def workroom_start(body: WorkroomStart | None = None):
    payload = body or WorkroomStart()
    session = agent_workroom.create_workroom(user_session_id=payload.user_session_id)
    return {"ok": True, **session.to_dict(), "catalog": agent_workroom.workroom_catalog()}


@router.get("/agent-workroom/{workroom_id}")
async def workroom_get(workroom_id: str):
    session = _workroom_or_404(workroom_id)
    return session.to_dict()


@router.get("/agent-workroom/{workroom_id}/export")
async def workroom_export(workroom_id: str):
    """Pełna zawartość workroom (wątek, ledger, odpowiedź) — pole text do schowka."""
    session = _workroom_or_404(workroom_id)
    text = agent_workroom.format_workroom_export(session)
    return {
        "workroom_id": workroom_id,
        "text": text,
        "goal": session.goal,
        "status": session.status,
        "ledger_entries": len(session.ledger),
        "thread_messages": len(session.agent_thread),
    }


@router.post("/agent-workroom/{workroom_id}/run")
async def workroom_run(workroom_id: str, body: WorkroomMessage):
    result = await agent_workroom.run_workroom(
        workroom_id,
        body.message,
        wait_for_confirmation=body.wait_for_confirmation,
    )
    if not result.get("ok"):
        raise HTTPException(status_code=400, detail=result.get("error", "run failed"))
    return result


def _workroom_or_404(workroom_id: str) -> agent_workroom.WorkroomSession:
    session = agent_workroom.get_workroom(workroom_id)
    if not session:
        raise HTTPException(status_code=404, detail="workroom not found")
    return session
