from __future__ import annotations

import os
from typing import Any

import httpx
from fastapi import APIRouter, File, Form, HTTPException, UploadFile
from pydantic import BaseModel, Field

from app import agent_workroom
from app import chat as chat_service
from app import resource_areas
from app import workspace as workspace_service
from app.tickets import enrich_task, status_meta, ticket_uri, ticket_web_path

router = APIRouter()

ORCHESTRATOR_URL = os.getenv(
    "ORCHESTRATOR_URL",
    os.getenv("MULLM_ORCHESTRATOR_URL", "http://orchestrator:8000"),
)
PROJECTOR_URL = os.getenv(
    "PROJECTOR_URL",
    os.getenv("MULLM_PROJECTOR_URL", "http://projector:8000"),
)

chat_service.ORCHESTRATOR_URL = ORCHESTRATOR_URL


class ChatSessionStart(BaseModel):
    ticket_id: str = ""
    project: str = ""


class ChatMessage(BaseModel):
    session_id: str | None = None
    message: str = ""
    mode: str = "discuss"  # discuss | create_task | run_task | search_context
    use_rag: bool = True
    form_values: dict[str, Any] | None = None
    wait_for_confirmation: bool = False


class TaskDraftRequest(BaseModel):
    session_id: str
    message: str


class CreateTaskBody(BaseModel):
    session_id: str | None = None
    title: str
    description: str = ""
    shell_command: str | None = None
    auto_assign: bool = True
    wait_for_confirmation: bool = False
    priority: str = "medium"
    ticket_id: str | None = None


class CreateFromDraftBody(BaseModel):
    session_id: str
    draft: dict[str, Any] | None = None
    run: bool = False
    wait_for_confirmation: bool = False


class ConfirmTicketBody(BaseModel):
    session_id: str = ""


class ContextAttachBody(BaseModel):
    session_id: str
    ticket_id: str | None = None
    project: str | None = None
    branch: str | None = None
    agent_id: str | None = None
    resource_id: str | None = None
    uri: str | None = None
    note: str | None = None
    filename: str | None = None


@router.post("/chat/session")
async def start_chat_session(body: ChatSessionStart | None = None):
    payload = body or ChatSessionStart()
    session = workspace_service.new_session(
        ticket_id=payload.ticket_id,
        project=payload.project,
    )
    return workspace_service.workspace_state(session.session_id)


@router.get("/chat/session")
async def get_chat_session(session_id: str | None = None):
    if session_id:
        return workspace_service.workspace_state(session_id)
    session = workspace_service.new_session()
    return workspace_service.workspace_state(session.session_id)


@router.get("/workspace/state")
async def workspace_state(session_id: str):
    board = await workspace_service.fetch_live_board()
    state = workspace_service.workspace_state(session_id)
    return {**state, "board": board}


@router.post("/chat/message")
async def chat_message(body: ChatMessage):
    session = workspace_service.get_or_create(body.session_id)
    if body.form_values and not (body.message or "").strip():
        from app.conductor import handle_turn

        outcome = await handle_turn(
            session_id=session.session_id,
            message="",
            nlp_conversation_id=session.nlp2dsl_conversation_id,
            scope_files=list(session.context.file_names),
            scope_uris=list(session.context.uris),
            form_values=body.form_values,
            wait_for_confirmation=body.wait_for_confirmation,
        )
        if outcome.get("nlp2dsl_conversation_id"):
            session.nlp2dsl_conversation_id = outcome["nlp2dsl_conversation_id"]
        return outcome
    outcome = await workspace_service.handle_chat_message(
        session_id=session.session_id,
        message=body.message,
        mode=body.mode,
        use_rag=body.use_rag,
        wait_for_confirmation=body.wait_for_confirmation,
    )
    if outcome.get("error"):
        raise HTTPException(status_code=400, detail=outcome["error"])
    return outcome


@router.post("/tasks/draft")
async def task_draft(body: TaskDraftRequest):
    draft = workspace_service.propose_task_draft(body.session_id, body.message)
    return {"draft": draft, "session_id": body.session_id}


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


@router.post("/context/attach")
async def context_attach(body: ContextAttachBody):
    ctx = workspace_service.attach_context(
        body.session_id,
        ticket_id=body.ticket_id,
        project=body.project,
        branch=body.branch,
        agent_id=body.agent_id,
        resource_id=body.resource_id,
        uri=body.uri,
        note=body.note,
        filename=body.filename,
    )
    return {"context": ctx}


@router.post("/files/upload")
async def upload_files(
    session_id: str = Form(""),
    files: list[UploadFile] = File(...),
    classification: str = Form("document"),
):
    uploaded: list[dict[str, Any]] = []
    async with httpx.AsyncClient(timeout=120.0) as client:
        for upload in files:
            content = await upload.read()
            if not content:
                continue
            resp = await client.post(
                f"{ORCHESTRATOR_URL}/api/access/resources/upload",
                files={
                    "file": (
                        upload.filename,
                        content,
                        upload.content_type or "application/octet-stream",
                    )
                },
                data={"classification": classification},
            )
            if resp.status_code >= 400:
                uploaded.append(
                    {"filename": upload.filename, "ok": False, "error": resp.text}
                )
            else:
                payload = resp.json()
                item = {
                    "filename": upload.filename,
                    "ok": True,
                    "resource_id": payload.get("resource_id"),
                    "uri": payload.get("uri"),
                }
                uploaded.append(item)
                if session_id:
                    workspace_service.attach_context(
                        session_id,
                        resource_id=payload.get("resource_id"),
                        uri=payload.get("uri"),
                        filename=upload.filename,
                    )
    return {"items": uploaded}


@router.get("/board")
async def board_snapshot():
    return await workspace_service.fetch_live_board()


@router.get("/tickets")
async def list_tickets(session_id: str | None = None, view: str = "active"):
    board = await workspace_service.fetch_live_board()
    archived: set[str] = set()
    if session_id:
        session = workspace_service.get_or_create(session_id)
        archived = set(session.context.archived_task_ids)
    items = [enrich_task(t, archived_ids=archived) for t in board.get("tasks") or []]
    if view == "archived":
        items = [t for t in items if t["status_key"] == "archived"]
    elif view == "active":
        items = [t for t in items if t["status_key"] != "archived"]
    return {"items": items}


@router.get("/tickets/{task_id}")
async def get_ticket(task_id: str, session_id: str | None = None):
    board = await workspace_service.fetch_live_board()
    archived: set[str] = set()
    if session_id:
        session = workspace_service.get_or_create(session_id)
        archived = set(session.context.archived_task_ids)
    for row in board.get("tasks") or []:
        if row.get("task_id") == task_id:
            return enrich_task(row, archived_ids=archived)
    raise HTTPException(status_code=404, detail="ticket not found")


class SessionRef(BaseModel):
    session_id: str


@router.post("/tickets/{task_id}/confirm")
async def confirm_ticket(task_id: str, body: ConfirmTicketBody | None = None):
    session_id = (body or ConfirmTicketBody()).session_id
    """Przypisz wolnego agenta i uruchom ticket z kolejki (po zaznaczeniu „czekaj”)."""
    board = await workspace_service.fetch_live_board()
    task = next(
        (t for t in (board.get("tasks") or []) if t.get("task_id") == task_id),
        None,
    )
    if not task:
        raise HTTPException(status_code=404, detail="ticket not found")
    status = (task.get("status") or "pending").lower()
    if status not in ("pending",):
        raise HTTPException(status_code=400, detail="ticket nie jest w kolejce")

    agents = [
        a
        for a in (board.get("agents") or [])
        if (a.get("status") or "").lower() == "idle"
    ]
    if not agents:
        raise HTTPException(status_code=409, detail="brak wolnego agenta")

    agent_id = agents[0].get("agent_id")
    if not agent_id:
        raise HTTPException(status_code=409, detail="brak agenta")

    desc = task.get("description") or task.get("title") or ""
    shell = workspace_service._extract_shell_command(desc)

    async with httpx.AsyncClient(timeout=30.0) as client:
        payload: dict[str, Any] = {"task_id": task_id, "agent_id": agent_id}
        if shell:
            payload["command"] = shell
        resp = await client.post(
            f"{ORCHESTRATOR_URL}/api/commands/tasks/assign",
            json=payload,
        )
        if resp.status_code >= 400:
            raise HTTPException(status_code=resp.status_code, detail=resp.text)

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


@router.get("/tickets/meta/statuses")
async def ticket_statuses():
    from app.tickets import STATUS_UI

    return {"items": STATUS_UI}


@router.get("/workspace/chat/export")
async def workspace_chat_export(session_id: str):
    """Transkrypt chatu do schowka (tylko rozmowa, bez RAG health)."""
    session = workspace_service.get_or_create(session_id)
    history = chat_service.get_history(session.session_id)
    lines = [
        "# Mullm — transkrypt chatu",
        f"session_id: {session.session_id}",
        "",
    ]
    for msg in history:
        role = msg.get("role", "?")
        content = (msg.get("content") or "").strip()
        if not content:
            continue
        lines.append(f"## {role}")
        lines.append(content)
        if msg.get("sources"):
            lines.append(f"(źródeł RAG: {len(msg['sources'])})")
        lines.append("")
    if session.draft:
        lines.append("## draft (nieutworzony ticket)")
        lines.append(f"tytuł: {session.draft.get('title')}")
        lines.append(f"shell: {session.draft.get('shell_command') or '—'}")
        lines.append(f"hint: {session.draft.get('execution_hint', '')}")
    text = "\n".join(lines).strip() + "\n"
    return {"session_id": session.session_id, "text": text, "message_count": len(history)}


@router.get("/workspace/logs/export")
async def workspace_logs_export(session_id: str, limit: int = 30):
    """
    Paczka logów do schowka: RAG health, incydenty, historia sesji, feed.
    W UI: przycisk „Kopiuj logi” → navigator.clipboard.writeText(data.text).
    """
    limit = min(max(limit, 1), 100)
    workspace_service.get_or_create(session_id)
    return await workspace_service.export_debug_logs(session_id, limit=limit)


# ── Agent Workroom (multi-agent) ───────────────────────────────


class WorkroomStart(BaseModel):
    user_session_id: str | None = None


class WorkroomMessage(BaseModel):
    message: str
    wait_for_confirmation: bool = False


@router.post("/agent-workroom/session")
async def workroom_start(body: WorkroomStart | None = None):
    payload = body or WorkroomStart()
    session = agent_workroom.create_workroom(user_session_id=payload.user_session_id)
    return {"ok": True, **session.to_dict(), "catalog": agent_workroom.workroom_catalog()}


@router.get("/agent-workroom/{workroom_id}")
async def workroom_get(workroom_id: str):
    session = agent_workroom.get_workroom(workroom_id)
    if not session:
        raise HTTPException(status_code=404, detail="workroom not found")
    return session.to_dict()


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


@router.get("/resource-areas")
async def api_resource_areas():
    return {
        "areas": resource_areas.list_areas(),
        "groups": resource_areas.list_groups(),
        "labels": resource_areas.LABEL_VOCABULARY,
    }


@router.get("/resource-areas/roles")
async def api_role_scopes():
    return {"roles": resource_areas.DEFAULT_ROLE_SCOPES}
