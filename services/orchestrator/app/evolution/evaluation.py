from __future__ import annotations

from datetime import datetime, timezone
from typing import Any


class EvaluationEngine:
    """Pętla oceny skutków — metryki jakości ewolucji i runtime."""

    def __init__(self, postgres: Any) -> None:
        self.postgres = postgres

    async def record_task_outcome(
        self,
        *,
        task_id: str,
        workflow_id: str | None,
        agent_id: str | None,
        success: bool,
        duration_ms: int | None = None,
        human_takeover: bool = False,
    ) -> None:
        subject_type = "workflow" if workflow_id else "task"
        subject_id = workflow_id or task_id
        await self._upsert_metrics(
            subject_type=subject_type,
            subject_id=subject_id,
            success=success,
            duration_ms=duration_ms,
            human_takeover=human_takeover,
        )
        if agent_id:
            await self._upsert_metrics(
                subject_type="agent",
                subject_id=agent_id,
                success=success,
                duration_ms=duration_ms,
                human_takeover=human_takeover,
            )

    async def _upsert_metrics(
        self,
        *,
        subject_type: str,
        subject_id: str,
        success: bool,
        duration_ms: int | None,
        human_takeover: bool,
    ) -> None:
        now = datetime.now(timezone.utc)
        row = await self.postgres.fetchrow(
            """
            select sample_count, success_count, failure_count,
                   retry_count, human_takeover_count, total_duration_ms
            from evolution_metrics
            where subject_type = $1 and subject_id = $2
              and window_start <= $3 and window_end >= $3
            """,
            subject_type,
            subject_id,
            now,
        )
        if row:
            sample = int(row["sample_count"]) + 1
            success_count = int(row["success_count"]) + (1 if success else 0)
            failure_count = int(row["failure_count"]) + (0 if success else 1)
            retry_count = int(row["retry_count"])
            takeover_count = int(row["human_takeover_count"]) + (
                1 if human_takeover else 0
            )
            total_ms = int(row["total_duration_ms"] or 0) + (duration_ms or 0)
            await self.postgres.execute(
                """
                update evolution_metrics
                set sample_count = $3,
                    success_count = $4,
                    failure_count = $5,
                    human_takeover_count = $6,
                    total_duration_ms = $7,
                    success_rate = $4::float / nullif($3, 0),
                    human_takeover_rate = $6::float / nullif($3, 0),
                    median_duration_ms = $7 / nullif($3, 0),
                    updated_at = $8
                where subject_type = $1 and subject_id = $2
                  and window_start <= $8 and window_end >= $8
                """,
                subject_type,
                subject_id,
                sample,
                success_count,
                failure_count,
                takeover_count,
                total_ms,
                now,
            )
            return

        await self.postgres.execute(
            """
            insert into evolution_metrics (
              subject_type, subject_id, window_start, window_end,
              sample_count, success_count, failure_count, retry_count,
              human_takeover_count, total_duration_ms, success_rate,
              human_takeover_rate, median_duration_ms, rollback_count, updated_at
            )
            values ($1, $2, date_trunc('day', $3), date_trunc('day', $3) + interval '1 day',
                    1, $4, $5, 0, $6, $7, $8, $9, $7, 0, $3)
            """,
            subject_type,
            subject_id,
            now,
            1 if success else 0,
            0 if success else 1,
            1 if human_takeover else 0,
            duration_ms or 0,
            1.0 if success else 0.0,
            1.0 if human_takeover else 0.0,
        )

    async def should_auto_rollback(self, subject_type: str, subject_id: str) -> bool:
        row = await self.postgres.fetchrow(
            """
            select success_rate, human_takeover_rate, sample_count
            from evolution_metrics
            where subject_type = $1 and subject_id = $2
            order by updated_at desc
            limit 1
            """,
            subject_type,
            subject_id,
        )
        if not row:
            return False
        thresholds = {
            "max_failure_rate": 0.15,
            "max_human_takeover_rate": 0.25,
            "min_samples": 10,
        }
        if int(row["sample_count"]) < thresholds["min_samples"]:
            return False
        failure_rate = 1.0 - float(row["success_rate"] or 0)
        if failure_rate > thresholds["max_failure_rate"]:
            return True
        if float(row["human_takeover_rate"] or 0) > thresholds["max_human_takeover_rate"]:
            return True
        return False
