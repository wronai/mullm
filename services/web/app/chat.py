from __future__ import annotations

import re
import uuid
from typing import Any

import httpx

_FILE_LIST_INTENT = re.compile(
    r"(lista\s+plik|jakie\s+pliki|poka[zż]\s+plik|wykaz\s+plik|"
    r"list\s+files|show\s+files|dost[eę]pne\s+plik|"
    r"co\s+jest\s+w\s+indeks|pliki\s+w\s+scope|zasoby\s+w\s+systemie)",
    re.IGNORECASE,
)

ORCHESTRATOR_URL = None  # set from main


def _orch() -> str:
    import os

    return ORCHESTRATOR_URL or os.getenv(
        "ORCHESTRATOR_URL", os.getenv("MULLM_ORCHESTRATOR_URL", "http://orchestrator:8000")
    )


def _projector() -> str:
    import os

    return os.getenv(
        "PROJECTOR_URL",
        os.getenv("MULLM_PROJECTOR_URL", "http://projector:8000"),
    )


def is_file_list_intent(message: str) -> bool:
    text = (message or "").strip()
    if _FILE_LIST_INTENT.search(text):
        return True
    # literówki: „liat plikoq”
    lowered = text.lower()
    if re.search(r"l[i1][sa]t?\s+plik", lowered):
        return True
    if "plik" in lowered and any(w in lowered for w in ("lista", "list", "wykaz", "poka")):
        return True
    return False


def file_list_scope(message: str) -> str:
    """
    Zakres listy: all | user | system | session | rag.
    Np. „lista plikow usera” → user.
    """
    lowered = (message or "").lower()
    if re.search(r"\b(systemu|systemow[eay]?|systemowe|system\b)", lowered):
        return "system"
    if re.search(
        r"\b(usera|użytkownika|uzytkownika|użytkownik|user\b|moje\s+plik|wgrane|upload)",
        lowered,
    ):
        return "user"
    if re.search(r"\b(rag|indeks|indeksie)\b", lowered) and "plik" in lowered:
        return "rag"
    if re.search(r"\b(scope|sesji|tej\s+sesji)\b", lowered):
        return "session"
    return "all"


def _uri_is_user_resource(uri: str) -> bool:
    u = (uri or "").lower()
    if u.startswith("mullm://localfs/"):
        return True
    if u.startswith("file://"):
        return True
    if "/inbox/" in u or "/upload" in u:
        return True
    return False


def _uri_is_system_resource(uri: str) -> bool:
    u = (uri or "").lower()
    if u.startswith("mullm://ticket/"):
        return True
    if u.startswith("mullm://") and not _uri_is_user_resource(uri):
        return True
    return False


def filter_file_inventory(
    inventory: dict[str, Any],
    list_scope: str,
    *,
    scope_files: list[str] | None = None,
    scope_uris: list[str] | None = None,
) -> dict[str, Any]:
    """Filtruje rejestr i RAG według zakresu."""
    resources = list(inventory.get("resources") or [])
    rag_docs = list(inventory.get("rag_documents") or [])
    scope_files = scope_files or []
    scope_uris = scope_uris or []

    if list_scope == "user":
        resources = [r for r in resources if _uri_is_user_resource(r.get("uri") or "")]
        rag_docs = [d for d in rag_docs if _uri_is_user_resource(d.get("uri") or "")]
    elif list_scope == "system":
        resources = [r for r in resources if _uri_is_system_resource(r.get("uri") or "")]
        rag_docs = [d for d in rag_docs if _uri_is_system_resource(d.get("uri") or "")]
    elif list_scope == "session":
        uri_set = {u for u in scope_uris if _uri_is_user_resource(u)}
        resources = [r for r in resources if (r.get("uri") or "") in uri_set]
        rag_docs = [d for d in rag_docs if (d.get("uri") or "") in uri_set]
    elif list_scope == "rag":
        resources = []

    return {
        **inventory,
        "resources": resources,
        "rag_documents": rag_docs,
        "list_scope": list_scope,
        "session_uploads": list(scope_files),
    }


def _dedupe_rows_by_uri(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Jeden wiersz na URI (projector/RAG czasem zwraca duplikaty)."""
    seen: set[str] = set()
    out: list[dict[str, Any]] = []
    for row in rows:
        uri = (row.get("uri") or row.get("resource_id") or "").strip()
        key = uri or str(row.get("name") or row.get("document_id") or id(row))
        if key in seen:
            continue
        seen.add(key)
        out.append(row)
    return out


async def fetch_file_inventory() -> dict[str, Any]:
    inventory: dict[str, Any] = {
        "resources": [],
        "rag_documents": [],
        "errors": [],
    }
    async with httpx.AsyncClient(timeout=15.0) as client:
        try:
            r = await client.get(f"{_projector()}/projections/resources", params={"limit": 50})
            if r.status_code == 200:
                inventory["resources"] = _dedupe_rows_by_uri(r.json().get("items") or [])
            else:
                inventory["errors"].append(f"resources HTTP {r.status_code}")
        except httpx.HTTPError as exc:
            inventory["errors"].append(f"resources: {exc}")
        try:
            r = await client.get(f"{_orch()}/api/rag/documents", params={"limit": 50})
            if r.status_code == 200:
                inventory["rag_documents"] = _dedupe_rows_by_uri(r.json().get("items") or [])
            else:
                inventory["errors"].append(f"rag HTTP {r.status_code}")
        except httpx.HTTPError as exc:
            inventory["errors"].append(f"rag: {exc}")
    return inventory


def format_file_list_reply(
    inventory: dict[str, Any],
    *,
    scope_files: list[str] | None = None,
    scope_uris: list[str] | None = None,
    list_scope: str | None = None,
) -> str:
    scope_files = scope_files or []
    scope_uris = scope_uris or []
    list_scope = list_scope or inventory.get("list_scope") or "all"

    titles = {
        "all": "Zarejestrowane pliki i zasoby",
        "user": "Pliki użytkownika (wgrane, localfs)",
        "system": "Zasoby systemowe i kontekst (tickety, …)",
        "session": "Pliki w scope tej sesji",
        "rag": "Dokumenty w indeksie RAG",
    }
    lines = [titles.get(list_scope, titles["all"]), ""]

    if list_scope in ("all", "session", "user"):
        lines.append("Wgrane w tej sesji (chat):")
        if scope_files:
            for name in scope_files:
                lines.append(f"  • {name}")
        else:
            lines.append("  • (brak — użyj 📎 Załącz plik)")
        if list_scope == "all":
            lines.append("")
            lines.append("URI powiązane z sesją (kontekst, nie zawsze plik):")
            if scope_uris:
                for uri in scope_uris:
                    tag = "plik" if _uri_is_user_resource(uri) else "kontekst"
                    lines.append(f"  • {uri} ({tag})")
            else:
                lines.append("  • —")
        lines.append("")

    resources = inventory.get("resources") or []
    reg_label = {
        "user": "Rejestr — pliki użytkownika (Access Fabric)",
        "system": "Rejestr — zasoby systemowe",
        "session": "Rejestr — dopasowane do sesji",
        "rag": "Rejestr",
        "all": "Rejestr zasobów (Access Fabric)",
    }.get(list_scope, "Rejestr zasobów (Access Fabric)")
    lines.append(f"{reg_label}: {len(resources)}")
    if resources:
        for i, row in enumerate(resources, 1):
            name = row.get("name") or row.get("resource_id", "?")[:8]
            uri = row.get("uri") or "—"
            status = row.get("status") or "?"
            cls = row.get("classification") or ""
            lines.append(f"  {i}. {name} | {uri} | status={status} | {cls}")
    else:
        if list_scope == "user":
            lines.append(
                "  (brak w rejestrze — wgraj plik przez 📎; "
                "pliki użytkownika to zwykle mullm://localfs/…)"
            )
        else:
            lines.append("  (pusto — wgraj plik na dole workspace)")

    rag_docs = inventory.get("rag_documents") or []
    if list_scope != "user" or rag_docs:
        lines.append("")
        rag_label = "Indeks RAG" if list_scope != "rag" else "Indeks RAG (tylko)"
        lines.append(f"{rag_label}: {len(rag_docs)} dokument(ów)")
    if rag_docs:
        for i, doc in enumerate(rag_docs, 1):
            name = doc.get("name") or doc.get("resource_id", "?")[:8]
            uri = doc.get("uri") or "—"
            status = doc.get("status") or "?"
            chunks = doc.get("chunk_count", "?")
            lines.append(f"  {i}. {name} | {uri} | RAG={status} | chunków={chunks}")
    else:
        lines.append("  (pusto)")

    errs = inventory.get("errors") or []
    if errs:
        lines.append("")
        lines.append("Uwagi: " + "; ".join(errs))

    lines.append("")
    if list_scope == "user" and not resources and not scope_files:
        lines.append(
            "Tip: aby dodać plik użytkownika — 📎 w czacie lub skopiuj do "
            "volume Access Fabric (localfs)."
        )
    else:
        lines.append(
            "Tip: treść pliku — tryb „RAG” w czacie + konkretne pytanie o fragmencie."
        )
    return "\n".join(lines)


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


def _format_incident(payload: dict[str, Any]) -> str | None:
    incident = payload.get("incident") or {}
    code = incident.get("incident_code") or payload.get("incident_code")
    if not code and not payload.get("llm_error"):
        return None
    trace = payload.get("retrieval_trace_id") or incident.get("retrieval_trace_id")
    cid = payload.get("correlation_id") or incident.get("correlation_id")
    msg = incident.get("message") or payload.get("llm_error") or ""
    parts = [f"{code}"] if code else []
    if msg:
        parts.append(msg[:200])
    if trace:
        parts.append(f"trace={trace}")
    if cid:
        parts.append(f"correlation={cid[:8]}…")
    fallback = incident.get("fallback_taken") or payload.get("fallback_taken")
    if fallback:
        parts.append(f"fallback={fallback}")
    return " — ".join(parts)


async def handle_message(
    *,
    session_id: str,
    message: str,
    use_rag: bool = True,
    scope_files: list[str] | None = None,
    scope_uris: list[str] | None = None,
) -> dict[str, Any]:
    message = (message or "").strip()
    if not message:
        return {"error": "empty message"}

    _append(session_id, "user", message)
    sources: list[dict[str, Any]] = []
    answer: str | None = None
    last_payload: dict[str, Any] | None = None
    inventory: dict[str, Any] | None = None

    if is_file_list_intent(message):
        scope_kind = file_list_scope(message)
        inventory = filter_file_inventory(
            await fetch_file_inventory(),
            scope_kind,
            scope_files=scope_files,
            scope_uris=scope_uris,
        )
        answer = format_file_list_reply(
            inventory,
            scope_files=scope_files,
            scope_uris=scope_uris,
            list_scope=scope_kind,
        )
        use_rag = False

    async with httpx.AsyncClient(timeout=90.0) as client:
        if use_rag:
            history_block = _format_history(session_id)
            query = (
                f"Kontekst rozmowy:\n{history_block}\n\n"
                f"Aktualne pytanie użytkownika: {message}"
            )
            incident_note: str | None = None
            correlation_id = session_id
            headers = {
                "X-Correlation-ID": correlation_id,
                "X-Chat-Session-ID": session_id,
            }
            try:
                resp = await client.post(
                    f"{_orch()}/api/rag/ask",
                    json={"query": query, "limit": 6, "chat_session_id": session_id},
                    headers=headers,
                )
                if resp.status_code == 200:
                    payload = resp.json()
                    last_payload = payload
                    answer = payload.get("answer")
                    sources = payload.get("sources") or []
                    incident_note = _format_incident(payload)
                    if incident_note and answer:
                        answer = f"[{incident_note}]\n\n{answer}"
                    elif incident_note and not answer:
                        answer = f"[{incident_note}]"
                    if not answer and sources:
                        previews = [
                            f"- {s.get('name') or s.get('uri')}: {s.get('content_preview', '')[:200]}"
                            for s in sources[:4]
                        ]
                        err = payload.get("llm_error") or payload.get("reason")
                        answer = (
                            (f"Uwaga: {err}\n\n" if err else "")
                            + "Znalezione fragmenty:\n"
                            + "\n".join(previews)
                        )
                elif resp.status_code >= 500:
                    # fallback: samo wyszukiwanie bez LLM
                    search_resp = await client.post(
                        f"{_orch()}/api/rag/search",
                        json={"query": message, "limit": 6},
                    )
                    if search_resp.status_code == 200:
                        sources = search_resp.json().get("items") or []
                        if sources:
                            answer = "Wyszukiwanie (bez LLM):\n" + "\n".join(
                                f"- {s.get('content_preview', '')[:200]}"
                                for s in sources[:4]
                            )
                    if not answer:
                        diag = await client.get(
                            f"{_orch()}/api/observability/health/rag",
                            headers=headers,
                        )
                        hint = ""
                        if diag.status_code == 200:
                            d = diag.json()
                            code = d.get("primary_incident_code")
                            recs = d.get("recommendations") or []
                            hint = f" {code}" if code else ""
                            if recs:
                                hint += f" — {recs[0]}"
                        answer = (
                            f"RAG_BACKEND_UNAVAILABLE ({resp.status_code}){hint}. "
                            f"trace={headers['X-Correlation-ID'][:12]}… "
                            "Użyj formularza zadań."
                        )
                else:
                    answer = (
                        f"RAG niedostępny ({resp.status_code}). "
                        f"correlation={correlation_id[:12]}…"
                    )
            except httpx.HTTPError as exc:
                answer = f"Nie udało się połączyć z orchestratorem: {exc}"

        if not answer:
            answer = (
                "Otrzymałem wiadomość. Mogę pomóc w kontekście z plików po uploadzie "
                "lub utworzyć zadanie agenta (shell) z formularza po prawej."
            )

    _append(session_id, "assistant", answer, sources=sources)
    out: dict[str, Any] = {
        "session_id": session_id,
        "reply": answer,
        "sources": sources,
        "history": get_history(session_id),
        "correlation_id": session_id,
        "intent": "file_list" if inventory else "rag" if use_rag else "general",
    }
    if inventory:
        out["inventory"] = inventory
    if last_payload:
        out["incident"] = last_payload.get("incident")
        out["retrieval_trace_id"] = last_payload.get("retrieval_trace_id")
        out["trace_steps"] = last_payload.get("trace_steps")
    return out


async def create_task(
    *,
    title: str,
    description: str | None = None,
    shell_command: str | None = None,
    auto_assign: bool = True,
    wait_for_confirmation: bool = False,
    priority: str = "medium",
) -> dict[str, Any]:
    if wait_for_confirmation:
        auto_assign = False
    payload: dict[str, Any] = {
        "title": title,
        "description": description or "",
        "priority": priority,
        "auto_assign": auto_assign,
        "required_capabilities": ["shell"],
    }
    if shell_command:
        payload["shell_command"] = shell_command
        if not wait_for_confirmation:
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
