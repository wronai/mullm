from __future__ import annotations

from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel, Field

router = APIRouter()


class SearchQuery(BaseModel):
    query: str
    limit: int = Field(default=8, ge=1, le=50)


class AskQuery(BaseModel):
    query: str
    limit: int = Field(default=6, ge=1, le=20)


@router.get("/health")
async def rag_health(request: Request):
    client = request.app.state.openrouter
    return await client.health()


@router.get("/documents")
async def list_documents(request: Request, limit: int = 100):
    rows = await request.app.state.rag_store.list_documents(limit=limit)
    return {"items": rows}


@router.post("/search")
async def search(body: SearchQuery, request: Request):
    hits = await request.app.state.rag_retriever.search(body.query, limit=body.limit)
    return {"query": body.query, "items": hits}


@router.post("/ask")
async def ask(body: AskQuery, request: Request):
    result = await request.app.state.rag_retriever.ask(body.query, limit=body.limit)
    return result


@router.post("/ingest/{resource_id}")
async def ingest_resource(resource_id: str, request: Request):
    events = await request.app.state.event_store.get_events_for_aggregate(
        "resource", resource_id
    )
    if not events:
        raise HTTPException(status_code=404, detail="resource not found")
    first = events[0].data
    outcome = await request.app.state.rag_indexer.ingest_resource(
        resource_id=resource_id,
        uri=first["uri"],
        name=first.get("name", ""),
        classification=first.get("classification", "document"),
    )
    return {"result": outcome}
