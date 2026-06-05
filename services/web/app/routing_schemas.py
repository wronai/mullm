"""
Schematy (Pydantic) dla granic routingu — analiza NL przez zewnętrzne biblioteki.

- nlp2cmd.service.QueryRequest / QueryResponse (HTTP POST /query)
- OpenRouter — klasyfikator tras (JSON)
- Mullm — agregat analizy do decision_tree / policy_flags
"""

from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, Field, ValidationError

SCHEMA_BUNDLE_ID = "mullm.routing.schemas.v1"

RouteKindLiteral = Literal[
    "mullm_file_list",
    "mullm_shell",
    "nlp2cmd_shell",
    "nlp2dsl",
    "rag",
    "workroom_hint",
    "unknown",
]

ListScopeLiteral = Literal["all", "user", "system", "session", "rag"]


class Nlp2CmdQueryRequest(BaseModel):
    """Zgodne z nlp2cmd.service.QueryRequest."""

    schema_id: str = Field(default="nlp2cmd.service.QueryRequest.v1")
    query: str = Field(..., min_length=1)
    dsl: str = Field(default="auto", description="DSL nlp2cmd (auto = shell + browser/canvas)")
    explain: bool = Field(default=False, description="Dołącz explanation w odpowiedzi")
    execute: bool = Field(default=False, description="Mullm nigdy nie wykonuje — tylko analiza")


class Nlp2CmdQueryResponse(BaseModel):
    """Zgodne z nlp2cmd.service.QueryResponse."""

    schema_id: str = Field(default="nlp2cmd.service.QueryResponse.v1")
    success: bool
    command: str | None = None
    explanation: str | None = None
    confidence: float | None = Field(default=None, ge=0.0, le=1.0)
    domain: str | None = None
    intent: str | None = None
    entities: dict[str, Any] | None = None
    metadata: dict[str, Any] | None = None
    errors: list[Any] | None = None
    warnings: list[Any] | None = None
    execution_result: dict[str, Any] | None = None

    model_config = {"extra": "allow"}

    @property
    def command_text(self) -> str:
        return (self.command or "").strip()


class LlmRouteClassifierOutput(BaseModel):
    """JSON z OpenRouter (PROMPT_ROUTER_MODE llm/hybrid)."""

    schema_id: str = Field(default="mullm.router.llm_classifier.v1")
    route: RouteKindLiteral
    intent: str = Field(min_length=1, max_length=64)
    confidence: float = Field(ge=0.0, le=1.0)
    list_scope: ListScopeLiteral | None = None
    reason_codes: list[str] = Field(default_factory=list)



class NlpCommandAnalysis(BaseModel):
    """Walidowany wynik analizy NL (nlp2cmd) używany przez router Mullm."""

    schema_id: str = Field(default="mullm.routing.nlp_analysis.v1")
    source: Literal["nlp2cmd"] = "nlp2cmd"
    request: Nlp2CmdQueryRequest
    response: Nlp2CmdQueryResponse

    def to_shell_translation(self) -> Any:
        from app.agent_plugins.protocol import ShellTranslation

        return ShellTranslation.from_validated_analysis(self)

    def to_policy_flags(self) -> dict[str, Any]:
        return {
            "nlp_analysis_schema": self.schema_id,
            "nlp2cmd_translation": {
                "command": self.response.command_text,
                "confidence": float(self.response.confidence or 0.0),
                "domain": self.response.domain or "",
                "intent": self.response.intent or "",
            },
            "nlp2cmd_analysis": self.model_dump(mode="json"),
        }


def routing_analysis_use_explain() -> bool:
    import os

    return os.getenv("MULLM_ROUTING_NLP2CMD_EXPLAIN", "1").strip().lower() not in (
        "0",
        "false",
        "no",
    )


def build_nlp2cmd_request(message: str, *, dsl: str = "auto") -> Nlp2CmdQueryRequest:
    return Nlp2CmdQueryRequest(
        query=message.strip(),
        dsl=dsl,
        explain=routing_analysis_use_explain(),
        execute=False,
    )


def parse_nlp2cmd_response(data: Any) -> Nlp2CmdQueryResponse | None:
    if not isinstance(data, dict):
        return None
    try:
        return Nlp2CmdQueryResponse.model_validate(data)
    except ValidationError:
        return None


def parse_llm_classifier(data: Any) -> LlmRouteClassifierOutput | None:
    if not isinstance(data, dict):
        return None
    try:
        return LlmRouteClassifierOutput.model_validate(data)
    except ValidationError:
        return None


def llm_classifier_json_schema() -> dict[str, Any]:
    return LlmRouteClassifierOutput.model_json_schema()


def llm_system_prompt_with_schema() -> str:
    """Prompt LLM z osadzonym JSON Schema (OpenRouter / lokalny klasyfikator)."""
    import json

    schema = llm_classifier_json_schema()
    return (
        "Klasyfikuj intencję użytkownika Mullm. Odpowiedz WYŁĄCZNIE jednym obiektem JSON "
        "zgodnym ze schematem (bez markdown):\n"
        f"{json.dumps(schema, ensure_ascii=False)}\n"
        "Pola wymagane: route, intent, confidence, reason_codes."
    )


def schemas_bundle() -> dict[str, Any]:
    """Eksport schematów dla API / dokumentacji integracji."""
    return {
        "bundle_id": SCHEMA_BUNDLE_ID,
        "nlp2cmd": {
            "request": Nlp2CmdQueryRequest.model_json_schema(),
            "response": Nlp2CmdQueryResponse.model_json_schema(),
            "upstream": "nlp2cmd.service@QueryRequest|QueryResponse",
        },
        "openrouter_classifier": {
            "output": llm_classifier_json_schema(),
            "upstream": "mullm.router.llm_classifier.v1",
        },
        "mullm": {
            "nlp_analysis": NlpCommandAnalysis.model_json_schema(),
        },
    }
