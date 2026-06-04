from __future__ import annotations

from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel, Field

router = APIRouter()


class ProposeChangeCommand(BaseModel):
    change_type: str
    target_id: str
    hypothesis: str = ""
    proposed_by: str
    payload: dict = Field(default_factory=dict)


class ShadowWorkflowCommand(BaseModel):
    workflow_id: str
    traffic_percent: int = 10


@router.get("/metrics")
async def evolution_metrics(
    request: Request,
    subject_type: str | None = None,
    subject_id: str | None = None,
    limit: int = 50,
):
    db = request.app.state.postgres
    if subject_type and subject_id:
        rows = await db.fetch(
            """
            select * from evolution_metrics
            where subject_type = $1 and subject_id = $2
            order by updated_at desc
            limit $3
            """,
            subject_type,
            subject_id,
            limit,
        )
    else:
        rows = await db.fetch(
            """
            select * from evolution_metrics
            order by updated_at desc
            limit $1
            """,
            limit,
        )
    return {"items": [dict(r) for r in rows]}


@router.get("/experiments")
async def list_experiments(request: Request, status: str | None = None, limit: int = 50):
    db = request.app.state.postgres
    if status:
        rows = await db.fetch(
            """
            select * from experiments where status = $1
            order by started_at desc limit $2
            """,
            status,
            limit,
        )
    else:
        rows = await db.fetch(
            "select * from experiments order by started_at desc limit $1",
            limit,
        )
    return {"items": [dict(r) for r in rows]}


@router.get("/capabilities/registry")
async def capability_registry(request: Request, limit: int = 100):
    rows = await request.app.state.postgres.fetch(
        "select * from capability_registry order by capability_id asc limit $1",
        limit,
    )
    return {"items": [dict(r) for r in rows]}


@router.post("/changes/propose")
async def propose_change(command: ProposeChangeCommand, request: Request):
    try:
        result = await request.app.state.command_bus.handle(
            command_type="ProposeChange",
            data=command.model_dump(),
        )
        return {"result": result}
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.post("/workflows/shadow")
async def shadow_workflow(command: ShadowWorkflowCommand, request: Request):
    try:
        result = await request.app.state.command_bus.handle(
            command_type="ShadowWorkflowVersion",
            data=command.model_dump(),
        )
        return {"result": result}
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
