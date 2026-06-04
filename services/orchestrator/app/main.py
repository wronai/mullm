import asyncio
import json
import uuid
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.infrastructure.nats_bus import NATSBus
from app.infrastructure.postgres import PostgresConnection
from app.infrastructure.eventstore import EventStore
from app.application.command_bus import CommandBus
from app.api.commands import router as commands_router
from app.api.queries import router as queries_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    app.state.nats_bus = NATSBus(settings.nats_url)
    app.state.postgres = PostgresConnection(settings.database_url)
    app.state.event_store = EventStore(app.state.postgres)
    app.state.command_bus = CommandBus(
        event_store=app.state.event_store,
        message_bus=app.state.nats_bus
    )
    
    await app.state.nats_bus.connect()
    await app.state.postgres.connect()
    await _subscribe_shell_results(app)
    
    yield
    
    # Shutdown
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


@app.get("/health")
async def health_check():
    return {"status": "healthy", "service": "orchestrator"}


@app.get("/")
async def root():
    return {"message": "Mullm Orchestrator Service", "version": "1.0.0"}


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
