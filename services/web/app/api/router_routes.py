from __future__ import annotations

from fastapi import APIRouter

from app import prompt_router

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
