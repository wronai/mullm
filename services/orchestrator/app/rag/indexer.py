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
            fetched = await self.transport.fetch(uri, max_bytes=512_000)
            if not fetched.get("ok"):
                raise ValueError(fetched.get("error") or "fetch failed")
            body = (fetched.get("body_preview") or "").strip()
            if not body:
                raise ValueError("empty content after fetch")

            chunks = chunk_text(body)
            if not chunks:
                raise ValueError("no chunks produced")

            embeddings: list[list[float] | None] | None = None
            embedding_model: str | None = None
            if self.openrouter.configured:
                try:
                    vectors = await self.openrouter.embed(chunks)
                    if vectors and len(vectors) == len(chunks):
                        embeddings = vectors
                        embedding_model = self.openrouter.embedding_model
                except Exception as exc:
                    logger.warning("OpenRouter embeddings failed: %s", exc)

            packed = [
                (idx, text, embeddings[idx] if embeddings else None)
                for idx, text in enumerate(chunks)
            ]
            await self.store.replace_chunks(resource_id=resource_id, chunks=packed)
            await self.store.mark_indexed(
                resource_id=resource_id,
                chunk_count=len(chunks),
                embedding_model=embedding_model,
            )
            return {
                "resource_id": resource_id,
                "status": "indexed",
                "chunk_count": len(chunks),
                "embedding_model": embedding_model,
            }
        except Exception as exc:
            await self.store.mark_failed(resource_id=resource_id, error=str(exc))
            return {
                "resource_id": resource_id,
                "status": "failed",
                "error": str(exc),
            }
