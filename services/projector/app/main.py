from __future__ import annotations

from contextlib import asynccontextmanager
from typing import Any
import json
import logging
import os

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.db import Database
from app.projections import project_event

try:
    from nats.aio.client import Client as NATS
except ModuleNotFoundError:  # pragma: no cover
    NATS = None


logger = logging.getLogger(__name__)

DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://mullm:mullm_password@localhost:5432/mullm")
NATS_URL = os.getenv("NATS_URL", "nats://localhost:4222")


@asynccontextmanager
async def lifespan(app: FastAPI):
    app.state.db = Database(DATABASE_URL)
    app.state.nats = None

    await app.state.db.connect()

    if NATS is not None:
        nats = NATS()
        try:
            await nats.connect(servers=[NATS_URL])

            async def handle_message(msg):
                event = json.loads(msg.data.decode())
                await project_event(app.state.db, event)

            await nats.subscribe("mullm.events", cb=handle_message)
            app.state.nats = nats
        except Exception as exc:  # pragma: no cover - depends on external NATS
            logger.warning("Could not connect projector to NATS at %s: %s", NATS_URL, exc)

    yield

    if app.state.nats:
        await app.state.nats.drain()
    await app.state.db.disconnect()


app = FastAPI(
    title="Mullm Projector",
    description="Read model projection service",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
async def health_check():
    return {"status": "healthy", "service": "projector"}


@app.get("/projections/feed")
async def operational_feed(limit: int = 100, offset: int = 0):
    rows = await app.state.db.fetch(
        """
        select event_id, stream_id, aggregate_type, aggregate_id, event_type,
               occurred_at, correlation_id, causation_id, actor_type, actor_id,
               title, summary, payload
        from operational_feed
        order by occurred_at desc
        limit $1 offset $2
        """,
        limit,
        offset,
    )
    return {"items": [_row_to_dict(row) for row in rows]}


@app.get("/projections/tasks")
async def task_board(status: str | None = None, limit: int = 100, offset: int = 0):
    if status:
        rows = await app.state.db.fetch(
            """
            select *
            from task_board
            where status = $1
            order by updated_at desc
            limit $2 offset $3
            """,
            status,
            limit,
            offset,
        )
    else:
        rows = await app.state.db.fetch(
            """
            select *
            from task_board
            order by updated_at desc
            limit $1 offset $2
            """,
            limit,
            offset,
        )
    return {"items": [_row_to_dict(row) for row in rows]}


@app.get("/projections/agents")
async def agent_fleet(status: str | None = None, limit: int = 100, offset: int = 0):
    if status:
        rows = await app.state.db.fetch(
            """
            select *
            from agent_fleet
            where status = $1
            order by updated_at desc
            limit $2 offset $3
            """,
            status,
            limit,
            offset,
        )
    else:
        rows = await app.state.db.fetch(
            """
            select *
            from agent_fleet
            order by updated_at desc
            limit $1 offset $2
            """,
            limit,
            offset,
        )
    return {"items": [_row_to_dict(row) for row in rows]}


@app.get("/projections/workflows")
async def workflow_versions(limit: int = 100, offset: int = 0):
    rows = await app.state.db.fetch(
        """
        select *
        from workflow_versions
        order by proposed_at desc
        limit $1 offset $2
        """,
        limit,
        offset,
    )
    return {"items": [_row_to_dict(row) for row in rows]}


def _row_to_dict(row: Any) -> dict[str, Any]:
    item = dict(row)
    for key, value in list(item.items()):
        if hasattr(value, "isoformat"):
            item[key] = value.isoformat()
    return item


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
