from __future__ import annotations

import os
from typing import Any

import httpx
from fastapi import APIRouter, File, Form, HTTPException, UploadFile
from pydantic import BaseModel, Field

from app import chat as chat_service
from app import workspace as workspace_service

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
    message: str
    mode: str = "discuss"  # discuss | create_task | run_task | search_context
    use_rag: bool = True


class TaskDraftRequest(BaseModel):
    session_id: str
    message: str


class CreateTaskBody(BaseModel):
    session_id: str | None = None
    title: str
    description: str = ""
    shell_command: str | None = None
    auto_assign: bool = True
    priority: str = "medium"
    ticket_id: str | None = None


class CreateFromDraftBody(BaseModel):
    session_id: str
    draft: dict[str, Any] | None = None
    run: bool = False


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
    outcome = await workspace_service.handle_chat_message(
        session_id=session.session_id,
        message=body.message,
        mode=body.mode,
        use_rag=body.use_rag,
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
        auto_assign=body.auto_assign,
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
    )
    if not result.get("ok"):
        raise HTTPException(status_code=400, detail=result.get("error", "create failed"))
    return result


@router.post("/tasks/create-and-run")
async def create_and_run_task(body: CreateFromDraftBody):
    result = await workspace_service.create_and_run(
        body.session_id,
        draft=body.draft,
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
