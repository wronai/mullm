import os
from unittest.mock import AsyncMock

import pytest

from app.access.uri import build_uri
from app.rag.chunking import chunk_text
from app.rag import OpenRouterClient, RagIndexer, RagRetriever, RagStore
from app.access.transport import TransportService


def test_chunk_text_overlap():
    text = "word " * 400
    chunks = chunk_text(text, max_chars=500, overlap=50)
    assert len(chunks) >= 2
    assert all(len(c) <= 500 for c in chunks)


@pytest.mark.asyncio
async def test_auto_ingest_on_register(command_bus, fake_postgres, tmp_path):
    os.environ["MULLM_LOCALFS_ROOT"] = str(tmp_path)
    doc = tmp_path / "notes.txt"
    doc.write_text("mullm rag pipeline indexes documents for retrieval", encoding="utf-8")

    result = await command_bus.handle(
        command_type="RegisterResource",
        data={
            "uri": build_uri("localfs", "notes.txt"),
            "name": "Notes",
            "classification": "document",
        },
    )
    resource_id = result["aggregate_id"]
    indexed = fake_postgres.rag_documents.get(resource_id)
    assert indexed is not None
    assert indexed["status"] == "indexed"
    assert indexed["chunk_count"] >= 1
    assert len(fake_postgres.rag_chunks) >= 1


@pytest.mark.asyncio
async def test_rag_search_keyword(fake_postgres):
    store = RagStore(fake_postgres)
    await store.upsert_document_pending(
        resource_id="r1",
        uri="mullm://localfs/a.txt",
        name="A",
        classification="document",
    )
    await store.replace_chunks(
        resource_id="r1",
        chunks=[(0, "kubernetes deployment manifests for staging", None)],
    )
    await store.mark_indexed(resource_id="r1", chunk_count=1, embedding_model=None)

    retriever = RagRetriever(store, OpenRouterClient(None, llm_model="x", embedding_model="y"))
    hits = await retriever.search("kubernetes staging")
    assert hits
    assert hits[0]["resource_id"] == "r1"


@pytest.mark.asyncio
async def test_rag_ask_without_api_key(fake_postgres):
    store = RagStore(fake_postgres)
    await store.upsert_document_pending(
        resource_id="r2",
        uri="mullm://localfs/b.txt",
        name="B",
        classification="document",
    )
    await store.replace_chunks(
        resource_id="r2",
        chunks=[(0, "OpenRouter LLM_MODEL configures chat answers", None)],
    )
    await store.mark_indexed(resource_id="r2", chunk_count=1, embedding_model=None)

    retriever = RagRetriever(store, OpenRouterClient("", llm_model="m", embedding_model="e"))
    result = await retriever.ask("What configures chat?")
    assert result["sources"]
    assert result["answer"] is None
    assert "OPENROUTER_API_KEY" in result["reason"]


@pytest.mark.asyncio
async def test_openrouter_embed_mock():
    client = OpenRouterClient("sk-test", llm_model="m", embedding_model="e")
    mock_response = AsyncMock()
    mock_response.raise_for_status = lambda: None
    mock_response.json = lambda: {
        "data": [{"index": 0, "embedding": [0.1, 0.2, 0.3]}]
    }

    class FakeClient:
        def __init__(self, *args, **kwargs):
            pass

        async def __aenter__(self):
            return self

        async def __aexit__(self, *args):
            return None

        async def post(self, url, headers=None, json=None):
            return mock_response

    import app.rag.openrouter as mod

    original = mod.httpx.AsyncClient
    mod.httpx.AsyncClient = FakeClient
    try:
        vectors = await client.embed(["hello"])
        assert vectors == [[0.1, 0.2, 0.3]]
    finally:
        mod.httpx.AsyncClient = original
