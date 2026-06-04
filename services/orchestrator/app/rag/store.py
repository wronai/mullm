from __future__ import annotations

import json
import math
import re
from datetime import datetime, timezone
from typing import Any
from uuid import uuid4


def _cosine(a: list[float], b: list[float]) -> float:
    if not a or not b or len(a) != len(b):
        return 0.0
    dot = sum(x * y for x, y in zip(a, b))
    na = math.sqrt(sum(x * x for x in a))
    nb = math.sqrt(sum(y * y for y in b))
    if na == 0 or nb == 0:
        return 0.0
    return dot / (na * nb)


class RagStore:
    def __init__(self, postgres: Any) -> None:
        self.postgres = postgres

    async def upsert_document_pending(
        self,
        *,
        resource_id: str,
        uri: str,
        name: str,
        classification: str,
    ) -> None:
        await self.postgres.execute(
            """
            insert into rag_documents (
              resource_id, uri, name, classification, status, updated_at
            )
            values ($1, $2, $3, $4, 'indexing', now())
            on conflict (resource_id) do update set
              uri = excluded.uri,
              name = excluded.name,
              classification = excluded.classification,
              status = 'indexing',
              error = null,
              updated_at = now()
            """,
            resource_id,
            uri,
            name,
            classification,
        )

    async def mark_indexed(
        self,
        *,
        resource_id: str,
        chunk_count: int,
        embedding_model: str | None,
    ) -> None:
        await self.postgres.execute(
            """
            update rag_documents
            set status = 'indexed',
                chunk_count = $2,
                embedding_model = $3,
                indexed_at = now(),
                updated_at = now(),
                error = null
            where resource_id = $1
            """,
            resource_id,
            chunk_count,
            embedding_model,
        )

    async def mark_failed(self, *, resource_id: str, error: str) -> None:
        await self.postgres.execute(
            """
            update rag_documents
            set status = 'failed',
                error = $2,
                updated_at = now()
            where resource_id = $1
            """,
            resource_id,
            error[:2000],
        )

    async def replace_chunks(
        self,
        *,
        resource_id: str,
        chunks: list[tuple[int, str, list[float] | None]],
    ) -> None:
        await self.postgres.execute(
            "delete from rag_chunks where resource_id = $1",
            resource_id,
        )
        for position, content, embedding in chunks:
            await self.postgres.execute(
                """
                insert into rag_chunks (chunk_id, resource_id, position, content, embedding)
                values ($1, $2, $3, $4, $5::jsonb)
                """,
                str(uuid4()),
                resource_id,
                position,
                content,
                json.dumps(embedding) if embedding is not None else None,
            )

    async def list_documents(self, *, limit: int = 100) -> list[dict[str, Any]]:
        rows = await self.postgres.fetch(
            """
            select resource_id, uri, name, classification, status,
                   chunk_count, embedding_model, error, indexed_at, updated_at
            from rag_documents
            order by updated_at desc
            limit $1
            """,
            limit,
        )
        return [_row_dict(row) for row in rows]

    async def search(
        self,
        query: str,
        *,
        limit: int = 8,
        query_embedding: list[float] | None = None,
    ) -> list[dict[str, Any]]:
        query = (query or "").strip()
        if not query:
            return []

        if query_embedding:
            rows = await self.postgres.fetch(
                """
                select c.chunk_id, c.resource_id, c.position, c.content, c.embedding,
                       d.uri, d.name
                from rag_chunks c
                join rag_documents d on d.resource_id = c.resource_id
                where d.status = 'indexed' and c.embedding is not null
                order by c.created_at desc
                limit 500
                """
            )
            scored: list[tuple[float, dict[str, Any]]] = []
            for row in rows:
                emb = _parse_embedding(row)
                if emb is None:
                    continue
                score = _cosine(query_embedding, emb)
                scored.append((score, _chunk_hit(row, score)))
            scored.sort(key=lambda item: item[0], reverse=True)
            return [item[1] for item in scored[:limit] if item[0] > 0]

        rows = await self.postgres.fetch(
            """
            select c.chunk_id, c.resource_id, c.position, c.content,
                   d.uri, d.name,
                   ts_rank(to_tsvector('english', c.content),
                           plainto_tsquery('english', $1)) as rank
            from rag_chunks c
            join rag_documents d on d.resource_id = c.resource_id
            where d.status = 'indexed'
              and to_tsvector('english', c.content) @@ plainto_tsquery('english', $1)
            order by rank desc
            limit $2
            """,
            query,
            limit,
        )
        if rows:
            return [
                _chunk_hit(row, float(_row_dict(row).get("rank", 0)))
                for row in rows
            ]

        return await self._keyword_fallback(query, limit=limit)

    async def _keyword_fallback(self, query: str, *, limit: int) -> list[dict[str, Any]]:
        tokens = [t for t in re.split(r"\W+", query.lower()) if len(t) > 2]
        if not tokens:
            return []
        rows = await self.postgres.fetch(
            """
            select c.chunk_id, c.resource_id, c.position, c.content,
                   d.uri, d.name
            from rag_chunks c
            join rag_documents d on d.resource_id = c.resource_id
            where d.status = 'indexed'
            order by c.created_at desc
            limit 300
            """
        )
        hits: list[tuple[int, dict[str, Any]]] = []
        for row in rows:
            data = _row_dict(row)
            text = (data.get("content") or "").lower()
            score = sum(1 for token in tokens if token in text)
            if score:
                hits.append((score, _chunk_hit(row, float(score))))
        hits.sort(key=lambda item: item[0], reverse=True)
        return [item[1] for item in hits[:limit]]


def _parse_embedding(row: Any) -> list[float] | None:
    raw = _row_dict(row).get("embedding")
    if raw is None:
        return None
    if isinstance(raw, str):
        raw = json.loads(raw)
    if isinstance(raw, list):
        return [float(x) for x in raw]
    return None


def _row_dict(row: Any) -> dict[str, Any]:
    if hasattr(row, "_data"):
        return dict(row._data)
    if hasattr(row, "keys"):
        return {key: row[key] for key in row.keys()}
    return dict(row)


def _chunk_hit(row: Any, score: float) -> dict[str, Any]:
    data = _row_dict(row)
    content = data["content"]
    preview = content[:400] + ("…" if len(content) > 400 else "")
    return {
        "chunk_id": data["chunk_id"],
        "resource_id": data["resource_id"],
        "uri": data.get("uri", ""),
        "name": data.get("name", ""),
        "position": data["position"],
        "score": round(score, 4),
        "content_preview": preview,
    }
