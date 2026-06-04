from __future__ import annotations

from fastapi import APIRouter

from app import prompt_router
from app.routing_policy import load_policy

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


@router.get("/routing/policy")
async def routing_policy_get(reload: bool = False):
    """Aktualna polityka ingress (YAML + domyślne)."""
    return load_policy(reload=reload).to_dict()
