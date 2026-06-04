from __future__ import annotations

from app import chat as chat_service
from app import workspace as workspace_service
from fastapi import APIRouter, HTTPException

router = APIRouter()


@router.get("/workspace/artifacts")
async def workspace_list_artifacts(session_id: str):
    session = workspace_service.get_or_create(session_id)
    return {
        "session_id": session.session_id,
        "items": workspace_service.artifact_summaries(session),
    }


@router.get("/workspace/artifacts/{artifact_id}")
async def workspace_get_artifact(session_id: str, artifact_id: str):
    art = workspace_service.get_artifact(session_id, artifact_id)
    if not art:
        raise HTTPException(status_code=404, detail="artifact not found")
    return art


@router.get("/workspace/files/list/export")
async def workspace_file_list_export(
    session_id: str,
    message: str = "",
    scope: str = "all",
):
    """
    Lista plików jako artefakt (text + json).
    scope: all|user|system|session|rag — lub wyciągany z message (np. „lista plikow usera”).
    """
    session = workspace_service.get_or_create(session_id)
    ctx = session.context
    scope_kind = chat_service.file_list_scope(message) if message.strip() else scope
    inv = chat_service.filter_file_inventory(
        await chat_service.fetch_file_inventory(),
        scope_kind,
        scope_files=list(ctx.file_names),
        scope_uris=list(ctx.uris),
    )
    reply = chat_service.format_file_list_reply(
        inv,
        scope_files=list(ctx.file_names),
        scope_uris=list(ctx.uris),
        list_scope=scope_kind,
    )
    return chat_service.build_file_list_artifact(
        reply,
        inv,
        session_id=session.session_id,
        list_scope=scope_kind,
    )


@router.get("/workspace/chat/export")
async def workspace_chat_export(session_id: str):
    """Transkrypt chatu do schowka (rozmowa + routing, bez RAG health)."""
    session = workspace_service.get_or_create(session_id)
    history = chat_service.get_history(session.session_id)
    text = workspace_service.format_chat_export_text(session)
    return {"session_id": session.session_id, "text": text, "message_count": len(history)}


@router.get("/workspace/logs/export")
async def workspace_logs_export(
    session_id: str,
    limit: int = workspace_service.DEFAULT_LOG_EXPORT_LIMIT,
):
    """
    Paczka logów do schowka: RAG health, incydenty, historia sesji, feed.
    W UI: przycisk „Kopiuj logi” → navigator.clipboard.writeText(data.text).
    """
    limit = workspace_service.clamp_log_export_limit(limit)
    workspace_service.get_or_create(session_id)
    return await workspace_service.export_debug_logs(session_id, limit=limit)
