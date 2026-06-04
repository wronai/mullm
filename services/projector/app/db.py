from __future__ import annotations

from typing import Any

try:
    import asyncpg
except ModuleNotFoundError:  # pragma: no cover
    asyncpg = None


class Database:
    def __init__(self, database_url: str):
        self.database_url = database_url
        self.pool: Any = None

    async def connect(self) -> None:
        if asyncpg is None:
            raise RuntimeError("asyncpg is required to use the projector database")
        self.pool = await asyncpg.create_pool(self.database_url)

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
