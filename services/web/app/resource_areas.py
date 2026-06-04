"""
Obszary dostępu (Resource Areas) — manifesty konektorów + etykiety/grupy.

Rozszerzalne: nowy obszar = wpis w AREA_CATALOG + connector (później).
"""

from __future__ import annotations

from typing import Any

# area_id → definicja
AREA_CATALOG: dict[str, dict[str, Any]] = {
    "email": {
        "title": "Skrzynka e-mail",
        "connector_type": "email",
        "risk_level": "high",
        "default_policy": "approval",
        "supported_actions": ["read", "search", "send"],
        "labels": ["communication", "external"],
    },
    "filesystem:user": {
        "title": "Pliki użytkownika",
        "connector_type": "localfs",
        "risk_level": "medium",
        "default_policy": "scoped",
        "supported_actions": ["read", "write", "list"],
        "labels": ["filesystem", "user-owned"],
    },
    "filesystem:system": {
        "title": "Pliki systemu",
        "connector_type": "localfs",
        "risk_level": "high",
        "default_policy": "approval",
        "supported_actions": ["read", "list"],
        "labels": ["filesystem", "system", "sensitive"],
    },
    "services:system": {
        "title": "Usługi systemowe",
        "connector_type": "systemd",
        "risk_level": "high",
        "default_policy": "approval",
        "supported_actions": ["status", "logs", "restart"],
        "labels": ["ops", "system"],
    },
    "browser:chrome": {
        "title": "Przeglądarka Chrome",
        "connector_type": "browser",
        "risk_level": "high",
        "default_policy": "approval",
        "supported_actions": ["navigate", "snapshot", "click"],
        "labels": ["browser", "ui"],
    },
    "docker": {
        "title": "Docker",
        "connector_type": "docker",
        "risk_level": "high",
        "default_policy": "approval",
        "supported_actions": ["ps", "logs", "exec"],
        "labels": ["containers", "ops"],
    },
    "http": {
        "title": "HTTP / API",
        "connector_type": "http",
        "risk_level": "medium",
        "default_policy": "allow_read",
        "supported_actions": ["get", "post"],
        "labels": ["network"],
    },
    "mullm:rag": {
        "title": "Mullm RAG + Access Fabric",
        "connector_type": "mullm",
        "risk_level": "low",
        "default_policy": "allow",
        "supported_actions": ["list", "search", "read"],
        "labels": ["mullm", "readonly", "local"],
    },
}

# role_id → dozwolone area_id (MVP — rozszerzane grantami runtime)
DEFAULT_ROLE_SCOPES: dict[str, list[str]] = {
    "coordinator": ["mullm:rag", "http"],
    "files_agent": ["mullm:rag", "filesystem:user"],
    "shell_agent": ["mullm:rag", "filesystem:user", "docker"],
    "mail_agent": ["email"],
    "browser_agent": ["browser:chrome"],
}

LABEL_VOCABULARY = [
    "prod",
    "dev",
    "readonly",
    "sensitive",
    "pii",
    "local",
    "admin",
    "user-owned",
    "mullm",
]


def list_areas() -> list[dict[str, Any]]:
    return [{"area_id": k, **v} for k, v in AREA_CATALOG.items()]


def list_groups() -> list[dict[str, Any]]:
    """Grupy logiczne — filtrowanie polityk po labelach."""
    return [
        {
            "group_id": "mullm-local",
            "title": "Zasoby Mullm (lokalne)",
            "labels": ["mullm", "local", "readonly"],
            "area_ids": ["mullm:rag", "filesystem:user"],
        },
        {
            "group_id": "ops-high-risk",
            "title": "Operacje wysokiego ryzyka",
            "labels": ["ops", "system", "sensitive"],
            "area_ids": ["filesystem:system", "services:system", "docker"],
        },
        {
            "group_id": "external-comms",
            "title": "Komunikacja zewnętrzna",
            "labels": ["communication", "external"],
            "area_ids": ["email", "http"],
        },
    ]


def agent_may_access(role_id: str, area_id: str, action: str = "read") -> dict[str, Any]:
    """Decyzja MVP: allow | deny | approval."""
    areas = DEFAULT_ROLE_SCOPES.get(role_id, [])
    meta = AREA_CATALOG.get(area_id)
    if not meta:
        return {"decision": "deny", "reason": "unknown_area"}
    if area_id not in areas:
        return {"decision": "deny", "reason": "role_not_in_scope"}
    policy = meta.get("default_policy", "approval")
    if policy == "allow":
        return {"decision": "allow", "area_id": area_id, "action": action}
    if policy == "allow_read" and action in ("read", "search", "list", "get"):
        return {"decision": "allow", "area_id": area_id, "action": action}
    if policy == "approval":
        return {"decision": "approval", "area_id": area_id, "action": action}
    return {"decision": "allow", "area_id": area_id, "action": action}
