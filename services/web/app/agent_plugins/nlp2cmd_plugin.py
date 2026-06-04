"""Plugin nlp2cmd — NL → shell; wykonanie przez shell_agent Mullm."""

from __future__ import annotations

import os
from typing import Any

import httpx

from app.agent_plugins.protocol import ShellTranslation

_PLUGIN_ID = "nlp2cmd"
_EXECUTOR = "shell_agent"


def backend_candidates() -> list[str]:
    urls = [
        os.getenv("NLP2CMD_BACKEND_URL"),
        os.getenv("MULLM_NLP2CMD_BACKEND_URL"),
        "http://nlp2cmd:8000",
        "http://host.docker.internal:8020",
        "http://127.0.0.1:8020",
        "http://localhost:8000",
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


class Nlp2CmdPlugin:
    plugin_id = _PLUGIN_ID
    title = "nlp2cmd (NL → shell)"
    executor_agent_id = _EXECUTOR
    ingress_steps = frozenset({"agent_shell"})
    route_kinds = frozenset({"mullm_shell", "nlp2cmd_shell"})

    async def health(self) -> bool:
        async with httpx.AsyncClient(timeout=3.0) as client:
            for base in backend_candidates():
                try:
                    r = await client.get(f"{base}/health")
                    if r.status_code == 200:
                        return True
                except httpx.HTTPError:
                    continue
        return False

    async def translate_shell(
        self,
        message: str,
        *,
        dsl: str = "shell",
    ) -> ShellTranslation | None:
        text = (message or "").strip()
        if not text:
            return None
        payload = {"query": text, "dsl": dsl, "explain": False, "execute": False}
        async with httpx.AsyncClient(timeout=30.0) as client:
            for base in backend_candidates():
                try:
                    r = await client.post(f"{base}/query", json=payload)
                    r.raise_for_status()
                    data = r.json()
                    return _translation_from_response(data)
                except httpx.HTTPError:
                    continue
        return None


def _translation_from_response(data: dict[str, Any]) -> ShellTranslation | None:
    if not data.get("success"):
        return None
    command = (data.get("command") or "").strip()
    if not command:
        return None
    return ShellTranslation(
        command=command,
        confidence=float(data.get("confidence") or 0.0),
        domain=str(data.get("domain") or ""),
        intent=str(data.get("intent") or ""),
        raw=data,
    )


plugin = Nlp2CmdPlugin()
