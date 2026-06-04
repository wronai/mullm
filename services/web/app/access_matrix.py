"""
Macierze dostępu: agenci × zasoby oraz human × agenci (checkboxy w UI /access).
Domyślnie wszystkie zaznaczone (allow).
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any

import yaml

from app.resource_areas import AREA_CATALOG, DEFAULT_ROLE_SCOPES

_DEFAULT_AGENTS = [
    {"id": "coordinator", "title": "Coordinator"},
    {"id": "files_agent", "title": "Files Agent"},
    {"id": "shell_agent", "title": "Shell Agent"},
    {"id": "mail_agent", "title": "Mail Agent"},
    {"id": "browser_agent", "title": "Browser Agent"},
    {"id": "ops_agent", "title": "Ops Agent"},
    {"id": "user", "title": "User (chat)"},
]

_DEFAULT_HUMANS = [
    {"id": "human@localhost", "title": "Human — ten komputer"},
    {"id": "human@laptop", "title": "Human — laptop"},
    {"id": "human@desktop", "title": "Human — stacja robocza"},
]


def _matrix_path() -> Path:
    env = os.getenv("MULLM_ACCESS_MATRIX_PATH")
    if env:
        return Path(env)
    return Path(__file__).resolve().parent.parent / "data" / "access_matrices.yaml"


def _default_resources() -> list[dict[str, str]]:
    return [
        {"id": area_id, "title": meta.get("title") or area_id}
        for area_id, meta in AREA_CATALOG.items()
    ]


def _default_agents() -> list[dict[str, str]]:
    seen: set[str] = set()
    out: list[dict[str, str]] = []
    for item in _DEFAULT_AGENTS:
        if item["id"] not in seen:
            seen.add(item["id"])
            out.append(item)
    for role_id in DEFAULT_ROLE_SCOPES:
        if role_id not in seen:
            seen.add(role_id)
            out.append({"id": role_id, "title": role_id.replace("_", " ").title()})
    return out


def _empty_agent_resource(
    resources: list[dict[str, str]], agents: list[dict[str, str]], *, default: bool
) -> dict[str, dict[str, bool]]:
    return {
        r["id"]: {a["id"]: default for a in agents} for r in resources
    }


def _empty_human_agent(
    agents: list[dict[str, str]], humans: list[dict[str, str]], *, default: bool
) -> dict[str, dict[str, bool]]:
    return {a["id"]: {h["id"]: default for h in humans} for a in agents}


def default_state() -> dict[str, Any]:
    resources = _default_resources()
    agents = _default_agents()
    humans = list(_DEFAULT_HUMANS)
    return {
        "resources": resources,
        "agents": agents,
        "humans": humans,
        "agent_resource": _empty_agent_resource(resources, agents, default=True),
        "human_agent": _empty_human_agent(agents, humans, default=True),
        "default_all": True,
    }


def load_state() -> dict[str, Any]:
    path = _matrix_path()
    if not path.is_file():
        return default_state()
    try:
        raw = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    except (OSError, yaml.YAMLError):
        return default_state()
    base = default_state()
    for key in ("resources", "agents", "humans"):
        if raw.get(key):
            base[key] = raw[key]
    if raw.get("agent_resource"):
        base["agent_resource"] = _merge_bool_matrix(
            base["agent_resource"], raw["agent_resource"]
        )
    if raw.get("human_agent"):
        base["human_agent"] = _merge_bool_matrix(base["human_agent"], raw["human_agent"])
    base["default_all"] = bool(raw.get("default_all", True))
    base = _reindex_state(base)
    return base


def _merge_bool_matrix(
    base: dict[str, dict[str, bool]], patch: dict[str, Any]
) -> dict[str, dict[str, bool]]:
    out = {rid: dict(cols) for rid, cols in base.items()}
    for row_id, cols in (patch or {}).items():
        if row_id not in out:
            out[row_id] = {}
        for col_id, val in (cols or {}).items():
            out[row_id][col_id] = bool(val)
    return out


def _reindex_state(state: dict[str, Any]) -> dict[str, Any]:
    """Uzupełnia brakujące wiersze/kolumny po edycji list agentów/human/zasobów."""
    resources = state.get("resources") or _default_resources()
    agents = state.get("agents") or _default_agents()
    humans = state.get("humans") or list(_DEFAULT_HUMANS)
    ar = state.get("agent_resource") or {}
    ha = state.get("human_agent") or {}
    default = bool(state.get("default_all", True))
    new_ar: dict[str, dict[str, bool]] = {}
    for r in resources:
        rid = r["id"]
        row = dict(ar.get(rid) or {})
        for a in agents:
            row.setdefault(a["id"], default)
        new_ar[rid] = row
    new_ha: dict[str, dict[str, bool]] = {}
    for a in agents:
        aid = a["id"]
        row = dict(ha.get(aid) or {})
        for h in humans:
            row.setdefault(h["id"], default)
        new_ha[aid] = row
    return {
        **state,
        "resources": resources,
        "agents": agents,
        "humans": humans,
        "agent_resource": new_ar,
        "human_agent": new_ha,
    }


def save_state(state: dict[str, Any]) -> dict[str, Any]:
    state = _reindex_state(state)
    path = _matrix_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "default_all": state.get("default_all", True),
        "resources": state["resources"],
        "agents": state["agents"],
        "humans": state["humans"],
        "agent_resource": state["agent_resource"],
        "human_agent": state["human_agent"],
    }
    path.write_text(
        yaml.safe_dump(payload, allow_unicode=True, sort_keys=False),
        encoding="utf-8",
    )
    return state


def agent_may_access_resource(agent_id: str, resource_id: str) -> bool:
    state = load_state()
    row = state.get("agent_resource") or {}
    cols = row.get(resource_id) or {}
    if agent_id in cols:
        return bool(cols[agent_id])
    return bool(state.get("default_all", True))


def human_may_use_agent(human_id: str, agent_id: str) -> bool:
    state = load_state()
    row = state.get("human_agent") or {}
    cols = row.get(agent_id) or {}
    if human_id in cols:
        return bool(cols[human_id])
    return bool(state.get("default_all", True))


def diagnose_file_list_command() -> dict[str, Any]:
    """Wyjaśnienie: lista plików ≠ shell, ≠ dysk hosta."""
    return {
        "uses_shell_agent": False,
        "uses_host_filesystem_directly": False,
        "data_sources": [
            "GET projector /projections/resources (Access Fabric)",
            "GET orchestrator /api/rag/documents (indeks RAG)",
        ],
        "user_scope_filter": "mullm://localfs/, file://, upload/inbox — bez mullm://ticket/",
        "shell_agent_role": "Wykonanie poleceń przez ticket/shell-agent (np. run ls -la), nie lista rejestru",
        "typical_wrong_expectation": "Odpowiedź z ls /home/user zamiast zarejestrowanych URI w Mullm",
    }
