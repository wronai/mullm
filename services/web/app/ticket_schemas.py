"""
Standardy ticketów Mullm — trzy kolejki i mapowanie na planfile (Koru).

1. execution — orchestrator EventStore (shell_agent / NATS)
2. improvement — routing feedback (JSONL)
3. workflow — nlp2dsl conversation (in_progress → ready)

Planfile może zastąpić (2) i część (3); (1) wymaga adaptera executor=shell + mostu do NATS lub koru --queue.
"""

from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, Field

SCHEMA_BUNDLE_ID = "mullm.tickets.schemas.v1"

TicketKind = Literal["execution", "improvement", "workflow"]
PlanfileExecutorKind = Literal["human", "shell", "mcp", "api", "llm"]


class MullmTicketRef(BaseModel):
    """Wspólny nagłówek odniesienia (URI + źródło)."""

    schema_id: str
    kind: TicketKind
    ticket_id: str
    status: str
    uri: str = ""
    source_system: str = "mullm"
    planfile_id: str | None = None


class ExecutionTicketCreate(BaseModel):
    """POST orchestrator /api/commands/tasks (CreateTask)."""

    schema_id: str = Field(default="mullm.ticket.execution.v1")
    title: str
    description: str = ""
    shell_command: str | None = None
    agent_id: str | None = None
    priority: str = "medium"
    auto_assign: bool = True
    wait_for_confirmation: bool = False
    required_capabilities: list[str] = Field(default_factory=lambda: ["shell"])
    session_id: str | None = None
    route: str | None = None


class ImprovementTicket(BaseModel):
    """mullm.routing.improvement_ticket.v1 (routing feedback)."""

    schema_id: str = Field(default="mullm.routing.improvement_ticket.v1")
    ticket_id: str
    status: str = "open"
    session_id: str
    turn_id: str
    rating: str
    user_message: str = ""
    actual_route: str | None = None
    expected_route: str | None = None
    expected_reply_hint: str = ""
    improvement_notes: str = ""
    tags: list[str] = Field(default_factory=list)
    suggested_actions: list[str] = Field(default_factory=list)
    created_at: str = ""

    def planfile_title(self) -> str:
        exp = self.expected_route or "?"
        act = self.actual_route or "?"
        return f"[Mullm routing] {act} → {exp}"

    def planfile_description(self) -> str:
        lines = [
            f"Oczekiwana trasa: `{self.expected_route}`",
            f"Faktyczna trasa: `{self.actual_route}`",
            f"Wiadomość: {self.user_message[:500]}",
        ]
        if self.expected_reply_hint:
            lines.append(f"Oczekiwana odpowiedź: {self.expected_reply_hint}")
        if self.improvement_notes:
            lines.append(f"Notatki: {self.improvement_notes}")
        if self.suggested_actions:
            lines.append("Sugerowane działania:")
            lines.extend(f"- {a}" for a in self.suggested_actions)
        return "\n".join(lines)

    def planfile_labels(self) -> list[str]:
        out = ["mullm", "routing-improvement", f"rating:{self.rating}"]
        if self.expected_route:
            out.append(f"expected:{self.expected_route}")
        if self.actual_route:
            out.append(f"actual:{self.actual_route}")
        out.append(f"dedupe:mullm-routing-{self.turn_id}")
        return out


class WorkflowTicketRef(BaseModel):
    """nlp2dsl — rozmowa workflow (nie UUID orchestratora)."""

    schema_id: str = Field(default="mullm.ticket.workflow.v1")
    conversation_id: str
    status: Literal["in_progress", "ready", "done"] = "in_progress"
    session_id: str = ""
    missing_fields: list[str] = Field(default_factory=list)


def schemas_bundle() -> dict[str, Any]:
    return {
        "bundle_id": SCHEMA_BUNDLE_ID,
        "kinds": {
            "execution": ExecutionTicketCreate.model_json_schema(),
            "improvement": ImprovementTicket.model_json_schema(),
            "workflow": WorkflowTicketRef.model_json_schema(),
        },
        "planfile_mapping": {
            "improvement": {
                "executor_kind": "human",
                "executor_mode": "interactive",
                "queue": "mullm-routing",
                "source": "mullm.routing",
            },
            "execution_shell": {
                "executor_kind": "shell",
                "executor_mode": "automatic",
                "queue": "mullm-shell",
                "source": "mullm.execution",
                "note": "Wymaga adaptera NATS/shell-agent lub koru --queue",
            },
            "workflow": {
                "executor_kind": "human",
                "executor_mode": "interactive",
                "queue": "mullm-workflow",
                "source": "mullm.nlp2dsl",
            },
        },
        "uris": {
            "execution": "mullm://ticket/{task_id}",
            "improvement": "mullm://routing-improvement/{ticket_id}",
            "workflow": "mullm://nlp2dsl/{conversation_id}",
        },
    }
