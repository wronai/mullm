from __future__ import annotations

import json
import re
import uuid
from datetime import datetime, timezone
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
    archived_task_ids: list[str] = field(default_factory=list)
    linked_ticket_id: str | None = None

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
            "archived_task_ids": self.archived_task_ids,
            "linked_ticket_id": self.linked_ticket_id,
        }


@dataclass
class WorkspaceSession:
    session_id: str
    context: WorkspaceContext = field(default_factory=WorkspaceContext)
    draft: dict[str, Any] | None = None
    events: list[dict[str, Any]] = field(default_factory=list)
    artifacts: list[dict[str, Any]] = field(default_factory=list)
    nlp2dsl_conversation_id: str | None = None

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
    if session_id:
        existing = _sessions.get(session_id)
        if existing:
            return existing
        # Przywróć sesję po odświeżeniu strony / restarcie web (in-memory dict pusty).
        session = WorkspaceSession(session_id=session_id)
        _sessions[session_id] = session
        chat_service._sessions.setdefault(session_id, [])
        session.add_event(
            "ChatSessionResumed",
            "Sesja wznowiona (historia chatu mogła wygasnąć po restarcie serwisu)",
        )
        return session
    return new_session()


def _artifact_title(artifact: dict[str, Any]) -> str:
    kind = artifact.get("kind") or "artifact"
    if kind == "file_list":
        scope = artifact.get("list_scope") or "all"
        return f"Lista plików ({scope})"
    return artifact.get("filename") or artifact.get("title") or kind


def register_artifact(
    session: WorkspaceSession,
    artifact: dict[str, Any],
    *,
    source_message: str = "",
) -> dict[str, Any]:
    """Zapisuje artefakt w sesji (lista + podgląd po prawej w UI)."""
    entry = {
        **artifact,
        "artifact_id": artifact.get("artifact_id") or str(uuid.uuid4()),
        "created_at": artifact.get("created_at")
        or datetime.now(timezone.utc).isoformat(),
        "title": _artifact_title(artifact),
        "source_message": (source_message or "")[:200],
    }
    session.artifacts.append(entry)
    if len(session.artifacts) > 50:
        session.artifacts = session.artifacts[-50:]
    session.add_event(
        "ArtifactCreated",
        entry["title"],
        artifact_id=entry["artifact_id"],
        kind=entry.get("kind"),
    )
    return entry


def artifact_summaries(session: WorkspaceSession) -> list[dict[str, Any]]:
    """Metadane do listy (bez dużego json — pełny podgląd po id)."""
    out: list[dict[str, Any]] = []
    for a in session.artifacts:
        out.append(
            {
                "artifact_id": a.get("artifact_id"),
                "title": a.get("title"),
                "kind": a.get("kind"),
                "filename": a.get("filename"),
                "list_scope": a.get("list_scope"),
                "mime": a.get("mime"),
                "created_at": a.get("created_at"),
                "source_message": a.get("source_message"),
                "has_json": bool(a.get("json")),
            }
        )
    return out


def get_artifact(session_id: str, artifact_id: str) -> dict[str, Any] | None:
    session = get_session(session_id)
    if not session:
        return None
    for a in session.artifacts:
        if a.get("artifact_id") == artifact_id:
            return a
    return None


def workspace_state(session_id: str) -> dict[str, Any]:
    session = get_or_create(session_id)
    return {
        "session_id": session.session_id,
        "context": session.context.to_dict(),
        "draft": session.draft,
        "events": session.events,
        "history": chat_service.get_history(session.session_id),
        "artifacts": artifact_summaries(session),
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


def build_task_payload(session_id: str, message: str) -> dict[str, Any]:
    """Szkic pól zadania (tylko API /tasks/draft) — nie zapisuje sesji."""
    session = get_or_create(session_id)
    message = (message or "").strip()
    ticket = _extract_ticket(message) or session.context.ticket_id
    shell = _extract_shell_command(message)
    return {
        "title": message[:80] or "Nowe zadanie",
        "description": message,
        "shell_command": shell,
        "priority": "medium",
        "ticket_id": ticket,
        "scope": {
            "uris": list(session.context.uris),
            "resource_ids": list(session.context.resource_ids),
            "files": list(session.context.file_names),
        },
    }


def propose_task_draft(session_id: str, message: str) -> dict[str, Any]:
    """Kompatybilność API — zwraca payload bez trzymania szkicu w sesji."""
    return build_task_payload(session_id, message)


async def create_task_immediate(
    session_id: str,
    *,
    title: str,
    description: str = "",
    shell_command: str | None = None,
    wait_for_confirmation: bool = False,
    priority: str = "medium",
) -> dict[str, Any]:
    """Tworzy ticket od razu; domyślnie przypisuje agenta (uruchomienie)."""
    session = get_or_create(session_id)
    session.draft = None
    result = await chat_service.create_task(
        title=title,
        description=description,
        shell_command=shell_command,
        wait_for_confirmation=wait_for_confirmation,
        auto_assign=not wait_for_confirmation,
        priority=priority,
    )
    if result.get("ok") and result.get("task_id"):
        link_ticket(session_id, result["task_id"])
        session.add_event(
            "TaskCreatedFromChat",
            title,
            task_id=result.get("task_id"),
            wait_for_confirmation=wait_for_confirmation,
        )
    return result


async def handle_chat_message(
    *,
    session_id: str,
    message: str,
    mode: str = "discuss",
    use_rag: bool = True,
    wait_for_confirmation: bool = False,
) -> dict[str, Any]:
    session = get_or_create(session_id)
    message = (message or "").strip()
    if not message and mode != "discuss":
        return {"error": "empty message"}

    ticket = _extract_ticket(message)
    if ticket:
        attach_context(session.session_id, ticket_id=ticket)

    ctx = session.context
    task_result = None

    if mode in ("run_task", "create_task"):
        shell = _extract_shell_command(message)
        payload = build_task_payload(session.session_id, message)
        task_result = await create_task_immediate(
            session.session_id,
            title=payload["title"],
            description=payload.get("description", ""),
            shell_command=shell,
            wait_for_confirmation=wait_for_confirmation,
            priority=payload.get("priority", "medium"),
        )
        tid = task_result.get("task_id", "?")
        if task_result.get("ok"):
            reply = (
                f"Ticket `{tid}` w kolejce — potwierdź na liście ticketów (◎)."
                if wait_for_confirmation
                else (
                    f"Uruchomiono ticket `{tid}`"
                    + (f" · `{shell}`" if shell else "")
                )
            )
        else:
            reply = f"Nie udało się utworzyć ticketu: {task_result.get('error')}"
        outcome = {
            "reply": reply,
            "task": task_result,
            "history": chat_service.get_history(session.session_id),
            "correlation_id": session.session_id,
        }
    elif mode == "search_context":
        outcome = await chat_service.handle_message(
            session_id=session.session_id,
            message=message,
            use_rag=True,
            scope_files=list(ctx.file_names),
            scope_uris=list(ctx.uris),
        )
    else:
        from app.conductor import handle_turn

        outcome = await handle_turn(
            session_id=session.session_id,
            message=message,
            nlp_conversation_id=session.nlp2dsl_conversation_id,
            scope_files=list(ctx.file_names),
            scope_uris=list(ctx.uris),
            form_values=None,
            wait_for_confirmation=wait_for_confirmation,
        )
        if outcome.get("nlp2dsl_conversation_id"):
            session.nlp2dsl_conversation_id = outcome["nlp2dsl_conversation_id"]

    if outcome.get("error"):
        return outcome

    session.add_event("ChatMessageAdded", message[:120] or "(formularz)", mode=mode)
    if outcome.get("artifact"):
        registered = register_artifact(
            session,
            outcome["artifact"],
            source_message=message,
        )
        outcome["artifact"] = registered

    if outcome.get("intent") == "file_list":
        session.add_event("FileListReturned", "Lista plików z rejestru + RAG")
    if outcome.get("retrieval_trace_id"):
        session.add_event(
            "RagTrace",
            outcome["retrieval_trace_id"],
            trace=outcome["retrieval_trace_id"],
        )
    if outcome.get("incident"):
        inc = outcome["incident"]
        session.add_event(
            "RagIncident",
            f"{inc.get('incident_code', '?')}: {(inc.get('message') or '')[:80]}",
            retrieval_trace_id=outcome.get("retrieval_trace_id"),
            correlation_id=outcome.get("correlation_id"),
        )

    if task_result and task_result.get("ok"):
        session.add_event(
            "TaskCreatedFromChat",
            f"Ticket {task_result.get('task_id', '')[:8]}",
            task_id=task_result.get("task_id"),
        )
        if task_result.get("task_id"):
            link_ticket(session.session_id, task_result["task_id"])

    return {
        **outcome,
        "draft": session.draft,
        "task": task_result or outcome.get("task"),
        "context": session.context.to_dict(),
        "events": session.events,
        "artifacts": artifact_summaries(session),
    }


async def create_task_from_draft(
    session_id: str,
    *,
    draft: dict[str, Any] | None = None,
    run: bool = False,
    wait_for_confirmation: bool = False,
) -> dict[str, Any]:
    data = draft or get_or_create(session_id).draft
    if not data:
        return {"ok": False, "error": "brak danych zadania"}
    if run:
        wait_for_confirmation = False
    return await create_task_immediate(
        session_id,
        title=data["title"],
        description=data.get("description", ""),
        shell_command=data.get("shell_command"),
        wait_for_confirmation=wait_for_confirmation,
        priority=data.get("priority", "medium"),
    )


async def create_and_run(
    session_id: str,
    *,
    draft: dict[str, Any] | None = None,
    wait_for_confirmation: bool = False,
) -> dict[str, Any]:
    data = draft or get_or_create(session_id).draft
    if not data:
        return {"ok": False, "error": "brak danych zadania"}
    shell = data.get("shell_command")
    if not shell:
        return {"ok": False, "error": "Uruchomienie wymaga polecenia shell"}
    result = await create_task_immediate(
        session_id,
        title=data["title"],
        description=data.get("description", ""),
        shell_command=shell,
        wait_for_confirmation=wait_for_confirmation,
        priority=data.get("priority", "medium"),
    )
    if result.get("ok"):
        get_or_create(session_id).add_event(
            "TaskRunRequested",
            f"Wysłano do agenta: {shell[:60]}",
            task_id=result.get("task_id"),
        )
    return {**result, "queued": not wait_for_confirmation}


async def export_debug_logs(session_id: str, *, limit: int = 30) -> dict[str, Any]:
    """Zbiera logi sesji + orchestrator + feed do kopiowania do schowka."""
    session = get_or_create(session_id)
    correlation_id = session.session_id
    headers = {"X-Correlation-ID": correlation_id}

    bundle: dict[str, Any] = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "correlation_id": correlation_id,
        "service": "web-bff",
        "session": {
            "session_id": session.session_id,
            "context": session.context.to_dict(),
            "events": session.events,
            "chat_history": chat_service.get_history(session.session_id),
            "draft": session.draft,
        },
    }

    try:
        bundle["inventory"] = await chat_service.fetch_file_inventory()
    except Exception as exc:
        bundle["inventory"] = {"errors": [str(exc)]}

    async with httpx.AsyncClient(timeout=30.0) as client:
        try:
            r = await client.get(
                f"{_orch()}/api/observability/logs/export",
                params={"correlation_id": correlation_id, "limit": limit},
                headers=headers,
            )
            if r.status_code == 200:
                orch = r.json()
                bundle["rag_health"] = orch.get("rag_health")
                bundle["incidents"] = orch.get("incidents")
                bundle["incident_feed"] = orch.get("incident_feed")
                all_snaps = orch.get("rag_snapshots") or []
                bundle["rag_snapshots"] = [
                    s for s in all_snaps if s.get("correlation_id") == correlation_id
                ][:10]
                bundle["rag_health"] = bundle.get("rag_health") or orch.get("rag_health")
        except httpx.HTTPError as exc:
            bundle["orchestrator_error"] = str(exc)

        try:
            feed_r = await client.get(
                f"{_projector()}/projections/feed",
                params={"limit": 25},
            )
            if feed_r.status_code == 200:
                items = feed_r.json().get("items") or []
                bundle["operational_feed"] = [
                    i
                    for i in items
                    if (i.get("correlation_id") == correlation_id)
                    or "Incident" in (i.get("event_type") or "")
                ][:limit]
        except httpx.HTTPError:
            bundle["operational_feed"] = []

    bundle["text"] = _format_export_text(bundle)
    return bundle


def _format_export_text(bundle: dict[str, Any]) -> str:
    lines = [
        "# Mullm workspace — export logów",
        f"generated_at: {bundle.get('generated_at') or datetime.now(timezone.utc).isoformat()}",
        f"correlation_id: {bundle.get('correlation_id', '')}",
        "",
    ]
    sess = bundle.get("session") or {}
    ctx = sess.get("context") or {}
    if ctx:
        lines.append("## Kontekst")
        for key in ("ticket_id", "project", "branch", "agent_id"):
            if ctx.get(key):
                lines.append(f"- {key}: {ctx[key]}")
        if ctx.get("uris"):
            lines.append(f"- uris: {', '.join(ctx['uris'][:8])}")
        if ctx.get("file_names"):
            lines.append(f"- pliki w sesji: {', '.join(ctx['file_names'][:8])}")
        lines.append("")

    inv = bundle.get("inventory") or {}
    resources = inv.get("resources") or []
    rag_docs = inv.get("rag_documents") or []
    if resources or rag_docs:
        lines.append("## Pliki i zasoby (stan systemu)")
        for row in resources:
            lines.append(
                f"- {row.get('name') or '?'} | {row.get('uri')} | {row.get('status')}"
            )
        for doc in rag_docs:
            lines.append(
                f"- [RAG] {doc.get('name') or '?'} | {doc.get('uri')} | "
                f"{doc.get('status')} chunks={doc.get('chunk_count')}"
            )
        lines.append("")

    history = sess.get("chat_history") or []
    lines.append("## Historia chatu")
    if not history:
        lines.append("(brak — wyślij wiadomość w workspace lub sesja wygasła po restarcie web)")
    else:
        for msg in history:
            role = msg.get("role", "?")
            content = (msg.get("content") or "").strip()
            if not content:
                continue
            lines.append(f"\n### {role}")
            lines.append(content[:4000])
            if msg.get("sources"):
                lines.append(f"(źródeł RAG: {len(msg['sources'])})")
    lines.append("")

    if sess.get("draft"):
        d = sess["draft"]
        lines.append("## Szkic (nieużywany — tickety tworzone od razu z chatu)")
        lines.append(f"- tytuł: {d.get('title')}")
        lines.append(f"- shell: {d.get('shell_command') or '—'}")
        lines.append("")

    if sess.get("events"):
        lines.append("## Zdarzenia sesji")
        for ev in sess["events"][-30:]:
            extra = ""
            if ev.get("task_id"):
                extra = f" task_id={ev['task_id']}"
            if ev.get("retrieval_trace_id"):
                extra += f" trace={ev['retrieval_trace_id']}"
            lines.append(f"- {ev.get('type')}: {ev.get('summary', '')}{extra}")
        lines.append("")

    rag = bundle.get("rag_health") or {}
    if rag:
        lines.append("## RAG health (skrót)")
        lines.append(f"status: {rag.get('status')} · code: {rag.get('primary_incident_code')}")
        for check in rag.get("checks") or []:
            lines.append(f"  - {check.get('name')}: {check.get('status')} {check.get('detail', '')}")
        lines.append("")

    incidents = bundle.get("incidents") or []
    if incidents:
        lines.append("## Incydenty (ta sesja)")
        for inc in incidents:
            lines.append(
                f"- {inc.get('incident_code')} {inc.get('message', '')[:120]} "
                f"trace={inc.get('retrieval_trace_id', '')}"
            )
        lines.append("")

    snapshots = [
        s
        for s in (bundle.get("rag_snapshots") or [])
        if s.get("correlation_id") == bundle.get("correlation_id")
    ][:5]
    if snapshots:
        lines.append("## RAG snapshots (ta sesja)")
        for s in snapshots:
            lines.append(f"- {s.get('created_at')} {s.get('status')}")
        lines.append("")

    feed = bundle.get("operational_feed") or []
    if feed:
        lines.append("## Operational feed")
        for row in feed[:15]:
            lines.append(
                f"- {str(row.get('occurred_at', ''))[:19]} "
                f"{row.get('event_type')} — {row.get('summary') or row.get('title', '')}"
            )
        lines.append("")

    if bundle.get("orchestrator_error"):
        lines.append(f"(orchestrator: {bundle['orchestrator_error']})")

    lines.append("---")
    lines.append("Wklej do ticketa / Cursor / support.")
    return "\n".join(lines)


def archive_task(session_id: str, task_id: str) -> dict[str, Any]:
    session = get_or_create(session_id)
    if task_id not in session.context.archived_task_ids:
        session.context.archived_task_ids.append(task_id)
    session.add_event("TaskArchived", f"Ticket {task_id[:8]}… w archiwum")
    return {"ok": True, "task_id": task_id}


def link_ticket(session_id: str, task_id: str | None) -> dict[str, Any]:
    session = get_or_create(session_id)
    session.context.linked_ticket_id = task_id
    if task_id:
        uri = f"mullm://ticket/{task_id}"
        if uri not in session.context.uris:
            session.context.uris.append(uri)
    return session.context.to_dict()


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
