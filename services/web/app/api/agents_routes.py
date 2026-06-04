from __future__ import annotations

from fastapi import APIRouter

from app.agent_plugins import agents_status

router = APIRouter()


@router.get("/agents/status")
async def agents_status_get():
    """Health pluginów agentów (nlp2cmd, nlp2dsl, …)."""
    return {"agents": await agents_status()}
