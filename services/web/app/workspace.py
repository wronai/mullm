from __future__ import annotations

import json
import re
import uuid
from datetime import datetime, timezone
from dataclasses import dataclass, field
from typing import Any

import httpx

from app import chat as chat_service

DEFAULT_LOG_EXPORT_LIMIT = 100
MAX_LOG_EXPORT_LIMIT = 500
NFO_EXPORT_SCHEMA = "mullm.logs.nfo.v1"

try:  # Optional in local tests; pinned in service requirements for Docker.
    import nfo as _nfo
except Exception:  # pragma: no cover - depends on runtime image extras.
    _nfo = None


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
    from app.routing_policy import load_policy

    session = get_or_create(session_id)
    return {
        "session_id": session.session_id,
        "context": session.context.to_dict(),
        "draft": session.draft,
        "events": session.events,
        "history": chat_service.get_history(session.session_id),
        "artifacts": artifact_summaries(session),
        "routing_policy": load_policy().to_dict(),
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
    _apply_context_scalars(
        session.context,
        ticket_id=ticket_id,
        project=project,
        branch=branch,
        agent_id=agent_id,
    )
    _append_unique(session.context.resource_ids, resource_id)
    _append_unique(session.context.uris, uri)
    _append_unique(session.context.file_names, filename)
    if note:
        session.context.notes.append(note)
    session.add_event("ContextUpdated", "Kontekst zaktualizowany")
    return session.context.to_dict()


def _apply_context_scalars(
    ctx: WorkspaceContext,
    *,
    ticket_id: str | None,
    project: str | None,
    branch: str | None,
    agent_id: str | None,
) -> None:
    if ticket_id:
        ctx.ticket_id = ticket_id
    if project:
        ctx.project = project
    if branch:
        ctx.branch = branch
    if agent_id is not None:
        ctx.agent_id = agent_id.strip() if agent_id else ""


def _append_unique(items: list[str], value: str | None) -> None:
    if value and value not in items:
        items.append(value)


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
    agent_id: str | None = None,
) -> dict[str, Any]:
    """Tworzy ticket od razu; domyślnie przypisuje agenta (uruchomienie)."""
    session = get_or_create(session_id)
    session.draft = None
    resolved_agent = _resolved_task_agent(session, agent_id, shell_command)
    result = await chat_service.create_task(
        title=title,
        description=description,
        shell_command=shell_command,
        wait_for_confirmation=wait_for_confirmation,
        auto_assign=not wait_for_confirmation and not resolved_agent,
        priority=priority,
        agent_id=resolved_agent,
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


def _resolved_task_agent(
    session: WorkspaceSession,
    agent_id: str | None,
    shell_command: str | None,
) -> str | None:
    from app.routing_policy import load_policy

    resolved_agent = agent_id or session.context.agent_id or None
    if not resolved_agent and shell_command:
        return load_policy().agent_for_route("mullm_shell")
    return resolved_agent


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

    session.add_event("PromptReceived", message[:120] or "(pusty)", mode=mode)
    _attach_ticket_context(session, message)

    ctx = session.context
    outcome, task_result = await _dispatch_chat_mode(
        session,
        message=message,
        mode=mode,
        use_rag=use_rag,
        wait_for_confirmation=wait_for_confirmation,
        scope_files=list(ctx.file_names),
        scope_uris=list(ctx.uris),
    )

    if outcome.get("error"):
        return outcome

    _record_chat_outcome(session, message, mode=mode, outcome=outcome)
    _record_task_outcome(session, task_result)
    return _chat_response(session, outcome, task_result)


def _attach_ticket_context(session: WorkspaceSession, message: str) -> None:
    ticket = _extract_ticket(message)
    if ticket:
        attach_context(session.session_id, ticket_id=ticket)


async def _dispatch_chat_mode(
    session: WorkspaceSession,
    *,
    message: str,
    mode: str,
    use_rag: bool,
    wait_for_confirmation: bool,
    scope_files: list[str],
    scope_uris: list[str],
) -> tuple[dict[str, Any], dict[str, Any] | None]:
    if mode in ("run_task", "create_task"):
        task_result = await _create_task_from_message(
            session,
            message,
            wait_for_confirmation=wait_for_confirmation,
        )
        return _task_chat_outcome(session, task_result, message, wait_for_confirmation), task_result

    if mode == "search_context":
        return await _search_context_outcome(session, message, scope_files, scope_uris), None

    return await _conductor_outcome(
        session,
        message=message,
        mode=mode,
        use_rag=use_rag,
        wait_for_confirmation=wait_for_confirmation,
        scope_files=scope_files,
        scope_uris=scope_uris,
    ), None


async def _create_task_from_message(
    session: WorkspaceSession,
    message: str,
    *,
    wait_for_confirmation: bool,
) -> dict[str, Any]:
    shell = _extract_shell_command(message)
    payload = build_task_payload(session.session_id, message)
    return await create_task_immediate(
        session.session_id,
        title=payload["title"],
        description=payload.get("description", ""),
        shell_command=shell,
        wait_for_confirmation=wait_for_confirmation,
        priority=payload.get("priority", "medium"),
    )


def _task_chat_outcome(
    session: WorkspaceSession,
    task_result: dict[str, Any],
    message: str,
    wait_for_confirmation: bool,
) -> dict[str, Any]:
    shell = _extract_shell_command(message)
    return {
        "reply": _task_result_reply(task_result, shell, wait_for_confirmation),
        "task": task_result,
        "history": chat_service.get_history(session.session_id),
        "correlation_id": session.session_id,
    }


def _task_result_reply(
    task_result: dict[str, Any],
    shell: str | None,
    wait_for_confirmation: bool,
) -> str:
    tid = task_result.get("task_id", "?")
    if not task_result.get("ok"):
        return f"Nie udało się utworzyć ticketu: {task_result.get('error')}"
    if wait_for_confirmation:
        return f"Ticket `{tid}` w kolejce — potwierdź na liście ticketów (◎)."
    return f"Uruchomiono ticket `{tid}`" + (f" · `{shell}`" if shell else "")


async def _search_context_outcome(
    session: WorkspaceSession,
    message: str,
    scope_files: list[str],
    scope_uris: list[str],
) -> dict[str, Any]:
    return await chat_service.handle_message(
        session_id=session.session_id,
        message=message,
        use_rag=True,
        scope_files=scope_files,
        scope_uris=scope_uris,
    )


async def _conductor_outcome(
    session: WorkspaceSession,
    *,
    message: str,
    mode: str,
    use_rag: bool,
    wait_for_confirmation: bool,
    scope_files: list[str],
    scope_uris: list[str],
) -> dict[str, Any]:
    from app.conductor import handle_turn

    outcome = await handle_turn(
        session_id=session.session_id,
        message=message,
        nlp_conversation_id=session.nlp2dsl_conversation_id,
        scope_files=scope_files,
        scope_uris=scope_uris,
        form_values=None,
        wait_for_confirmation=wait_for_confirmation,
        chat_mode=mode,
        use_rag=use_rag,
    )
    if outcome.get("nlp2dsl_conversation_id"):
        session.nlp2dsl_conversation_id = outcome["nlp2dsl_conversation_id"]
    return outcome


def _record_chat_outcome(
    session: WorkspaceSession,
    message: str,
    *,
    mode: str,
    outcome: dict[str, Any],
) -> None:
    session.add_event("ChatMessageAdded", message[:120] or "(formularz)", mode=mode)
    _register_outcome_artifact(session, message, outcome)
    _record_file_list_event(session, outcome)
    _record_rag_trace_event(session, outcome)
    _record_rag_incident_event(session, outcome)


def _register_outcome_artifact(
    session: WorkspaceSession,
    message: str,
    outcome: dict[str, Any],
) -> None:
    if not outcome.get("artifact"):
        return
    outcome["artifact"] = register_artifact(
        session,
        outcome["artifact"],
        source_message=message,
    )


def _record_file_list_event(session: WorkspaceSession, outcome: dict[str, Any]) -> None:
    if outcome.get("intent") == "file_list":
        session.add_event("FileListReturned", "Lista plików z rejestru + RAG")


def _record_rag_trace_event(session: WorkspaceSession, outcome: dict[str, Any]) -> None:
    if outcome.get("retrieval_trace_id"):
        session.add_event(
            "RagTrace",
            outcome["retrieval_trace_id"],
            trace=outcome["retrieval_trace_id"],
        )


def _record_rag_incident_event(session: WorkspaceSession, outcome: dict[str, Any]) -> None:
    if outcome.get("incident"):
        inc = outcome["incident"]
        session.add_event(
            "RagIncident",
            f"{inc.get('incident_code', '?')}: {(inc.get('message') or '')[:80]}",
            retrieval_trace_id=outcome.get("retrieval_trace_id"),
            correlation_id=outcome.get("correlation_id"),
        )


def _record_task_outcome(
    session: WorkspaceSession,
    task_result: dict[str, Any] | None,
) -> None:
    if task_result and task_result.get("ok"):
        session.add_event(
            "TaskCreatedFromChat",
            f"Ticket {task_result.get('task_id', '')[:8]}",
            task_id=task_result.get("task_id"),
        )
        if task_result.get("task_id"):
            link_ticket(session.session_id, task_result["task_id"])


def _chat_response(
    session: WorkspaceSession,
    outcome: dict[str, Any],
    task_result: dict[str, Any] | None,
) -> dict[str, Any]:
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


_CHAT_ROLE_LABELS = {"user": "Ty", "assistant": "AI", "system": "System"}


def format_chat_export_text(session: WorkspaceSession) -> str:
    """Transkrypt czatu do schowka (rozmowa + routing pod odpowiedziami AI)."""
    history = chat_service.get_history(session.session_id)
    lines = [
        "# Mullm — transkrypt czatu",
        f"session_id: {session.session_id}",
        "",
    ]
    for msg in history:
        _append_chat_export_message(lines, msg)

    _append_chat_export_trace(lines, _collect_routing_trace(history, session.events))
    _append_chat_export_draft(lines, session.draft)
    return "\n".join(lines).strip() + "\n"


def _append_chat_export_message(lines: list[str], msg: dict[str, Any]) -> None:
    role = msg.get("role", "?")
    content = (msg.get("content") or "").strip()
    if not content:
        return
    label = _CHAT_ROLE_LABELS.get(role, role)
    lines.append(f"## {label}")
    lines.append(content)
    if msg.get("sources"):
        lines.append(f"(źródeł RAG: {len(msg['sources'])})")
    if role == "assistant" and msg.get("routing"):
        lines.append(_format_routing_line(msg["routing"]))
    lines.append("")


def _append_chat_export_trace(
    lines: list[str],
    trace: list[dict[str, Any]],
) -> None:
    if not trace:
        return
    lines.append("## Routing trace")
    for row in trace:
        lines.append(_format_routing_line(row))
    lines.append("")


def _append_chat_export_draft(
    lines: list[str],
    draft: dict[str, Any] | None,
) -> None:
    if not draft:
        return
    lines.append("## Szkic (nieutworzony ticket)")
    lines.append(f"tytuł: {draft.get('title')}")
    lines.append(f"shell: {draft.get('shell_command') or '—'}")
    lines.append("")


def clamp_log_export_limit(limit: int | str | None) -> int:
    try:
        value = int(limit) if limit is not None else DEFAULT_LOG_EXPORT_LIMIT
    except (TypeError, ValueError):
        value = DEFAULT_LOG_EXPORT_LIMIT
    return min(max(value, 1), MAX_LOG_EXPORT_LIMIT)


async def export_debug_logs(
    session_id: str,
    *,
    limit: int = DEFAULT_LOG_EXPORT_LIMIT,
) -> dict[str, Any]:
    """Zbiera logi sesji + orchestrator + feed do kopiowania do schowka."""
    limit = clamp_log_export_limit(limit)
    session = get_or_create(session_id)
    correlation_id = session.session_id
    bundle = _debug_export_base(session)
    bundle["log_limit"] = limit
    _emit_nfo_event(
        "workspace.logs_export.started",
        correlation_id=correlation_id,
        limit=limit,
        session_events=len(session.events),
        chat_messages=len(chat_service.get_history(session.session_id)),
    )

    try:
        bundle["inventory"] = await chat_service.fetch_file_inventory()
    except Exception as exc:
        bundle["inventory"] = {"errors": [str(exc)]}
        _emit_nfo_event(
            "workspace.logs_export.inventory_error",
            correlation_id=correlation_id,
            error=str(exc),
        )

    async with httpx.AsyncClient(timeout=30.0) as client:
        await _attach_orchestrator_debug_export(client, bundle, limit=limit)
        await _attach_operational_feed(client, bundle, limit=limit)

    bundle["nfo"] = _build_nfo_package(bundle)
    bundle["text"] = _format_export_text(bundle)
    _emit_nfo_event(
        "workspace.logs_export.finished",
        correlation_id=correlation_id,
        limit=limit,
        **_nfo_counts(bundle),
    )
    return bundle


def _debug_export_base(session: WorkspaceSession) -> dict[str, Any]:
    return {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "correlation_id": session.session_id,
        "service": "web-bff",
        "session": {
            "session_id": session.session_id,
            "context": session.context.to_dict(),
            "events": session.events,
            "chat_history": chat_service.get_history(session.session_id),
            "artifacts": artifact_summaries(session),
            "draft": session.draft,
        },
    }


async def _attach_orchestrator_debug_export(
    client: httpx.AsyncClient,
    bundle: dict[str, Any],
    *,
    limit: int,
) -> None:
    correlation_id = bundle.get("correlation_id")
    headers = {"X-Correlation-ID": str(correlation_id)}
    try:
        response = await client.get(
            f"{_orch()}/api/observability/logs/export",
            params={"correlation_id": correlation_id, "limit": limit},
            headers=headers,
        )
        if response.status_code == 200:
            _merge_orchestrator_debug_payload(bundle, response.json())
    except httpx.HTTPError as exc:
        bundle["orchestrator_error"] = str(exc)
        _emit_nfo_event(
            "workspace.logs_export.orchestrator_error",
            correlation_id=correlation_id,
            error=str(exc),
        )


def _merge_orchestrator_debug_payload(
    bundle: dict[str, Any],
    orch: dict[str, Any],
) -> None:
    bundle["rag_health"] = orch.get("rag_health")
    bundle["incidents"] = orch.get("incidents")
    bundle["incident_feed"] = orch.get("incident_feed")
    if orch.get("nfo"):
        bundle["orchestrator_nfo"] = orch["nfo"]
    correlation_id = bundle.get("correlation_id")
    limit = _visible_log_limit(bundle)
    bundle["rag_snapshots"] = [
        snap
        for snap in (orch.get("rag_snapshots") or [])
        if snap.get("correlation_id") == correlation_id
    ][:limit]
    bundle["rag_health"] = bundle.get("rag_health") or orch.get("rag_health")


async def _attach_operational_feed(
    client: httpx.AsyncClient,
    bundle: dict[str, Any],
    *,
    limit: int,
) -> None:
    try:
        response = await client.get(
            f"{_projector()}/projections/feed",
            params={"limit": limit},
        )
        if response.status_code == 200:
            bundle["operational_feed"] = _filter_operational_feed(
                response.json().get("items") or [],
                correlation_id=str(bundle.get("correlation_id") or ""),
                limit=limit,
            )
    except httpx.HTTPError:
        bundle["operational_feed"] = []


def _filter_operational_feed(
    items: list[dict[str, Any]],
    *,
    correlation_id: str,
    limit: int,
) -> list[dict[str, Any]]:
    return [
        item
        for item in items
        if (item.get("correlation_id") == correlation_id)
        or "Incident" in (item.get("event_type") or "")
    ][:limit]


def _format_export_text(bundle: dict[str, Any]) -> str:
    lines = _export_header(bundle)
    sess = bundle.get("session") or {}
    _append_export_sections(lines, bundle, sess)
    _append_orchestrator_error(lines, bundle)
    lines.extend(["---", "Wklej do ticketa / Cursor / support."])
    return "\n".join(lines)


def _export_header(bundle: dict[str, Any]) -> list[str]:
    generated_at = bundle.get("generated_at") or datetime.now(timezone.utc).isoformat()
    return [
        "# Mullm workspace — export logów",
        f"generated_at: {generated_at}",
        f"correlation_id: {bundle.get('correlation_id', '')}",
        "",
    ]


def _append_export_sections(
    lines: list[str],
    bundle: dict[str, Any],
    sess: dict[str, Any],
) -> None:
    history = _list_section(sess, "chat_history")
    events = _list_section(sess, "events")
    limit = _visible_log_limit(bundle)
    _append_nfo_section(lines, _dict_section(bundle, "nfo") or _build_nfo_package(bundle))
    _append_context_section(lines, _dict_section(sess, "context"))
    _append_inventory_section(lines, _dict_section(bundle, "inventory"))
    _append_history_section(lines, history)
    _append_routing_trace_section(lines, history, events)
    _append_draft_section(lines, sess)
    _append_session_events_section(lines, events, limit=limit)
    _append_rag_health_section(lines, _dict_section(bundle, "rag_health"))
    _append_incidents_section(lines, _list_section(bundle, "incidents"))
    _append_rag_snapshots_section(lines, bundle, limit=limit)
    _append_operational_feed_section(
        lines,
        _list_section(bundle, "operational_feed"),
        limit=limit,
    )


def _list_section(payload: dict[str, Any], key: str) -> list[Any]:
    value = payload.get(key)
    return value if isinstance(value, list) else []


def _dict_section(payload: dict[str, Any], key: str) -> dict[str, Any]:
    value = payload.get(key)
    return value if isinstance(value, dict) else {}


def _visible_log_limit(bundle: dict[str, Any]) -> int:
    return clamp_log_export_limit(bundle.get("log_limit"))


def _nfo_package_version() -> str:
    return str(getattr(_nfo, "__version__", "unavailable"))


def _emit_nfo_event(name: str, **fields: Any) -> None:
    if _nfo is None:
        return
    try:
        _nfo.configure(name="mullm.web.nfo", propagate_stdlib=True)
        _nfo.event(name, service="web-bff", **fields)
    except Exception:
        return


def _build_nfo_package(bundle: dict[str, Any]) -> dict[str, Any]:
    return {
        "schema": NFO_EXPORT_SCHEMA,
        "package": "nfo",
        "package_version": _nfo_package_version(),
        "service": bundle.get("service") or "web-bff",
        "generated_at": bundle.get("generated_at"),
        "correlation_id": bundle.get("correlation_id"),
        "limit": _visible_log_limit(bundle),
        "counts": _nfo_counts(bundle),
        "errors": _nfo_errors(bundle),
    }


def _nfo_counts(bundle: dict[str, Any]) -> dict[str, int]:
    sess = _dict_section(bundle, "session")
    inventory = _dict_section(bundle, "inventory")
    return {
        "chat_messages": len(_list_section(sess, "chat_history")),
        "session_events": len(_list_section(sess, "events")),
        "artifacts": len(_list_section(sess, "artifacts")),
        "inventory_resources": len(_list_section(inventory, "resources")),
        "rag_documents": len(_list_section(inventory, "rag_documents")),
        "incidents": len(_list_section(bundle, "incidents")),
        "incident_feed": len(_list_section(bundle, "incident_feed")),
        "rag_snapshots": len(_list_section(bundle, "rag_snapshots")),
        "operational_feed": len(_list_section(bundle, "operational_feed")),
    }


def _nfo_errors(bundle: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    for key in ("orchestrator_error", "inventory_error"):
        if bundle.get(key):
            errors.append(f"{key}: {bundle[key]}")
    inventory = _dict_section(bundle, "inventory")
    for err in inventory.get("errors") or []:
        errors.append(f"inventory: {err}")
    return errors


def _append_nfo_section(lines: list[str], nfo_package: dict[str, Any]) -> None:
    if not nfo_package:
        return
    lines.append("## NFO")
    lines.append(
        f"- package: {nfo_package.get('package')} "
        f"{nfo_package.get('package_version')}"
    )
    lines.append(f"- schema: {nfo_package.get('schema')}")
    lines.append(f"- service: {nfo_package.get('service')}")
    lines.append(f"- limit: {nfo_package.get('limit')}")
    counts = nfo_package.get("counts") or {}
    if counts:
        lines.append(
            "- counts: "
            + ", ".join(f"{key}={value}" for key, value in counts.items())
        )
    for err in nfo_package.get("errors") or []:
        lines.append(f"- error: {err}")
    lines.append("")


def _append_orchestrator_error(
    lines: list[str],
    bundle: dict[str, Any],
) -> None:
    if bundle.get("orchestrator_error"):
        lines.append(f"(orchestrator: {bundle['orchestrator_error']})")


def _trace_event_row(
    ev: dict[str, Any],
    index: int,
) -> tuple[str, dict[str, Any]] | None:
    event_type = ev.get("type") or ""
    routing = ev.get("routing")
    if not event_type.startswith("Route") or not routing:
        return None
    outcome = ev.get("outcome") or ""
    if outcome == "selected":
        return None
    key = f"ev:{index}:{event_type}:{outcome}"
    row = {
        **routing,
        "source": "event",
        "event_type": event_type,
        "outcome": outcome,
    }
    return key, row


def _trace_message_row(
    msg: dict[str, Any],
    assistant_index: int,
) -> tuple[str, dict[str, Any]] | None:
    routing = msg.get("routing")
    if not routing:
        return None
    fp = _routing_fingerprint(routing)
    key = f"msg:{assistant_index}:{fp}"
    return key, {**routing, "source": "chat", "event_type": "chat"}


def _routing_fingerprint(routing: dict[str, Any]) -> str:
    return (
        f"{routing.get('route')}:{routing.get('handler')}:"
        f"{','.join(routing.get('reason_codes') or [])}"
    )


def _append_context_section(lines: list[str], ctx: dict[str, Any]) -> None:
    lines.append("## Kontekst")
    if not ctx:
        lines.append("- (brak danych kontekstu)")
        lines.append("")
        return
    wrote = _append_context_scalars(lines, ctx)
    wrote = _append_context_collections(lines, ctx) or wrote
    if not wrote:
        lines.append(
            "- (pusty — brak ticketu, wgranych plików 📎; lista plików i tak działa z rejestru)"
        )
    lines.append("")


def _append_context_scalars(lines: list[str], ctx: dict[str, Any]) -> bool:
    wrote = False
    for key in ("ticket_id", "linked_ticket_id", "project", "branch", "agent_id"):
        if ctx.get(key):
            lines.append(f"- {key}: {ctx[key]}")
            wrote = True
    return wrote


def _append_context_collections(lines: list[str], ctx: dict[str, Any]) -> bool:
    wrote = False
    if ctx.get("uris"):
        lines.append(f"- uris: {', '.join(ctx['uris'][:8])}")
        wrote = True
    if ctx.get("file_names"):
        lines.append(f"- pliki w sesji: {', '.join(ctx['file_names'][:8])}")
        wrote = True
    if ctx.get("notes"):
        lines.append(f"- notatki: {len(ctx['notes'])}")
        wrote = True
    return wrote


def _append_inventory_section(lines: list[str], inv: dict[str, Any]) -> None:
    resources = inv.get("resources") or []
    rag_docs = inv.get("rag_documents") or []
    if not resources and not rag_docs:
        return
    lines.append("## Pliki i zasoby (stan systemu)")
    _append_resource_inventory(lines, resources)
    _append_rag_inventory(lines, rag_docs)
    lines.append("")


def _append_resource_inventory(
    lines: list[str],
    resources: list[dict[str, Any]],
) -> None:
    for row in resources:
        lines.append(
            f"- {row.get('name') or '?'} | {row.get('uri')} | {row.get('status')}"
        )


def _append_rag_inventory(
    lines: list[str],
    rag_docs: list[dict[str, Any]],
) -> None:
    for doc in rag_docs:
        lines.append(
            f"- [RAG] {doc.get('name') or '?'} | {doc.get('uri')} | "
            f"{doc.get('status')} chunks={doc.get('chunk_count')}"
        )


def _append_history_section(lines: list[str], history: list[dict[str, Any]]) -> None:
    lines.append("## Historia chatu")
    if not history:
        lines.append("(brak — wyślij wiadomość w workspace lub sesja wygasła po restarcie web)")
        lines.append("")
        return
    for msg in history:
        _append_history_message(lines, msg)
    lines.append("")


def _append_history_message(lines: list[str], msg: dict[str, Any]) -> None:
    role = msg.get("role", "?")
    content = (msg.get("content") or "").strip()
    if not content:
        return
    lines.append(f"\n### {role}")
    lines.append(content[:4000])
    if msg.get("sources"):
        lines.append(f"(źródeł RAG: {len(msg['sources'])})")
    routing = msg.get("routing")
    if role == "assistant" and routing:
        lines.append(_format_routing_line(routing))


def _format_routing_line(routing: dict[str, Any]) -> str:
    route = routing.get("route", "?")
    inner = _routing_base_parts(routing, route)
    inner.extend(_routing_optional_parts(routing, route))
    return "(" + " · ".join(inner) + ")"


def _routing_base_parts(routing: dict[str, Any], route: str) -> list[str]:
    confidence = int((routing.get("confidence") or 0) * 100)
    return [
        f"route: {route}",
        f"{confidence}%",
        f"handler: {routing.get('handler', '')}",
    ]


def _routing_optional_parts(routing: dict[str, Any], route: str) -> list[str]:
    parts: list[str] = []
    codes = ", ".join(routing.get("reason_codes") or [])
    if codes:
        parts.append(f"codes: {codes}")
    parts.extend(_routing_fallback_parts(routing, route))
    parts.extend(_routing_shell_plugin_parts(routing))
    parts.extend(_routing_nlp2dsl_parts(routing))
    if routing.get("timing_ms") is not None:
        parts.append(f"{routing['timing_ms']}ms")
    parts.append(f"mode: {routing.get('router_mode', 'rules')}")
    return parts


def _routing_fallback_parts(routing: dict[str, Any], route: str) -> list[str]:
    fallback = routing.get("fallback_route")
    if fallback and fallback != route:
        return [f"if_not_chosen: {fallback}"]
    return []


def _routing_shell_plugin_parts(routing: dict[str, Any]) -> list[str]:
    plugin = routing.get("shell_plugin")
    if not plugin:
        return []
    parts = [f"shell_plugin: {plugin}"]
    nlp2cmd = routing.get("nlp2cmd")
    if isinstance(nlp2cmd, dict) and nlp2cmd.get("command"):
        parts.append(f"cmd: {nlp2cmd['command'][:80]}")
    return parts


def _routing_nlp2dsl_parts(routing: dict[str, Any]) -> list[str]:
    if routing.get("nlp2dsl_skipped"):
        return ["nlp2dsl: skipped"]
    parts = ["nlp2dsl: invoked"] if routing.get("nlp2dsl_invoked") else []
    nlp2dsl = routing.get("nlp2dsl")
    if nlp2dsl:
        action = nlp2dsl.get("action") or nlp2dsl.get("intent") or "?"
        parts.append(f"nlp2dsl_action: {action}")
    return parts


def _append_routing_trace_section(
    lines: list[str],
    history: list[dict[str, Any]],
    events: list[dict[str, Any]],
) -> None:
    trace = _collect_routing_trace(history, events)
    if not trace:
        return
    lines.append("## Routing trace")
    for i, row in enumerate(trace, 1):
        _append_routing_trace_decision(lines, i, row)
    lines.append("")


def _append_routing_trace_decision(
    lines: list[str],
    index: int,
    row: dict[str, Any],
) -> None:
    label = row.get("event_type") or row.get("outcome") or row.get("source", "?")
    lines.append(f"\n### decyzja {index} ({label})")
    lines.append(_format_routing_line(row))
    _append_candidate_routes(lines, row.get("candidate_routes") or [])


def _append_candidate_routes(
    lines: list[str],
    candidates: list[dict[str, Any]],
) -> None:
    if not candidates:
        return
    lines.append("kandydaci:")
    for candidate in candidates[:5]:
        lines.append(_format_candidate_route(candidate))


def _format_candidate_route(candidate: dict[str, Any]) -> str:
    confidence = int((candidate.get("confidence") or 0) * 100)
    codes = ",".join(candidate.get("reason_codes") or [])
    return f"  - {candidate.get('route')} @ {confidence}% {codes}"


def _collect_routing_trace(
    history: list[dict[str, Any]],
    events: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    """Łączy eventy Route* z routingiem zapisanym na wiadomościach asystenta."""
    trace: list[dict[str, Any]] = []
    seen: set[str] = set()

    for idx, ev in enumerate(events):
        _append_unique_trace_row(trace, seen, _trace_event_row(ev, idx))

    assistant_idx = 0
    for msg in history:
        if msg.get("role") != "assistant":
            continue
        _append_unique_trace_row(trace, seen, _trace_message_row(msg, assistant_idx))
        assistant_idx += 1
    return trace


def _append_unique_trace_row(
    trace: list[dict[str, Any]],
    seen: set[str],
    item: tuple[str, dict[str, Any]] | None,
) -> None:
    if not item:
        return
    key, row = item
    if key in seen:
        return
    if row.get("source") == "chat" and trace:
        if _routing_fingerprint(trace[-1]) == _routing_fingerprint(row):
            return
    seen.add(key)
    trace.append(row)


def _append_draft_section(lines: list[str], sess: dict[str, Any]) -> None:
    if sess.get("draft"):
        d = sess["draft"]
        lines.append("## Szkic (nieużywany — tickety tworzone od razu z chatu)")
        lines.append(f"- tytuł: {d.get('title')}")
        lines.append(f"- shell: {d.get('shell_command') or '—'}")
        lines.append("")


def _append_session_events_section(
    lines: list[str],
    events: list[dict[str, Any]],
    *,
    limit: int,
) -> None:
    if not events:
        return
    lines.append("## Zdarzenia sesji")
    for ev in events[-limit:]:
        extra = _event_extra(ev)
        lines.append(f"- {ev.get('type')}: {ev.get('summary', '')}{extra}")
    lines.append("")


def _event_extra(ev: dict[str, Any]) -> str:
    return "".join([*_event_extra_parts(ev), _routing_event_extra(ev)])


def _event_extra_parts(ev: dict[str, Any]) -> list[str]:
    parts: list[str] = []
    if ev.get("task_id"):
        parts.append(f" task_id={ev['task_id']}")
    if ev.get("retrieval_trace_id"):
        parts.append(f" trace={ev['retrieval_trace_id']}")
    if ev.get("outcome"):
        parts.append(f" outcome={ev['outcome']}")
    return parts


def _routing_event_extra(ev: dict[str, Any]) -> str:
    routing = ev.get("routing")
    if not routing:
        return ""
    conf = int((routing.get("confidence") or 0) * 100)
    extra = f" | {routing.get('route')} @{conf}%"
    codes = ",".join((routing.get("reason_codes") or [])[:4])
    if codes:
        extra += f" [{codes}]"
    if routing.get("timing_ms") is not None:
        extra += f" {routing['timing_ms']}ms"
    return extra


def _append_rag_health_section(lines: list[str], rag: dict[str, Any]) -> None:
    if not rag:
        return
    lines.append("## RAG health (skrót)")
    lines.append(f"status: {rag.get('status')} · code: {rag.get('primary_incident_code')}")
    for check in rag.get("checks") or []:
        lines.append(f"  - {check.get('name')}: {check.get('status')} {check.get('detail', '')}")
    lines.append("")


def _append_incidents_section(lines: list[str], incidents: list[dict[str, Any]]) -> None:
    if not incidents:
        return
    lines.append("## Incydenty (ta sesja)")
    for inc in incidents:
        lines.append(
            f"- {inc.get('incident_code')} {inc.get('message', '')[:120]} "
            f"trace={inc.get('retrieval_trace_id', '')}"
        )
    lines.append("")


def _append_rag_snapshots_section(
    lines: list[str],
    bundle: dict[str, Any],
    *,
    limit: int,
) -> None:
    snapshots = _session_rag_snapshots(bundle, limit=limit)
    if not snapshots:
        return
    lines.append("## RAG snapshots (ta sesja)")
    for s in snapshots:
        lines.append(f"- {s.get('created_at')} {s.get('status')}")
    lines.append("")


def _session_rag_snapshots(
    bundle: dict[str, Any],
    *,
    limit: int,
) -> list[dict[str, Any]]:
    return [
        s
        for s in (bundle.get("rag_snapshots") or [])
        if s.get("correlation_id") == bundle.get("correlation_id")
    ][:limit]


def _append_operational_feed_section(
    lines: list[str],
    feed: list[dict[str, Any]],
    *,
    limit: int,
) -> None:
    if not feed:
        return
    lines.append("## Operational feed")
    for row in feed[:limit]:
        lines.append(
            f"- {str(row.get('occurred_at', ''))[:19]} "
            f"{row.get('event_type')} — {row.get('summary') or row.get('title', '')}"
        )
    lines.append("")


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
