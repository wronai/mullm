"""Jedno wejście orientacji: nlp-service → backend → local_orient."""

from __future__ import annotations

import time
from typing import Any

import httpx

from app import nlp2dsl_bridge as nlp
from app.local_orient import orient_query
from app.routing.decision import OrientationDecision
from app.routing.ingress_cache import get_cached_orient, set_cached_orient


async def _orient_remote(text: str, *, connector: str) -> dict[str, Any] | None:
    payload = {"text": text, "connector": connector}
    async with httpx.AsyncClient(timeout=_orient_timeout()) as client:
        for url in nlp.nlp_service_candidates():
            try:
                r = await client.post(f"{url}/nlp/orient", json=payload)
                if r.status_code == 200:
                    body = r.json()
                    body.setdefault("source", "nlp2dsl_service")
                    return body
            except httpx.HTTPError:
                continue
    try:
        remote = await nlp.orient(text, connector=connector)
        if remote:
            remote.setdefault("source", "nlp2dsl_backend")
            return remote
    except httpx.HTTPError:
        pass
    return None


def _orient_timeout() -> float:
    import os

    raw = os.getenv("MULLM_ORIENTATION_TIMEOUT_SECONDS", "8").strip()
    try:
        return max(1.0, float(raw))
    except ValueError:
        return 8.0


async def orient_message(
    text: str,
    *,
    connector: str = "mullm",
    session_id: str | None = None,
    chat_mode: str = "discuss",
    use_cache: bool = True,
) -> OrientationDecision:
    if use_cache and session_id:
        cached = get_cached_orient(session_id, text, chat_mode=chat_mode)
        if cached is not None:
            return cached

    started = time.perf_counter()
    remote = await _orient_remote(text, connector=connector)
    if remote:
        orient = OrientationDecision.from_dict(remote)
    else:
        local = orient_query(text, connector=connector)
        orient = OrientationDecision.from_dict(local.to_dict())
    if orient is None:
        orient = OrientationDecision(
            category="unknown",
            suggested_action=None,
            confidence=0.0,
            reason_codes=["orientation_failed"],
            connector=connector,
            source="unknown",
        )
    orient.latency_ms = (time.perf_counter() - started) * 1000.0

    if use_cache and session_id:
        set_cached_orient(session_id, text, orient, chat_mode=chat_mode)
    return orient
