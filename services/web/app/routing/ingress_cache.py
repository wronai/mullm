"""Cache orientacji per wiadomość — trace i execution czytają tę samą decyzję."""

from __future__ import annotations

import re
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from app.routing.decision import OrientationDecision

_CACHE: dict[str, OrientationDecision] = {}


def _normalize_text(text: str) -> str:
    return re.sub(r"\s+", " ", (text or "").strip().lower())


def cache_key(session_id: str, message: str, *, chat_mode: str = "discuss") -> str:
    return f"{session_id}:{chat_mode}:{_normalize_text(message)}"


def get_cached_orient(
    session_id: str,
    message: str,
    *,
    chat_mode: str = "discuss",
) -> OrientationDecision | None:
    return _CACHE.get(cache_key(session_id, message, chat_mode=chat_mode))


def set_cached_orient(
    session_id: str,
    message: str,
    orient: OrientationDecision,
    *,
    chat_mode: str = "discuss",
) -> None:
    _CACHE[cache_key(session_id, message, chat_mode=chat_mode)] = orient


def clear_cache() -> None:
    """Tylko dla testów."""
    _CACHE.clear()
