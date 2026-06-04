from __future__ import annotations

from fastapi import APIRouter, Request

router = APIRouter()


@router.get("")
async def catalog_index(request: Request):
    catalog = request.app.state.catalog
    return catalog.index


@router.get("/graph")
async def catalog_graph(request: Request):
    return request.app.state.catalog.as_graph()


@router.get("/domains")
async def catalog_domains(request: Request):
    return request.app.state.catalog.domains


@router.get("/events")
async def catalog_events(request: Request):
    return {"events": request.app.state.catalog.list_events()}


@router.get("/capabilities")
async def catalog_capabilities(request: Request):
    return request.app.state.catalog.capabilities


@router.get("/services")
async def catalog_services(request: Request):
    return request.app.state.catalog.services


@router.get("/policies")
async def catalog_policies(request: Request):
    return request.app.state.catalog.policies
