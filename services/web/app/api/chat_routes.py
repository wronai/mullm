from __future__ import annotations

from typing import Any

import httpx
from fastapi import APIRouter, File, Form, HTTPException, UploadFile

from app import workspace as workspace_service
from app.api.config import ORCHESTRATOR_URL
from app.api.models import (
    ChatMessage,
    ChatSessionStart,
    ContextAttachBody,
    SessionRef,
    TaskDraftRequest,
)

router = APIRouter()


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
    if _form_only_message(body):
        return await _form_only_chat_message(session, body)
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


def _form_only_message(body: ChatMessage) -> bool:
    return bool(body.form_values and not (body.message or "").strip())


async def _form_only_chat_message(session, body: ChatMessage) -> dict[str, Any]:
    from app.conductor import handle_turn

    outcome = await handle_turn(
        session_id=session.session_id,
        message="",
        nlp_conversation_id=session.nlp2dsl_conversation_id,
        scope_files=list(session.context.file_names),
        scope_uris=list(session.context.uris),
        form_values=body.form_values,
        wait_for_confirmation=body.wait_for_confirmation,
        chat_mode=body.mode or "discuss",
        use_rag=body.use_rag,
    )
    _update_nlp_conversation(session, outcome)
    return outcome


def _update_nlp_conversation(session, outcome: dict[str, Any]) -> None:
    if outcome.get("nlp2dsl_conversation_id"):
        session.nlp2dsl_conversation_id = outcome["nlp2dsl_conversation_id"]
    if outcome.get("nlp2dsl_status"):
        session.nlp2dsl_status = str(outcome["nlp2dsl_status"])


@router.post("/tasks/draft")
async def task_draft(body: TaskDraftRequest):
    draft = workspace_service.propose_task_draft(body.session_id, body.message)
    return {"draft": draft, "session_id": body.session_id}


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


@router.post("/context/clear-tickets")
async def context_clear_tickets(body: SessionRef):
    return {"context": workspace_service.clear_ticket_uris(body.session_id)}


@router.post("/files/upload")
async def upload_files(
    session_id: str = Form(""),
    files: list[UploadFile] = File(...),
    classification: str = Form("document"),
):
    uploaded: list[dict[str, Any]] = []
    async with httpx.AsyncClient(timeout=120.0) as client:
        for upload in files:
            item = await _upload_one_file(
                client,
                upload,
                classification=classification,
                session_id=session_id,
            )
            if item:
                uploaded.append(item)
    return {"items": uploaded}


async def _upload_one_file(
    client: httpx.AsyncClient,
    upload: UploadFile,
    *,
    classification: str,
    session_id: str,
) -> dict[str, Any] | None:
    content = await upload.read()
    if not content:
        return None
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
        return {"filename": upload.filename, "ok": False, "error": resp.text}
    payload = resp.json()
    item = {
        "filename": upload.filename,
        "ok": True,
        "resource_id": payload.get("resource_id"),
        "uri": payload.get("uri"),
    }
    if session_id:
        workspace_service.attach_context(
            session_id,
            resource_id=payload.get("resource_id"),
            uri=payload.get("uri"),
            filename=upload.filename,
        )
    return item


@router.get("/board")
async def board_snapshot():
    return await workspace_service.fetch_live_board()
