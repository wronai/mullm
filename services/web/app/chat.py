from __future__ import annotations

import uuid
from typing import Any

import httpx

ORCHESTRATOR_URL = None  # set from main


def _orch() -> str:
    import os

    return ORCHESTRATOR_URL or os.getenv(
        "ORCHESTRATOR_URL", os.getenv("MULLM_ORCHESTRATOR_URL", "http://orchestrator:8000")
    )


_sessions: dict[str, list[dict[str, Any]]] = {}


def new_session_id() -> str:
    return str(uuid.uuid4())


def get_history(session_id: str) -> list[dict[str, Any]]:
    return list(_sessions.get(session_id, []))


def _append(session_id: str, role: str, content: str, **extra: Any) -> None:
    _sessions.setdefault(session_id, []).append({"role": role, "content": content, **extra})


def _format_history(session_id: str, *, limit: int = 12) -> str:
    lines = []
    for item in get_history(session_id)[-limit:]:
        role = "Użytkownik" if item["role"] == "user" else "Asystent"
        lines.append(f"{role}: {item['content']}")
    return "\n".join(lines)


async def handle_message(
    *,
    session_id: str,
    message: str,
    use_rag: bool = True,
) -> dict[str, Any]:
    message = (message or "").strip()
    if not message:
        return {"error": "empty message"}

    _append(session_id, "user", message)
    sources: list[dict[str, Any]] = []
    answer: str | None = None

    async with httpx.AsyncClient(timeout=90.0) as client:
        if use_rag:
            history_block = _format_history(session_id)
            query = (
                f"Kontekst rozmowy:\n{history_block}\n\n"
                f"Aktualne pytanie użytkownika: {message}"
            )
            try:
                resp = await client.post(
                    f"{_orch()}/api/rag/ask",
                    json={"query": query, "limit": 6},
                )
                if resp.status_code == 200:
                    payload = resp.json()
                    answer = payload.get("answer")
                    sources = payload.get("sources") or []
                    if not answer and sources:
                        previews = [
                            f"- {s.get('name') or s.get('uri')}: {s.get('content_preview', '')[:200]}"
                            for s in sources[:4]
                        ]
                        answer = (
                            "Brak odpowiedzi LLM (sprawdź OPENROUTER_API_KEY). "
                            "Znalezione fragmenty:\n" + "\n".join(previews)
                        )
                else:
                    answer = f"RAG niedostępny ({resp.status_code}). Użyj formularza zadań."
            except httpx.HTTPError as exc:
                answer = f"Nie udało się połączyć z orchestratorem: {exc}"

        if not answer:
            answer = (
                "Otrzymałem wiadomość. Mogę pomóc w kontekście z plików po uploadzie "
                "lub utworzyć zadanie agenta (shell) z formularza po prawej."
            )

    _append(session_id, "assistant", answer, sources=sources)
    return {
        "session_id": session_id,
        "reply": answer,
        "sources": sources,
        "history": get_history(session_id),
    }


async def create_task(
    *,
    title: str,
    description: str | None = None,
    shell_command: str | None = None,
    auto_assign: bool = True,
    priority: str = "medium",
) -> dict[str, Any]:
    payload: dict[str, Any] = {
        "title": title,
        "description": description or "",
        "priority": priority,
        "auto_assign": auto_assign,
        "required_capabilities": ["shell"],
    }
    if shell_command:
        payload["shell_command"] = shell_command
        payload["auto_assign"] = True

    async with httpx.AsyncClient(timeout=30.0) as client:
        resp = await client.post(f"{_orch()}/api/commands/tasks", json=payload)
        if resp.status_code >= 400:
            return {"ok": False, "error": resp.text, "status": resp.status_code}
        data = resp.json()
        result = data.get("result") or {}
        return {
            "ok": True,
            "command_id": data.get("command_id"),
            "task_id": result.get("aggregate_id"),
            "events": result.get("events"),
        }
