from __future__ import annotations

from pathlib import Path
from typing import Any
import logging
import os

try:
    import asyncpg
except ModuleNotFoundError:  # pragma: no cover - exercised only without deps installed
    asyncpg = None


logger = logging.getLogger(__name__)


EVENTS_SCHEMA = """
create table if not exists events (
  id bigserial primary key,
  event_id text not null unique,
  stream_id text not null,
  aggregate_type text not null,
  aggregate_id text not null,
  event_type text not null,
  revision integer not null,
  occurred_at timestamptz not null,
  causation_id text,
  correlation_id text,
  payload jsonb not null default '{}'::jsonb,
  metadata jsonb not null default '{}'::jsonb,
  unique (stream_id, revision)
);

create index if not exists idx_events_stream_revision
  on events (stream_id, revision);

create index if not exists idx_events_aggregate
  on events (aggregate_type, aggregate_id);

create index if not exists idx_events_occurred_at
  on events (occurred_at);
"""


class PostgresConnection:
    def __init__(self, database_url: str):
        self.database_url = database_url
        self.pool: Any = None

    async def connect(self) -> None:
        if asyncpg is None:
            raise RuntimeError("asyncpg is required to use PostgresConnection")
        self.pool = await asyncpg.create_pool(self.database_url)
        await self._run_schema_migrations()

    async def disconnect(self) -> None:
        if self.pool:
            await self.pool.close()
            self.pool = None

    async def execute(self, query: str, *args: Any) -> str:
        if not self.pool:
            raise RuntimeError("PostgresConnection is not connected")
        async with self.pool.acquire() as connection:
            return await connection.execute(query, *args)

    async def fetch(self, query: str, *args: Any) -> list[Any]:
        if not self.pool:
            raise RuntimeError("PostgresConnection is not connected")
        async with self.pool.acquire() as connection:
            return await connection.fetch(query, *args)

    async def fetchrow(self, query: str, *args: Any) -> Any:
        if not self.pool:
            raise RuntimeError("PostgresConnection is not connected")
        async with self.pool.acquire() as connection:
            return await connection.fetchrow(query, *args)

    async def _run_schema_migrations(self) -> None:
        schema_dir = Path(os.getenv("MULLM_DB_INIT_DIR", "/app/db/init"))
        paths = sorted(schema_dir.glob("*.sql")) if schema_dir.exists() else []
        if not paths:
            await self.execute(EVENTS_SCHEMA)
            return

        async with self.pool.acquire() as connection:
            for path in paths:
                sql = path.read_text(encoding="utf-8").strip()
                if not sql:
                    continue
                logger.info("Applying schema file %s", path)
                await connection.execute(sql)
