from __future__ import annotations

import uuid
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any

from app.config import settings
from app.observability.context import get_correlation_id, get_retrieval_trace_id
from app.observability.incidents import IncidentCode
from app.observability.logging import log_event


@dataclass
class RagDiagnostics:
    postgres: Any
    rag_store: Any
    openrouter: Any

    async def run(self, *, query: str | None = None) -> dict[str, Any]:
        trace_id = get_retrieval_trace_id() or f"diag-{uuid.uuid4().hex[:12]}"
        correlation_id = get_correlation_id()
        checks: list[dict[str, Any]] = []

        checks.append(await self._check_postgres())
        checks.append(await self._check_rag_tables())
        checks.append(await self._check_openrouter_config())
        checks.append(await self._check_embedding())
        if query:
            checks.append(await self._check_search(query))

        failed = [c for c in checks if c.get("status") == "fail"]
        degraded = [c for c in checks if c.get("status") == "warn"]
        overall = "healthy"
        if failed:
            overall = "unhealthy"
        elif degraded:
            overall = "degraded"

        primary_code = None
        if failed:
            primary_code = failed[0].get("incident_code")
        elif degraded:
            primary_code = degraded[0].get("incident_code")

        result = {
            "retrieval_trace_id": trace_id,
            "correlation_id": correlation_id,
            "status": overall,
            "checks": checks,
            "primary_incident_code": primary_code,
            "recommendations": self._recommendations(checks),
            "ran_at": datetime.now(timezone.utc).isoformat(),
        }

        log_event(
            severity="info" if overall == "healthy" else "warning",
            component="rag_diagnostics",
            message=f"RAG diagnostics {overall}",
            error_code=primary_code,
            check_count=len(checks),
        )

        await self._snapshot(result)
        return result

    async def _check_postgres(self) -> dict[str, Any]:
        try:
            row = await self.postgres.fetchrow("select 1 as ok")
            ok = row and row["ok"] == 1
            return {"name": "postgres", "status": "pass" if ok else "fail"}
        except Exception as exc:
            return {
                "name": "postgres",
                "status": "fail",
                "detail": str(exc),
                "incident_code": IncidentCode.VECTOR_DB_UNAVAILABLE.value,
            }

    async def _check_rag_tables(self) -> dict[str, Any]:
        try:
            doc_row = await self.postgres.fetchrow(
                "select count(*)::int as n from rag_documents"
            )
            chunk_row = await self.postgres.fetchrow(
                "select count(*)::int as n from rag_chunks"
            )
            docs = doc_row["n"] if doc_row else 0
            chunks = chunk_row["n"] if chunk_row else 0
            status = "pass"
            code = None
            if chunks == 0:
                status = "warn"
                code = IncidentCode.RETRIEVER_EMPTY_RESULT.value
            return {
                "name": "rag_index",
                "status": status,
                "detail": {"documents": docs, "chunks": chunks},
                "incident_code": code,
            }
        except Exception as exc:
            return {
                "name": "rag_index",
                "status": "fail",
                "detail": str(exc),
                "incident_code": IncidentCode.VECTOR_DB_UNAVAILABLE.value,
            }

    async def _check_openrouter_config(self) -> dict[str, Any]:
        if not settings.openrouter_api_key:
            return {
                "name": "openrouter_config",
                "status": "fail",
                "detail": "OPENROUTER_API_KEY missing",
                "incident_code": IncidentCode.LLM_UNAVAILABLE.value,
            }
        return {
            "name": "openrouter_config",
            "status": "pass",
            "detail": {
                "llm_model": settings.llm_model,
                "embedding_model": settings.embedding_model,
            },
        }

    async def _check_embedding(self) -> dict[str, Any]:
        try:
            vectors = await self.openrouter.embed(["healthcheck"])
            if not vectors:
                return {
                    "name": "embedding_pipeline",
                    "status": "fail",
                    "detail": "empty embedding",
                    "incident_code": IncidentCode.EMBEDDING_PIPELINE_FAILED.value,
                }
            vec = vectors[0]
            return {
                "name": "embedding_pipeline",
                "status": "pass",
                "detail": {"dimensions": len(vec)},
            }
        except Exception as exc:
            return {
                "name": "embedding_pipeline",
                "status": "fail",
                "detail": str(exc),
                "incident_code": IncidentCode.EMBEDDING_PIPELINE_FAILED.value,
            }

    async def _check_search(self, query: str) -> dict[str, Any]:
        try:
            hits = await self.rag_store.search(query, limit=3)
            if not hits:
                return {
                    "name": "vector_search",
                    "status": "warn",
                    "detail": "no hits for smoke query",
                    "incident_code": IncidentCode.RETRIEVER_EMPTY_RESULT.value,
                }
            return {
                "name": "vector_search",
                "status": "pass",
                "detail": {"hits": len(hits)},
            }
        except Exception as exc:
            return {
                "name": "vector_search",
                "status": "fail",
                "detail": str(exc),
                "incident_code": IncidentCode.VECTOR_DB_UNAVAILABLE.value,
            }

    def _recommendations(self, checks: list[dict[str, Any]]) -> list[str]:
        recs: list[str] = []
        names = {c["name"]: c for c in checks}
        if names.get("openrouter_config", {}).get("status") == "fail":
            recs.append("Ustaw OPENROUTER_API_KEY i poprawny LLM_MODEL w .env")
        if names.get("rag_index", {}).get("status") in {"warn", "fail"}:
            recs.append("Zarejestruj zasób (upload) lub uruchom reindex dokumentów RAG")
        if names.get("embedding_pipeline", {}).get("status") == "fail":
            recs.append("Sprawdź model embeddingów i limit OpenRouter")
        if names.get("vector_search", {}).get("status") == "warn":
            recs.append("Dodaj dokumenty do indeksu lub zmień zapytanie testowe")
        return recs

    async def _snapshot(self, result: dict[str, Any]) -> None:
        try:
            import json

            await self.postgres.execute(
                """
                insert into rag_health_snapshots (
                  snapshot_id, retrieval_trace_id, correlation_id, status, checks
                )
                values ($1,$2,$3,$4,$5::jsonb)
                """,
                str(uuid.uuid4()),
                result["retrieval_trace_id"],
                result.get("correlation_id"),
                result["status"],
                json.dumps(result["checks"], default=str),
            )
        except Exception:
            pass
