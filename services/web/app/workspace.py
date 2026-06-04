from __future__ import annotations

import re
import uuid
from dataclasses import dataclass, field
from typing import Any

import httpx

from app import chat as chat_service


def _orch() -> str:
    return chat_service._orch()


def _projector() -> str:
    import os

    return os.getenv(
        "PROJECTOR_URL",
        os.getenv("MULLM_PROJECTOR_URL", "http://projector:8000"),
    )


@dataclass
class WorkspaceContext:
    project: str = ""
    branch: str = ""
    ticket_id: str = ""
    agent_id: str = ""
    notes: list[str] = field(default_factory=list)
    resource_ids: list[str] = field(default_factory=list)
    uris: list[str] = field(default_factory=list)
    file_names: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "project": self.project,
            "branch": self.branch,
            "ticket_id": self.ticket_id,
            "agent_id": self.agent_id,
            "notes": self.notes,
            "resource_ids": self.resource_ids,
            "uris": self.uris,
            "file_names": self.file_names,
        }


@dataclass
class WorkspaceSession:
    session_id: str
    context: WorkspaceContext = field(default_factory=WorkspaceContext)
    draft: dict[str, Any] | None = None
    events: list[dict[str, Any]] = field(default_factory=list)

    def add_event(self, event_type: str, summary: str, **extra: Any) -> None:
        self.events.append(
            {
                "type": event_type,
                "summary": summary,
                **extra,
            }
        )
        if len(self.events) > 100:
            self.events = self.events[-100:]


_sessions: dict[str, WorkspaceSession] = {}


def new_session(*, ticket_id: str = "", project: str = "") -> WorkspaceSession:
    session_id = str(uuid.uuid4())
    ctx = WorkspaceContext(ticket_id=ticket_id, project=project)
    session = WorkspaceSession(session_id=session_id, context=ctx)
    _sessions[session_id] = session
    session.add_event("ChatSessionStarted", "Sesja workspace rozpoczęta")
    chat_service._sessions[session_id] = []
    return session


def get_session(session_id: str) -> WorkspaceSession | None:
    return _sessions.get(session_id)


def get_or_create(session_id: str | None) -> WorkspaceSession:
    if session_id and session_id in _sessions:
        return _sessions[session_id]
    return new_session()


def workspace_state(session_id: str) -> dict[str, Any]:
    session = get_or_create(session_id)
    return {
        "session_id": session.session_id,
        "context": session.context.to_dict(),
        "draft": session.draft,
        "events": session.events,
        "history": chat_service.get_history(session.session_id),
    }


def attach_context(
    session_id: str,
    *,
    ticket_id: str | None = None,
    project: str | None = None,
    branch: str | None = None,
    agent_id: str | None = None,
    resource_id: str | None = None,
    uri: str | None = None,
    note: str | None = None,
    filename: str | None = None,
) -> dict[str, Any]:
    session = get_or_create(session_id)
    ctx = session.context
    if ticket_id:
        ctx.ticket_id = ticket_id
    if project:
        ctx.project = project
    if branch:
        ctx.branch = branch
    if agent_id:
        ctx.agent_id = agent_id
    if resource_id and resource_id not in ctx.resource_ids:
        ctx.resource_ids.append(resource_id)
    if uri and uri not in ctx.uris:
        ctx.uris.append(uri)
    if filename and filename not in ctx.file_names:
        ctx.file_names.append(filename)
    if note:
        ctx.notes.append(note)
    session.add_event("ContextUpdated", "Kontekst zaktualizowany")
    return session.context.to_dict()


def _extract_ticket(text: str) -> str | None:
    match = re.search(r"\b([A-Z]{2,}-\d+)\b", text)
    return match.group(1) if match else None


def _extract_shell_command(text: str) -> str | None:
    lowered = text.lower().strip()
    for prefix in ("run ", "exec ", "shell ", "wykonaj ", "uruchom "):
        if lowered.startswith(prefix):
            return text[len(prefix) :].strip()
    if text.strip().startswith(("echo ", "ls ", "cat ", "git ", "python ", "npm ")):
        return text.strip()
    return None


def propose_task_draft(session_id: str, message: str) -> dict[str, Any]:
    session = get_or_create(session_id)
    message = (message or "").strip()
    ticket = _extract_ticket(message) or session.context.ticket_id
    shell = _extract_shell_command(message)
    draft = {
        "title": message[:80] or "Nowe zadanie",
        "description": message,
        "executor_kind": "shell" if shell else "semi_auto",
        "shell_command": shell,
        "priority": "medium",
        "auto_assign": bool(shell),
        "ticket_id": ticket,
        "scope": {
            "uris": list(session.context.uris),
            "resource_ids": list(session.context.resource_ids),
            "files": list(session.context.file_names),
        },
    }
    session.draft = draft
    session.add_event("TaskDraftProposed", draft["title"], draft=draft)
    return draft


async def handle_chat_message(
    *,
    session_id: str,
    message: str,
    mode: str = "discuss",
    use_rag: bool = True,
) -> dict[str, Any]:
    session = get_or_create(session_id)
    message = (message or "").strip()
    if not message:
        return {"error": "empty message"}

    ticket = _extract_ticket(message)
    if ticket:
        attach_context(session.session_id, ticket_id=ticket)

    draft = None
    task_result = None

    if mode == "search_context":
        use_rag = True
    elif mode in {"create_task", "run_task"}:
        draft = propose_task_draft(session.session_id, message)
    elif mode == "discuss":
        draft = propose_task_draft(session.session_id, message)

    outcome = await chat_service.handle_message(
        session_id=session.session_id,
        message=message,
        use_rag=use_rag and mode != "create_task",
    )
    if outcome.get("error"):
        return outcome

    session.add_event("ChatMessageAdded", message[:120])

    if mode == "create_task" and draft:
        task_result = await chat_service.create_task(
            title=draft["title"],
            description=draft["description"],
            shell_command=draft.get("shell_command"),
            auto_assign=draft.get("auto_assign", False),
            priority=draft.get("priority", "medium"),
        )
        if task_result.get("ok"):
            session.add_event(
                "TaskCreatedFromChat",
                f"Utworzono zadanie {task_result.get('task_id')}",
                task_id=task_result.get("task_id"),
            )
    elif mode == "run_task" and draft:
        task_result = await create_and_run(session.session_id, draft=draft)

    return {
        **outcome,
        "draft": draft or session.draft,
        "task": task_result,
        "context": session.context.to_dict(),
        "events": session.events,
    }


async def create_task_from_draft(
    session_id: str,
    *,
    draft: dict[str, Any] | None = None,
    run: bool = False,
) -> dict[str, Any]:
    session = get_or_create(session_id)
    data = draft or session.draft
    if not data:
        return {"ok": False, "error": "brak draftu zadania"}

    if run:
        return await create_and_run(session_id, draft=data)

    result = await chat_service.create_task(
        title=data["title"],
        description=data.get("description", ""),
        shell_command=data.get("shell_command"),
        auto_assign=data.get("auto_assign", True),
        priority=data.get("priority", "medium"),
    )
    if result.get("ok"):
        session.add_event(
            "TaskCreatedFromChat",
            data["title"],
            task_id=result.get("task_id"),
        )
    return result


async def create_and_run(
    session_id: str,
    *,
    draft: dict[str, Any] | None = None,
) -> dict[str, Any]:
    session = get_or_create(session_id)
    data = draft or session.draft
    if not data:
        return {"ok": False, "error": "brak draftu"}

    shell = data.get("shell_command")
    if not shell:
        return {
            "ok": False,
            "error": "Uruchomienie wymaga polecenia shell w draftzie",
        }

    result = await chat_service.create_task(
        title=data["title"],
        description=data.get("description", ""),
        shell_command=shell,
        auto_assign=True,
        priority=data.get("priority", "medium"),
    )
    if result.get("ok"):
        session.add_event(
            "TaskRunRequested",
            f"Wysłano do agenta: {shell[:60]}",
            task_id=result.get("task_id"),
        )
    return {**result, "queued": True}


async def fetch_live_board() -> dict[str, Any]:
    async with httpx.AsyncClient(timeout=10.0) as client:
        async def items(path: str, *, limit: int | None = None) -> list:
            try:
                params = {"limit": limit} if limit else None
                r = await client.get(f"{_projector()}{path}", params=params)
                return r.json().get("items", []) if r.status_code == 200 else []
            except httpx.HTTPError:
                return []

        return {
            "tasks": await items("/projections/tasks"),
            "agents": await items("/projections/agents"),
            "feed": await items("/projections/feed", limit=25),
            "resources": await items("/projections/resources"),
            "rag_documents": await items("/projections/rag/documents"),
            "approvals": await items("/projections/approvals", limit=10),
        }
