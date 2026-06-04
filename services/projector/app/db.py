from __future__ import annotations

from pathlib import Path
from typing import Any
import logging
import os

try:
    import asyncpg
except ModuleNotFoundError:  # pragma: no cover
    asyncpg = None


logger = logging.getLogger(__name__)


class Database:
    def __init__(self, database_url: str):
        self.database_url = database_url
        self.pool: Any = None

    async def connect(self) -> None:
        if asyncpg is None:
            raise RuntimeError("asyncpg is required to use the projector database")
        self.pool = await asyncpg.create_pool(self.database_url)
        await self._run_schema_migrations()

    async def disconnect(self) -> None:
        if self.pool:
            await self.pool.close()
            self.pool = None

    async def execute(self, query: str, *args: Any) -> str:
        if not self.pool:
            raise RuntimeError("Database is not connected")
        async with self.pool.acquire() as connection:
            return await connection.execute(query, *args)

    async def fetch(self, query: str, *args: Any) -> list[Any]:
        if not self.pool:
            raise RuntimeError("Database is not connected")
        async with self.pool.acquire() as connection:
            return await connection.fetch(query, *args)

    async def _run_schema_migrations(self) -> None:
        schema_dir = Path(os.getenv("MULLM_DB_INIT_DIR", "/app/db/init"))
        if not schema_dir.exists():
            return

        async with self.pool.acquire() as connection:
            for path in sorted(schema_dir.glob("*.sql")):
                sql = path.read_text(encoding="utf-8").strip()
                if not sql:
                    continue
                logger.info("Applying schema file %s", path)
                await connection.execute(sql)
