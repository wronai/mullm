from __future__ import annotations

from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel, Field

from app.access.uri import build_uri, parse_uri

router = APIRouter()


class RegisterResourceCommand(BaseModel):
    uri: str
    name: str
    classification: str = "document"
    metadata: dict = Field(default_factory=dict)


class TransferResourceCommand(BaseModel):
    resource_id: str
    destination_uri: str
    requested_by: str = "api"


class ProbeUriCommand(BaseModel):
    uri: str


@router.post("/resources/register")
async def register_resource(command: RegisterResourceCommand, request: Request):
    try:
        parsed = parse_uri(command.uri)
        result = await request.app.state.command_bus.handle(
            command_type="RegisterResource",
            data={
                **command.model_dump(),
                "adapter": parsed.adapter,
            },
        )
        return {"result": result}
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.post("/resources/transfer")
async def transfer_resource(command: TransferResourceCommand, request: Request):
    try:
        result = await request.app.state.command_bus.handle(
            command_type="RequestTransfer",
            data=command.model_dump(),
        )
        return {"result": result}
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.post("/probe")
async def probe_uri(command: ProbeUriCommand, request: Request):
    try:
        return await request.app.state.transport.probe(command.uri)
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.post("/fetch")
async def fetch_uri(command: ProbeUriCommand, request: Request):
    try:
        return await request.app.state.transport.fetch(command.uri)
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.get("/resources")
async def list_resources(request: Request, limit: int = 100):
    rows = await request.app.state.postgres.fetch(
        """
        select resource_id, uri, name, adapter, classification, status, updated_at
        from resource_registry
        order by updated_at desc
        limit $1
        """,
        limit,
    )
    return {"items": [dict(r) for r in rows]}


@router.get("/uri/build")
async def build_resource_uri(adapter: str, path: str):
    return {"uri": build_uri(adapter, path)}
