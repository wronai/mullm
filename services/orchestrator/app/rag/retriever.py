from __future__ import annotations

from typing import Any

from app.rag.openrouter import OpenRouterClient
from app.rag.store import RagStore


class RagRetriever:
    def __init__(self, store: RagStore, openrouter: OpenRouterClient) -> None:
        self.store = store
        self.openrouter = openrouter

    async def search(self, query: str, *, limit: int = 8) -> list[dict[str, Any]]:
        query_embedding = None
        if self.openrouter.configured:
            try:
                vectors = await self.openrouter.embed([query])
                if vectors:
                    query_embedding = vectors[0]
            except Exception:
                query_embedding = None
        return await self.store.search(
            query,
            limit=limit,
            query_embedding=query_embedding,
        )

    async def ask(
        self,
        query: str,
        *,
        limit: int = 6,
    ) -> dict[str, Any]:
        hits = await self.search(query, limit=limit)
        if not hits:
            return {
                "query": query,
                "answer": None,
                "sources": [],
                "llm_model": self.openrouter.llm_model,
                "reason": "no matching chunks",
            }

        if not self.openrouter.configured:
            return {
                "query": query,
                "answer": None,
                "sources": hits,
                "llm_model": None,
                "reason": "OPENROUTER_API_KEY not set",
            }

        context = "\n\n---\n\n".join(
            f"[{h['uri']}] {h['content_preview']}" for h in hits
        )
        answer = await self.openrouter.chat(
            [
                {
                    "role": "system",
                    "content": (
                        "Answer using only the provided context. "
                        "If context is insufficient, say so briefly."
                    ),
                },
                {
                    "role": "user",
                    "content": f"Context:\n{context}\n\nQuestion: {query}",
                },
            ]
        )
        return {
            "query": query,
            "answer": answer,
            "sources": hits,
            "llm_model": self.openrouter.llm_model,
        }
