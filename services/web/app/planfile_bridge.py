"""
Opcjonalna synchronizacja ticketów Mullm → planfile (Koru).

Włącz: MULLM_PLANFILE_PROJECT=/path/to/repo z .planfile/
"""

from __future__ import annotations

import os
import subprocess
from pathlib import Path
from typing import Any

from app.ticket_schemas import ImprovementTicket


def planfile_sync_enabled() -> bool:
    return bool((os.getenv("MULLM_PLANFILE_PROJECT") or "").strip())


def planfile_project_path() -> Path | None:
    raw = (os.getenv("MULLM_PLANFILE_PROJECT") or "").strip()
    if not raw:
        return None
    path = Path(raw).expanduser().resolve()
    if not (path / ".planfile").is_dir() and not (path / "planfile.yaml").exists():
        return None
    return path


def sync_improvement_ticket(ticket: dict[str, Any]) -> dict[str, Any] | None:
    """
    Tworzy ticket planfile z improvement_ticket (best-effort).
    Zwraca {planfile_id, ok, detail} lub None gdy wyłączone.
    """
    project = planfile_project_path()
    if not project:
        return None
    parsed = ImprovementTicket.model_validate(ticket)
    cmd = _build_create_cmd(parsed)
    try:
        proc = subprocess.run(
            cmd,
            cwd=str(project),
            capture_output=True,
            text=True,
            timeout=30,
            check=False,
        )
    except (OSError, subprocess.TimeoutExpired) as exc:
        return {"ok": False, "detail": str(exc)}
    if proc.returncode != 0:
        detail = (proc.stderr or proc.stdout or "").strip()[:500]
        return {"ok": False, "detail": detail or f"exit {proc.returncode}"}
    planfile_id = _parse_created_id(proc.stdout or "")
    return {
        "ok": True,
        "planfile_id": planfile_id,
        "detail": (proc.stdout or "").strip()[:200],
    }


def _build_create_cmd(ticket: ImprovementTicket) -> list[str]:
    cmd = [
        "planfile",
        "ticket",
        "create",
        ticket.planfile_title(),
        "--priority",
        "medium",
        "--source",
        "mullm.routing",
        "--description",
        ticket.planfile_description(),
    ]
    for label in ticket.planfile_labels():
        cmd.extend(["--label", label])
    files = _improvement_files(ticket)
    for fp in files:
        cmd.extend(["--files", fp])
    return cmd


def _improvement_files(ticket: ImprovementTicket) -> list[str]:
    """Pliki do edycji przy poprawie routingu."""
    out: list[str] = []
    if ticket.expected_route or ticket.actual_route:
        out.append("services/web/data/routing_policy.yaml")
        out.append("services/web/app/prompt_router.py")
        out.append("services/web/app/chat.py")
    return out


def _parse_created_id(stdout: str) -> str | None:
    for line in stdout.splitlines():
        line = line.strip()
        if not line:
            continue
        for token in line.replace(",", " ").split():
            if "-" in token and any(c.isdigit() for c in token):
                return token.strip("'\"")
    return None
