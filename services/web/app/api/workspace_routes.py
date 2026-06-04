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
    """Transkrypt chatu do schowka (tylko rozmowa, bez RAG health)."""
    session = workspace_service.get_or_create(session_id)
    history = chat_service.get_history(session.session_id)
    text = _format_chat_export(session, history)
    return {"session_id": session.session_id, "text": text, "message_count": len(history)}


def _format_chat_export(session, history: list[dict]) -> str:
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
    return "\n".join(lines).strip() + "\n"


@router.get("/workspace/logs/export")
async def workspace_logs_export(session_id: str, limit: int = 30):
    """
    Paczka logów do schowka: RAG health, incydenty, historia sesji, feed.
    W UI: przycisk „Kopiuj logi” → navigator.clipboard.writeText(data.text).
    """
    limit = min(max(limit, 1), 100)
    workspace_service.get_or_create(session_id)
    return await workspace_service.export_debug_logs(session_id, limit=limit)
