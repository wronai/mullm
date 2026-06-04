from __future__ import annotations

from typing import Any

from app.evolution.catalog import ArchitectureCatalog


class PolicyViolation(Exception):
    def __init__(self, rule: str, message: str, *, details: dict[str, Any] | None = None):
        self.rule = rule
        self.details = details or {}
        super().__init__(message)


class PolicyEngine:
    """Reguły first — AI proponuje tylko w granicach polityk z katalogu."""

    def __init__(self, catalog: ArchitectureCatalog | None = None) -> None:
        self.catalog = catalog or ArchitectureCatalog()

    def rule_for(self, command_type: str) -> dict[str, Any]:
        return self.catalog.policies.get("rules", {}).get(command_type, {})

    def validate_command(
        self,
        command_type: str,
        data: dict[str, Any],
        *,
        environment: str = "dev",
    ) -> None:
        rule = self.rule_for(command_type)
        if not rule:
            return

        allowed = rule.get("allowed_environments")
        if allowed and environment not in allowed:
            raise PolicyViolation(
                command_type,
                f"Command {command_type} not allowed in environment {environment}",
                details={"allowed": allowed},
            )

        if rule.get("requires_manifest"):
            manifest = data.get("manifest") or {}
            missing = [
                field
                for field in rule.get("required_manifest_fields", [])
                if field not in manifest
            ]
            if missing:
                raise PolicyViolation(
                    command_type,
                    f"Plugin manifest missing fields: {', '.join(missing)}",
                    details={"missing": missing},
                )

        max_risk = rule.get("max_auto_risk")
        if max_risk and not data.get("approval_id") and not data.get("skip_approval"):
            manifest = data.get("manifest") or {}
            risk_order = ["low", "medium", "high", "critical"]
            manifest_risk = manifest.get("risk_level", "medium")
            if risk_order.index(manifest_risk) > risk_order.index(max_risk):
                raise PolicyViolation(
                    command_type,
                    f"Risk level {manifest_risk} exceeds auto threshold {max_risk}",
                )

    async def validate_activation_metrics(
        self,
        postgres: Any,
        command_type: str,
        target_id: str,
    ) -> None:
        """Sprawdza min_success_rate przed aktywacją workflow."""
        rule = self.rule_for(command_type)
        min_rate = rule.get("min_success_rate")
        if min_rate is None:
            return
        if postgres is None:
            return

        row = await postgres.fetchrow(
            """
            select success_rate, sample_count
            from evolution_metrics
            where subject_type = 'workflow' and subject_id = $1
            order by window_end desc
            limit 1
            """,
            target_id,
        )
        if not row or "sample_count" not in row:
            return
        if int(row["sample_count"]) < int(
            self.catalog.policies.get("experiment_thresholds", {}).get("min_samples", 10)
        ):
            return
        if float(row["success_rate"]) < float(min_rate):
            raise PolicyViolation(
                command_type,
                f"Workflow {target_id} success_rate {row['success_rate']} below {min_rate}",
                details={"metrics": dict(row)},
            )
