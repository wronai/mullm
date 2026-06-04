from __future__ import annotations

import logging
from typing import Any

from app.rag.chunking import chunk_text
from app.rag.openrouter import OpenRouterClient
from app.rag.store import RagStore

logger = logging.getLogger(__name__)


class RagIndexer:
    """Ingest zasobu po rejestracji — fetch → chunk → embed → store."""

    def __init__(
        self,
        store: RagStore,
        transport: Any,
        openrouter: OpenRouterClient,
    ) -> None:
        self.store = store
        self.transport = transport
        self.openrouter = openrouter

    async def ingest_resource(
        self,
        *,
        resource_id: str,
        uri: str,
        name: str,
        classification: str = "document",
    ) -> dict[str, Any]:
        await self.store.upsert_document_pending(
            resource_id=resource_id,
            uri=uri,
            name=name,
            classification=classification,
        )
        try:
            body = await self._fetch_body(uri)
            chunks = _chunks_for_body(body)
            embeddings, embedding_model = await self._embed_chunks(chunks)
            packed = _packed_chunks(chunks, embeddings)
            await self.store.replace_chunks(resource_id=resource_id, chunks=packed)
            await self.store.mark_indexed(
                resource_id=resource_id,
                chunk_count=len(chunks),
                embedding_model=embedding_model,
            )
            return _indexed_result(resource_id, chunks, embedding_model)
        except Exception as exc:
            await self.store.mark_failed(resource_id=resource_id, error=str(exc))
            return _failed_result(resource_id, exc)

    async def _fetch_body(self, uri: str) -> str:
        fetched = await self.transport.fetch(uri, max_bytes=512_000)
        if not fetched.get("ok"):
            raise ValueError(fetched.get("error") or "fetch failed")
        body = (fetched.get("body_preview") or "").strip()
        if not body:
            raise ValueError("empty content after fetch")
        return body

    async def _embed_chunks(
        self, chunks: list[str]
    ) -> tuple[list[list[float] | None] | None, str | None]:
        if not self.openrouter.configured:
            return None, None
        try:
            vectors = await self.openrouter.embed(chunks)
        except Exception as exc:
            logger.warning("OpenRouter embeddings failed: %s", exc)
            return None, None
        if vectors and len(vectors) == len(chunks):
            return vectors, self.openrouter.embedding_model
        return None, None


def _chunks_for_body(body: str) -> list[str]:
    chunks = chunk_text(body)
    if not chunks:
        raise ValueError("no chunks produced")
    return chunks


def _packed_chunks(
    chunks: list[str],
    embeddings: list[list[float] | None] | None,
) -> list[tuple[int, str, list[float] | None]]:
    return [
        (idx, text, embeddings[idx] if embeddings else None)
        for idx, text in enumerate(chunks)
    ]


def _indexed_result(
    resource_id: str,
    chunks: list[str],
    embedding_model: str | None,
) -> dict[str, Any]:
    return {
        "resource_id": resource_id,
        "status": "indexed",
        "chunk_count": len(chunks),
        "embedding_model": embedding_model,
    }


def _failed_result(resource_id: str, exc: Exception) -> dict[str, Any]:
    return {
        "resource_id": resource_id,
        "status": "failed",
        "error": str(exc),
    }
