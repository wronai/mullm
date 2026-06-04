from __future__ import annotations

from typing import Any

import httpx
from fastapi import APIRouter, HTTPException

from app import chat as chat_service
from app import workspace as workspace_service
from app.api.config import ORCHESTRATOR_URL
from app.api.models import (
    ConfirmTicketBody,
    CreateFromDraftBody,
    CreateTaskBody,
    SessionRef,
)
from app.tickets import enrich_task

router = APIRouter()


@router.post("/tasks")
async def create_task(body: CreateTaskBody):
    if body.session_id and body.ticket_id:
        workspace_service.attach_context(body.session_id, ticket_id=body.ticket_id)
    result = await chat_service.create_task(
        title=body.title,
        description=body.description,
        shell_command=body.shell_command,
        auto_assign=body.auto_assign and not body.wait_for_confirmation,
        wait_for_confirmation=body.wait_for_confirmation,
        priority=body.priority,
    )
    if not result.get("ok"):
        raise HTTPException(status_code=400, detail=result.get("error", "task failed"))
    if body.session_id:
        session = workspace_service.get_or_create(body.session_id)
        session.add_event("TaskCreatedFromChat", body.title, task_id=result.get("task_id"))
    return result


@router.post("/tasks/create")
async def create_task_from_draft(body: CreateFromDraftBody):
    result = await workspace_service.create_task_from_draft(
        body.session_id,
        draft=body.draft,
        run=False,
        wait_for_confirmation=body.wait_for_confirmation,
    )
    if not result.get("ok"):
        raise HTTPException(status_code=400, detail=result.get("error", "create failed"))
    return result


@router.post("/tasks/create-and-run")
async def create_and_run_task(body: CreateFromDraftBody):
    result = await workspace_service.create_and_run(
        body.session_id,
        draft=body.draft,
        wait_for_confirmation=body.wait_for_confirmation,
    )
    if not result.get("ok"):
        raise HTTPException(status_code=400, detail=result.get("error", "run failed"))
    return result


@router.get("/tickets")
async def list_tickets(session_id: str | None = None, view: str = "active"):
    board = await workspace_service.fetch_live_board()
    archived = _archived_ids(session_id)
    items = [enrich_task(t, archived_ids=archived) for t in board.get("tasks") or []]
    return {"items": _filter_tickets_view(items, view)}


@router.get("/tickets/meta/statuses")
async def ticket_statuses():
    from app.tickets import STATUS_UI

    return {"items": STATUS_UI}


@router.get("/tickets/{task_id}")
async def get_ticket(task_id: str, session_id: str | None = None):
    board = await workspace_service.fetch_live_board()
    archived = _archived_ids(session_id)
    for row in board.get("tasks") or []:
        if row.get("task_id") == task_id:
            return enrich_task(row, archived_ids=archived)
    raise HTTPException(status_code=404, detail="ticket not found")


@router.post("/tickets/{task_id}/confirm")
async def confirm_ticket(task_id: str, body: ConfirmTicketBody | None = None):
    session_id = (body or ConfirmTicketBody()).session_id
    task, agent_id = await _confirmable_task_and_agent(task_id)
    shell = workspace_service._extract_shell_command(
        task.get("description") or task.get("title") or ""
    )
    await _assign_ticket(task_id, agent_id, shell)
    if session_id:
        session = workspace_service.get_or_create(session_id)
        session.add_event("TaskConfirmed", f"Uruchomiono {task_id[:8]}", task_id=task_id)
    return {"ok": True, "task_id": task_id, "agent_id": agent_id, "shell_command": shell}


@router.post("/tickets/{task_id}/archive")
async def archive_ticket(task_id: str, body: SessionRef):
    return workspace_service.archive_task(body.session_id, task_id)


@router.post("/tickets/{task_id}/link")
async def link_ticket(task_id: str, body: SessionRef):
    return {"context": workspace_service.link_ticket(body.session_id, task_id)}


def _archived_ids(session_id: str | None) -> set[str]:
    if not session_id:
        return set()
    session = workspace_service.get_or_create(session_id)
    return set(session.context.archived_task_ids)


def _filter_tickets_view(items: list[dict[str, Any]], view: str) -> list[dict[str, Any]]:
    predicate = _TICKET_VIEW_FILTERS.get(view)
    return [item for item in items if predicate(item)] if predicate else items


def _is_archived_ticket(item: dict[str, Any]) -> bool:
    return item["status_key"] == "archived"


def _is_active_ticket(item: dict[str, Any]) -> bool:
    return item["status_key"] != "archived"


_TICKET_VIEW_FILTERS = {
    "archived": _is_archived_ticket,
    "active": _is_active_ticket,
}


async def _confirmable_task_and_agent(task_id: str) -> tuple[dict[str, Any], str]:
    board = await workspace_service.fetch_live_board()
    task = _task_from_board(board, task_id)
    _assert_confirmable_task(task)
    agent_id = _first_idle_agent_id(board)
    if not agent_id:
        raise HTTPException(status_code=409, detail="brak wolnego agenta")
    return task, agent_id


def _task_from_board(board: dict[str, Any], task_id: str) -> dict[str, Any]:
    task = next(
        (item for item in (board.get("tasks") or []) if item.get("task_id") == task_id),
        None,
    )
    if not task:
        raise HTTPException(status_code=404, detail="ticket not found")
    return task


def _assert_confirmable_task(task: dict[str, Any]) -> None:
    status = (task.get("status") or "pending").lower()
    if status not in ("pending",):
        raise HTTPException(status_code=400, detail="ticket nie jest w kolejce")


def _first_idle_agent_id(board: dict[str, Any]) -> str | None:
    for agent in board.get("agents") or []:
        if (agent.get("status") or "").lower() == "idle":
            return agent.get("agent_id")
    return None


async def _assign_ticket(task_id: str, agent_id: str, shell: str | None) -> None:
    payload: dict[str, Any] = {"task_id": task_id, "agent_id": agent_id}
    if shell:
        payload["command"] = shell
    async with httpx.AsyncClient(timeout=30.0) as client:
        resp = await client.post(
            f"{ORCHESTRATOR_URL}/api/commands/tasks/assign",
            json=payload,
        )
        if resp.status_code >= 400:
            raise HTTPException(status_code=resp.status_code, detail=resp.text)
