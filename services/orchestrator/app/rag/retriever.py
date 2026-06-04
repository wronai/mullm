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
            return _no_hits_answer(query, self.openrouter.llm_model)

        if not self.openrouter.configured:
            return _unconfigured_answer(query, hits)

        context = _context_from_hits(hits)
        answer, llm_error = await self.openrouter.chat(
            _rag_messages(context, query)
        )
        if not answer and llm_error:
            answer = _fragment_fallback_answer(hits, llm_error)
        return {
            "query": query,
            "answer": answer,
            "sources": hits,
            "llm_model": self.openrouter.llm_model,
            "llm_error": llm_error,
        }


def _no_hits_answer(query: str, llm_model: str) -> dict[str, Any]:
    return {
        "query": query,
        "answer": None,
        "sources": [],
        "llm_model": llm_model,
        "reason": "no matching chunks",
    }


def _unconfigured_answer(query: str, hits: list[dict[str, Any]]) -> dict[str, Any]:
    return {
        "query": query,
        "answer": None,
        "sources": hits,
        "llm_model": None,
        "reason": "OPENROUTER_API_KEY not set",
    }


def _context_from_hits(hits: list[dict[str, Any]]) -> str:
    return "\n\n---\n\n".join(f"[{hit['uri']}] {hit['content_preview']}" for hit in hits)


def _rag_messages(context: str, query: str) -> list[dict[str, str]]:
    return [
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


def _fragment_fallback_answer(hits: list[dict[str, Any]], llm_error: str) -> str:
    previews = "\n".join(
        f"- {hit.get('name') or hit.get('uri')}: "
        f"{hit.get('content_preview', '')[:180]}"
        for hit in hits[:4]
    )
    return f"(LLM niedostępny: {llm_error})\n\nFragmenty z indeksu:\n{previews}"
