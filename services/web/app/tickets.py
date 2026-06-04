from __future__ import annotations

from typing import Any

# Statusy widoczne w UI (kolor + etykieta PL)
STATUS_UI: dict[str, dict[str, str]] = {
    "draft": {"label": "Szkic", "color": "#a78bfa", "phase": "nieutworzony"},
    "pending": {"label": "Kolejka", "color": "#8b9bb4", "phase": "oczekuje"},
    "assigned": {"label": "Przypisany", "color": "#3d8bfd", "phase": "oczekuje"},
    "running": {"label": "W toku", "color": "#f0b429", "phase": "aktywny"},
    "completed": {"label": "Zrobiony", "color": "#3dd68c", "phase": "koniec"},
    "failed": {"label": "Błąd", "color": "#ff6b6b", "phase": "koniec"},
    "archived": {"label": "Archiwum", "color": "#5c6b82", "phase": "archiwum"},
}


def ticket_uri(task_id: str) -> str:
    return f"mullm://ticket/{task_id}"


def ticket_web_path(task_id: str) -> str:
    return f"/t/{task_id}"


def status_meta(status: str, *, archived: bool = False) -> dict[str, str]:
    if archived:
        return {**STATUS_UI["archived"], "key": "archived"}
    key = (status or "pending").lower()
    meta = STATUS_UI.get(key, STATUS_UI["pending"])
    return {**meta, "key": key}


def enrich_task(row: dict[str, Any], *, archived_ids: set[str] | None = None) -> dict[str, Any]:
    tid = row.get("task_id") or ""
    archived = tid in (archived_ids or set())
    sm = status_meta(row.get("status") or "pending", archived=archived)
    return {
        **row,
        "uri": ticket_uri(tid),
        "web_url": ticket_web_path(tid),
        "status_label": sm["label"],
        "status_color": sm["color"],
        "status_key": sm["key"],
        "status_phase": sm["phase"],
    }
