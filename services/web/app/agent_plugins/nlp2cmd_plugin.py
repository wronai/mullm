"""Plugin nlp2cmd — NL → shell; wykonanie przez shell_agent Mullm."""

from __future__ import annotations

import os
from typing import Any

import httpx

from app.agent_plugins.nlp2cmd_helpers import resolve_command_text
from app.agent_plugins.protocol import ShellTranslation
from app.routing_schemas import (
    NlpCommandAnalysis,
    build_nlp2cmd_request,
    parse_nlp2cmd_response,
)

_PLUGIN_ID = "nlp2cmd"
_EXECUTOR = "shell_agent"


def backend_candidates() -> list[str]:
    urls = [
        os.getenv("NLP2CMD_BACKEND_URL"),
        os.getenv("MULLM_NLP2CMD_BACKEND_URL"),
        "http://nlp2cmd:8000",
        "http://host.docker.internal:8020",
        "http://127.0.0.1:8020",
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
        dsl: str = "auto",
        explain: bool | None = None,
    ) -> ShellTranslation | None:
        analysis = await self.analyze_shell_nl(message, dsl=dsl, explain=explain)
        return analysis.to_shell_translation() if analysis else None

    async def analyze_shell_nl(
        self,
        message: str,
        *,
        dsl: str = "auto",
        explain: bool | None = None,
    ) -> NlpCommandAnalysis | None:
        text = (message or "").strip()
        if not text:
            return None
        req = build_nlp2cmd_request(text, dsl=dsl)
        if explain is not None:
            req = req.model_copy(update={"explain": explain})
        payload = req.model_dump(mode="json", exclude={"schema_id"})
        async with httpx.AsyncClient(timeout=30.0) as client:
            for base in backend_candidates():
                try:
                    r = await client.post(f"{base}/query", json=payload)
                    r.raise_for_status()
                    parsed = parse_nlp2cmd_response(r.json())
                    if not parsed or not parsed.success:
                        continue
                    cmd = resolve_command_text(text, parsed)
                    if not cmd:
                        continue
                    if cmd != parsed.command_text:
                        parsed = parsed.model_copy(update={"command": cmd})
                    return NlpCommandAnalysis(request=req, response=parsed)
                except httpx.HTTPError:
                    continue
        return None


def _translation_from_response(
    data: dict[str, Any],
    *,
    query: str = "",
) -> ShellTranslation | None:
    parsed = parse_nlp2cmd_response(data)
    if not parsed or not parsed.success:
        return None
    cmd = resolve_command_text(query, parsed) if query else parsed.command_text
    if not cmd:
        return None
    return ShellTranslation(
        command=cmd,
        confidence=float(parsed.confidence or 0.0),
        domain=str(parsed.domain or ""),
        intent=str(parsed.intent or ""),
        raw=parsed.model_dump(mode="json"),
    )


plugin = Nlp2CmdPlugin()
