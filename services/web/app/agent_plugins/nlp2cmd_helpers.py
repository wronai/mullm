"""Pomocniki nlp2cmd — multi-step / browser bez gotowego polecenia shell."""

from __future__ import annotations

import shlex

from app.routing_schemas import Nlp2CmdQueryResponse

_RUN_MODE_DOMAINS = frozenset(
    {"multi_step", "browser", "canvas", "dom", "webops", "desktop"},
)
_RUN_MODE_INTENT_PARTS = (
    "canvas",
    "multistep",
    "multi_step",
    "browser",
    "dom_",
    "desktop",
    "blueprint",
)


def needs_run_wrapper(parsed: Nlp2CmdQueryResponse) -> bool:
    """nlp2cmd rozpoznał intencję, ale wynik wymaga `nlp2cmd -r` zamiast cmd shell."""
    if parsed.command_text:
        return False
    if not parsed.success:
        return False
    domain = (parsed.domain or "").lower()
    intent = (parsed.intent or "").lower()
    if domain in _RUN_MODE_DOMAINS:
        return True
    return any(part in intent for part in _RUN_MODE_INTENT_PARTS)


def nlp2cmd_run_command(query: str) -> str:
    return f"nlp2cmd -r {shlex.quote(query.strip())}"


def resolve_command_text(query: str, parsed: Nlp2CmdQueryResponse) -> str:
    cmd = parsed.command_text
    if cmd:
        return cmd
    if needs_run_wrapper(parsed):
        return nlp2cmd_run_command(query)
    return ""
