"""
Agent Workroom — drugi chat: agenci rozmawiają między sobą i realizują kroki planu.

MVP: coordinator → files_agent / shell_agent (reguły + istniejące API Mullm).
Widoczny ledger: goal, plan, kroki, wiadomości agentów, wyniki.
"""

from __future__ import annotations

import re
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any

from app import chat as chat_service
from app import workspace as workspace_service
from app.resource_areas import agent_may_access, list_areas, list_groups


@dataclass
class LedgerEntry:
    kind: str  # goal | plan | step | message | result | permission | error
    agent_id: str
    summary: str
    detail: str = ""
    status: str = "info"  # info | running | ok | blocked | denied
    meta: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "kind": self.kind,
            "agent_id": self.agent_id,
            "summary": self.summary,
            "detail": self.detail,
            "status": self.status,
            "meta": self.meta,
        }


@dataclass
class WorkroomSession:
    workroom_id: str
    user_session_id: str | None = None
    goal: str = ""
    status: str = "idle"  # idle | running | done | error
    ledger: list[LedgerEntry] = field(default_factory=list)
    agent_thread: list[dict[str, Any]] = field(default_factory=list)
    result_summary: str = ""
    linked_task_id: str | None = None

    def add_ledger(
        self,
        kind: str,
        agent_id: str,
        summary: str,
        *,
        detail: str = "",
        status: str = "info",
        **meta: Any,
    ) -> None:
        self.ledger.append(
            LedgerEntry(
                kind=kind,
                agent_id=agent_id,
                summary=summary,
                detail=detail,
                status=status,
                meta=meta,
            )
        )

    def agent_say(self, agent_id: str, role: str, text: str, *, status: str = "info") -> None:
        self.agent_thread.append(
            {"agent_id": agent_id, "role": role, "text": text, "status": status}
        )
        self.add_ledger("message", agent_id, text[:200], detail=text, status=status)

    def to_dict(self) -> dict[str, Any]:
        return {
            "workroom_id": self.workroom_id,
            "user_session_id": self.user_session_id,
            "goal": self.goal,
            "status": self.status,
            "ledger": [e.to_dict() for e in self.ledger],
            "agent_thread": self.agent_thread,
            "result_summary": self.result_summary,
            "linked_task_id": self.linked_task_id,
        }


_workrooms: dict[str, WorkroomSession] = {}


def create_workroom(*, user_session_id: str | None = None) -> WorkroomSession:
    wid = uuid.uuid4().hex[:12]
    session = WorkroomSession(workroom_id=wid, user_session_id=user_session_id)
    _workrooms[wid] = session
    return session


def get_workroom(workroom_id: str) -> WorkroomSession | None:
    return _workrooms.get(workroom_id)


def _plan_steps(goal: str) -> list[dict[str, str]]:
    lowered = goal.lower()
    steps: list[dict[str, str]] = [
        {"id": "1", "agent": "coordinator", "action": "analyze", "label": "Analiza celu"},
    ]
    if (
        chat_service.is_file_list_intent(goal)
        or "plik" in lowered
        or re.search(r"\baplik", lowered)
    ):
        scope = chat_service.file_list_scope(goal)
        labels = {
            "user": "Lista plików użytkownika",
            "system": "Lista zasobów systemowych",
            "session": "Pliki w scope sesji",
            "rag": "Dokumenty RAG",
            "all": "Lista plików i zasobów",
        }
        steps.append(
            {
                "id": "2",
                "agent": "files_agent",
                "action": "list_files",
                "label": labels.get(scope, labels["all"]),
                "list_scope": scope,
            }
        )
    elif _extract_shell(goal):
        steps.append(
            {
                "id": "2",
                "agent": "shell_agent",
                "action": "run_shell",
                "label": "Uruchomienie polecenia shell",
            }
        )
    else:
        steps.append(
            {
                "id": "2",
                "agent": "files_agent",
                "action": "context_scan",
                "label": "Skan kontekstu (pliki + RAG)",
            }
        )
        steps.append(
            {
                "id": "3",
                "agent": "coordinator",
                "action": "summarize",
                "label": "Podsumowanie dla użytkownika",
            }
        )
    return steps


async def _build_file_list_for_goal(
    goal: str,
    *,
    scope_files: list[str],
    scope_uris: list[str],
) -> tuple[str, dict[str, Any], str]:
    scope_kind = chat_service.file_list_scope(goal)
    inv = chat_service.filter_file_inventory(
        await chat_service.fetch_file_inventory(),
        scope_kind,
        scope_files=scope_files,
        scope_uris=scope_uris,
    )
    reply = chat_service.format_file_list_reply(
        inv,
        scope_files=scope_files,
        scope_uris=scope_uris,
        list_scope=scope_kind,
    )
    return reply, inv, scope_kind


def format_workroom_export(session: WorkroomSession) -> str:
    """Pełna treść workroom do schowka (wątek + ledger + odpowiedź)."""
    lines = [
        "# Mullm — Agent Workroom export",
        f"generated_at: {datetime.now(timezone.utc).isoformat()}",
        f"workroom_id: {session.workroom_id}",
        f"user_session_id: {session.user_session_id or '—'}",
        f"status: {session.status}",
        "",
        "## Cel",
        session.goal or "—",
        "",
        "## Rozmowa agentów",
    ]
    if not session.agent_thread:
        lines.append("(brak)")
    else:
        for m in session.agent_thread:
            who = m.get("role") or m.get("agent_id") or "?"
            lines.append(f"\n### {who}")
            lines.append((m.get("text") or "").strip())
    lines.append("")
    lines.append("## Ledger wykonania")
    if not session.ledger:
        lines.append("(brak)")
    else:
        for e in session.ledger:
            lines.append(
                f"- [{e.kind}] {e.agent_id} ({e.status}): {e.summary}"
            )
            if e.detail and e.detail != e.summary:
                lines.append(f"  detail: {e.detail[:500]}")
    lines.append("")
    lines.append("## Odpowiedź dla użytkownika")
    lines.append(session.result_summary or "—")
    return "\n".join(lines).strip() + "\n"


def _extract_shell(text: str) -> str | None:
    for prefix in ("run ", "exec ", "shell ", "wykonaj ", "uruchom "):
        if text.lower().strip().startswith(prefix):
            return text[len(prefix) :].strip()
    if re.match(r"^(echo|ls|cat|git|python|npm)\s", text.strip(), re.I):
        return text.strip()
    return None


async def run_workroom(
    workroom_id: str,
    user_message: str,
    *,
    wait_for_confirmation: bool = False,
) -> dict[str, Any]:
    session = get_workroom(workroom_id)
    if not session:
        return {"ok": False, "error": "workroom not found"}

    user_message = (user_message or "").strip()
    if not user_message:
        return {"ok": False, "error": "empty message"}

    session.goal = user_message
    session.status = "running"
    session.ledger.clear()
    session.agent_thread.clear()
    session.add_ledger("goal", "user", user_message, status="info")

    steps = _plan_steps(user_message)
    plan_text = "\n".join(f"  {s['id']}. [{s['agent']}] {s['label']}" for s in steps)
    session.add_ledger("plan", "coordinator", f"Plan ({len(steps)} kroków)", detail=plan_text)
    session.agent_say(
        "coordinator",
        "Coordinator",
        f"Cel: {user_message}\nPlan:\n{plan_text}",
    )

    scope_files: list[str] = []
    scope_uris: list[str] = []
    if session.user_session_id:
        ws = workspace_service.get_session(session.user_session_id)
        if ws:
            scope_files = list(ws.context.file_names)
            scope_uris = list(ws.context.uris)

    final_parts: list[str] = []

    for step in steps:
        agent = step["agent"]
        action = step["action"]
        session.add_ledger(
            "step",
            agent,
            f"▶ {step['label']}",
            status="running",
            step_id=step["id"],
            action=action,
        )

        if agent == "coordinator" and action == "analyze":
            session.agent_say(
                "coordinator",
                "Coordinator",
                "Rozpoznano intencję i dobrano agentów (files / shell).",
                status="ok",
            )
            continue

        if agent == "files_agent":
            perm = agent_may_access("files_agent", "mullm:rag", "list")
            if perm["decision"] == "deny":
                session.add_ledger(
                    "permission",
                    "files_agent",
                    "Brak dostępu do mullm:rag",
                    status="denied",
                    **perm,
                )
                final_parts.append("Odmowa dostępu do listy plików.")
                continue
            if perm["decision"] == "approval":
                session.add_ledger(
                    "permission",
                    "files_agent",
                    "Wymaga zatwierdzenia: mullm:rag",
                    status="blocked",
                    **perm,
                )

            scope_kind = step.get("list_scope") or chat_service.file_list_scope(
                user_message
            )
            perm_user = agent_may_access("files_agent", "filesystem:user", "list")
            if scope_kind == "user" and perm_user["decision"] == "deny":
                session.add_ledger(
                    "permission",
                    "files_agent",
                    "Brak dostępu do filesystem:user",
                    status="denied",
                    **perm_user,
                )
                final_parts.append("Odmowa dostępu do plików użytkownika.")
                continue

            session.agent_say(
                "files_agent",
                "Files Agent",
                f"Pobieram rejestr (zakres: {scope_kind})…",
                status="running",
            )
            reply, inv, scope_kind = await _build_file_list_for_goal(
                user_message,
                scope_files=scope_files,
                scope_uris=scope_uris,
            )
            session.agent_say("files_agent", "Files Agent", reply, status="ok")
            session.add_ledger(
                "result",
                "files_agent",
                f"Lista plików gotowa ({scope_kind})",
                detail=reply[:2000],
                status="ok",
                list_scope=scope_kind,
            )
            if session.user_session_id:
                ws = workspace_service.get_or_create(session.user_session_id)
                artifact = chat_service.build_file_list_artifact(
                    reply,
                    inv,
                    session_id=ws.session_id,
                    list_scope=scope_kind,
                )
                workspace_service.register_artifact(
                    ws,
                    artifact,
                    source_message=user_message,
                )
            final_parts.append(reply)
            continue

        if agent == "shell_agent" and action == "run_shell":
            shell = _extract_shell(user_message)
            perm = agent_may_access("shell_agent", "filesystem:user", "read")
            session.agent_say(
                "shell_agent",
                "Shell Agent",
                f"Sprawdzam uprawnienia… ({perm['decision']})",
            )
            if not shell:
                session.agent_say(
                    "shell_agent",
                    "Shell Agent",
                    "Brak polecenia shell w wiadomości.",
                    status="blocked",
                )
                final_parts.append("Podaj polecenie, np. `run ls -la`.")
                continue
            if not session.user_session_id:
                session.agent_say(
                    "shell_agent",
                    "Shell Agent",
                    "Brak sesji workspace — nie mogę utworzyć ticketu.",
                    status="blocked",
                )
                continue
            session.agent_say(
                "shell_agent",
                "Shell Agent",
                f"Tworzę ticket i uruchamiam: `{shell}`",
                status="running",
            )
            result = await workspace_service.create_task_immediate(
                session.user_session_id,
                title=user_message[:80],
                description=user_message,
                shell_command=shell,
                wait_for_confirmation=wait_for_confirmation,
            )
            if result.get("ok"):
                tid = result.get("task_id", "?")
                session.linked_task_id = tid
                msg = f"Ticket `{tid}` — {'kolejka' if wait_for_confirmation else 'uruchomiony'}."
                session.agent_say("shell_agent", "Shell Agent", msg, status="ok")
                session.add_ledger(
                    "result",
                    "shell_agent",
                    msg,
                    status="ok",
                    task_id=tid,
                )
                final_parts.append(msg)
            else:
                err = result.get("error", "błąd")
                session.agent_say("shell_agent", "Shell Agent", err, status="blocked")
                final_parts.append(err)
            continue

        if agent == "coordinator" and action == "summarize":
            session.agent_say(
                "coordinator",
                "Coordinator",
                "Składam odpowiedź końcową dla użytkownika.",
                status="ok",
            )

    session.result_summary = (
        "\n\n".join(final_parts)
        if final_parts
        else (
            "Agenci zakończyli plan, ale nie wygenerowano treści odpowiedzi. "
            "Spróbuj: „lista plików”, „run ls -la”, lub pytanie w trybie RAG w czacie użytkownika."
        )
    )
    session.status = "done"
    session.add_ledger(
        "result",
        "coordinator",
        "Odpowiedź dla użytkownika",
        detail=session.result_summary[:3000],
        status="ok",
    )
    return {"ok": True, **session.to_dict()}


def workroom_catalog() -> dict[str, Any]:
    return {
        "areas": list_areas(),
        "groups": list_groups(),
        "agents": [
            {"id": "coordinator", "title": "Coordinator", "role": "planowanie"},
            {"id": "files_agent", "title": "Files Agent", "role": "mullm:rag, filesystem:user"},
            {"id": "shell_agent", "title": "Shell Agent", "role": "zadania shell"},
            {"id": "mail_agent", "title": "Mail Agent", "role": "email (przyszły connector)"},
            {"id": "browser_agent", "title": "Browser Agent", "role": "chrome (przyszły)"},
        ],
    }
