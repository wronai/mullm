import asyncio
import json
import uuid
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.infrastructure.nats_bus import NATSBus
from app.infrastructure.postgres import PostgresConnection
from app.api.access import router as access_router
from app.api.rag import router as rag_router
from app.api.catalog import router as catalog_router
from app.api.evolution import router as evolution_router
from app.application.command_bus import CommandBus
from app.access.transport import TransportService
from app.evolution import ArchitectureCatalog, EvaluationEngine, ExperimentManager, PolicyEngine
from app.rag import OpenRouterClient, RagIndexer, RagRetriever, RagStore
from app.infrastructure.eventstore_factory import build_event_store
from app.api.commands import router as commands_router
from app.api.queries import router as queries_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    app.state.nats_bus = NATSBus(settings.nats_url)
    app.state.postgres = PostgresConnection(settings.database_url)
    await app.state.postgres.connect()

    event_store, store_info = await build_event_store(
        backend=settings.event_store_backend,
        postgres=app.state.postgres,
        eventstore_url=settings.eventstore_url,
    )
    app.state.event_store = event_store
    app.state.event_store_info = store_info
    catalog_root = settings.catalog_path or None
    app.state.catalog = ArchitectureCatalog(catalog_root)
    app.state.policy_engine = PolicyEngine(app.state.catalog)
    app.state.evaluation = EvaluationEngine(app.state.postgres)
    app.state.experiments = ExperimentManager(app.state.postgres)
    app.state.transport = TransportService()
    app.state.openrouter = OpenRouterClient(
        settings.openrouter_api_key,
        llm_model=settings.llm_model,
        embedding_model=settings.embedding_model,
    )
    app.state.rag_store = RagStore(app.state.postgres)
    app.state.rag_indexer = RagIndexer(
        app.state.rag_store,
        app.state.transport,
        app.state.openrouter,
    )
    app.state.rag_retriever = RagRetriever(app.state.rag_store, app.state.openrouter)
    app.state.command_bus = CommandBus(
        event_store=app.state.event_store,
        message_bus=app.state.nats_bus,
        postgres=app.state.postgres,
        policy_engine=app.state.policy_engine,
        evaluation=app.state.evaluation,
        experiments=app.state.experiments,
        transport=app.state.transport,
        rag_indexer=app.state.rag_indexer if settings.rag_auto_ingest else None,
        environment=settings.environment,
    )

    await _seed_capability_registry(app)
    await app.state.nats_bus.connect()
    await _subscribe_shell_results(app)
    
    yield
    
    # Shutdown
    store = app.state.event_store
    if hasattr(store, "mirror") and hasattr(store.mirror, "disconnect"):
        await store.mirror.disconnect()
    elif hasattr(store, "disconnect"):
        await store.disconnect()
    await app.state.nats_bus.disconnect()
    await app.state.postgres.disconnect()


app = FastAPI(
    title="Mullm Orchestrator",
    description="Command handling and domain logic service",
    version="1.0.0",
    lifespan=lifespan
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(commands_router, prefix="/api/commands", tags=["commands"])
app.include_router(queries_router, prefix="/api/queries", tags=["queries"])
app.include_router(catalog_router, prefix="/api/catalog", tags=["catalog"])
app.include_router(evolution_router, prefix="/api/evolution", tags=["evolution"])
app.include_router(access_router, prefix="/api/access", tags=["access"])
app.include_router(rag_router, prefix="/api/rag", tags=["rag"])


@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "service": "orchestrator",
        "event_store": getattr(app.state, "event_store_info", {}),
    }


@app.get("/")
async def root():
    return {"message": "Mullm Orchestrator Service", "version": "1.0.0"}


async def _seed_capability_registry(app: FastAPI) -> None:
    import json

    for cap in app.state.catalog.capabilities.get("capabilities", []):
        try:
            await app.state.postgres.execute(
                """
                insert into capability_registry (
                  capability_id, kind, description, provided_by, risk_level,
                  status, manifest, source, updated_at
                )
                values ($1, $2, $3, $4::jsonb, $5, $6, '{}'::jsonb, 'catalog', now())
                on conflict (capability_id) do update set
                  description = excluded.description,
                  updated_at = now()
                """,
                cap["id"],
                cap.get("kind", "runtime"),
                cap.get("description", ""),
                json.dumps(cap.get("provided_by", [])),
                cap.get("risk_level", "medium"),
                cap.get("status", "active"),
            )
        except Exception:
            pass


async def _subscribe_shell_results(app: FastAPI) -> None:
    async def complete_from_shell(msg):
        payload = json.loads(msg.data.decode())
        await app.state.command_bus.handle(
            command_type="CompleteTask",
            command_id=f"shell-completed-{payload['task_id']}",
            data={"task_id": payload["task_id"], "result": payload},
            metadata={"actor": {"type": "agent", "id": payload.get("agent_id")}},
        )

    async def fail_from_shell(msg):
        payload = json.loads(msg.data.decode())
        error = payload.get("stderr") or f"Shell command failed with exit code {payload.get('exit_code')}"
        await app.state.command_bus.handle(
            command_type="FailTask",
            command_id=f"shell-failed-{payload['task_id']}",
            data={"task_id": payload["task_id"], "error": error},
            metadata={"actor": {"type": "agent", "id": payload.get("agent_id")}},
        )

    await app.state.nats_bus.subscribe("task.shell.completed", complete_from_shell)
    await app.state.nats_bus.subscribe("task.shell.failed", fail_from_shell)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
