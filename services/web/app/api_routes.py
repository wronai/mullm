from __future__ import annotations

from fastapi import APIRouter

from app.api.access_routes import router as access_router
from app.api.agents_routes import router as agents_router
from app.api.chat_routes import router as chat_router
from app.api.feedback_routes import router as feedback_router
from app.api.router_routes import router as prompt_router_api
from app.api.config import ORCHESTRATOR_URL, PROJECTOR_URL
from app.api.task_routes import router as task_router
from app.api.workroom_routes import router as workroom_router
from app.api.workspace_routes import router as workspace_router

router = APIRouter()
router.include_router(chat_router)
router.include_router(task_router)
router.include_router(workspace_router)
router.include_router(workroom_router)
router.include_router(access_router)
router.include_router(prompt_router_api)
router.include_router(feedback_router)
router.include_router(agents_router)

__all__ = ["ORCHESTRATOR_URL", "PROJECTOR_URL", "router"]
