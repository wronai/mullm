from __future__ import annotations

import os
from typing import Any

import httpx

MULLM_LOCAL_ACTIONS = {
    "system_file_list",
    "mullm_shell_task",
    "mullm_create_ticket",
}


def backend_url() -> str:
    return backend_candidates()[0]


def backend_candidates() -> list[str]:
    urls = [
        os.getenv("NLP2DSL_BACKEND_URL"),
        os.getenv("MULLM_NLP2DSL_BACKEND_URL"),
        "http://nlp2dsl-backend:8000",
        "http://host.docker.internal:8010",
        "http://localhost:8010",
    ]
    seen: set[str] = set()
    out: list[str] = []
    for url in urls:
        if not url:
            continue
        normalized = url.rstrip("/")
        if normalized not in seen:
            out.append(normalized)
            seen.add(normalized)
    return out


async def health() -> bool:
    async with httpx.AsyncClient(timeout=3.0) as client:
        for url in backend_candidates():
            try:
                r = await client.get(f"{url}/docs")
                if r.status_code == 200:
                    return True
            except httpx.HTTPError:
                continue
    return False


async def chat_start(text: str) -> dict[str, Any]:
    return await _post_json("/workflow/chat/start", {"text": text})


async def chat_message(conversation_id: str, text: str) -> dict[str, Any]:
    return await _post_json(
        "/workflow/chat/message",
        {"conversation_id": conversation_id, "text": text},
    )


async def _post_json(path: str, payload: dict[str, Any]) -> dict[str, Any]:
    last_error: Exception | None = None
    async with httpx.AsyncClient(timeout=60.0) as client:
        for url in backend_candidates():
            try:
                r = await client.post(f"{url}{path}", json=payload)
                r.raise_for_status()
                return r.json()
            except httpx.HTTPError as exc:
                last_error = exc
                continue
    if last_error:
        raise last_error
    raise RuntimeError("nlp2dsl backend URL is not configured")


def form_to_prompt(form: dict[str, Any] | None, values: dict[str, Any]) -> str:
    if not form or not values:
        return ""
    parts = [f"{k}: {v}" for k, v in values.items() if v is not None and str(v).strip()]
    return ", ".join(parts)


def primary_action(dsl: dict[str, Any] | None) -> str | None:
    if not dsl:
        return None
    steps = dsl.get("steps") or []
    if steps:
        return steps[0].get("action")
    return None


def step_config(dsl: dict[str, Any] | None) -> dict[str, Any]:
    if not dsl:
        return {}
    steps = dsl.get("steps") or []
    if steps:
        return steps[0].get("config") or {}
    return {}


def routing_from_response(resp: dict[str, Any]) -> dict[str, Any] | None:
    """IntentDecision z nlp2dsl (pole routing w ConversationResponse)."""
    routing = resp.get("routing")
    return routing if isinstance(routing, dict) else None


def intent_routing_policy_flags(routing: dict[str, Any] | None) -> dict[str, Any]:
    """Mapuje routing nlp2dsl → policy_flags RouteDecision (PR-C / observability)."""
    if not routing:
        return {}
    flags: dict[str, Any] = {
        "nlp2dsl_action": routing.get("action"),
        "nlp2dsl_intent": routing.get("intent"),
        "nlp2dsl_source": routing.get("source"),
        "nlp2dsl_confidence": routing.get("confidence"),
        "nlp2dsl_authorized": routing.get("authorized"),
    }
    codes = routing.get("reason_codes")
    if codes:
        flags["nlp2dsl_reason_codes"] = codes
    if routing.get("deny_reason"):
        flags["nlp2dsl_deny_reason"] = routing["deny_reason"]
    return {k: v for k, v in flags.items() if v is not None}


def merge_intent_into_policy_flags(
    policy_flags: dict[str, Any],
    routing: dict[str, Any] | None,
) -> None:
    if routing:
        policy_flags.update(intent_routing_policy_flags(routing))
