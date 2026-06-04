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
