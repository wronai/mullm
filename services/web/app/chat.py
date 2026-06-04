from __future__ import annotations

import re
import uuid
from datetime import datetime, timezone
from typing import Any

import httpx

_FILE_LIST_INTENT = re.compile(
    r"(lista\s+plik|jakie\s+pliki|poka[zż]\s+plik|wykaz\s+plik|"
    r"list\s+files|show\s+files|list\s+user\s+files|lista\s+user\s+files|"
    r"user\s+files|lista\s+plik[oó]w\s+usera|"
    r"dost[eę]pne\s+plik|co\s+jest\s+w\s+indeks|pliki\s+w\s+scope|zasoby\s+w\s+systemie)",
    re.IGNORECASE,
)

_FILE_LIST_TITLES = {
    "all": "Zarejestrowane pliki i zasoby",
    "user": "Pliki użytkownika (wgrane, localfs)",
    "system": "Zasoby systemowe i kontekst (tickety, …)",
    "session": "Pliki w scope tej sesji",
    "rag": "Dokumenty w indeksie RAG",
}

_RESOURCE_LABELS = {
    "user": "Rejestr — pliki użytkownika (Access Fabric)",
    "system": "Rejestr — zasoby systemowe",
    "session": "Rejestr — dopasowane do sesji",
    "rag": "Rejestr",
    "all": "Rejestr zasobów (Access Fabric)",
}

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
    lowered = text.lower()
    return any(
        predicate(lowered)
        for predicate in (
            _looks_like_misspelled_file_list,
            _has_polish_file_list_words,
            _has_english_file_list_words,
            _has_user_files_phrase,
        )
    )


def _has_list_word(text: str, *, english: bool = False) -> bool:
    words = ("lista", "list", "show", "wykaz", "poka") if english else (
        "lista",
        "list",
        "wykaz",
        "poka",
    )
    return any(word in text for word in words)


def _looks_like_misspelled_file_list(text: str) -> bool:
    if re.search(r"l[i1][sa]t?\s+plik", text):
        return True
    if re.search(r"\baplik", text) and _has_list_word(text):
        return True
    return bool(re.search(r"\bpik[o0]?w", text) and _has_list_word(text))


def _has_polish_file_list_words(text: str) -> bool:
    return "plik" in text and _has_list_word(text)


def _has_english_file_list_words(text: str) -> bool:
    return bool(re.search(r"\b(files?|file)\b", text) and _has_list_word(text, english=True))


def _has_user_files_phrase(text: str) -> bool:
    return bool(
        re.search(r"\buser\s+files?\b", text)
        or re.search(r"\bfiles?\s+user\b", text)
    )


def file_list_scope(message: str) -> str:
    """
    Zakres listy: all | user | system | session | rag.
    Np. „lista plikow usera” → user.
    """
    lowered = (message or "").lower()
    if _system_scope_requested(lowered):
        return "system"
    if _user_scope_requested(lowered):
        return "user"
    if _rag_scope_requested(lowered):
        return "rag"
    if _session_scope_requested(lowered):
        return "session"
    return "all"


def _system_scope_requested(text: str) -> bool:
    return bool(re.search(r"\b(systemu|systemow[eay]?|systemowe|system\b)", text))


def _user_scope_requested(text: str) -> bool:
    return bool(
        re.search(
            r"\b(usera|użytkownika|uzytkownika|użytkownik|user\b|"
            r"user\s+files?|files?\s+user|moje\s+plik|wgrane|upload)",
            text,
        )
    )


def _rag_scope_requested(text: str) -> bool:
    return bool(re.search(r"\b(rag|indeks|indeksie)\b", text) and "plik" in text)


def _session_scope_requested(text: str) -> bool:
    return bool(re.search(r"\b(scope|sesji|tej\s+sesji)\b", text))


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

    return {
        **inventory,
        "resources": _filtered_resources(resources, list_scope, scope_uris),
        "rag_documents": _filter_rows_by_scope(rag_docs, list_scope, scope_uris),
        "list_scope": list_scope,
        "session_uploads": list(scope_files),
    }


def _filtered_resources(
    resources: list[dict[str, Any]],
    list_scope: str,
    scope_uris: list[str],
) -> list[dict[str, Any]]:
    if list_scope == "rag":
        return []
    return _filter_rows_by_scope(resources, list_scope, scope_uris)


def _filter_rows_by_scope(
    rows: list[dict[str, Any]],
    list_scope: str,
    scope_uris: list[str],
) -> list[dict[str, Any]]:
    if list_scope == "user":
        return _rows_matching_uri(rows, _uri_is_user_resource)
    if list_scope == "system":
        return _rows_matching_uri(rows, _uri_is_system_resource)
    if list_scope == "session":
        return _rows_in_session_scope(rows, scope_uris)
    return rows


def _rows_matching_uri(
    rows: list[dict[str, Any]],
    predicate,
) -> list[dict[str, Any]]:
    return [row for row in rows if predicate(row.get("uri") or "")]


def _rows_in_session_scope(
    rows: list[dict[str, Any]],
    scope_uris: list[str],
) -> list[dict[str, Any]]:
    uri_set = {uri for uri in scope_uris if _uri_is_user_resource(uri)}
    return [row for row in rows if (row.get("uri") or "") in uri_set]


def _dedupe_rows_by_uri(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Jeden wiersz na URI (projector/RAG czasem zwraca duplikaty)."""
    seen: set[str] = set()
    out: list[dict[str, Any]] = []
    for row in rows:
        key = _row_dedupe_key(row)
        if key in seen:
            continue
        seen.add(key)
        out.append(row)
    return out


def _row_dedupe_key(row: dict[str, Any]) -> str:
    uri = (row.get("uri") or row.get("resource_id") or "").strip()
    return uri or str(row.get("name") or row.get("document_id") or id(row))


async def fetch_file_inventory() -> dict[str, Any]:
    inventory: dict[str, Any] = {
        "resources": [],
        "rag_documents": [],
        "errors": [],
    }
    async with httpx.AsyncClient(timeout=15.0) as client:
        inventory["resources"] = await _fetch_inventory_rows(
            client,
            f"{_projector()}/projections/resources",
            "resources",
            inventory["errors"],
        )
        inventory["rag_documents"] = await _fetch_inventory_rows(
            client,
            f"{_orch()}/api/rag/documents",
            "rag",
            inventory["errors"],
        )
    return inventory


async def _fetch_inventory_rows(
    client: httpx.AsyncClient,
    url: str,
    label: str,
    errors: list[str],
) -> list[dict[str, Any]]:
    try:
        response = await client.get(url, params={"limit": 50})
    except httpx.HTTPError as exc:
        errors.append(f"{label}: {exc}")
        return []
    if response.status_code != 200:
        errors.append(f"{label} HTTP {response.status_code}")
        return []
    return _dedupe_rows_by_uri(response.json().get("items") or [])


def format_file_list_reply(
    inventory: dict[str, Any],
    *,
    scope_files: list[str] | None = None,
    scope_uris: list[str] | None = None,
    list_scope: str | None = None,
) -> str:
    scope_files = _safe_list(scope_files)
    scope_uris = _safe_list(scope_uris)
    list_scope = _list_scope_value(inventory, list_scope)

    lines = [_FILE_LIST_TITLES.get(list_scope, _FILE_LIST_TITLES["all"]), ""]
    _append_session_files(lines, list_scope, scope_files, scope_uris)
    resources = _safe_list(inventory.get("resources"))
    _append_resource_rows(lines, list_scope, resources)
    rag_docs = _safe_list(inventory.get("rag_documents"))
    _append_rag_rows(lines, list_scope, rag_docs)
    _append_file_list_errors(lines, _safe_list(inventory.get("errors")))
    _append_file_list_tip(lines, list_scope, resources, scope_files)
    return "\n".join(lines)


def _safe_list(value: Any) -> list[Any]:
    return value if isinstance(value, list) else []


def _list_scope_value(inventory: dict[str, Any], list_scope: str | None) -> str:
    return list_scope or inventory.get("list_scope") or "all"


def _append_session_files(
    lines: list[str],
    list_scope: str,
    scope_files: list[str],
    scope_uris: list[str],
) -> None:
    if list_scope not in ("all", "session", "user"):
        return
    _append_uploaded_session_files(lines, scope_files)
    _append_user_context_only(lines, list_scope, scope_uris)
    _append_scope_uris(lines, list_scope, scope_uris)
    lines.append("")


def _append_uploaded_session_files(lines: list[str], scope_files: list[str]) -> None:
    lines.append("Wgrane w tej sesji (chat):")
    lines.extend(f"  • {name}" for name in scope_files)
    if not scope_files:
        lines.append("  • (brak — użyj 📎 Załącz plik)")


def _append_user_context_only(
    lines: list[str],
    list_scope: str,
    scope_uris: list[str],
) -> None:
    if list_scope == "user":
        ctx_only = [u for u in scope_uris if not _uri_is_user_resource(u)]
        if ctx_only:
            lines.append("")
            lines.append("Powiązany kontekst (nie plik użytkownika):")
            for uri in ctx_only:
                lines.append(f"  • {uri}")


def _append_scope_uris(
    lines: list[str],
    list_scope: str,
    scope_uris: list[str],
) -> None:
    if list_scope == "all":
        lines.append("")
        lines.append("URI powiązane z sesją (kontekst, nie zawsze plik):")
        lines.extend(_format_scope_uri(uri) for uri in scope_uris)
        if not scope_uris:
            lines.append("  • —")


def _format_scope_uri(uri: str) -> str:
    tag = "plik" if _uri_is_user_resource(uri) else "kontekst"
    return f"  • {uri} ({tag})"


def _append_resource_rows(
    lines: list[str],
    list_scope: str,
    resources: list[dict[str, Any]],
) -> None:
    label = _RESOURCE_LABELS.get(list_scope, _RESOURCE_LABELS["all"])
    lines.append(f"{label}: {len(resources)}")
    if not resources:
        lines.append(_empty_resource_hint(list_scope))
        return
    for i, row in enumerate(resources, 1):
        lines.append(_format_resource_row(i, row))


def _format_resource_row(index: int, row: dict[str, Any]) -> str:
    name = row.get("name") or row.get("resource_id", "?")[:8]
    uri = row.get("uri") or "—"
    status = row.get("status") or "?"
    cls = row.get("classification") or ""
    return f"  {index}. {name} | {uri} | status={status} | {cls}"


def _empty_resource_hint(list_scope: str) -> str:
    if list_scope == "user":
        return (
            "  (brak w rejestrze — wgraj plik przez 📎; "
            "pliki użytkownika to zwykle mullm://localfs/…)"
        )
    return "  (pusto — wgraj plik na dole workspace)"


def _append_rag_rows(
    lines: list[str],
    list_scope: str,
    rag_docs: list[dict[str, Any]],
) -> None:
    if list_scope == "user" and not rag_docs:
        return
    lines.append("")
    lines.append(f"{_rag_rows_label(list_scope)}: {len(rag_docs)} dokument(ów)")
    if not rag_docs:
        lines.append("  (pusto)")
        return
    for i, doc in enumerate(rag_docs, 1):
        lines.append(_format_rag_doc_row(i, doc))


def _rag_rows_label(list_scope: str) -> str:
    return "Indeks RAG" if list_scope != "rag" else "Indeks RAG (tylko)"


def _format_rag_doc_row(index: int, doc: dict[str, Any]) -> str:
    name = doc.get("name") or doc.get("resource_id", "?")[:8]
    uri = doc.get("uri") or "—"
    status = doc.get("status") or "?"
    chunks = doc.get("chunk_count", "?")
    return f"  {index}. {name} | {uri} | RAG={status} | chunków={chunks}"


def _append_file_list_errors(lines: list[str], errors: list[str]) -> None:
    if errors:
        lines.append("")
        lines.append("Uwagi: " + "; ".join(errors))


def _append_file_list_tip(
    lines: list[str],
    list_scope: str,
    resources: list[dict[str, Any]],
    scope_files: list[str],
) -> None:
    lines.append("")
    if list_scope == "user" and not resources and not scope_files:
        lines.append(
            "Tip: aby dodać plik użytkownika — 📎 w czacie lub skopiuj do "
            "volume Access Fabric (localfs)."
        )
        lines.append(
            "ℹ Źródło listy: rejestr Mullm (Access Fabric + RAG), nie dysk hosta. "
            "Shell agent nie jest używany — do ls na hoście użyj trybu Shell / run …"
        )
        return
    if list_scope == "user":
        lines.append(
            "ℹ Lista z rejestru Mullm (nie shell). Shell agent = osobne tickety, nie ta komenda."
        )
        return
    lines.append(
        "Tip: treść pliku — tryb „RAG” w czacie + konkretne pytanie o fragmencie."
    )


def build_file_list_artifact(
    reply_text: str,
    inventory: dict[str, Any],
    *,
    session_id: str,
    list_scope: str,
) -> dict[str, Any]:
    """Artefakt do pobrania w UI (Blob) lub ponownego exportu API."""
    ts = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    filename = f"mullm-pliki-{list_scope}-{session_id[:8]}-{ts}.txt"
    return {
        "kind": "file_list",
        "list_scope": list_scope,
        "filename": filename,
        "mime": "text/plain; charset=utf-8",
        "text": reply_text,
        "json": inventory,
    }


_sessions: dict[str, list[dict[str, Any]]] = {}


def new_session_id() -> str:
    return str(uuid.uuid4())


def get_history(session_id: str) -> list[dict[str, Any]]:
    return list(_sessions.get(session_id, []))


def _append(session_id: str, role: str, content: str, **extra: Any) -> None:
    _sessions.setdefault(session_id, []).append({"role": role, "content": content, **extra})


def stamp_last_assistant_routing(session_id: str, routing: dict[str, Any]) -> None:
    """Dołącza decyzję routera do ostatniej wiadomości asystenta (badge w UI)."""
    items = _sessions.get(session_id)
    if not items:
        return
    for i in range(len(items) - 1, -1, -1):
        if items[i].get("role") == "assistant":
            items[i]["routing"] = routing
            return


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
    parts = [f"{code}"] if code else []
    parts.extend(_incident_detail_parts(payload, incident))
    return " — ".join(parts)


def _incident_detail_parts(
    payload: dict[str, Any],
    incident: dict[str, Any],
) -> list[str]:
    return [
        part
        for part in (
            _incident_message_part(payload, incident),
            _incident_trace_part(payload, incident),
            _incident_correlation_part(payload, incident),
            _incident_fallback_part(payload, incident),
        )
        if part
    ]


def _incident_message_part(
    payload: dict[str, Any],
    incident: dict[str, Any],
) -> str | None:
    msg = incident.get("message") or payload.get("llm_error") or ""
    return msg[:200] if msg else None


def _incident_trace_part(
    payload: dict[str, Any],
    incident: dict[str, Any],
) -> str | None:
    trace = payload.get("retrieval_trace_id") or incident.get("retrieval_trace_id")
    return f"trace={trace}" if trace else None


def _incident_correlation_part(
    payload: dict[str, Any],
    incident: dict[str, Any],
) -> str | None:
    cid = payload.get("correlation_id") or incident.get("correlation_id")
    return f"correlation={cid[:8]}…" if cid else None


def _incident_fallback_part(
    payload: dict[str, Any],
    incident: dict[str, Any],
) -> str | None:
    fallback = incident.get("fallback_taken") or payload.get("fallback_taken")
    return f"fallback={fallback}" if fallback else None


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
    last_payload: dict[str, Any] | None = None
    inventory, answer, use_rag = await _file_list_answer(
        message,
        use_rag=use_rag,
        scope_files=scope_files,
        scope_uris=scope_uris,
    )

    if use_rag:
        rag = await _ask_rag(session_id=session_id, message=message)
        answer = rag["answer"]
        sources = rag["sources"]
        last_payload = rag.get("payload")

    answer = answer or _default_chat_reply()

    _append(session_id, "assistant", answer, sources=sources)
    return _message_response(
        session_id=session_id,
        answer=answer,
        sources=sources,
        inventory=inventory,
        use_rag=use_rag,
        last_payload=last_payload,
    )


async def _file_list_answer(
    message: str,
    *,
    use_rag: bool,
    scope_files: list[str] | None,
    scope_uris: list[str] | None,
) -> tuple[dict[str, Any] | None, str | None, bool]:
    if not is_file_list_intent(message):
        return None, None, use_rag
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
    return inventory, answer, False


async def probe_rag(
    *,
    session_id: str,
    message: str,
    limit: int = 4,
) -> dict[str, Any]:
    """Lekkie wyszukiwanie RAG (bez LLM) — krok rag_probe w polityce ingress."""
    async with httpx.AsyncClient(timeout=30.0) as client:
        try:
            resp = await client.post(
                f"{_orch()}/api/rag/search",
                json={"query": message, "limit": limit},
                headers=_rag_headers(session_id),
            )
            if resp.status_code != 200:
                return {"hits": 0, "sources": [], "payload": None}
            payload = resp.json()
            items = payload.get("items") or []
            return {
                "hits": len(items),
                "sources": items,
                "payload": payload,
                "retrieval_trace_id": payload.get("retrieval_trace_id"),
            }
        except httpx.HTTPError:
            return {"hits": 0, "sources": [], "payload": None}


async def _ask_rag(*, session_id: str, message: str) -> dict[str, Any]:
    headers = _rag_headers(session_id)
    query = _rag_query(session_id, message)
    async with httpx.AsyncClient(timeout=90.0) as client:
        try:
            resp = await client.post(
                f"{_orch()}/api/rag/ask",
                json={"query": query, "limit": 6, "chat_session_id": session_id},
                headers=headers,
            )
            if resp.status_code == 200:
                payload = resp.json()
                sources = payload.get("sources") or []
                return {
                    "answer": _answer_from_rag_payload(payload, sources),
                    "sources": sources,
                    "payload": payload,
                }
            if resp.status_code >= 500:
                return await _rag_backend_fallback(
                    client,
                    message=message,
                    headers=headers,
                    status_code=resp.status_code,
                )
            return {
                "answer": (
                    f"RAG niedostępny ({resp.status_code}). "
                    f"correlation={session_id[:12]}…"
                ),
                "sources": [],
                "payload": None,
            }
        except httpx.HTTPError as exc:
            return {
                "answer": f"Nie udało się połączyć z orchestratorem: {exc}",
                "sources": [],
                "payload": None,
            }


def _rag_headers(session_id: str) -> dict[str, str]:
    return {
        "X-Correlation-ID": session_id,
        "X-Chat-Session-ID": session_id,
    }


def _rag_query(session_id: str, message: str) -> str:
    history_block = _format_history(session_id)
    return (
        f"Kontekst rozmowy:\n{history_block}\n\n"
        f"Aktualne pytanie użytkownika: {message}"
    )


def _answer_from_rag_payload(
    payload: dict[str, Any],
    sources: list[dict[str, Any]],
) -> str | None:
    answer = payload.get("answer")
    incident_note = _format_incident(payload)
    if incident_note and answer:
        return f"[{incident_note}]\n\n{answer}"
    if incident_note:
        return f"[{incident_note}]"
    if sources and not answer:
        return _sources_fallback_answer(payload, sources)
    return answer


def _sources_fallback_answer(
    payload: dict[str, Any],
    sources: list[dict[str, Any]],
) -> str:
    err = payload.get("llm_error") or payload.get("reason")
    prefix = f"Uwaga: {err}\n\n" if err else ""
    return prefix + "Znalezione fragmenty:\n" + "\n".join(
        _source_preview(source) for source in sources[:4]
    )


def _source_preview(source: dict[str, Any]) -> str:
    label = source.get("name") or source.get("uri")
    return f"- {label}: {source.get('content_preview', '')[:200]}"


async def _rag_backend_fallback(
    client: httpx.AsyncClient,
    *,
    message: str,
    headers: dict[str, str],
    status_code: int,
) -> dict[str, Any]:
    search = await _rag_search_fallback(client, message)
    if search["answer"]:
        return search
    return {
        "answer": await _rag_unavailable_answer(client, headers, status_code),
        "sources": [],
        "payload": None,
    }


async def _rag_search_fallback(
    client: httpx.AsyncClient,
    message: str,
) -> dict[str, Any]:
    search_resp = await client.post(
        f"{_orch()}/api/rag/search",
        json={"query": message, "limit": 6},
    )
    if search_resp.status_code != 200:
        return {"answer": None, "sources": [], "payload": None}
    sources = search_resp.json().get("items") or []
    if not sources:
        return {"answer": None, "sources": [], "payload": None}
    answer = "Wyszukiwanie (bez LLM):\n" + "\n".join(
        f"- {s.get('content_preview', '')[:200]}" for s in sources[:4]
    )
    return {"answer": answer, "sources": sources, "payload": None}


async def _rag_unavailable_answer(
    client: httpx.AsyncClient,
    headers: dict[str, str],
    status_code: int,
) -> str:
    hint = await _rag_diagnostics_hint(client, headers)
    return (
        f"RAG_BACKEND_UNAVAILABLE ({status_code}){hint}. "
        f"trace={headers['X-Correlation-ID'][:12]}… "
        "Użyj formularza zadań."
    )


async def _rag_diagnostics_hint(
    client: httpx.AsyncClient,
    headers: dict[str, str],
) -> str:
    diag = await client.get(f"{_orch()}/api/observability/health/rag", headers=headers)
    if diag.status_code != 200:
        return ""
    data = diag.json()
    hint = f" {data.get('primary_incident_code')}" if data.get("primary_incident_code") else ""
    recs = data.get("recommendations") or []
    if recs:
        hint += f" — {recs[0]}"
    return hint


def _default_chat_reply() -> str:
    return (
        "Otrzymałem wiadomość. Mogę pomóc w kontekście z plików po uploadzie "
        "lub utworzyć zadanie agenta (shell) z formularza po prawej."
    )


def _message_response(
    *,
    session_id: str,
    answer: str,
    sources: list[dict[str, Any]],
    inventory: dict[str, Any] | None,
    use_rag: bool,
    last_payload: dict[str, Any] | None,
) -> dict[str, Any]:
    out: dict[str, Any] = {
        "session_id": session_id,
        "reply": answer,
        "sources": sources,
        "history": get_history(session_id),
        "correlation_id": session_id,
        "intent": _response_intent(inventory, use_rag),
    }
    _attach_inventory_response(out, answer, inventory, session_id)
    _attach_trace_response(out, last_payload)
    return out


def _response_intent(inventory: dict[str, Any] | None, use_rag: bool) -> str:
    if inventory:
        return "file_list"
    return "rag" if use_rag else "general"


def _attach_inventory_response(
    out: dict[str, Any],
    answer: str,
    inventory: dict[str, Any] | None,
    session_id: str,
) -> None:
    if not inventory:
        return
    out["inventory"] = inventory
    out["artifact"] = build_file_list_artifact(
        answer or "",
        inventory,
        session_id=session_id,
        list_scope=inventory.get("list_scope") or "all",
    )


def _attach_trace_response(
    out: dict[str, Any],
    last_payload: dict[str, Any] | None,
) -> None:
    if not last_payload:
        return
    out["incident"] = last_payload.get("incident")
    out["retrieval_trace_id"] = last_payload.get("retrieval_trace_id")
    out["trace_steps"] = last_payload.get("trace_steps")


async def create_task(
    *,
    title: str,
    description: str | None = None,
    shell_command: str | None = None,
    auto_assign: bool = True,
    wait_for_confirmation: bool = False,
    priority: str = "medium",
    agent_id: str | None = None,
) -> dict[str, Any]:
    payload = _task_create_payload(
        title=title,
        description=description,
        shell_command=shell_command,
        auto_assign=auto_assign,
        wait_for_confirmation=wait_for_confirmation,
        priority=priority,
        agent_id=agent_id,
    )
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


def _task_create_payload(
    *,
    title: str,
    description: str | None,
    shell_command: str | None,
    auto_assign: bool,
    wait_for_confirmation: bool,
    priority: str,
    agent_id: str | None,
) -> dict[str, Any]:
    payload: dict[str, Any] = {
        "title": title,
        "description": description or "",
        "priority": priority,
        "auto_assign": auto_assign and not wait_for_confirmation,
        "required_capabilities": ["shell"],
    }
    _apply_task_agent(payload, agent_id)
    _apply_task_shell(payload, shell_command, wait_for_confirmation, agent_id)
    return payload


def _apply_task_agent(payload: dict[str, Any], agent_id: str | None) -> None:
    if not agent_id:
        return
    payload["agent_id"] = agent_id
    payload["auto_assign"] = False


def _apply_task_shell(
    payload: dict[str, Any],
    shell_command: str | None,
    wait_for_confirmation: bool,
    agent_id: str | None,
) -> None:
    if not shell_command:
        return
    payload["shell_command"] = shell_command
    if not wait_for_confirmation and not agent_id:
        payload["auto_assign"] = True
