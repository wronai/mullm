from __future__ import annotations

from typing import Any
from uuid import uuid4


class ExperimentManager:
    """Shadow / canary — stan eksperymentu powiązany z wersją workflow lub pluginu."""

    def __init__(self, postgres: Any) -> None:
        self.postgres = postgres

    async def start_experiment(
        self,
        *,
        subject_type: str,
        subject_id: str,
        version: int | str,
        mode: str,
        traffic_percent: int = 0,
        metadata: dict[str, Any] | None = None,
    ) -> str:
        experiment_id = str(uuid4())
        await self.postgres.execute(
            """
            insert into experiments (
              experiment_id, subject_type, subject_id, version, mode,
              traffic_percent, status, metadata, started_at
            )
            values ($1, $2, $3, $4, $5, $6, 'running', $7::jsonb, now())
            """,
            experiment_id,
            subject_type,
            subject_id,
            str(version),
            mode,
            traffic_percent,
            __import__("json").dumps(metadata or {}, default=str),
        )
        return experiment_id

    async def complete_experiment(
        self,
        experiment_id: str,
        *,
        outcome: str,
        metrics: dict[str, Any] | None = None,
    ) -> None:
        await self.postgres.execute(
            """
            update experiments
            set status = $2,
                outcome = $3,
                metrics = $4::jsonb,
                completed_at = now()
            where experiment_id = $1
            """,
            experiment_id,
            "completed",
            outcome,
            __import__("json").dumps(metrics or {}, default=str),
        )

    async def active_shadow(self, workflow_id: str) -> dict[str, Any] | None:
        row = await self.postgres.fetchrow(
            """
            select experiment_id, version, traffic_percent, mode
            from experiments
            where subject_type = 'workflow' and subject_id = $1
              and mode = 'shadow' and status = 'running'
            order by started_at desc
            limit 1
            """,
            workflow_id,
        )
        return dict(row) if row else None
