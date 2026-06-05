from __future__ import annotations

from fastapi import APIRouter

from app import prompt_router
from app import routing_trace
from app.routing_policy import load_policy
from app.routing_schemas import schemas_bundle
from app.ticket_schemas import schemas_bundle as ticket_schemas_bundle
from app.workspace import get_session

router = APIRouter()


@router.get("/router/decide")
async def router_decide(
    message: str,
    mode: str = "discuss",
    use_rag: bool = True,
):
    """
    Podgląd trasy promptu (debug): reguły lub LLM (PROMPT_ROUTER_MODE).
    Nie wykonuje akcji — tylko decyzja gdzie poszedłby request.
    """
    decision = await prompt_router.decide_route(
        message,
        chat_mode=mode,
        use_rag=use_rag,
    )
    return decision.to_dict()


@router.get("/routing/schemas")
async def routing_schemas_get():
    """JSON Schema (Pydantic) granic routingu: nlp2cmd, OpenRouter, agregat Mullm."""
    return schemas_bundle()


@router.get("/tickets/schemas")
async def ticket_schemas_get():
    """Standardy ticketów Mullm + mapowanie na planfile (kolejki)."""
    return ticket_schemas_bundle()


@router.get("/routing/policy")
async def routing_policy_get(reload: bool = False):
    """Aktualna polityka ingress (YAML + domyślne)."""
    return load_policy(reload=reload).to_dict()


@router.get("/routing/explain")
async def routing_explain(
    message: str,
    mode: str = "discuss",
    use_rag: bool = True,
    session_id: str | None = None,
):
    """
    Drzewo decyzji ingress + kaskada reguł (bez wykonania handlerów).
    Użyj do podglądu np. „lista plikow usera” i dopasowania user_expectations.
    """
    return await routing_trace.explain_pipeline(
        message,
        chat_mode=mode,
        use_rag=use_rag,
        session_id=session_id,
    )


@router.get("/routing/trace")
async def routing_trace_last(session_id: str):
    """Ostatnie drzewo decyzji z sesji (event RoutingDecisionTree lub routing w historii)."""
    session = get_session(session_id)
    if not session:
        return {"session_id": session_id, "decision_tree": None}
    for event in reversed(session.events):
        if event.get("type") == "RoutingDecisionTree" and event.get("decision_tree"):
            return {"session_id": session_id, "decision_tree": event["decision_tree"]}
    from app import chat as chat_service

    for msg in reversed(chat_service.get_history(session_id)):
        if msg.get("role") == "assistant" and (msg.get("routing") or {}).get("decision_tree"):
            return {
                "session_id": session_id,
                "decision_tree": msg["routing"]["decision_tree"],
            }
    return {"session_id": session_id, "decision_tree": None}
