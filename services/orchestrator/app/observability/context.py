from __future__ import annotations

import contextvars
import uuid
from contextlib import contextmanager
from typing import Iterator

_correlation_id: contextvars.ContextVar[str | None] = contextvars.ContextVar(
    "correlation_id", default=None
)
_retrieval_trace_id: contextvars.ContextVar[str | None] = contextvars.ContextVar(
    "retrieval_trace_id", default=None
)
_chat_session_id: contextvars.ContextVar[str | None] = contextvars.ContextVar(
    "chat_session_id", default=None
)


def new_correlation_id() -> str:
    return str(uuid.uuid4())


def new_retrieval_trace_id() -> str:
    return f"rag-{uuid.uuid4().hex[:12]}"


def get_correlation_id() -> str | None:
    return _correlation_id.get()


def get_retrieval_trace_id() -> str | None:
    return _retrieval_trace_id.get()


def get_chat_session_id() -> str | None:
    return _chat_session_id.get()


@contextmanager
def observability_context(
    *,
    correlation_id: str | None = None,
    retrieval_trace_id: str | None = None,
    chat_session_id: str | None = None,
) -> Iterator[None]:
    tokens = []
    if correlation_id:
        tokens.append((_correlation_id, _correlation_id.set(correlation_id)))
    if retrieval_trace_id:
        tokens.append(
            (_retrieval_trace_id, _retrieval_trace_id.set(retrieval_trace_id))
        )
    if chat_session_id:
        tokens.append((_chat_session_id, _chat_session_id.set(chat_session_id)))
    try:
        yield
    finally:
        for var, token in reversed(tokens):
            var.reset(token)
